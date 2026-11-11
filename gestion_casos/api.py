import json
import logging
import os
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import connection, transaction
from django.db.models import Case as ConditionalCase, IntegerField, OuterRef, Q, Subquery, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.validators import validate_email
from django.utils import timezone
from django.utils.dateparse import parse_date
from resend.exceptions import ResendError
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .controllers.dashboard_controller import obtener_datos_dashboard
from .services.caso_service import crear_caso_persistido
from .controllers.notification_controller import (
    _mensaje_notificacion_seguro,
    _regla_notificacion_operativa,
)
from .services.seguimiento_service import obtener_filas_seguimiento
from .services.estadistica_service import obtener_datos_estadisticas
from .controllers.auth_casos_controller import (
    caso_visible_para_curso,
    puede_editar_caso,
    puede_eliminar_caso,
)
from .controllers.auth_controller import solicitar_recuperacion_contrasena
from .reglamento import evaluar_reglas_para_caso
from .models import (
    AccionSeguimiento,
    Caso,
    Curso,
    Estudiante,
    HistorialAccionSeguimiento,
    HistorialNotificacion,
    HistorialSeguimientoCaso,
    HistorialUsuario,
    Involucran,
    Lugar,
    Notificacion,
    ProfesorJefe,
    SeguimientoCaso,
    SolicitudCaso,
    Usuario,
)
from .permissions import (
    ROLES_APROBACION_CASOS,
    ROLES_GESTION_SEGUIMIENTO,
    ROLES_SEGUIMIENTO,
)

logger = logging.getLogger(__name__)


class TokenObtainView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía correo y contraseña en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correo = request.data.get('correo', '')
        contrasena = request.data.get('contrasena', '')
        if not isinstance(correo, str) or not isinstance(contrasena, str):
            return Response(
                {'detail': 'Envía correo y contraseña en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = (
            Usuario.objects.select_related('rol')
            .filter(usuario_correo=correo.strip())
            .first()
        )
        if usuario is None:
            return Response(
                {'detail': 'Usuario no existente.', 'code': 'user_not_found'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if usuario.usuario_bloqueado:
            return Response(
                {'detail': 'Cuenta bloqueada.', 'code': 'account_locked'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not check_password(contrasena, usuario.usuario_contrasena):
            usuario.usuario_intentos_fallidos += 1
            update_fields = ['usuario_intentos_fallidos']
            if usuario.usuario_intentos_fallidos >= 5:
                usuario.usuario_bloqueado = True
                update_fields.append('usuario_bloqueado')
            usuario.save(update_fields=update_fields)
            if usuario.usuario_bloqueado:
                return Response(
                    {'detail': 'Cuenta bloqueada.', 'code': 'account_locked'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {'detail': 'Contraseña incorrecta.', 'code': 'invalid_password'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not usuario.usuario_activo:
            return Response(
                {'detail': 'La cuenta está inactiva.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if usuario.usuario_primer_ingreso:
            return Response(
                {
                    'detail': 'Debes cambiar tu contraseña antes de continuar.',
                    'code': 'password_change_required',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario.usuario_intentos_fallidos = 0
        usuario.usuario_ultimo_acceso = timezone.now()
        usuario.save(
            update_fields=['usuario_intentos_fallidos', 'usuario_ultimo_acceso']
        )

        refresh = RefreshToken()
        refresh[api_settings.USER_ID_CLAIM] = usuario.pk
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'token_type': 'Bearer',
        })

class PasswordRecoveryAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía un correo válido en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correo = request.data.get('correo', '')
        if not isinstance(correo, str) or not correo.strip():
            return Response(
                {'detail': 'El correo es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correo = correo.strip()
        try:
            validate_email(correo)
        except ValidationError:
            return Response(
                {'detail': 'Ingresa una dirección de correo válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            solicitar_recuperacion_contrasena(correo)
        except ResendError:
            logger.exception('Falló el envío del correo de recuperación.')
            return Response(
                {'detail': 'No se pudo enviar el correo. Inténtalo más tarde o contacta al administrador.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'mensaje': 'Si el correo está registrado y activo, recibirás una contraseña temporal.'
        })


class RequiredPasswordChangeAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía los datos en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correo = request.data.get('correo', '')
        contrasena_actual = request.data.get('contrasena_actual', '')
        contrasena_nueva = request.data.get('contrasena_nueva', '')
        if not all(isinstance(value, str) for value in (correo, contrasena_actual, contrasena_nueva)):
            return Response(
                {'detail': 'Los datos enviados no son válidos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(contrasena_nueva) < 12:
            return Response(
                {'detail': 'La nueva contraseña debe tener al menos 12 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = Usuario.objects.filter(
            usuario_correo=correo.strip(),
            usuario_activo=True,
            usuario_bloqueado=False,
            usuario_primer_ingreso=True,
        ).first()
        if (
            usuario is None
            or not check_password(contrasena_actual, usuario.usuario_contrasena)
            or contrasena_actual == contrasena_nueva
        ):
            return Response(
                {'detail': 'No se pudo validar la contraseña temporal.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.usuario_contrasena = make_password(contrasena_nueva)
        usuario.usuario_primer_ingreso = False
        usuario.usuario_intentos_fallidos = 0
        usuario.save(update_fields=[
            'usuario_contrasena',
            'usuario_primer_ingreso',
            'usuario_intentos_fallidos',
        ])
        return Response({'mensaje': 'Contraseña actualizada. Inicia sesión con tu nueva contraseña.'})


class TokenRefreshView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía el token refresh en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_token = request.data.get('refresh', '')
        if not isinstance(raw_token, str) or not raw_token:
            return Response(
                {'detail': 'El campo refresh es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(raw_token)
            user_id = refresh.get(api_settings.USER_ID_CLAIM)
            if user_id is None:
                raise TokenError('El token no identifica a un usuario.')
            usuario = Usuario.objects.get(pk=user_id)
        except (TokenError, Usuario.DoesNotExist, TypeError, ValueError):
            return Response(
                {'detail': 'El token refresh no es válido.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if (
            not usuario.usuario_activo
            or usuario.usuario_bloqueado
            or usuario.usuario_primer_ingreso
        ):
            return Response(
                {'detail': 'La cuenta no puede renovar tokens.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({'access': str(refresh.access_token), 'token_type': 'Bearer'})


class PerfilAPIView(APIView):
    def get(self, request):
        usuario = request.user
        return Response({
            'id': usuario.pk,
            'nombre': usuario.usuario_nombre,
            'apellido_paterno': usuario.usuario_apaterno,
            'apellido_materno': usuario.usuario_amaterno,
            'correo': usuario.usuario_correo,
            'rol': usuario.rol.rol_nombre,
        })

    def patch(self, request):
        usuario = request.user
        datos = request.data
        if not isinstance(datos, dict):
            return Response(
                {'detail': 'Envía los datos del perfil en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nombre = datos.get('nombre', '')
        apaterno = datos.get('apellido_paterno', '')
        amaterno = datos.get('apellido_materno', '')
        correo = datos.get('correo', '')
        if not all(
            isinstance(value, str) and value.strip()
            for value in (nombre, apaterno, amaterno, correo)
        ):
            return Response(
                {'detail': 'Completa todos los datos personales.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nombre, apaterno, amaterno, correo = (
            value.strip() for value in (nombre, apaterno, amaterno, correo)
        )
        try:
            validate_email(correo)
        except ValidationError:
            return Response(
                {'detail': 'Ingresa un correo electrónico válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Usuario.objects.filter(
            usuario_correo__iexact=correo,
        ).exclude(pk=usuario.pk).exists():
            return Response(
                {'detail': 'Ese correo ya está asociado a otra cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.usuario_nombre = nombre
        usuario.usuario_apaterno = apaterno
        usuario.usuario_amaterno = amaterno
        usuario.usuario_correo = correo
        usuario.save(update_fields=[
            'usuario_nombre',
            'usuario_apaterno',
            'usuario_amaterno',
            'usuario_correo',
        ])
        return Response({
            'id': usuario.pk,
            'nombre': usuario.usuario_nombre,
            'apellido_paterno': usuario.usuario_apaterno,
            'apellido_materno': usuario.usuario_amaterno,
            'correo': usuario.usuario_correo,
            'rol': usuario.rol.rol_nombre,
        })

    def put(self, request):
        usuario = request.user
        datos = request.data
        current_password = datos.get('contrasena_actual', '')
        new_password = datos.get('contrasena_nueva', '')
        if not isinstance(current_password, str) or not isinstance(new_password, str):
            return Response(
                {'detail': 'Envía ambas contraseñas en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not check_password(current_password, usuario.usuario_contrasena):
            return Response(
                {'detail': 'La contraseña actual no es correcta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 12:
            return Response(
                {'detail': 'La nueva contraseña debe tener al menos 12 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.contrib.auth.hashers import make_password

        usuario.usuario_contrasena = make_password(new_password)
        usuario.usuario_primer_ingreso = False
        usuario.save(update_fields=[
            'usuario_contrasena',
            'usuario_primer_ingreso',
        ])
        return Response({'mensaje': 'La contraseña se cambió correctamente.'})


class DashboardAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.rol.rol_nombre == 'Profesor Jefe':
            return Response(
                {'detail': 'Tu rol no tiene acceso al panel general.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        datos = obtener_datos_dashboard(request)
        pagina = datos['pagina_casos']
        return Response({
            'metricas': {
                'total_casos': datos['total_casos'],
                'casos_leves': datos['casos_leves'],
                'casos_graves': datos['casos_graves'],
                'casos_gravisimas': datos['casos_gravisimas'],
            },
            'periodo': {
                'casos': datos['casos_periodo'],
                'curso_mas_incidentes': datos['curso_mas_incidentes'],
                'tipo_falta_frecuente': datos['tipo_falta_frecuente'],
                'zona_mas_conflictos': datos['zona_mas_conflictos'],
                'variacion': datos['variacion_periodo'],
                'zonas': datos['casos_por_zona'],
            },
            'casos': {
                'resultados': [
                    {
                        'id': caso['id'],
                        'titulo': caso['titulo'],
                        'fecha': caso['fecha'].isoformat() if caso['fecha'] else None,
                        'lugar': caso['lugar'],
                    }
                    for caso in datos['casos_recientes']
                ],
                'pagina': pagina.number,
                'total_paginas': pagina.paginator.num_pages,
                'total': pagina.paginator.count,
                'tiene_anterior': pagina.has_previous(),
                'tiene_siguiente': pagina.has_next(),
            },
        })


class HistorialCasosAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.rol.rol_nombre == 'Profesor Jefe':
            return Response(
                {'detail': 'Tu rol no tiene acceso al historial general de casos.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        busqueda = request.query_params.get('q', '').strip()
        curso_id = request.query_params.get('curso', '').strip()
        gravedad = request.query_params.get('gravedad', '').strip()
        estudiante_id = request.query_params.get('estudiante', '').strip()
        usuario_id = request.query_params.get('usuario', '').strip()
        fecha_desde_texto = request.query_params.get('fecha_desde', '').strip()
        fecha_hasta_texto = request.query_params.get('fecha_hasta', '').strip()
        fecha_desde = parse_date(fecha_desde_texto) if fecha_desde_texto else None
        fecha_hasta = parse_date(fecha_hasta_texto) if fecha_hasta_texto else None

        if fecha_desde_texto and fecha_desde is None:
            return Response(
                {'detail': 'La fecha desde no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if fecha_hasta_texto and fecha_hasta is None:
            return Response(
                {'detail': 'La fecha hasta no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return Response(
                {'detail': 'La fecha desde debe ser anterior o igual a la fecha hasta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        curso_id_numero = None
        if curso_id:
            if not curso_id.isdecimal() or len(curso_id) > 10:
                return Response(
                    {'detail': 'El curso seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            curso_id_numero = int(curso_id)
            if not 1 <= curso_id_numero <= 2147483647:
                return Response(
                    {'detail': 'El curso seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if gravedad and gravedad not in ('Leve', 'Grave', 'Gravísima'):
            return Response(
                {'detail': 'La clasificación de gravedad no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        estudiante_id_numero = None
        if estudiante_id:
            if not estudiante_id.isdecimal() or len(estudiante_id) > 10:
                return Response(
                    {'detail': 'El estudiante seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            estudiante_id_numero = int(estudiante_id)
            if not 1 <= estudiante_id_numero <= 2147483647:
                return Response(
                    {'detail': 'El estudiante seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        usuario_id_numero = None
        if usuario_id:
            if not usuario_id.isdecimal() or len(usuario_id) > 10:
                return Response(
                    {'detail': 'El funcionario seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            usuario_id_numero = int(usuario_id)
            if not 1 <= usuario_id_numero <= 2147483647:
                return Response(
                    {'detail': 'El funcionario seleccionado no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        casos = Caso.objects.select_related('lugar').order_by(
            '-caso_fecha',
            '-caso_id',
        )
        if busqueda:
            casos = casos.filter(caso_descripcion__icontains=busqueda)
        if curso_id_numero:
            casos = casos.filter(estudiantes__curso_id=curso_id_numero).distinct()
        if estudiante_id_numero:
            casos = casos.filter(estudiantes__pk=estudiante_id_numero).distinct()
            tipo_falta = Involucran.objects.filter(
                caso_id=OuterRef('caso_id'),
                estudiante_id=estudiante_id_numero,
            ).values('tipo_falta')[:1]
            casos = casos.annotate(
                estudiante_tipo_falta=Subquery(tipo_falta),
            ).annotate(
                orden_tipo_falta=ConditionalCase(
                    When(estudiante_tipo_falta='Leve', then=0),
                    When(estudiante_tipo_falta='Grave', then=1),
                    When(estudiante_tipo_falta='Gravísima', then=2),
                    default=3,
                    output_field=IntegerField(),
                ),
            ).order_by('orden_tipo_falta', '-caso_fecha', '-caso_id')
        if usuario_id_numero:
            casos = casos.filter(usuario_id=usuario_id_numero)
        if fecha_desde:
            casos = casos.filter(caso_fecha__gte=fecha_desde)
        if fecha_hasta:
            casos = casos.filter(caso_fecha__lte=fecha_hasta)
        if gravedad:
            ids_con_gravedad = Involucran.objects.filter(
                tipo_falta=gravedad,
            ).values_list('caso_id', flat=True)
            casos = casos.filter(caso_id__in=ids_con_gravedad)

        pagina = Paginator(casos, 10).get_page(request.query_params.get('pagina'))
        resultados = []
        rol_usuario = request.user.rol.rol_nombre
        ahora = timezone.now()
        for caso in pagina:
            descripcion = caso.caso_descripcion or ''
            titulo = 'Sin título'
            if descripcion.startswith('['):
                partes = descripcion.split('] - ', 1)
                if len(partes) == 2:
                    titulo = partes[0].replace('[', '')
                    descripcion = partes[1]
            else:
                titulo = descripcion[:40] + '...' if len(descripcion) > 40 else descripcion

            resultados.append({
                'id': caso.caso_id,
                'titulo': titulo,
                'descripcion': descripcion,
                'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
                'fecha': caso.caso_fecha.isoformat() if caso.caso_fecha else None,
                'usuario_id': caso.usuario_id,
                'puede_editar': puede_editar_caso(rol_usuario, caso, ahora),
                'puede_eliminar': puede_eliminar_caso(rol_usuario, caso, ahora),
            })

        return Response({
            'resultados': resultados,
            'pagina': pagina.number,
            'total_paginas': pagina.paginator.num_pages,
            'total': pagina.paginator.count,
            'tiene_anterior': pagina.has_previous(),
            'tiene_siguiente': pagina.has_next(),
            'cursos': [
                {
                    'id': curso.curso_id,
                    'nombre': f'{curso.curso_grado} {curso.curso_letra}',
                }
                for curso in Curso.objects.all().order_by('curso_grado', 'curso_letra')
            ],
            'mostrar_contador': rol_usuario in ('Administrador', 'Inspector', 'PConvivencia'),
        })


class CasoDetalleAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def _caso(self, caso_id):
        return get_object_or_404(
            Caso.objects.select_related('lugar', 'usuario'),
            pk=caso_id,
        )

    def _puede_ver(self, request, caso_id):
        if request.user.rol.rol_nombre != 'Profesor Jefe':
            return True
        profesor = ProfesorJefe.objects.select_related('curso').filter(
            usuario_id=request.user.pk,
        ).first()
        return bool(
            profesor
            and caso_visible_para_curso(caso_id, profesor.curso)
        )

    @staticmethod
    def _involucrados(caso_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.estudiante_id, e.estudiante_nombre,
                       e.estudiante_apaterno, e.estudiante_amaterno,
                       e.estudiante_numero_lista, e.curso_id,
                       cu.curso_grado, cu.curso_letra, i.tipo_falta
                FROM involucran i
                INNER JOIN estudiante e ON e.estudiante_id = i.estudiante_id
                INNER JOIN curso cu ON cu.curso_id = e.curso_id
                WHERE i.caso_id = %s
                ORDER BY e.estudiante_apaterno, e.estudiante_nombre
                """,
                [caso_id],
            )
            filas = cursor.fetchall()
        return [
            {
                'id': fila[0],
                'nombre': fila[1],
                'apellido_paterno': fila[2],
                'apellido_materno': fila[3],
                'numero_lista': fila[4],
                'curso_id': fila[5],
                'curso': f'{fila[6]} {fila[7]}',
                'tipo_falta': fila[8],
            }
            for fila in filas
        ]

    def get(self, request, caso_id):
        caso = self._caso(caso_id)
        if not self._puede_ver(request, caso_id):
            return Response(
                {'detail': 'Este caso no corresponde a estudiantes de tu curso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        texto = caso.caso_descripcion or ''
        titulo = 'Sin título'
        descripcion = texto
        if texto.startswith('[') and '] - ' in texto:
            titulo, descripcion = texto[1:].split('] - ', 1)
        elif texto:
            titulo = texto[:40] + ('...' if len(texto) > 40 else '')

        evidencia_url = ''
        if caso.evidencia:
            if default_storage.exists(caso.evidencia):
                evidencia_url = default_storage.url(caso.evidencia)
            else:
                evidencia_url = f'/media/{caso.evidencia.lstrip("/")}'

        rol = request.user.rol.rol_nombre
        puede_eliminar = puede_eliminar_caso(rol, caso)
        return Response({
            'id': caso.pk,
            'titulo': titulo,
            'descripcion': descripcion,
            'fecha': caso.caso_fecha.isoformat() if caso.caso_fecha else None,
            'lugar_id': caso.lugar_id,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
            'evidencia_url': evidencia_url,
            'creado_por': (
                f'{caso.usuario.usuario_nombre} {caso.usuario.usuario_apaterno}'
                if caso.usuario else 'Usuario eliminado'
            ),
            'estudiantes': self._involucrados(caso_id),
            'puede_editar': puede_editar_caso(rol, caso),
            'puede_eliminar': puede_eliminar,
            'lugares': [
                {'id': lugar.pk, 'nombre': lugar.lugar_nombre}
                for lugar in Lugar.objects.all().order_by('lugar_nombre')
            ],
            'cursos': [
                {
                    'id': curso.pk,
                    'nombre': f'{curso.curso_grado} {curso.curso_letra}',
                }
                for curso in Curso.objects.all().order_by(
                    'curso_grado', 'curso_letra',
                )
            ],
            'gravedades': [
                {'valor': valor, 'etiqueta': etiqueta}
                for valor, etiqueta in Involucran._meta.get_field(
                    'tipo_falta',
                ).choices
            ] if Involucran._meta.get_field('tipo_falta').choices else [
                {'valor': valor, 'etiqueta': valor}
                for valor in ('Leve', 'Grave', 'Gravísima')
            ],
        })

    def put(self, request, caso_id):
        caso = self._caso(caso_id)
        rol = request.user.rol.rol_nombre
        if not puede_editar_caso(rol, caso):
            return Response(
                {'detail': 'No tienes permiso para editar este caso o venció el plazo de 48 horas.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        datos = request.data
        if not isinstance(datos, dict):
            return Response(
                {'detail': 'Envía los datos del caso como un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        titulo = datos.get('titulo')
        descripcion = datos.get('descripcion')
        tipo_falta = datos.get('tipo_falta')
        estudiantes = datos.get('estudiantes')
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo.strip()) > 180:
            return Response(
                {'detail': 'El título es obligatorio y no debe superar 180 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(descripcion, str) or not descripcion.strip():
            return Response(
                {'detail': 'La descripción es obligatoria.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if tipo_falta not in ('Leve', 'Grave', 'Gravísima'):
            return Response(
                {'detail': 'Selecciona una clasificación de gravedad válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            lugar = Lugar.objects.get(pk=int(datos.get('lugar_id')))
        except (TypeError, ValueError, Lugar.DoesNotExist):
            return Response(
                {'detail': 'Selecciona un lugar válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(estudiantes, list) or not estudiantes:
            return Response(
                {'detail': 'El caso debe conservar al menos un estudiante involucrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        actuales = {
            item['id']: item for item in self._involucrados(caso_id)
        }
        ids = []
        for estudiante in estudiantes:
            if not isinstance(estudiante, dict):
                return Response(
                    {'detail': 'Los datos de los estudiantes no son válidos.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                estudiante_id = int(estudiante.get('id'))
                curso_id = int(estudiante.get('curso_id'))
            except (TypeError, ValueError):
                return Response(
                    {'detail': 'Selecciona estudiantes y cursos válidos.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if estudiante_id not in actuales or estudiante_id in ids:
                return Response(
                    {'detail': 'No puedes asociar estudiantes que no pertenecen a este caso.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not all(
                isinstance(estudiante.get(campo), str)
                and estudiante[campo].strip()
                for campo in ('nombre', 'apellido_paterno', 'apellido_materno')
            ):
                return Response(
                    {'detail': 'Completa el nombre y los apellidos de cada estudiante.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not Curso.objects.filter(pk=curso_id).exists():
                return Response(
                    {'detail': 'Selecciona un curso válido para cada estudiante.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ids.append(estudiante_id)

        try:
            with transaction.atomic():
                caso.caso_descripcion = f'[{titulo.strip()}] - {descripcion.strip()}'
                caso.lugar = lugar
                caso.save(update_fields=['caso_descripcion', 'lugar'])
                for estudiante in estudiantes:
                    estudiante_id = int(estudiante['id'])
                    Estudiante.objects.filter(pk=estudiante_id).update(
                        estudiante_nombre=estudiante['nombre'].strip(),
                        estudiante_apaterno=estudiante['apellido_paterno'].strip(),
                        estudiante_amaterno=estudiante['apellido_materno'].strip(),
                        curso_id=int(estudiante['curso_id']),
                    )
                    with connection.cursor() as cursor:
                        cursor.execute(
                            'UPDATE involucran SET tipo_falta = %s '
                            'WHERE caso_id = %s AND estudiante_id = %s',
                            [tipo_falta, caso_id, estudiante_id],
                        )
                estudiantes_actualizados = list(
                    Estudiante.objects.filter(pk__in=ids)
                )
                evaluar_reglas_para_caso(
                    caso,
                    estudiantes_actualizados,
                    request.user,
                    evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    fecha_evento=timezone.now(),
                )
                eliminados = set(actuales) - set(ids)
                for estudiante_id in eliminados:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            'DELETE FROM involucran WHERE caso_id = %s '
                            'AND estudiante_id = %s',
                            [caso_id, estudiante_id],
                        )
                if caso.usuario_id and caso.usuario_id != request.user.pk:
                    notificacion = Notificacion.objects.create(
                        usuario=caso.usuario,
                        notificacion_titulo='Caso actualizado',
                        notificacion_mensaje=(
                            f'El caso #{caso_id} fue modificado por '
                            f'{request.user.usuario_nombre} '
                            f'{request.user.usuario_apaterno}.'
                        ),
                        notificacion_icono='✏️',
                        caso=caso,
                        evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    )
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion,
                        estado=notificacion.estado,
                        cambiado_por=request.user,
                        motivo='Notificación creada al modificar un caso.',
                    )
                HistorialUsuario.objects.create(
                    usuario=request.user,
                    historial_accion='Modificación',
                    historial_detalle=f'Modificó los registros del caso #{caso_id}.',
                )
            return Response({'mensaje': f'El caso #{caso_id} fue actualizado.'})
        except Exception:
            logger.exception('No se pudo actualizar el caso %s vía API.', caso_id)
            return Response(
                {'detail': 'No se pudo actualizar el caso. Intenta nuevamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, caso_id):
        caso = self._caso(caso_id)
        rol = request.user.rol.rol_nombre
        permitido = puede_eliminar_caso(rol, caso)
        if not permitido:
            return Response(
                {'detail': 'No tienes permiso para eliminar este caso o venció el plazo de 12 horas.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            with transaction.atomic():
                caso_id_eliminado = caso.pk
                creador = caso.usuario
                if creador and creador.pk != request.user.pk:
                    notificacion, creada = Notificacion.objects.get_or_create(
                        evento_clave=(
                            f'caso_eliminado:{caso_id_eliminado}:'
                            f'creador:{creador.pk}'
                        ),
                        defaults={
                            'usuario': creador,
                            'notificacion_titulo': 'Caso eliminado',
                            'notificacion_mensaje': (
                                f'El caso #{caso_id_eliminado} que registraste '
                                'fue eliminado por otro usuario.'
                            ),
                            'notificacion_icono': '🗑️',
                        },
                    )
                    if creada:
                        HistorialNotificacion.objects.create(
                            notificacion=notificacion,
                            estado=notificacion.estado,
                            cambiado_por=request.user,
                            motivo='Notificación creada al eliminar un caso de otro usuario.',
                        )
                caso.delete()
                HistorialUsuario.objects.create(
                    usuario=request.user,
                    historial_accion='Eliminación',
                    historial_detalle=(
                        f'Eliminó el caso #{caso_id_eliminado} '
                        'de la bitácora de convivencia.'
                    ),
                )
            return Response({'mensaje': f'El caso #{caso_id_eliminado} fue eliminado.'})
        except Exception:
            logger.exception('No se pudo eliminar el caso %s vía API.', caso_id)
            return Response(
                {'detail': 'No se pudo eliminar el caso. Intenta nuevamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NotificacionesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        rol = request.user.rol.rol_nombre
        es_profesor = rol == 'Profesor Jefe'
        if rol not in ROLES_SEGUIMIENTO and not es_profesor:
            return Response(
                {'detail': 'No tienes permiso para consultar notificaciones.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        notificaciones = list(
            Notificacion.objects.filter(
                usuario_id=request.user.pk,
            )
            .select_related(
                'caso',
                'estudiante',
                'regla',
                'regla__version',
                'version_reglamento',
            )
            .prefetch_related('historial_estados__cambiado_por')
            .distinct()
            .order_by('-notificacion_fecha')
        )
        caso_ids = {n.caso_id for n in notificaciones if n.caso_id}
        categorias_por_caso = {}
        for caso_id, categoria in Involucran.objects.filter(
            caso_id__in=caso_ids,
        ).values_list('caso_id', 'tipo_falta'):
            categorias_por_caso.setdefault(caso_id, set()).add(categoria)

        puede_gestionar = rol in ROLES_GESTION_SEGUIMIENTO
        datos = []
        for notificacion in notificaciones:
            regla_operativa = _regla_notificacion_operativa(notificacion.regla)
            titulo = notificacion.notificacion_titulo
            mensaje = _mensaje_notificacion_seguro(notificacion)
            if notificacion.regla and not regla_operativa:
                titulo = 'Referencia reglamentaria para revisión'
                mensaje = (
                    'La disposición asociada no está actualmente aprobada y vigente '
                    'para orientar acciones. Revisa el detalle del caso y consulta '
                    'al personal autorizado.'
                )
            categorias = sorted(categorias_por_caso.get(notificacion.caso_id, set()))
            regla = notificacion.regla
            datos.append({
                'id': notificacion.pk,
                'titulo': titulo,
                'mensaje': mensaje,
                'icono': notificacion.notificacion_icono,
                'fecha': notificacion.notificacion_fecha.isoformat(),
                'leida': notificacion.notificacion_leido,
                'estado': notificacion.estado,
                'estado_etiqueta': notificacion.get_estado_display(),
                'evento_tipo': notificacion.evento_tipo,
                'caso_id': notificacion.caso_id,
                'categoria_falta': ', '.join(categorias) or 'No especificada',
                'fecha_limite': (
                    notificacion.fecha_limite.isoformat()
                    if notificacion.fecha_limite else None
                ),
                'version_reglamento': (
                    notificacion.version_reglamento.numero
                    if notificacion.version_reglamento else None
                ),
                'regla_operativa': regla_operativa,
                'regla_evidencia': regla.evidencia_textual if regla_operativa else '',
                'regla_titulo_fuente': regla.titulo_fuente if regla_operativa else '',
                'regla_seccion_fuente': regla.seccion_fuente if regla_operativa else '',
                'regla_pagina_impresa': regla.pagina_impresa if regla_operativa else None,
                'regla_pagina_pdf': regla.pagina_pdf if regla_operativa else None,
                'historial': [
                    {
                        'fecha': cambio.cambiado_en.isoformat(),
                        'estado': cambio.get_estado_display(),
                        'usuario': (
                            f'{cambio.cambiado_por.usuario_nombre} '
                            f'{cambio.cambiado_por.usuario_apaterno}'
                            if cambio.cambiado_por else ''
                        ),
                        'motivo': cambio.motivo,
                    }
                    for cambio in notificacion.historial_estados.all()
                ],
            })

        return Response({
            'notificaciones': datos,
            'puede_gestionar': puede_gestionar,
            'estados': [
                {'valor': valor, 'etiqueta': etiqueta}
                for valor, etiqueta in Notificacion.Estado.choices
            ],
        })

    def post(self, request, notificacion_id=None):
        rol = request.user.rol.rol_nombre
        es_profesor = rol == 'Profesor Jefe'
        if rol not in ROLES_SEGUIMIENTO and not es_profesor:
            return Response(
                {'detail': 'No tienes permiso para modificar notificaciones.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if notificacion_id is None:
            return Response(
                {'detail': 'Falta el identificador de la notificación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notificacion = get_object_or_404(
            Notificacion.objects.filter(
                usuario_id=request.user.pk,
            ),
            pk=notificacion_id,
        )
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía los cambios como un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        accion = request.data.get('accion', '')
        if accion == 'leer':
            if notificacion.notificacion_leido:
                return Response({'leida': True})
            notificacion.notificacion_leido = True
            notificacion.save(update_fields=['notificacion_leido'])
            return Response({'leida': True})

        if accion != 'estado' or rol not in ROLES_GESTION_SEGUIMIENTO:
            return Response(
                {'detail': 'No tienes permiso para cambiar el estado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        estado = request.data.get('estado', '')
        motivo = request.data.get('motivo', '')
        if not isinstance(motivo, str):
            return Response(
                {'detail': 'Indica un motivo de hasta 500 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = motivo.strip()
        if estado not in Notificacion.Estado.values:
            return Response(
                {'detail': 'Selecciona un estado válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not motivo or len(motivo) > 500:
            return Response(
                {'detail': 'Indica un motivo de hasta 500 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if notificacion.estado == estado:
            return Response({
                'estado': estado,
                'estado_etiqueta': notificacion.get_estado_display(),
            })

        with transaction.atomic():
            notificacion.estado = estado
            notificacion.save(update_fields=['estado'])
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=estado,
                cambiado_por=request.user,
                motivo=motivo,
            )
        return Response({'estado': estado, 'estado_etiqueta': notificacion.get_estado_display()})


class CasoFormularioAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        rol = request.user.rol.rol_nombre
        if rol not in (*ROLES_SEGUIMIENTO, 'Profesor Jefe'):
            return Response(
                {'detail': 'No tienes permiso para registrar casos.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        curso_profesor = None
        if rol == 'Profesor Jefe':
            curso_profesor = (
                ProfesorJefe.objects.select_related('curso')
                .filter(usuario_id=request.user.pk)
                .first()
            )
            if not curso_profesor or not curso_profesor.curso:
                return Response(
                    {'detail': 'No se encontró un curso asignado a tu cuenta.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        cursos = Curso.objects.all().order_by('curso_grado', 'curso_letra')
        estudiantes = Estudiante.objects.filter(estudiante_activo=True).select_related(
            'curso'
        ).order_by('estudiante_apaterno', 'estudiante_amaterno', 'estudiante_nombre')
        if curso_profesor:
            cursos = cursos.filter(pk=curso_profesor.curso_id)
            estudiantes = estudiantes.filter(curso_id=curso_profesor.curso_id)

        return Response({
            'lugares': [
                {'id': lugar.pk, 'nombre': lugar.lugar_nombre}
                for lugar in Lugar.objects.all().order_by('lugar_nombre')
            ],
            'cursos': [
                {
                    'id': curso.pk,
                    'nombre': f'{curso.curso_grado} {curso.curso_letra}',
                }
                for curso in cursos
            ],
            'estudiantes': [
                {
                    'id': estudiante.pk,
                    'nombre': estudiante.estudiante_nombre,
                    'apellido_paterno': estudiante.estudiante_apaterno,
                    'apellido_materno': estudiante.estudiante_amaterno,
                    'numero_lista': estudiante.estudiante_numero_lista,
                    'curso_id': estudiante.curso_id,
                }
                for estudiante in estudiantes
            ],
            'requiere_aprobacion': rol == 'Profesor Jefe',
            'fecha_hoy': timezone.localdate().isoformat(),
        })


class RegistrarCasoAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def post(self, request):
        rol = request.user.rol.rol_nombre
        if rol not in (*ROLES_SEGUIMIENTO, 'Profesor Jefe'):
            return Response(
                {'detail': 'No tienes permiso para registrar casos.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        datos = request.data
        if hasattr(datos, 'get') and isinstance(datos.get('datos'), str):
            try:
                datos = json.loads(datos['datos'])
            except json.JSONDecodeError:
                return Response(
                    {'detail': 'Los datos del caso no tienen un formato válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not isinstance(datos, dict):
            return Response(
                {'detail': 'Envía los datos del caso como un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        titulo = datos.get('titulo')
        descripcion = datos.get('descripcion')
        fecha_texto = datos.get('fecha')
        tipo_falta = datos.get('tipo_falta')
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo.strip()) > 180:
            return Response(
                {'detail': 'El título es obligatorio y no debe superar 180 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(descripcion, str) or not descripcion.strip():
            return Response(
                {'detail': 'La descripción es obligatoria.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fecha = parse_date(fecha_texto) if isinstance(fecha_texto, str) else None
        if not fecha or fecha > timezone.localdate():
            return Response(
                {'detail': 'La fecha debe ser válida y no puede ser posterior a hoy.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if tipo_falta not in ('Leve', 'Grave', 'Gravísima'):
            return Response(
                {'detail': 'Selecciona una clasificación de gravedad válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            lugar_id = int(datos.get('lugar_id'))
            lugar_instancia = Lugar.objects.get(pk=lugar_id)
        except (TypeError, ValueError, Lugar.DoesNotExist):
            return Response(
                {'detail': 'Selecciona un lugar válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estudiantes = datos.get('estudiantes')
        if not isinstance(estudiantes, list) or not estudiantes:
            return Response(
                {'detail': 'Agrega al menos un estudiante involucrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        curso_profesor = None
        if rol == 'Profesor Jefe':
            curso_profesor = (
                ProfesorJefe.objects.select_related('curso')
                .filter(usuario_id=request.user.pk)
                .first()
            )
            if not curso_profesor or not curso_profesor.curso:
                return Response(
                    {'detail': 'No se encontró un curso asignado a tu cuenta.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        estudiantes_data = []
        for estudiante in estudiantes:
            if not isinstance(estudiante, dict):
                return Response(
                    {'detail': 'Los datos de los estudiantes no son válidos.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            nombre = estudiante.get('nombre', '')
            apellido_paterno = estudiante.get('apellido_paterno', '')
            apellido_materno = estudiante.get('apellido_materno', '')
            if (
                not isinstance(nombre, str)
                or not nombre.strip()
                or not isinstance(apellido_paterno, str)
                or not apellido_paterno.strip()
                or not isinstance(apellido_materno, str)
            ):
                return Response(
                    {'detail': 'Completa el nombre y apellido paterno de cada estudiante.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                curso_id = int(estudiante.get('curso_id'))
                curso = Curso.objects.get(pk=curso_id)
            except (TypeError, ValueError, Curso.DoesNotExist):
                return Response(
                    {'detail': 'Selecciona un curso válido para cada estudiante.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if curso_profesor and curso.pk != curso_profesor.curso_id:
                return Response(
                    {'detail': 'Solo puedes reportar estudiantes de tu curso asignado.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            numero_lista_raw = estudiante.get('numero_lista')
            if numero_lista_raw in (None, ''):
                numero_lista = None
            else:
                try:
                    numero_lista = int(numero_lista_raw)
                    if numero_lista < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    return Response(
                        {'detail': 'El número de lista debe ser un número entero válido.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            estudiante_id_raw = estudiante.get('estudiante_id')
            estudiante_id = None
            if estudiante_id_raw not in (None, ''):
                try:
                    estudiante_id = int(estudiante_id_raw)
                    estudiante_existente = Estudiante.objects.get(
                        pk=estudiante_id,
                        estudiante_activo=True,
                    )
                except (TypeError, ValueError, Estudiante.DoesNotExist):
                    return Response(
                        {'detail': 'El estudiante seleccionado no es válido o está inactivo.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if estudiante_existente.curso_id != curso.pk:
                    return Response(
                        {'detail': 'El curso del estudiante seleccionado no coincide.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            estudiantes_data.append({
                'nombre': nombre.strip(),
                'apellido_paterno': apellido_paterno.strip(),
                'apellido_materno': apellido_materno.strip(),
                'numero_lista': numero_lista,
                'curso_id': curso.pk,
                'estudiante_id': estudiante_id,
            })

        evidencia = request.FILES.get('evidencia_foto')
        if evidencia:
            extension = os.path.splitext(evidencia.name)[1].lower()
            extensiones_permitidas = {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
                '.png', '.jpg', '.jpeg',
            }
            if extension not in extensiones_permitidas:
                return Response(
                    {'detail': 'El archivo debe ser PDF, Word, Excel, texto o imagen.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if evidencia.size > 20 * 1024 * 1024:
                return Response(
                    {'detail': 'El archivo adjunto supera el límite de 20 MB.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        evidencia_guardada = None
        if evidencia:
            nombre_seguro = os.path.basename(evidencia.name)
            try:
                evidencia_guardada = default_storage.save(
                    f'evidencias/{nombre_seguro}',
                    evidencia,
                )
            except Exception:
                logger.exception('No se pudo guardar la evidencia del caso vía API.')
                return Response(
                    {'detail': 'No se pudo guardar el archivo adjunto. Intenta nuevamente.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            with transaction.atomic():
                if curso_profesor:
                    solicitud = SolicitudCaso.objects.create(
                        solicitante=request.user,
                        lugar=lugar_instancia,
                        fecha_evento=fecha,
                        titulo=titulo.strip(),
                        descripcion=descripcion.strip(),
                        tipo_falta=tipo_falta,
                        evidencia=evidencia_guardada or '',
                        estudiantes=estudiantes_data,
                    )
                    return Response(
                        {
                            'id': solicitud.pk,
                            'estado': solicitud.estado,
                            'mensaje': 'El caso fue enviado y está en espera de revisión.',
                        },
                        status=status.HTTP_201_CREATED,
                    )

                caso = crear_caso_persistido(
                    request._request,
                    request.user,
                    fecha,
                    titulo.strip(),
                    descripcion.strip(),
                    evidencia_guardada,
                    lugar_instancia,
                    tipo_falta,
                    estudiantes_data,
                )
                return Response(
                    {
                        'id': caso.pk,
                        'mensaje': 'El caso fue registrado correctamente.',
                    },
                    status=status.HTTP_201_CREATED,
                )
        except (ValidationError, Curso.DoesNotExist, Estudiante.DoesNotExist):
            if evidencia_guardada:
                default_storage.delete(evidencia_guardada)
            logger.exception('Los datos del caso fueron rechazados durante el registro vía API.')
            return Response(
                {'detail': 'No se pudo registrar el caso con los datos proporcionados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            if evidencia_guardada:
                default_storage.delete(evidencia_guardada)
            logger.exception('No se pudo registrar el caso vía API.')
            return Response(
                {'detail': 'No se pudo registrar el caso. Intenta nuevamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SolicitudesCasosAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.rol.rol_nombre not in ROLES_APROBACION_CASOS:
            return Response(
                {'detail': 'No tienes permiso para revisar solicitudes de casos.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        solicitudes = list(
            SolicitudCaso.objects.select_related(
                'solicitante__rol',
                'lugar',
            ).filter(estado=SolicitudCaso.Estado.PENDIENTE)
        )
        cursos = Curso.objects.in_bulk({
            estudiante['curso_id']
            for solicitud in solicitudes
            for estudiante in solicitud.estudiantes
            if isinstance(estudiante, dict) and 'curso_id' in estudiante
        })
        resultados = []
        for solicitud in solicitudes:
            estudiantes = []
            for estudiante in solicitud.estudiantes:
                curso = cursos.get(estudiante.get('curso_id'))
                estudiantes.append({
                    'nombre': estudiante.get('nombre', ''),
                    'apellido_paterno': estudiante.get('apellido_paterno', ''),
                    'apellido_materno': estudiante.get('apellido_materno', ''),
                    'curso': (
                        f'{curso.curso_grado} {curso.curso_letra}'
                        if curso else 'Curso no disponible'
                    ),
                })
            evidencia_url = ''
            if solicitud.evidencia and default_storage.exists(solicitud.evidencia):
                evidencia_url = default_storage.url(solicitud.evidencia)
            resultados.append({
                'id': solicitud.pk,
                'titulo': solicitud.titulo,
                'fecha': solicitud.fecha_evento.isoformat(),
                'lugar': solicitud.lugar.lugar_nombre,
                'tipo_falta': solicitud.tipo_falta,
                'descripcion': solicitud.descripcion,
                'solicitante': (
                    f'{solicitud.solicitante.usuario_nombre} '
                    f'{solicitud.solicitante.usuario_apaterno}'
                    if solicitud.solicitante else 'Usuario eliminado'
                ),
                'creada_en': solicitud.creada_en.isoformat(),
                'estudiantes': estudiantes,
                'evidencia_url': evidencia_url,
            })

        return Response({'solicitudes': resultados})

    def post(self, request, solicitud_id=None):
        if request.user.rol.rol_nombre not in ROLES_APROBACION_CASOS:
            return Response(
                {'detail': 'No tienes permiso para revisar solicitudes de casos.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if solicitud_id is None:
            return Response(
                {'detail': 'Falta el identificador de la solicitud.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía la decisión de revisión en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = request.data.get('decision')
        comentario = request.data.get('comentario', '')
        if decision not in ('aprobar', 'rechazar'):
            return Response(
                {'detail': 'La decisión de revisión no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(comentario, str) or len(comentario) > 2000:
            return Response(
                {'detail': 'El comentario no debe superar 2000 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                solicitud = get_object_or_404(
                    SolicitudCaso.objects.select_for_update().select_related(
                        'solicitante__rol',
                        'lugar',
                    ),
                    pk=solicitud_id,
                )
                if solicitud.estado != SolicitudCaso.Estado.PENDIENTE:
                    return Response(
                        {'detail': 'Esta solicitud ya fue revisada.'},
                        status=status.HTTP_409_CONFLICT,
                    )

                if decision == 'aprobar':
                    estudiantes_data = solicitud.estudiantes
                    if not estudiantes_data:
                        raise ValidationError(
                            'La solicitud no contiene estudiantes involucrados.'
                        )
                    if (
                        solicitud.solicitante
                        and solicitud.solicitante.rol.rol_nombre == 'Profesor Jefe'
                    ):
                        perfil_profesor = ProfesorJefe.objects.select_related(
                            'curso'
                        ).filter(usuario_id=solicitud.solicitante_id).first()
                        curso_profesor = (
                            perfil_profesor.curso if perfil_profesor else None
                        )
                        if not curso_profesor or any(
                            int(estudiante['curso_id']) != curso_profesor.pk
                            for estudiante in estudiantes_data
                        ):
                            raise ValidationError(
                                'El curso asignado al profesor cambió; no se puede '
                                'aprobar esta solicitud hasta corregir su información.'
                            )

                    caso = crear_caso_persistido(
                        request._request,
                        solicitud.solicitante or request.user,
                        solicitud.fecha_evento,
                        solicitud.titulo,
                        solicitud.descripcion,
                        solicitud.evidencia,
                        solicitud.lugar,
                        solicitud.tipo_falta,
                        estudiantes_data,
                    )
                    solicitud.estado = SolicitudCaso.Estado.APROBADA
                    resultado = {
                        'mensaje': f'Solicitud aprobada y registrada como caso #{caso.pk}.',
                        'caso_id': caso.pk,
                    }
                else:
                    solicitud.estado = SolicitudCaso.Estado.RECHAZADA
                    resultado = {'mensaje': 'La solicitud fue rechazada.'}

                solicitud.comentario_revision = (
                    comentario.strip()
                    or ('Solicitud rechazada.' if decision == 'rechazar' else '')
                )
                solicitud.revisada_por = request.user
                solicitud.revisada_en = timezone.now()
                solicitud.save(update_fields=[
                    'estado',
                    'comentario_revision',
                    'revisada_por',
                    'revisada_en',
                ])
                HistorialUsuario.objects.create(
                    usuario=request.user,
                    historial_accion=(
                        'Aprobación de caso'
                        if decision == 'aprobar'
                        else 'Rechazo de caso'
                    ),
                    historial_detalle=(
                        f"Revisó la solicitud #{solicitud.pk} del Profesor Jefe "
                        f"{solicitud.solicitante.usuario_nombre if solicitud.solicitante else 'sin usuario'}: "
                        f"{solicitud.get_estado_display()}."
                    ),
                )
                return Response(resultado)
        except Http404:
            raise
        except ValidationError as error:
            return Response(
                {'detail': str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.exception('No se pudo completar la revisión de la solicitud vía API.')
            return Response(
                {'detail': 'No se pudo completar la revisión. Intenta nuevamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SeguimientoAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        rol = request.user.rol.rol_nombre
        if rol not in ROLES_SEGUIMIENTO:
            return Response(
                {'detail': 'No tienes permiso para consultar el seguimiento.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        filtro_estado = request.query_params.get('estado', '')
        if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
            filtro_estado = ''
        filas = obtener_filas_seguimiento(filtro_estado)
        hoy = timezone.localdate()
        return Response({
            'puede_gestionar': rol in ROLES_GESTION_SEGUIMIENTO,
            'filas': [
                {
                    'caso_id': fila['caso'].pk,
                    'fecha_caso': fila['caso'].caso_fecha.isoformat(),
                    'registrado_en': (
                        fila['caso'].caso_creado_en.isoformat()
                        if fila['caso'].caso_creado_en else None
                    ),
                    'tiene_evidencia': bool(fila['caso'].evidencia),
                    'estudiante_id': fila['estudiante_id'],
                    'estudiante_pk': fila['estudiante_pk'],
                    'categoria': fila['categoria'] or 'No especificada',
                    'estado': fila['estado'],
                    'estado_etiqueta': fila['estado_label'],
                    'avance': fila['avance'],
                    'acciones': [
                        {
                            'id': accion.pk,
                            'titulo': accion.titulo,
                            'estado': accion.estado,
                            'estado_etiqueta': accion.get_estado_display(),
                            'responsable': (
                                f'{accion.responsable.usuario_nombre} '
                                f'{accion.responsable.usuario_apaterno}'
                                if accion.responsable
                                else accion.responsable_rol or 'Sin asignar'
                            ),
                            'fecha_limite': (
                                accion.fecha_limite.isoformat()
                                if accion.fecha_limite else None
                            ),
                            'vencida': bool(
                                accion.estado == AccionSeguimiento.Estado.PENDIENTE
                                and accion.fecha_limite
                                and accion.fecha_limite < hoy
                            ),
                        }
                        for accion in fila['acciones']
                    ],
                    'historial': [
                        {
                            'fecha': entrada.cambiado_en.isoformat(),
                            'estado': entrada.get_estado_display(),
                            'motivo': entrada.motivo,
                        }
                        for entrada in (
                            fila['seguimiento'].historial.all()
                            if fila['seguimiento'] else []
                        )
                    ],
                }
                for fila in filas
            ],
        })

    def post(
        self,
        request,
        accion_id=None,
        caso_id=None,
        estudiante_id=None,
    ):
        rol = request.user.rol.rol_nombre
        if rol not in ROLES_GESTION_SEGUIMIENTO:
            return Response(
                {'detail': 'Solo Administrador o Convivencia pueden gestionar seguimientos.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía los cambios como un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = request.data.get('motivo', '')
        if not isinstance(motivo, str):
            return Response(
                {'detail': 'El motivo del cambio es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = motivo.strip()

        if accion_id is not None:
            accion = get_object_or_404(AccionSeguimiento, pk=accion_id)
            estado = request.data.get('estado', '')
            if estado not in AccionSeguimiento.Estado.values or not motivo or len(motivo) > 500:
                return Response(
                    {'detail': 'El estado y un motivo de hasta 500 caracteres son obligatorios.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if accion.estado == estado:
                return Response({
                    'estado': estado,
                    'estado_etiqueta': accion.get_estado_display(),
                })
            with transaction.atomic():
                accion.estado = estado
                accion.completada_en = (
                    timezone.now()
                    if estado == AccionSeguimiento.Estado.COMPLETADA else None
                )
                accion.save(update_fields=['estado', 'completada_en'])
                HistorialAccionSeguimiento.objects.create(
                    accion=accion,
                    estado=estado,
                    cambiado_por=request.user,
                    motivo=motivo,
                )
            return Response({
                'estado': estado,
                'estado_etiqueta': accion.get_estado_display(),
            })

        if caso_id is None or estudiante_id is None or not motivo or len(motivo) > 1000:
            return Response(
                {'detail': 'El caso, estudiante y un motivo de hasta 1000 caracteres son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        caso = get_object_or_404(Caso, pk=caso_id)
        estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
        if not caso.estudiantes.filter(pk=estudiante.pk).exists():
            return Response(
                {'detail': 'El estudiante no está asociado a este caso.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            seguimiento, _ = SeguimientoCaso.objects.get_or_create(
                caso=caso,
                estudiante=estudiante,
            )
            seguimiento = SeguimientoCaso.objects.select_for_update().get(
                pk=seguimiento.pk
            )
            if seguimiento.acciones.exclude(
                estado=AccionSeguimiento.Estado.COMPLETADA
            ).exists():
                return Response(
                    {'detail': 'Completa todas las acciones requeridas antes de cerrar el seguimiento.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if seguimiento.estado != SeguimientoCaso.Estado.SOLUCIONADO:
                seguimiento.estado = SeguimientoCaso.Estado.SOLUCIONADO
                seguimiento.solucionado_en = timezone.now()
                seguimiento.solucionado_por = request.user
                seguimiento.motivo_cierre = motivo
                seguimiento.save(update_fields=[
                    'estado',
                    'solucionado_en',
                    'solucionado_por',
                    'motivo_cierre',
                ])
                HistorialSeguimientoCaso.objects.create(
                    seguimiento=seguimiento,
                    estado=seguimiento.estado,
                    cambiado_por=request.user,
                    motivo=motivo,
                )
                notificaciones = Notificacion.objects.filter(
                    caso=caso,
                    estudiante=estudiante,
                ).exclude(estado=Notificacion.Estado.SOLUCIONADO)
                for notificacion in notificaciones:
                    notificacion.estado = Notificacion.Estado.SOLUCIONADO
                    notificacion.save(update_fields=['estado'])
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion,
                        estado=notificacion.estado,
                        cambiado_por=request.user,
                        motivo=f'Cierre autorizado del seguimiento: {motivo}',
                    )

        return Response({
            'estado': SeguimientoCaso.Estado.SOLUCIONADO,
            'estado_etiqueta': seguimiento.get_estado_display(),
        })


class EstadisticasAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.rol.rol_nombre not in ROLES_SEGUIMIENTO:
            return Response(
                {'detail': 'No tienes permiso para consultar las estadísticas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        gravedad = request.query_params.get('gravedad', '').strip()
        if gravedad and gravedad not in ('Leve', 'Grave', 'Gravísima'):
            return Response(
                {'detail': 'La clasificación de gravedad no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for key in ('curso', 'zona'):
            valor = request.query_params.get(key, '').strip()
            if valor and (
                not valor.isdecimal()
                or len(valor) > 10
                or not 1 <= int(valor) <= 2147483647
            ):
                return Response(
                    {'detail': f'El filtro {key} no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        fecha_desde_texto = request.query_params.get('fecha_desde', '').strip()
        fecha_hasta_texto = request.query_params.get('fecha_hasta', '').strip()
        fecha_desde = parse_date(fecha_desde_texto) if fecha_desde_texto else None
        fecha_hasta = parse_date(fecha_hasta_texto) if fecha_hasta_texto else None
        if fecha_desde_texto and fecha_desde is None:
            return Response(
                {'detail': 'La fecha desde no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if fecha_hasta_texto and fecha_hasta is None:
            return Response(
                {'detail': 'La fecha hasta no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return Response(
                {'detail': 'La fecha desde debe ser anterior o igual a la fecha hasta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        datos = obtener_datos_estadisticas(request)
        datos['cursos_opciones'] = [
            {
                'id': curso.pk,
                'nombre': f'{curso.curso_grado} {curso.curso_letra}',
            }
            for curso in Curso.objects.all().order_by('curso_grado', 'curso_letra')
        ]
        datos['zonas_opciones'] = [
            {'id': lugar.pk, 'nombre': lugar.lugar_nombre}
            for lugar in Lugar.objects.all().order_by('lugar_nombre')
        ]
        return Response(datos)

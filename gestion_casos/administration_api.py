"""JWT endpoints for administrative user and student workflows."""

import logging
import os

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import connection, transaction
from django.db.models import Q
from django.utils.dateparse import parse_date
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Administrador,
    Caso,
    Curso,
    Estudiante,
    HistorialImportacionEstudiantes,
    HistorialUsuario,
    Inspector,
    PConvivencia,
    ProfesorJefe,
    Rol,
    Usuario,
    _quitar_tildes,
)

logger = logging.getLogger(__name__)


def _es_administrador(request):
    return request.user.rol.rol_nombre == 'Administrador'


def _persona_por_rol(usuario, rol, curso=None):
    if rol == 'Administrador':
        Administrador.objects.create(
            usuario=usuario,
            admin_nombre=usuario.usuario_nombre,
            admin_apaterno=usuario.usuario_apaterno,
            admin_amaterno=usuario.usuario_amaterno,
        )
    elif rol == 'Inspector':
        Inspector.objects.create(
            usuario=usuario,
            inspector_nombre=usuario.usuario_nombre,
            inspector_apaterno=usuario.usuario_apaterno,
            inspector_amaterno=usuario.usuario_amaterno,
        )
    elif rol == 'PConvivencia':
        PConvivencia.objects.create(
            usuario=usuario,
            convivencia_nombre=usuario.usuario_nombre,
            convivencia_apaterno=usuario.usuario_apaterno,
            convivencia_amaterno=usuario.usuario_amaterno,
        )
    elif rol == 'Profesor Jefe':
        ProfesorJefe.objects.create(
            usuario=usuario,
            curso=curso,
            profesor_nombre=usuario.usuario_nombre,
            profesor_apaterno=usuario.usuario_apaterno,
            profesor_amaterno=usuario.usuario_amaterno,
        )


def _datos_usuario(usuario, curso_por_usuario=None):
    curso = (curso_por_usuario or {}).get(usuario.pk)
    return {
        'id': usuario.pk,
        'nombre': usuario.usuario_nombre,
        'apellido_paterno': usuario.usuario_apaterno,
        'apellido_materno': usuario.usuario_amaterno,
        'correo': usuario.usuario_correo,
        'rol_id': usuario.rol_id,
        'rol': usuario.rol.rol_nombre,
        'curso_id': curso.pk if curso else None,
        'curso': (
            f'{curso.curso_grado} {curso.curso_letra}' if curso else ''
        ),
        'activo': usuario.usuario_activo,
        'bloqueado': usuario.usuario_bloqueado,
        'primer_ingreso': usuario.usuario_primer_ingreso,
        'ultimo_acceso': (
            usuario.usuario_ultimo_acceso.isoformat()
            if usuario.usuario_ultimo_acceso else None
        ),
    }


class UsuariosAdminAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        nombre = request.query_params.get('nombre', '').strip()
        rol_id = request.query_params.get('rol', '').strip()
        estado = request.query_params.get('estado', '').strip()
        desde = request.query_params.get('fecha_desde', '').strip()
        hasta = request.query_params.get('fecha_hasta', '').strip()
        usuarios = Usuario.objects.select_related('rol').all().order_by(
            'usuario_apaterno', 'usuario_nombre',
        )
        if nombre:
            normalizado = _quitar_tildes(nombre)
            for termino in normalizado.split():
                usuarios = usuarios.filter(
                    Q(usuario_nombre__icontains=termino)
                    | Q(usuario_apaterno__icontains=termino)
                    | Q(usuario_amaterno__icontains=termino)
                    | Q(usuario_correo__icontains=termino)
                )
        if rol_id:
            if not rol_id.isdigit():
                return Response(
                    {'detail': 'El filtro de rol no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            usuarios = usuarios.filter(rol_id=int(rol_id))
        if estado == 'activo':
            usuarios = usuarios.filter(usuario_activo=True)
        elif estado == 'inactivo':
            usuarios = usuarios.filter(usuario_activo=False)
        elif estado:
            return Response(
                {'detail': 'El filtro de estado no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fecha_desde = parse_date(desde) if desde else None
        fecha_hasta = parse_date(hasta) if hasta else None
        if (desde and not fecha_desde) or (hasta and not fecha_hasta):
            return Response(
                {'detail': 'Usa fechas válidas en los filtros.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if fecha_desde:
            usuarios = usuarios.filter(usuario_ultimo_acceso__date__gte=fecha_desde)
        if fecha_hasta:
            usuarios = usuarios.filter(usuario_ultimo_acceso__date__lte=fecha_hasta)

        pagina = Paginator(usuarios, 20).get_page(request.query_params.get('pagina'))
        ids = [usuario.pk for usuario in pagina]
        cursos = {
            perfil.usuario_id: perfil.curso
            for perfil in ProfesorJefe.objects.filter(
                usuario_id__in=ids,
            ).select_related('curso')
        }
        return Response({
            'resultados': [_datos_usuario(usuario, cursos) for usuario in pagina],
            'pagina': pagina.number,
            'total_paginas': pagina.paginator.num_pages,
            'total': pagina.paginator.count,
            'tiene_anterior': pagina.has_previous(),
            'tiene_siguiente': pagina.has_next(),
            'roles': [
                {'id': rol.pk, 'nombre': rol.rol_nombre}
                for rol in Rol.objects.all().order_by('rol_nombre')
            ],
            'cursos': [
                {'id': curso.pk, 'nombre': f'{curso.curso_grado} {curso.curso_letra}'}
                for curso in Curso.objects.all().order_by(
                    'curso_grado', 'curso_letra',
                )
            ],
        })

    def post(self, request):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede crear usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        datos = request.data
        if not isinstance(datos, dict):
            return Response(
                {'detail': 'Envía los datos como un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nombre = datos.get('nombre', '').strip() if isinstance(datos.get('nombre'), str) else ''
        apaterno = datos.get('apellido_paterno', '').strip() if isinstance(datos.get('apellido_paterno'), str) else ''
        amaterno = datos.get('apellido_materno', '').strip() if isinstance(datos.get('apellido_materno'), str) else ''
        correo = datos.get('correo', '').strip() if isinstance(datos.get('correo'), str) else ''
        try:
            validate_email(correo)
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError('Completa los nombres y apellidos.')
            if Usuario.objects.filter(usuario_correo__iexact=correo).exists():
                raise ValidationError('Ese correo ya está registrado.')
            rol = Rol.objects.get(pk=int(datos.get('rol_id')))
            curso = None
            if rol.rol_nombre == 'Profesor Jefe':
                curso = Curso.objects.get(pk=int(datos.get('curso_id')))
            from .controllers.user_controller import _generar_contrasena_temporal

            password = _generar_contrasena_temporal()
            with transaction.atomic():
                usuario = Usuario.objects.create(
                    usuario_nombre=nombre,
                    usuario_apaterno=apaterno,
                    usuario_amaterno=amaterno,
                    usuario_correo=correo,
                    usuario_contrasena=make_password(password),
                    usuario_primer_ingreso=True,
                    rol=rol,
                )
                _persona_por_rol(usuario, rol.rol_nombre, curso)
                from .controllers.email_controller import programar_tarea_correo
                from .tasks import enviar_credenciales_usuario

                programar_tarea_correo(
                    request._request,
                    enviar_credenciales_usuario,
                    (correo, nombre, apaterno, password),
                    'La cuenta se creó, pero no se pudo encolar el correo de contraseña temporal.',
                )
            return Response(
                {
                    'usuario': _datos_usuario(
                        usuario,
                        {usuario.pk: curso} if curso else {},
                    ),
                    'mensaje': 'Usuario creado; se enviará una contraseña temporal al correo.',
                },
                status=status.HTTP_201_CREATED,
            )
        except (ValidationError, ValueError, TypeError, Rol.DoesNotExist, Curso.DoesNotExist) as error:
            detail = ' '.join(error.messages) if isinstance(error, ValidationError) else 'Selecciona un rol y curso válidos.'
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception('No se pudo crear el usuario vía API.')
            return Response(
                {'detail': 'No se pudo crear el usuario. Revisa los datos e intenta nuevamente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def put(self, request, usuario_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede editar usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario = Usuario.objects.select_related('rol').filter(pk=usuario_id).first()
        if usuario is None:
            return Response({'detail': 'No se encontró el usuario.'}, status=404)
        datos = request.data
        nombre = datos.get('nombre', '').strip() if isinstance(datos.get('nombre'), str) else ''
        apaterno = datos.get('apellido_paterno', '').strip() if isinstance(datos.get('apellido_paterno'), str) else ''
        amaterno = datos.get('apellido_materno', '').strip() if isinstance(datos.get('apellido_materno'), str) else ''
        correo = datos.get('correo', '').strip() if isinstance(datos.get('correo'), str) else ''
        password = datos.get('contrasena', '')
        if not all((nombre, apaterno, amaterno, correo)):
            return Response(
                {'detail': 'Completa nombres, apellidos y correo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_email(correo)
            if Usuario.objects.filter(
                usuario_correo__iexact=correo,
            ).exclude(pk=usuario.pk).exists():
                raise ValidationError('Ese correo ya está asociado a otra cuenta.')
            rol = Rol.objects.get(pk=int(datos.get('rol_id')))
            curso = None
            if rol.rol_nombre == 'Profesor Jefe':
                curso = Curso.objects.get(pk=int(datos.get('curso_id')))
            with transaction.atomic():
                usuario.usuario_nombre = nombre
                usuario.usuario_apaterno = apaterno
                usuario.usuario_amaterno = amaterno
                usuario.usuario_correo = correo
                usuario.rol = rol
                usuario.usuario_activo = datos.get('activo', usuario.usuario_activo)
                if not isinstance(usuario.usuario_activo, bool):
                    raise ValidationError('El estado activo debe ser verdadero o falso.')
                usuario.usuario_bloqueado = False
                usuario.usuario_intentos_fallidos = 0
                if password:
                    if not isinstance(password, str) or len(password) < 12:
                        raise ValidationError('La contraseña debe tener al menos 12 caracteres.')
                    usuario.usuario_contrasena = make_password(password)
                usuario.save()
                Administrador.objects.filter(usuario=usuario).delete()
                Inspector.objects.filter(usuario=usuario).delete()
                PConvivencia.objects.filter(usuario=usuario).delete()
                ProfesorJefe.objects.filter(usuario=usuario).delete()
                _persona_por_rol(usuario, rol.rol_nombre, curso)
                HistorialUsuario.objects.create(
                    usuario=request.user,
                    historial_accion='Modificación de usuario',
                    historial_detalle=f'Actualizó la cuenta de {nombre} {apaterno} (#{usuario.pk}).',
                )
            return Response({'usuario': _datos_usuario(usuario, {usuario.pk: curso} if curso else {})})
        except (ValidationError, ValueError, TypeError, Rol.DoesNotExist, Curso.DoesNotExist) as error:
            detail = ' '.join(error.messages) if isinstance(error, ValidationError) else 'Selecciona un rol y curso válidos.'
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception('No se pudo actualizar el usuario %s vía API.', usuario_id)
            return Response(
                {'detail': 'No se pudo actualizar el usuario.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def patch(self, request, usuario_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario is None:
            return Response({'detail': 'No se encontró el usuario.'}, status=404)
        accion = request.data.get('accion')
        if accion == 'desbloquear':
            usuario.usuario_bloqueado = False
            usuario.usuario_intentos_fallidos = 0
            usuario.save(update_fields=['usuario_bloqueado', 'usuario_intentos_fallidos'])
            return Response({'mensaje': 'La cuenta fue desbloqueada.'})
        if accion == 'estado' and isinstance(request.data.get('activo'), bool):
            if usuario.pk == request.user.pk and not request.data['activo']:
                return Response(
                    {'detail': 'No puedes desactivar tu propia cuenta.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            usuario.usuario_activo = request.data['activo']
            usuario.save(update_fields=['usuario_activo'])
            return Response({'mensaje': 'El estado de la cuenta fue actualizado.'})
        return Response(
            {'detail': 'La acción solicitada no es válida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, usuario_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede eliminar usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if usuario_id == request.user.pk:
            return Response(
                {'detail': 'No puedes eliminar tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario is None:
            return Response({'detail': 'No se encontró el usuario.'}, status=404)
        usuario.delete()
        return Response({'mensaje': 'El usuario fue eliminado.'})


class UsuariosAdminBulkAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede ejecutar acciones masivas.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        accion = request.data.get('accion')
        ids = request.data.get('usuarios')
        if accion not in ('desactivar', 'eliminar') or not isinstance(ids, list):
            return Response(
                {'detail': 'Indica una acción y una lista de usuarios válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ids = {int(value) for value in ids}
        except (TypeError, ValueError):
            return Response(
                {'detail': 'La selección contiene identificadores no válidos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        omitio_propia_cuenta = request.user.pk in ids
        ids.discard(request.user.pk)
        usuarios = list(
            Usuario.objects.filter(pk__in=ids).exclude(pk=request.user.pk)
        )
        if not usuarios:
            return Response(
                {'detail': 'Selecciona usuarios distintos de tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nombres = ', '.join(
            f'{usuario.usuario_nombre} {usuario.usuario_apaterno} (#{usuario.pk})'
            for usuario in usuarios
        )
        with transaction.atomic():
            if accion == 'desactivar':
                Usuario.objects.filter(pk__in=[usuario.pk for usuario in usuarios]).update(
                    usuario_activo=False,
                )
                accion_hist = 'Desactivación masiva'
            else:
                Usuario.objects.filter(pk__in=[usuario.pk for usuario in usuarios]).delete()
                accion_hist = 'Eliminación masiva'
            HistorialUsuario.objects.create(
                usuario=request.user,
                historial_accion=accion_hist,
                historial_detalle=f'{accion_hist} de {len(usuarios)} usuario(s): {nombres}.',
            )
        return Response({
            'mensaje': f'{len(usuarios)} usuario(s) procesado(s).',
            'omitio_propia_cuenta': omitio_propia_cuenta,
        })


class EstudiantesAdminAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    @staticmethod
    def _estudiante(estudiante):
        return {
            'id': estudiante.pk,
            'nombre': estudiante.estudiante_nombre,
            'apellido_paterno': estudiante.estudiante_apaterno,
            'apellido_materno': estudiante.estudiante_amaterno,
            'correo': estudiante.estudiante_correo or '',
            'activo': estudiante.estudiante_activo,
            'curso_id': estudiante.curso_id,
            'curso': (
                f'{estudiante.curso.curso_grado} {estudiante.curso.curso_letra}'
                if estudiante.curso else 'Sin curso asignado'
            ),
            'numero_lista': estudiante.estudiante_numero_lista,
            'identificador': estudiante.estudiante_identificador or '',
        }

    def get(self, request, estudiante_id=None):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar estudiantes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if estudiante_id is not None:
            estudiante = Estudiante.objects.select_related('curso').filter(
                pk=estudiante_id,
            ).first()
            if estudiante is None:
                return Response({'detail': 'No se encontró el estudiante.'}, status=404)
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT caso_id, tipo_falta FROM involucran '
                    'WHERE estudiante_id = %s',
                    [estudiante_id],
                )
                relaciones = cursor.fetchall()
            severidad = {caso_id: tipo_falta for caso_id, tipo_falta in relaciones}
            casos = []
            for caso in Caso.objects.filter(
                pk__in=severidad,
            ).select_related('lugar').order_by('-caso_fecha'):
                texto = caso.caso_descripcion or ''
                titulo = texto.split('] - ', 1)[0].lstrip('[') if '] - ' in texto else texto[:40]
                casos.append({
                    'id': caso.pk,
                    'titulo': titulo or f'Caso #{caso.pk}',
                    'fecha': caso.caso_fecha.isoformat() if caso.caso_fecha else None,
                    'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
                    'gravedad': severidad.get(caso.pk, ''),
                })
            total = len(casos)
            conteo = {
                nivel: sum(item['gravedad'] == nivel for item in casos)
                for nivel in ('Leve', 'Grave', 'Gravísima')
            }
            puntaje = conteo['Leve'] + conteo['Grave'] * 3 + conteo['Gravísima'] * 5
            if puntaje >= 10:
                estado = ('alerta', 'Alerta: requiere intervención')
            elif puntaje >= 5:
                estado = ('atencion', 'Requiere atención')
            elif puntaje:
                estado = ('seguimiento', 'Bajo seguimiento')
            else:
                estado = ('sin_incidencias', 'Sin incidencias')
            return Response({
                'estudiante': self._estudiante(estudiante),
                'casos': casos,
                'total_casos': total,
                'conteo_gravedad': conteo,
                'puntaje_riesgo': puntaje,
                'estado_clave': estado[0],
                'estado_texto': estado[1],
            })

        busqueda = request.query_params.get('busqueda', '').strip()
        curso_id = request.query_params.get('curso', '').strip()
        numero_lista = request.query_params.get('numero_lista', '').strip()
        estado = request.query_params.get('estado', '').strip()
        estudiantes = Estudiante.objects.select_related('curso').all().order_by(
            'curso__curso_grado',
            'curso__curso_letra',
            'estudiante_apaterno',
            'estudiante_nombre',
        )
        if busqueda:
            for termino in _quitar_tildes(busqueda).split():
                estudiantes = estudiantes.filter(
                    Q(estudiante_nombre__icontains=termino)
                    | Q(estudiante_apaterno__icontains=termino)
                    | Q(estudiante_amaterno__icontains=termino)
                    | Q(estudiante_identificador__icontains=termino)
                )
        if curso_id:
            if not curso_id.isdigit():
                return Response(
                    {'detail': 'El filtro de curso no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            estudiantes = estudiantes.filter(curso_id=int(curso_id))
        if numero_lista:
            if not numero_lista.isdigit():
                return Response(
                    {'detail': 'El número de lista no es válido.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            estudiantes = estudiantes.filter(estudiante_numero_lista=int(numero_lista))
        if estado in ('activo', 'inactivo'):
            estudiantes = estudiantes.filter(estudiante_activo=(estado == 'activo'))
        elif estado:
            return Response(
                {'detail': 'El filtro de estado no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pagina = Paginator(estudiantes, 10).get_page(
            request.query_params.get('pagina'),
        )
        return Response({
            'resultados': [self._estudiante(item) for item in pagina],
            'pagina': pagina.number,
            'total_paginas': pagina.paginator.num_pages,
            'total': pagina.paginator.count,
            'tiene_anterior': pagina.has_previous(),
            'tiene_siguiente': pagina.has_next(),
            'cursos': [
                {'id': curso.pk, 'nombre': f'{curso.curso_grado} {curso.curso_letra}'}
                for curso in Curso.objects.all().order_by(
                    'curso_grado', 'curso_letra',
                )
            ],
            'importaciones': [
                {
                    'archivo': item.archivo,
                    'realizado_en': item.realizado_en.isoformat(),
                    'importador': item.usuario_correo_importo,
                    'alumnos_agregados': item.alumnos_agregados,
                    'duplicados_detectados': item.duplicados_detectados,
                    'filas_omitidas': item.filas_omitidas,
                }
                for item in HistorialImportacionEstudiantes.objects.all()[:10]
            ],
        })

    def post(self, request, estudiante_id=None):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar estudiantes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if estudiante_id is None and hasattr(request.data, 'get') and request.data.get('archivo_excel'):
            return self._importar(request)
        estudiante = (
            Estudiante.objects.filter(pk=estudiante_id).first()
            if estudiante_id is not None else None
        )
        if estudiante_id is not None and estudiante is None:
            return Response({'detail': 'No se encontró el estudiante.'}, status=404)
        datos = request.data
        nombre = datos.get('nombre', '').strip() if isinstance(datos.get('nombre'), str) else ''
        apaterno = datos.get('apellido_paterno', '').strip() if isinstance(datos.get('apellido_paterno'), str) else ''
        amaterno = datos.get('apellido_materno', '').strip() if isinstance(datos.get('apellido_materno'), str) else ''
        correo = datos.get('correo', '').strip() if isinstance(datos.get('correo'), str) else ''
        try:
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError('Completa los nombres y apellidos del estudiante.')
            if correo:
                validate_email(correo)
            curso = Curso.objects.get(pk=int(datos.get('curso_id')))
            numero_lista_raw = datos.get('numero_lista')
            numero_lista = int(numero_lista_raw) if numero_lista_raw not in (None, '') else None
            if numero_lista is not None and numero_lista < 0:
                raise ValidationError('El número de lista no puede ser negativo.')
            if numero_lista and Estudiante.objects.filter(
                curso=curso,
                estudiante_numero_lista=numero_lista,
            ).exclude(pk=estudiante.pk if estudiante else None).exists():
                raise ValidationError('Ese número de lista ya está usado en el curso.')
            if estudiante is None:
                estudiante = Estudiante()
            estudiante.estudiante_nombre = nombre
            estudiante.estudiante_apaterno = apaterno
            estudiante.estudiante_amaterno = amaterno
            estudiante.estudiante_correo = correo or None
            estudiante.curso = curso
            estudiante.estudiante_numero_lista = numero_lista
            estudiante.estudiante_activo = datos.get('activo', estudiante.estudiante_activo or True)
            if not isinstance(estudiante.estudiante_activo, bool):
                raise ValidationError('El estado debe ser verdadero o falso.')
            estudiante.save()
            return Response(
                {'estudiante': self._estudiante(estudiante)},
                status=status.HTTP_200_OK if estudiante_id else status.HTTP_201_CREATED,
            )
        except (ValidationError, ValueError, TypeError, Curso.DoesNotExist) as error:
            detail = ' '.join(error.messages) if isinstance(error, ValidationError) else 'Selecciona un curso y número de lista válidos.'
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, estudiante_id=None):
        if estudiante_id is None:
            return Response(
                {'detail': 'Falta el identificador del estudiante.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.post(request, estudiante_id)

    def _importar(self, request):
        archivo = request.FILES.get('archivo_excel')
        if not archivo or not archivo.name.lower().endswith('.xlsx'):
            return Response(
                {'detail': 'Selecciona un archivo Excel .xlsx válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if archivo.size > 10 * 1024 * 1024:
            return Response(
                {'detail': 'El archivo supera el límite de 10 MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            hoja = load_workbook(archivo, data_only=True).active
        except Exception:
            return Response(
                {'detail': 'No se pudo leer el archivo Excel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        agregados, duplicados, errores = [], [], []
        omitidos = 0
        for numero_fila, fila in enumerate(
            hoja.iter_rows(min_row=2, max_col=6, values_only=True),
            start=2,
        ):
            if not fila or all(valor is None or not str(valor).strip() for valor in fila):
                continue
            try:
                nombre, apaterno, amaterno = (
                    str(fila[indice]).strip() if fila[indice] is not None else ''
                    for indice in range(3)
                )
                grado_valor, letra_valor = fila[3], fila[4]
                if not all((nombre, apaterno, amaterno, grado_valor is not None, letra_valor)):
                    raise ValueError('faltan datos obligatorios')
                grado = (
                    f'{int(grado_valor)}° Medio'
                    if isinstance(grado_valor, (int, float))
                    else str(grado_valor).strip()
                )
                if grado.isdigit():
                    grado = f'{grado}° Medio'
                curso = Curso.objects.filter(
                    curso_grado__iexact=grado,
                    curso_letra__iexact=str(letra_valor).strip(),
                ).first()
                if curso is None:
                    raise ValueError(f'el curso {grado} {letra_valor} no existe')
                raw_lista = fila[5]
                lista = int(raw_lista) if raw_lista not in (None, '') and str(raw_lista).strip().isdigit() else None
                if lista and Estudiante.objects.filter(
                    curso=curso,
                    estudiante_numero_lista=lista,
                ).exists():
                    lista = None
                    errores.append(f'Fila {numero_fila}: número de lista duplicado; se omitió ese número.')
                estudiante, creado = Estudiante.objects.get_or_create(
                    estudiante_nombre=nombre,
                    estudiante_apaterno=apaterno,
                    estudiante_amaterno=amaterno,
                    curso=curso,
                    defaults={'estudiante_numero_lista': lista},
                )
                if creado:
                    agregados.append(
                        f'{nombre} {apaterno} {amaterno} ({grado} {curso.curso_letra})'
                    )
                else:
                    duplicados.append(f'{nombre} {apaterno} {amaterno} ({grado} {curso.curso_letra})')
                    omitidos += 1
            except Exception as error:
                logger.info('Fila %s del Excel no importada: %s', numero_fila, error)
                errores.append(f'Fila {numero_fila}: {error}')
                omitidos += 1
        HistorialImportacionEstudiantes.objects.create(
            archivo=os.path.basename(archivo.name)[:255],
            usuario_id_importo=request.user.pk,
            usuario_correo_importo=request.user.usuario_correo,
            alumnos_agregados=agregados,
            duplicados_detectados=duplicados,
            filas_omitidas=omitidos,
        )
        return Response({
            'agregados': agregados,
            'duplicados': duplicados,
            'omitidos': omitidos,
            'errores': errores[:20],
            'mensaje': f'Importación completada: {len(agregados)} nuevos, {omitidos} omitidos.',
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, estudiante_id=None):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar estudiantes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        estudiante = Estudiante.objects.filter(pk=estudiante_id).first()
        if estudiante is None:
            return Response({'detail': 'No se encontró el estudiante.'}, status=404)
        activo = request.data.get('activo')
        if not isinstance(activo, bool):
            return Response(
                {'detail': 'Indica el estado activo como verdadero o falso.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        estudiante.estudiante_activo = activo
        estudiante.save(update_fields=['estudiante_activo'])
        return Response({'estudiante': self._estudiante(estudiante)})

    def delete(self, request, estudiante_id=None):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar estudiantes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        estudiante = Estudiante.objects.filter(pk=estudiante_id).first()
        if estudiante is None:
            return Response({'detail': 'No se encontró el estudiante.'}, status=404)
        estudiante.estudiante_activo = False
        estudiante.save(update_fields=['estudiante_activo'])
        return Response({'mensaje': 'El estudiante fue desactivado; sus antecedentes se conservaron.'})


class HistorialUsuariosAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede consultar el historial.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = HistorialUsuario.objects.select_related('usuario').order_by(
            '-historial_fecha',
        )
        usuario_id = request.query_params.get('usuario', '').strip()
        accion = request.query_params.get('accion', '').strip()
        busqueda = request.query_params.get('busqueda', '').strip()
        desde = parse_date(request.query_params.get('fecha_desde', ''))
        hasta = parse_date(request.query_params.get('fecha_hasta', ''))
        if usuario_id:
            if not usuario_id.isdigit():
                return Response({'detail': 'Selecciona un usuario válido.'}, status=400)
            queryset = queryset.filter(usuario_id=int(usuario_id))
        if accion:
            queryset = queryset.filter(historial_accion=accion)
        if busqueda:
            queryset = queryset.filter(
                Q(historial_detalle__icontains=busqueda)
                | Q(usuario__usuario_nombre__icontains=busqueda)
                | Q(usuario__usuario_apaterno__icontains=busqueda)
                | Q(usuario__usuario_amaterno__icontains=busqueda)
            )
        if desde:
            queryset = queryset.filter(historial_fecha__date__gte=desde)
        if hasta:
            queryset = queryset.filter(historial_fecha__date__lte=hasta)
        pagina = Paginator(queryset, 30).get_page(request.query_params.get('pagina'))
        return Response({
            'resultados': [
                {
                    'id': item.pk,
                    'usuario_id': item.usuario_id,
                    'usuario': (
                        f'{item.usuario.usuario_nombre} {item.usuario.usuario_apaterno}'
                        if item.usuario else 'Usuario eliminado'
                    ),
                    'accion': item.historial_accion,
                    'detalle': item.historial_detalle,
                    'fecha': item.historial_fecha.isoformat(),
                }
                for item in pagina
            ],
            'pagina': pagina.number,
            'total_paginas': pagina.paginator.num_pages,
            'total': pagina.paginator.count,
            'acciones': list(
                HistorialUsuario.objects.order_by('historial_accion')
                .values_list('historial_accion', flat=True).distinct()
            ),
            'usuarios': [
                {'id': item.pk, 'nombre': f'{item.usuario_nombre} {item.usuario_apaterno}'}
                for item in Usuario.objects.filter(
                    historial_acciones__isnull=False,
                ).distinct().order_by('usuario_apaterno', 'usuario_nombre')
            ],
        })

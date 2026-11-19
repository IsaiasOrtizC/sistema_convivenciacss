"""JWT endpoints for administrative user and student workflows."""

import logging
import os
import re

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

_VALORES_NULOS_API = {"", "-", "--", "n/a", "na", "null", "none", "undefined", "nan"}
_CURSO_COMPACTO_API_RE = re.compile(r"^\s*(\d+)\s*(?:[°ºo.]*\s*)?([A-Za-zÁÉÍÓÚáéíóú]+)?\s*$")
_ALIASES_COLUMNAS_API = {
    "nombre_completo": {"nombre completo", "alumno", "estudiante", "nombre alumno", "nombre estudiante"},
    "nombre": {"nombres", "nombre", "primer nombre"},
    "apaterno": {"apellido paterno", "ap. paterno", "ap paterno", "apaterno", "paterno"},
    "amaterno": {"apellido materno", "ap. materno", "ap materno", "amaterno", "materno"},
    "curso": {"curso", "codigo curso", "código curso"},
    "grado": {"grado", "nivel", "enseñanza", "ensenanza"},
    "paralelo": {"paralelo", "letra", "seccion", "sección"},
    "lista": {"número de lista", "numero de lista", "n° lista", "no. lista", "nro lista", "lista", "n lista"},
}


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


def _limpiar_celda_api(valor):
    """Anula celdas vacías o con valores basura devolviendo None; si sirve, retorna texto limpio."""
    if valor is None:
        return None
    texto = " ".join(str(valor).strip().split())
    if texto.lower() in _VALORES_NULOS_API:
        return None
    return texto


def _normalizar_col_api(texto: str) -> str:
    """Normaliza tildes, espacios y mayúsculas para comparar encabezados."""
    return " ".join(_quitar_tildes(texto).strip().lower().split())


def _detectar_columnas_api(filas_crudas):
    """Busca la fila de encabezados y devuelve (indice_fila, {campo: indice_col}, aliases_norm_global)."""
    aliases_norm_global = {
        _normalizar_col_api(alias)
        for aliases in _ALIASES_COLUMNAS_API.values()
        for alias in aliases
    }
    for idx, fila in enumerate(filas_crudas):
        limpias = [_limpiar_celda_api(c) for c in fila]
        if not any(limpias):
            continue

        mapa_col = {}
        for col_idx, celda in enumerate(limpias):
            if not celda:
                continue
            clave_norm = _normalizar_col_api(celda)
            for campo, aliases in _ALIASES_COLUMNAS_API.items():
                if clave_norm in {_normalizar_col_api(a) for a in aliases} and campo not in mapa_col:
                    mapa_col[campo] = col_idx
                    break

        tiene_nombre = "nombre_completo" in mapa_col or "nombre" in mapa_col
        tiene_contexto = any(k in mapa_col for k in ("apaterno", "curso", "grado"))
        if tiene_nombre and tiene_contexto:
            return idx, mapa_col, aliases_norm_global

    return None, {}, aliases_norm_global


def _separar_nombre_completo_api(nombre_completo: str):
    """Separa un nombre completo en (nombre, apaterno, amaterno)."""
    partes = [p for p in nombre_completo.split() if p]
    if len(partes) >= 3:
        return " ".join(partes[2:]), partes[0], partes[1]
    if len(partes) == 2:
        return partes[1], partes[0], ""
    return (partes[0] if partes else ""), "", ""


def _parsear_curso_api(curso_val, grado_val, paralelo_val):
    """Extrae (grado_formateado, letra_paralelo) desde columnas separadas o combinadas."""
    curso_limpio = _limpiar_celda_api(curso_val)
    grado_limpio = _limpiar_celda_api(grado_val)
    paralelo_limpio = _limpiar_celda_api(paralelo_val)

    if grado_limpio:
        match_g = _CURSO_COMPACTO_API_RE.match(grado_limpio)
        grado_fmt = f"{int(match_g.group(1))}° Medio" if match_g else grado_limpio
        letra_fmt = (
            paralelo_limpio
            or (match_g.group(2) if match_g and match_g.group(2) else "")
        ).strip().upper()
        return grado_fmt, letra_fmt

    if curso_limpio:
        match_c = _CURSO_COMPACTO_API_RE.match(curso_limpio)
        if match_c:
            num = int(match_c.group(1))
            resto = (match_c.group(2) or "").strip()
            if paralelo_limpio:
                return f"{num}° Medio", paralelo_limpio.upper()
            if len(resto) > 1 and resto[-1].isalpha():
                return f"{num}° Medio", resto[-1].upper()
            if resto.isalpha():
                return f"{num}° Medio", resto.upper()
            return f"{num}° Medio", ""
        return curso_limpio, (paralelo_limpio or "").upper()

    return "", (paralelo_limpio or "").upper()


def _es_fila_ruido_api(valores_utiles: list[str], aliases_norm_global: set[str]) -> bool:
    """Descarta filas de encabezado institucional, totales o repeticiones de cabecera."""
    if not valores_utiles:
        return True
    union = " ".join(v.lower() for v in valores_utiles)
    ruidos = (
        "colegio particular",
        "listado simple de alumnos",
        "fono ",
        "contacto@",
        "total alumnos",
        "subtotal",
        "registros válidos",
        "registros validos",
    )
    if any(r in union for r in ruidos):
        return True

    coincidencias_header = sum(
        1 for v in valores_utiles if _normalizar_col_api(v) in aliases_norm_global
    )
    return coincidencias_header >= 2


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
                    Q(usuario_nombre__unaccent__icontains=termino)
                    | Q(usuario_apaterno__unaccent__icontains=termino)
                    | Q(usuario_amaterno__unaccent__icontains=termino)
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
            usuarios = usuarios.filter(
                usuario_activo=True,
                usuario_bloqueado=False,
            )
        elif estado == 'inactivo':
            usuarios = usuarios.filter(usuario_activo=False)
        elif estado == 'bloqueado':
            usuarios = usuarios.filter(usuario_bloqueado=True)
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
                    Q(estudiante_nombre__unaccent__icontains=termino)
                    | Q(estudiante_apaterno__unaccent__icontains=termino)
                    | Q(estudiante_amaterno__unaccent__icontains=termino)
                    | Q(estudiante_identificador__unaccent__icontains=termino)
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
            if numero_lista is not None and Estudiante.objects.filter(
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
            estudiante.estudiante_activo = datos.get(
                'activo',
                estudiante.estudiante_activo if estudiante.pk else True,
            )
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
            libro = load_workbook(archivo, data_only=True)
            hoja = libro.active
            filas_crudas = list(hoja.iter_rows(values_only=True))
            libro.close()
        except Exception:
            return Response(
                {'detail': 'No se pudo leer el archivo Excel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        idx_header, mapa_col, aliases_norm_global = _detectar_columnas_api(filas_crudas)
        if idx_header is None:
            return Response(
                {
                    'detail': (
                        'No se encontraron columnas reconocibles de estudiante '
                        '(nombre/nombre completo, apellido o curso/grado) en el Excel.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        def _celda_campo(fila_limpia, campo):
            col_idx = mapa_col.get(campo)
            if col_idx is not None and col_idx < len(fila_limpia):
                return fila_limpia[col_idx]
            return None

        agregados, duplicados, errores = [], [], []
        omitidos = 0

        for offset, fila in enumerate(filas_crudas[idx_header + 1:], start=idx_header + 2):
            fila_limpia = [_limpiar_celda_api(valor) for valor in fila]
            valores_utiles = [v for v in fila_limpia if v is not None]

            if _es_fila_ruido_api(valores_utiles, aliases_norm_global):
                continue

            try:
                nombre_completo = _celda_campo(fila_limpia, "nombre_completo")
                if nombre_completo:
                    nombre, apaterno, amaterno = _separar_nombre_completo_api(nombre_completo)
                    nombre = _celda_campo(fila_limpia, "nombre") or nombre
                    apaterno = _celda_campo(fila_limpia, "apaterno") or apaterno
                    amaterno = _celda_campo(fila_limpia, "amaterno") or amaterno
                else:
                    nombre = _celda_campo(fila_limpia, "nombre") or ""
                    apaterno = _celda_campo(fila_limpia, "apaterno") or ""
                    amaterno = _celda_campo(fila_limpia, "amaterno") or ""

                grado, letra = _parsear_curso_api(
                    _celda_campo(fila_limpia, "curso"),
                    _celda_campo(fila_limpia, "grado"),
                    _celda_campo(fila_limpia, "paralelo"),
                )

                if not all((nombre, apaterno, grado, letra)):
                    raise ValueError('faltan datos obligatorios (nombre, apellido o curso)')

                amaterno = amaterno or ""
                curso = Curso.objects.filter(
                    curso_grado__iexact=grado,
                    curso_letra__iexact=letra,
                ).first()
                if curso is None:
                    raise ValueError(f'el curso {grado} {letra} no existe')

                raw_lista = _limpiar_celda_api(_celda_campo(fila_limpia, "lista"))
                lista = None
                if raw_lista:
                    if raw_lista.endswith('.0') and raw_lista[:-2].isdigit():
                        raw_lista = raw_lista[:-2]
                    if raw_lista.isdigit():
                        cand = int(raw_lista)
                        if 1 <= cand <= 99:
                            lista = cand

                if lista is not None and Estudiante.objects.filter(
                    curso=curso,
                    estudiante_numero_lista=lista,
                ).exists():
                    lista = None
                    errores.append(f'Fila {offset}: número de lista duplicado; se omitió ese número.')

                estudiante, creado = Estudiante.objects.get_or_create(
                    estudiante_nombre=nombre,
                    estudiante_apaterno=apaterno,
                    estudiante_amaterno=amaterno,
                    curso=curso,
                    defaults={'estudiante_numero_lista': lista},
                )
                if creado:
                    agregados.append(
                        f'{nombre} {apaterno} {amaterno} ({grado} {curso.curso_letra})'.strip()
                    )
                else:
                    duplicados.append(
                        f'{nombre} {apaterno} {amaterno} ({grado} {curso.curso_letra})'.strip()
                    )
                    omitidos += 1
            except Exception as error:
                logger.info('Fila %s del Excel no importada: %s', offset, error)
                errores.append(f'Fila {offset}: {error}')
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
        es_administrador = _es_administrador(request)
        queryset = HistorialUsuario.objects.select_related('usuario').order_by(
            '-historial_fecha',
        )
        if not es_administrador:
            queryset = queryset.filter(usuario_id=request.user.pk)
        usuario_id = request.query_params.get('usuario', '').strip()
        accion = request.query_params.get('accion', '').strip()
        busqueda = request.query_params.get('busqueda', '').strip()
        desde = parse_date(request.query_params.get('fecha_desde', ''))
        hasta = parse_date(request.query_params.get('fecha_hasta', ''))
        if usuario_id and es_administrador:
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
                queryset.order_by('historial_accion')
                .values_list('historial_accion', flat=True).distinct()
            ),
            'usuarios': [
                {'id': item.pk, 'nombre': f'{item.usuario_nombre} {item.usuario_apaterno}'}
                for item in (Usuario.objects.filter(
                    historial_acciones__isnull=False,
                ).distinct().order_by('usuario_apaterno', 'usuario_nombre') if es_administrador else [])
            ],
        })
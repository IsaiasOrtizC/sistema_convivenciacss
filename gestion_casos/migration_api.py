"""JWT endpoints for the remaining course and global-search screens."""

from types import SimpleNamespace

from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .controllers.auth_casos_controller import caso_visible_para_curso
from .controllers.report_controller import (
    descargar_caso_pdf_view,
    descargar_caso_xlsx_view,
    descargar_casos_pdf_view,
    descargar_casos_xlsx_view,
    estadisticas_pdf_view,
    estadisticas_xlsx_view,
)
from .models import (
    Caso,
    Estudiante,
    ProfesorJefe,
    SolicitudCaso,
    Usuario,
    _quitar_tildes,
)
from .services.caso_service import filtrar_casos_del_curso


def _rol_nombre(user):
    rol = getattr(user, 'rol', None)
    return (getattr(rol, 'rol_nombre', '') or '').strip()


def _es_rol_profesor(user):
    return 'profesor' in _rol_nombre(user).casefold()


def _usuario_habilitado(user):
    return bool(
        getattr(user, 'usuario_activo', True)
        and not getattr(user, 'usuario_bloqueado', False)
    )


def _profesor_curso(user):
    if not _es_rol_profesor(user):
        return None
    return (
        ProfesorJefe.objects
        .select_related('curso')
        .filter(usuario_id=user.pk, curso__isnull=False)
        .first()
    )


def _course_filters(request):
    raw_desde = request.query_params.get('fecha_desde', '').strip()
    raw_hasta = request.query_params.get('fecha_hasta', '').strip()
    desde = parse_date(raw_desde) if raw_desde else None
    hasta = parse_date(raw_hasta) if raw_hasta else None
    if (raw_desde and desde is None) or (raw_hasta and hasta is None):
        return None, Response(
            {'detail': 'Las fechas del filtro deben tener formato válido (AAAA-MM-DD).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    gravedad = request.query_params.get('gravedad', '').strip()
    if gravedad not in ('', 'Leve', 'Grave', 'Gravísima'):
        return None, Response(
            {'detail': 'Selecciona una gravedad válida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde
    filtros = {
        'fecha_desde': desde.isoformat() if desde else '',
        'fecha_hasta': hasta.isoformat() if hasta else '',
        'gravedad': gravedad,
    }
    return filtros, None


def _legacy_request(request):
    return SimpleNamespace(
        session={
            'usuario_id': request.user.pk,
            'usuario_rol': _rol_nombre(request.user),
        },
        GET=request.query_params,
    )


class MiCursoAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not _usuario_habilitado(request.user):
            return Response(
                {'detail': 'Tu cuenta se encuentra desactivada o bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        profesor = _profesor_curso(request.user)
        if profesor is None:
            return Response(
                {'detail': 'Esta sección requiere una cuenta de Profesor Jefe con curso asignado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        filtros, error = _course_filters(request)
        if error:
            return error

        legacy_request = SimpleNamespace(GET=filtros)
        casos, filtros = filtrar_casos_del_curso(legacy_request, profesor.curso)
        solicitudes = (
            SolicitudCaso.objects
            .filter(solicitante=request.user)
            .select_related('lugar', 'revisada_por')[:10]
        )
        return Response({
            'curso': {
                'id': profesor.curso_id,
                'nombre': str(profesor.curso),
            },
            'casos': [
                {
                    **caso,
                    'fecha': caso['fecha'].isoformat() if caso['fecha'] else None,
                }
                for caso in casos
            ],
            'solicitudes': [
                {
                    'id': solicitud.pk,
                    'titulo': solicitud.titulo,
                    'fecha_evento': solicitud.fecha_evento.isoformat(),
                    'estado': solicitud.estado,
                    'lugar': solicitud.lugar.lugar_nombre,
                    'comentario_revision': solicitud.comentario_revision,
                    'revisada_por': (
                        f'{solicitud.revisada_por.usuario_nombre} '
                        f'{solicitud.revisada_por.usuario_apaterno}'.strip()
                        if solicitud.revisada_por else ''
                    ),
                }
                for solicitud in solicitudes
            ],
            'filtros': filtros,
        })


class BusquedaGlobalAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not _usuario_habilitado(request.user):
            return Response(
                {'detail': 'Tu cuenta se encuentra desactivada o bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if _es_rol_profesor(request.user):
            return Response(
                {'detail': 'El buscador global no está disponible para Profesor Jefe.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        query = request.query_params.get('q', '').strip()
        resultados = {'estudiantes': [], 'casos': [], 'usuarios': []}
        if len(query) < 2:
            return Response(resultados)
        if len(query) > 100:
            return Response(
                {'detail': 'La búsqueda no puede superar 100 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_normalizada = _quitar_tildes(query)
        rut_normalizado = query.upper().replace('.', '').strip()

        # ---- Estudiantes ----
        estudiantes = (
            Estudiante.objects
            .select_related('curso')
            .annotate(
                nombre_completo_db=Concat(
                    'estudiante_nombre',
                    Value(' '),
                    'estudiante_apaterno',
                    Value(' '),
                    'estudiante_amaterno',
                )
            )
            .filter(
                Q(nombre_completo_db__unaccent__icontains=query_normalizada)
                | Q(estudiante_identificador__icontains=rut_normalizado)
            )
            .order_by('estudiante_apaterno', 'estudiante_nombre')[:8]
        )
        resultados['estudiantes'] = [
            {
                'id': estudiante.pk,
                'nombre_completo': estudiante.nombre_completo,
                'curso': str(estudiante.curso) if estudiante.curso else 'Sin curso asignado',
            }
            for estudiante in estudiantes
        ]

        # ---- Casos (por #ID, descripción o alumno involucrado) ----
        filtro_casos = (
            Q(caso_descripcion__unaccent__icontains=query_normalizada)
            | Q(estudiantes__estudiante_nombre__unaccent__icontains=query_normalizada)
            | Q(estudiantes__estudiante_apaterno__unaccent__icontains=query_normalizada)
        )
        codigo_numerico = query.lstrip('#').strip()
        if codigo_numerico.isdigit():
            filtro_casos |= Q(caso_id=int(codigo_numerico))

        casos = (
            Caso.objects
            .filter(filtro_casos)
            .select_related('lugar')
            .distinct()
            .order_by('-caso_fecha', '-caso_id')[:8]
        )
        for caso in casos:
            texto = caso.caso_descripcion or ''
            titulo = texto
            if '] -' in texto:
                titulo = texto.split('] -', 1)[0].replace('[', '').strip()
            resultados['casos'].append({
                'id': caso.pk,
                'titulo': titulo or f'Caso #{caso.pk}',
                'fecha': caso.caso_fecha.isoformat() if caso.caso_fecha else '',
                'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
            })

        # ---- Funcionarios activos ----
        usuarios = (
            Usuario.objects
            .select_related('rol')
            .annotate(
                nombre_completo_db=Concat(
                    'usuario_nombre',
                    Value(' '),
                    'usuario_apaterno',
                    Value(' '),
                    'usuario_amaterno',
                )
            )
            .filter(usuario_activo=True)
            .filter(
                Q(nombre_completo_db__unaccent__icontains=query_normalizada)
                | Q(usuario_correo__icontains=query)
            )
            .order_by('usuario_apaterno', 'usuario_nombre')[:6]
        )
        resultados['usuarios'] = [
            {
                'id': usuario.pk,
                'nombre_completo': usuario.nombre_completo,
                'correo': usuario.usuario_correo,
                'rol': _rol_nombre(usuario),
            }
            for usuario in usuarios
        ]
        return Response(resultados)


class CasoExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, caso_id, formato):
        if not _usuario_habilitado(request.user):
            return Response(
                {'detail': 'Tu cuenta se encuentra desactivada o bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        rol = _rol_nombre(request.user)
        if rol not in ('Administrador', 'Inspector', 'PConvivencia') and not _es_rol_profesor(request.user):
            return Response({'detail': 'No tienes permiso para exportar casos.'}, status=status.HTTP_403_FORBIDDEN)

        get_object_or_404(Caso, pk=caso_id)
        if _es_rol_profesor(request.user):
            profesor = _profesor_curso(request.user)
            if not profesor or not caso_visible_para_curso(caso_id, profesor.curso):
                return Response(
                    {'detail': 'Ese caso no corresponde exclusivamente a tu curso.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        view = descargar_caso_pdf_view if formato == 'pdf' else descargar_caso_xlsx_view
        return view(_legacy_request(request), caso_id)


class MiCursoExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, formato):
        if not _usuario_habilitado(request.user):
            return Response(
                {'detail': 'Tu cuenta se encuentra desactivada o bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if _profesor_curso(request.user) is None:
            return Response(
                {'detail': 'Esta descarga requiere un Profesor Jefe con curso asignado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        filtros, error = _course_filters(request)
        if error:
            return error

        legacy_request = SimpleNamespace(
            session={
                'usuario_id': request.user.pk,
                'usuario_rol': _rol_nombre(request.user),
            },
            GET=filtros,
        )
        view = descargar_casos_pdf_view if formato == 'pdf' else descargar_casos_xlsx_view
        return view(legacy_request)


class EstadisticasExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, formato):
        if not _usuario_habilitado(request.user):
            return Response(
                {'detail': 'Tu cuenta se encuentra desactivada o bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if _rol_nombre(request.user) not in ('Administrador', 'Inspector', 'PConvivencia'):
            return Response(
                {'detail': 'No tienes permiso para exportar estadísticas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        view = estadisticas_pdf_view if formato == 'pdf' else estadisticas_xlsx_view
        return view(_legacy_request(request))
"""JWT endpoints for the remaining course and global-search screens."""

from types import SimpleNamespace

from django.db.models import Q
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


def _profesor_curso(user):
    if user.rol.rol_nombre != 'Profesor Jefe':
        return None
    return ProfesorJefe.objects.select_related('curso').filter(
        usuario_id=user.pk,
        curso__isnull=False,
    ).first()


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
            'usuario_rol': request.user.rol.rol_nombre,
        },
        GET=request.query_params,
    )


class MiCursoAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
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
        solicitudes = SolicitudCaso.objects.filter(
            solicitante=request.user,
        ).select_related('lugar', 'revisada_por')[:10]
        return Response({
            'curso': {
                'id': profesor.curso_id,
                'nombre': f'{profesor.curso.curso_grado} {profesor.curso.curso_letra}',
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
                        f'{solicitud.revisada_por.usuario_apaterno}'
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
        if request.user.rol.rol_nombre == 'Profesor Jefe':
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
        estudiantes = Estudiante.objects.select_related('curso').filter(
            Q(estudiante_nombre__unaccent__icontains=query_normalizada)
            | Q(estudiante_apaterno__unaccent__icontains=query_normalizada)
            | Q(estudiante_amaterno__unaccent__icontains=query_normalizada)
            | Q(estudiante_identificador__icontains=query.upper())
        )[:8]
        resultados['estudiantes'] = [
            {
                'id': estudiante.pk,
                'nombre_completo': (
                    f'{estudiante.estudiante_nombre} '
                    f'{estudiante.estudiante_apaterno} '
                    f'{estudiante.estudiante_amaterno}'
                ).strip(),
                'curso': (
                    f'{estudiante.curso.curso_grado} {estudiante.curso.curso_letra}'
                    if estudiante.curso else 'Sin curso asignado'
                ),
            }
            for estudiante in estudiantes
        ]

        casos = Caso.objects.filter(
            caso_descripcion__unaccent__icontains=query_normalizada,
        ).select_related('lugar').order_by('-caso_fecha')[:8]
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

        usuarios = Usuario.objects.select_related('rol').filter(
            Q(usuario_nombre__unaccent__icontains=query_normalizada)
            | Q(usuario_apaterno__unaccent__icontains=query_normalizada)
            | Q(usuario_amaterno__unaccent__icontains=query_normalizada)
            | Q(usuario_correo__icontains=query)
        )[:6]
        resultados['usuarios'] = [
            {
                'id': usuario.pk,
                'nombre_completo': (
                    f'{usuario.usuario_nombre} '
                    f'{usuario.usuario_apaterno} '
                    f'{usuario.usuario_amaterno}'
                ).strip(),
                'correo': usuario.usuario_correo,
                'rol': usuario.rol.rol_nombre if usuario.rol else '',
            }
            for usuario in usuarios
        ]
        return Response(resultados)


class CasoExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, caso_id, formato):
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=400)
        rol = request.user.rol.rol_nombre
        if rol not in ('Administrador', 'Inspector', 'PConvivencia', 'Profesor Jefe'):
            return Response({'detail': 'No tienes permiso para exportar casos.'}, status=403)
        get_object_or_404(Caso, pk=caso_id)
        if rol == 'Profesor Jefe':
            profesor = _profesor_curso(request.user)
            if not profesor or not caso_visible_para_curso(
                caso_id,
                profesor.curso,
            ):
                return Response(
                    {'detail': 'Ese caso no corresponde exclusivamente a tu curso.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        view = descargar_caso_pdf_view if formato == 'pdf' else descargar_caso_xlsx_view
        return view(_legacy_request(request), caso_id)


class MiCursoExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, formato):
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=400)
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
                'usuario_rol': request.user.rol.rol_nombre,
            },
            GET=filtros,
        )
        view = descargar_casos_pdf_view if formato == 'pdf' else descargar_casos_xlsx_view
        return view(legacy_request)


class EstadisticasExportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, formato):
        if formato not in ('pdf', 'xlsx'):
            return Response({'detail': 'Formato de descarga inválido.'}, status=400)
        if request.user.rol.rol_nombre not in ('Administrador', 'Inspector', 'PConvivencia'):
            return Response({'detail': 'No tienes permiso para exportar estadísticas.'}, status=403)
        view = estadisticas_pdf_view if formato == 'pdf' else estadisticas_xlsx_view
        return view(_legacy_request(request))

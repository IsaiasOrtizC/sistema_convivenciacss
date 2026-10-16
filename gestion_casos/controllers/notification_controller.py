"""Notification Controller: bandeja de notificaciones de casos, cambios y eventos."""

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..models import (
    HistorialNotificacion,
    Involucran,
    Notificacion,
    ReglaInstitucional,
    SeguimientoCaso,
    VersionReglamento,
)
from ..permissions import ROLES_GESTION_SEGUIMIENTO, rol_seguimiento_permitido
from ..services.seguimiento_service import obtener_filas_seguimiento


#vistas de notificaciones
def notificaciones_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para consultar el módulo de seguimiento.")

    id_usuario = request.session['usuario_id']

    alertas_reales = list(
        Notificacion.objects
        .filter(Q(usuario_id=id_usuario) | Q(regla__isnull=False))
        .select_related(
            'caso', 'estudiante', 'regla', 'regla__version',
            'version_reglamento', 'responsable',
        )
        .prefetch_related('historial_estados__cambiado_por')
        .distinct()
        .order_by('-notificacion_fecha')
    )
    caso_ids = {alerta.caso_id for alerta in alertas_reales if alerta.caso_id}
    categorias_por_caso = {}
    for caso_id, categoria in Involucran.objects.filter(
        caso_id__in=caso_ids,
    ).values_list('caso_id', 'tipo_falta'):
        categorias_por_caso.setdefault(caso_id, set()).add(categoria)

    categoria_css_por_gravedad = {
        'Leve': 'leve',
        'Grave': 'grave',
        'Gravísima': 'gravisima',
    }
    for alerta in alertas_reales:
        alerta.url_caso = _url_caso_notificacion(alerta)
        alerta.notificacion_mensaje = _mensaje_notificacion_seguro(alerta)
        categorias = sorted(categorias_por_caso.get(alerta.caso_id, set()))
        alerta.categoria_falta = ', '.join(categorias) or 'No especificada'
        alerta.categoria_css = (
            categoria_css_por_gravedad.get(categorias[0], 'sin-clasificar')
            if len(categorias) == 1
            else 'sin-clasificar'
        )
        regla = alerta.regla
        alerta.regla_operativa = _regla_notificacion_operativa(regla)
        if regla and not alerta.regla_operativa:
            alerta.notificacion_titulo = 'Referencia reglamentaria para revisión'
            alerta.notificacion_mensaje = (
                'La disposición asociada no está actualmente aprobada y vigente '
                'para orientar acciones. Revisa el detalle del caso y consulta '
                'al personal autorizado.'
            )

    filtro_estado = request.GET.get('estado_seguimiento', '')
    if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
        filtro_estado = ''
    context = {
        'notificaciones': alertas_reales,
        'filas_seguimiento': obtener_filas_seguimiento(filtro_estado),
        'filtro_estado': filtro_estado,
        'puede_gestionar': request.session.get('usuario_rol') in ROLES_GESTION_SEGUIMIENTO,
        'hoy': timezone.localdate(),
        'estados_notificacion': Notificacion.Estado.choices,
    }

    return render(
        request,
        'gestion_casos/notificaciones.html',
        context
    )


def marcar_notificacion_leida_view(request, notificacion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para modificar esta notificación.")

    if request.method != 'POST':
        return redirect('notificaciones')

    notificacion = get_object_or_404(
        Notificacion.objects.filter(
            Q(usuario_id=request.session['usuario_id']) | Q(regla__isnull=False)
        ),
        pk=notificacion_id,
    )

    if not notificacion.notificacion_leido:
        notificacion.notificacion_leido = True
        notificacion.save(update_fields=['notificacion_leido'])

    return redirect('notificaciones')


def cambiar_estado_notificacion_view(request, notificacion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden gestionar notificaciones.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    notificacion = get_object_or_404(
        Notificacion.objects.filter(
            Q(usuario_id=request.session['usuario_id']) | Q(regla__isnull=False)
        ),
        pk=notificacion_id,
    )
    estado = request.POST.get('estado', '')
    motivo = request.POST.get('motivo', '').strip()
    if estado not in Notificacion.Estado.values:
        messages.error(request, "Selecciona un estado válido.")
        return redirect('notificaciones')
    if not motivo:
        messages.error(request, "Debes indicar el motivo del cambio de estado.")
        return redirect('notificaciones')
    if notificacion.estado == estado:
        return redirect('notificaciones')

    with transaction.atomic():
        notificacion.estado = estado
        notificacion.save(update_fields=['estado'])
        HistorialNotificacion.objects.create(
            notificacion=notificacion,
            estado=estado,
            cambiado_por_id=request.session['usuario_id'],
            motivo=motivo,
        )
    return redirect('notificaciones')


def _regla_notificacion_operativa(regla):
    return bool(
        regla
        and regla.estado == ReglaInstitucional.Estado.APROBADA
        and regla.version.estado == VersionReglamento.Estado.VIGENTE
        and not regla.solo_presentacion
        and regla.activador != ReglaInstitucional.Activador.MANUAL
        and regla.accion_requerida.strip()
    )


def _mensaje_notificacion_seguro(notificacion):
    if (
        notificacion.notificacion_titulo in (
            'Nueva Bitácora Registrada',
            'Nuevo caso registrado',
        )
        or getattr(notificacion, 'evento_tipo', '')
        == Notificacion.TipoEvento.CASO_CREADO
    ):
        return (
            'Se registró un caso nuevo. Revisa sus antecedentes y el detalle '
            'antes de definir acciones.'
        )
    return notificacion.notificacion_mensaje


def _url_caso_notificacion(notificacion):
    if notificacion.caso_id:
        return reverse('detalle_caso', args=[notificacion.caso_id])
    if notificacion.notificacion_titulo == 'Nueva Bitácora Registrada':
        fecha = timezone.localtime(notificacion.notificacion_fecha).date().isoformat()
        return (
            f"{reverse('historial_casos')}?"
            f"fecha_desde={fecha}&fecha_hasta={fecha}"
        )
    return ''

"""Controlador de seguimiento de casos: panel, acciones y cierre del seguimiento."""

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from ..models import (
    AccionSeguimiento,
    Caso,
    Estudiante,
    HistorialAccionSeguimiento,
    HistorialNotificacion,
    HistorialSeguimientoCaso,
    HistorialUsuario,
    Notificacion,
    SeguimientoCaso,
    Usuario,
)
from ..permissions import ROLES_GESTION_SEGUIMIENTO, rol_seguimiento_permitido
from ..trazabilidad import trazar


def _usuario_activo_en_sesion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    return (
        Usuario.objects
        .filter(pk=usuario_id, usuario_activo=True, usuario_bloqueado=False)
        .first()
    )


def seguimiento_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para consultar el módulo de seguimiento.")

    return _redirect_to_seguimiento()


@trazar('CONTROLADOR', 'SeguimientoController', 'actualizando estado de acción de seguimiento')
def actualizar_accion_seguimiento_view(request, accion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden gestionar acciones.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    usuario_actual = _usuario_activo_en_sesion(request)
    if not usuario_actual:
        return redirect('login')

    estado = request.POST.get('estado', '').strip()
    motivo = request.POST.get('motivo', '').strip()
    if estado not in AccionSeguimiento.Estado.values or not motivo:
        messages.error(request, "El estado y el motivo del cambio son obligatorios.")
        return _redirect_to_seguimiento()

    with transaction.atomic():
        accion = get_object_or_404(
            AccionSeguimiento.objects.select_for_update().select_related('seguimiento'),
            pk=accion_id,
        )
        if accion.seguimiento.estado == SeguimientoCaso.Estado.SOLUCIONADO:
            messages.error(
                request,
                "No se puede modificar una acción de un seguimiento que ya fue cerrado.",
            )
            return _redirect_to_seguimiento()

        if accion.estado == estado:
            return _redirect_to_seguimiento()

        ahora = timezone.now()
        accion.estado = estado
        accion.completada_en = (
            ahora if estado == AccionSeguimiento.Estado.COMPLETADA else None
        )
        accion.save(update_fields=['estado', 'completada_en'])

        HistorialAccionSeguimiento.objects.create(
            accion=accion,
            estado=estado,
            cambiado_por=usuario_actual,
            motivo=motivo,
        )
        HistorialUsuario.objects.create(
            usuario=usuario_actual,
            historial_accion='Modificación',
            historial_detalle=(
                f"Actualizó la acción de seguimiento #{accion.pk} a "
                f"'{accion.get_estado_display()}': {motivo}."
            ),
        )

    messages.success(request, "Estado de la acción actualizado correctamente.")
    return _redirect_to_seguimiento()


@trazar('CONTROLADOR', 'SeguimientoController', 'cerrando seguimiento del estudiante en el caso')
def cerrar_seguimiento_view(request, caso_id, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden cerrar un seguimiento.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    usuario_actual = _usuario_activo_en_sesion(request)
    if not usuario_actual:
        return redirect('login')

    caso = get_object_or_404(Caso, pk=caso_id)
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if not caso.estudiantes.filter(pk=estudiante.pk).exists():
        return HttpResponseForbidden("El estudiante no está asociado a este caso.")

    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, "Debes indicar el motivo del cierre.")
        return _redirect_to_seguimiento()

    with transaction.atomic():
        seguimiento, _ = SeguimientoCaso.objects.get_or_create(
            caso=caso,
            estudiante=estudiante,
        )
        seguimiento = SeguimientoCaso.objects.select_for_update().get(pk=seguimiento.pk)

        if seguimiento.estado == SeguimientoCaso.Estado.SOLUCIONADO:
            messages.info(request, "Este seguimiento ya se encontraba cerrado.")
            return _redirect_to_seguimiento()

        acciones_qs = seguimiento.acciones.all()
        if not acciones_qs.exists():
            messages.error(
                request,
                "El seguimiento debe tener al menos una acción registrada antes de cerrarse.",
            )
            return _redirect_to_seguimiento()

        if acciones_qs.exclude(estado=AccionSeguimiento.Estado.COMPLETADA).exists():
            messages.error(
                request,
                "Completa todas las acciones requeridas antes de cerrar el seguimiento.",
            )
            return _redirect_to_seguimiento()

        ahora = timezone.now()
        seguimiento.estado = SeguimientoCaso.Estado.SOLUCIONADO
        seguimiento.solucionado_en = ahora
        seguimiento.solucionado_por = usuario_actual
        seguimiento.motivo_cierre = motivo
        seguimiento.save(update_fields=[
            'estado', 'solucionado_en', 'solucionado_por', 'motivo_cierre',
        ])

        HistorialSeguimientoCaso.objects.create(
            seguimiento=seguimiento,
            estado=seguimiento.estado,
            cambiado_por=usuario_actual,
            motivo=motivo,
        )

        notificaciones_pendientes = list(
            Notificacion.objects
            .select_for_update()
            .filter(caso=caso, estudiante=estudiante)
            .exclude(estado=Notificacion.Estado.SOLUCIONADO)
        )
        if notificaciones_pendientes:
            ids_notif = [n.pk for n in notificaciones_pendientes]
            Notificacion.objects.filter(pk__in=ids_notif).update(
                estado=Notificacion.Estado.SOLUCIONADO,
            )
            HistorialNotificacion.objects.bulk_create([
                HistorialNotificacion(
                    notificacion_id=notif_id,
                    estado=Notificacion.Estado.SOLUCIONADO,
                    cambiado_por=usuario_actual,
                    motivo=f'Cierre autorizado del seguimiento: {motivo}',
                )
                for notif_id in ids_notif
            ])

        HistorialUsuario.objects.create(
            usuario=usuario_actual,
            historial_accion='Modificación',
            historial_detalle=(
                f"Cerró el seguimiento del caso #{caso.pk} para "
                f"{estudiante.nombre_completo}: {motivo}."
            ),
        )

    messages.success(request, "El seguimiento fue cerrado y marcado como solucionado.")
    return _redirect_to_seguimiento()


def _redirect_to_seguimiento():
    return redirect(f"{reverse('notificaciones')}#seguimiento")
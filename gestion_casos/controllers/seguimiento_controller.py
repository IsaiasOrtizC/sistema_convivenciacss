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
    Notificacion,
    SeguimientoCaso,
)
from ..permissions import ROLES_GESTION_SEGUIMIENTO, rol_seguimiento_permitido


def seguimiento_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para consultar el módulo de seguimiento.")

    return _redirect_to_seguimiento()


def actualizar_accion_seguimiento_view(request, accion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden gestionar acciones.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    accion = get_object_or_404(AccionSeguimiento, pk=accion_id)
    estado = request.POST.get('estado', '')
    motivo = request.POST.get('motivo', '').strip()
    if estado not in AccionSeguimiento.Estado.values or not motivo:
        messages.error(request, "El estado y el motivo del cambio son obligatorios.")
        return _redirect_to_seguimiento()
    if accion.estado == estado:
        return _redirect_to_seguimiento()

    with transaction.atomic():
        accion.estado = estado
        accion.completada_en = (
            timezone.now() if estado == AccionSeguimiento.Estado.COMPLETADA else None
        )
        accion.save(update_fields=['estado', 'completada_en'])
        HistorialAccionSeguimiento.objects.create(
            accion=accion,
            estado=estado,
            cambiado_por_id=request.session['usuario_id'],
            motivo=motivo,
        )
    return _redirect_to_seguimiento()


def cerrar_seguimiento_view(request, caso_id, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden cerrar un seguimiento.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

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
            caso=caso, estudiante=estudiante,
        )
        seguimiento = SeguimientoCaso.objects.select_for_update().get(pk=seguimiento.pk)
        if seguimiento.acciones.exclude(estado=AccionSeguimiento.Estado.COMPLETADA).exists():
            messages.error(request, "Completa todas las acciones requeridas antes de cerrar el seguimiento.")
            return _redirect_to_seguimiento()
        if seguimiento.estado != SeguimientoCaso.Estado.SOLUCIONADO:
            seguimiento.estado = SeguimientoCaso.Estado.SOLUCIONADO
            seguimiento.solucionado_en = timezone.now()
            seguimiento.solucionado_por_id = request.session['usuario_id']
            seguimiento.motivo_cierre = motivo
            seguimiento.save(update_fields=[
                'estado', 'solucionado_en', 'solucionado_por', 'motivo_cierre',
            ])
            HistorialSeguimientoCaso.objects.create(
                seguimiento=seguimiento,
                estado=seguimiento.estado,
                cambiado_por_id=request.session['usuario_id'],
                motivo=motivo,
            )
            notificaciones = Notificacion.objects.filter(
                caso=caso, estudiante=estudiante,
            ).exclude(estado=Notificacion.Estado.SOLUCIONADO)
            for notificacion in notificaciones:
                notificacion.estado = Notificacion.Estado.SOLUCIONADO
                notificacion.save(update_fields=['estado'])
                HistorialNotificacion.objects.create(
                    notificacion=notificacion,
                    estado=notificacion.estado,
                    cambiado_por_id=request.session['usuario_id'],
                    motivo=f'Cierre autorizado del seguimiento: {motivo}',
                )
    return _redirect_to_seguimiento()


def _redirect_to_seguimiento():
    return redirect(f"{reverse('notificaciones')}#seguimiento")

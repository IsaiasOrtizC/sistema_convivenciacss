"""Configuracion Controller: ajustes de la cuenta (contraseña y opciones personales)."""

import logging

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import (
    Administrador,
    HistorialUsuario,
    Inspector,
    PConvivencia,
    ProfesorJefe,
    SesionActiva,
    Usuario,
)

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8


def _sincronizar_nombre_subtipo(usuario_perfil):
    """Mantiene sincronizados nombre y apellidos en la tabla específica del rol."""
    datos = {
        'nombre': usuario_perfil.usuario_nombre,
        'apaterno': usuario_perfil.usuario_apaterno,
        'amaterno': usuario_perfil.usuario_amaterno,
    }
    Administrador.objects.filter(usuario=usuario_perfil).update(
        admin_nombre=datos['nombre'],
        admin_apaterno=datos['apaterno'],
        admin_amaterno=datos['amaterno'],
    )
    Inspector.objects.filter(usuario=usuario_perfil).update(
        inspector_nombre=datos['nombre'],
        inspector_apaterno=datos['apaterno'],
        inspector_amaterno=datos['amaterno'],
    )
    PConvivencia.objects.filter(usuario=usuario_perfil).update(
        convivencia_nombre=datos['nombre'],
        convivencia_apaterno=datos['apaterno'],
        convivencia_amaterno=datos['amaterno'],
    )
    ProfesorJefe.objects.filter(usuario=usuario_perfil).update(
        profesor_nombre=datos['nombre'],
        profesor_apaterno=datos['apaterno'],
        profesor_amaterno=datos['amaterno'],
    )


def gestion_configuracion_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(
        Usuario.objects.select_related('rol'),
        pk=usuario_id_sesion,
    )

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        contrasena_actual = request.POST.get('contrasena_actual', '')
        nueva_contrasena = request.POST.get('contrasena', '').strip()
        confirmar_contrasena = request.POST.get('confirmar_contrasena', '')

        debe_cambiar = bool(
            usuario_perfil.usuario_primer_ingreso
            or request.session.get('primer_ingreso', False)
        )

        # Validar datos personales si fueron enviados en el formulario
        if any(campo in request.POST for campo in ('nombre', 'apaterno', 'amaterno')):
            if not (nombre and apaterno and amaterno):
                messages.error(request, "Completa tu nombre y ambos apellidos.")
                return redirect('gestion_configuracion')

        # Si es primer ingreso obligatorio, exigir contraseña nueva
        if debe_cambiar and not nueva_contrasena:
            messages.error(
                request,
                "Debes establecer una nueva contraseña personal antes de continuar.",
            )
            return redirect('gestion_configuracion')

        # Validaciones de cambio de contraseña
        if nueva_contrasena:
            if 'contrasena_actual' in request.POST and not check_password(
                contrasena_actual,
                usuario_perfil.usuario_contrasena,
            ):
                messages.error(request, "La contraseña actual ingresada no es correcta.")
                return redirect('gestion_configuracion')

            if len(nueva_contrasena) < MIN_PASSWORD_LENGTH:
                messages.error(
                    request,
                    f"La nueva contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.",
                )
                return redirect('gestion_configuracion')

            if 'confirmar_contrasena' in request.POST and nueva_contrasena != confirmar_contrasena.strip():
                messages.error(request, "La confirmación de la nueva contraseña no coincide.")
                return redirect('gestion_configuracion')

            if check_password(nueva_contrasena, usuario_perfil.usuario_contrasena):
                messages.error(
                    request,
                    "La nueva contraseña debe ser distinta a tu contraseña actual.",
                )
                return redirect('gestion_configuracion')

        try:
            campos_actualizar = []
            cambios_detalle = []

            if nombre and apaterno and amaterno:
                if (
                    usuario_perfil.usuario_nombre != nombre
                    or usuario_perfil.usuario_apaterno != apaterno
                    or usuario_perfil.usuario_amaterno != amaterno
                ):
                    usuario_perfil.usuario_nombre = nombre
                    usuario_perfil.usuario_apaterno = apaterno
                    usuario_perfil.usuario_amaterno = amaterno
                    campos_actualizar.extend([
                        'usuario_nombre',
                        'usuario_apaterno',
                        'usuario_amaterno',
                    ])
                    cambios_detalle.append("datos personales")

            if nueva_contrasena:
                usuario_perfil.usuario_contrasena = make_password(nueva_contrasena)
                usuario_perfil.usuario_primer_ingreso = False
                campos_actualizar.extend([
                    'usuario_contrasena',
                    'usuario_primer_ingreso',
                ])
                cambios_detalle.append("contraseña")

            if not campos_actualizar:
                messages.info(request, "No se detectaron cambios para guardar.")
                return redirect('gestion_configuracion')

            with transaction.atomic():
                usuario_perfil.save(update_fields=campos_actualizar)
                if 'usuario_nombre' in campos_actualizar:
                    _sincronizar_nombre_subtipo(usuario_perfil)

                HistorialUsuario.objects.create(
                    usuario=usuario_perfil,
                    historial_accion='Modificación',
                    historial_detalle=(
                        f"Actualizó su configuración personal ({', '.join(cambios_detalle)})."
                    ),
                )

            if 'usuario_nombre' in campos_actualizar:
                request.session['usuario_nombre'] = f"{nombre} {apaterno}".strip()

            if nueva_contrasena:
                request.session['primer_ingreso'] = False
                request.session.cycle_key()
                request.session.save()
                SesionActiva.objects.update_or_create(
                    usuario=usuario_perfil,
                    defaults={
                        'session_key': request.session.session_key,
                        'fecha_inicio': timezone.now(),
                    },
                )

            messages.success(
                request,
                "Tus credenciales y datos privados se actualizaron correctamente.",
            )
            return redirect('gestion_configuracion')

        except Exception:
            logger.exception(
                "Error al actualizar configuración del usuario %s.",
                usuario_id_sesion,
            )
            messages.error(request, "Ocurrió un error al intentar actualizar la configuración.")

    context = {
        'perfil': usuario_perfil,
        'debe_cambiar_contrasena': bool(
            usuario_perfil.usuario_primer_ingreso
            or request.session.get('primer_ingreso', False)
        ),
        'min_password_length': MIN_PASSWORD_LENGTH,
    }
    return render(request, 'gestion_casos/gestion_configuracion.html', context)
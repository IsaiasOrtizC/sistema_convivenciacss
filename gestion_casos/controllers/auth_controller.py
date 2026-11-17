"""Auth Controller: inicio y cierre de sesión, credenciales y recuperación de acceso."""

import logging
import secrets
import string

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.messages import get_messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import escape

from ..models import SesionActiva, Usuario
from .email_controller import enviar_correo_html

logger = logging.getLogger(__name__)


def _generar_contrasena_temporal(longitud=12):
    alfabeto = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabeto) for _ in range(longitud))


def solicitar_recuperacion_contrasena(correo_destino):
    correo_limpio = (correo_destino or '').strip()
    if not correo_limpio:
        return False

    usuario = Usuario.objects.filter(usuario_correo__iexact=correo_limpio).first()
    if usuario is None or not usuario.usuario_activo:
        return False

    contrasena_temporal = _generar_contrasena_temporal(12)
    html_recuperacion_contrasena = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 550px; margin: 0 auto; border: 1px solid rgba(123,26,26,0.15); border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(90deg, #5A1010 0%, #7B1A1A 100%); padding: 24px; text-align: center; border-bottom: 3px solid #D4A017;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.4rem;">ConviData</h1>
            <p style="color: #F0C030; margin: 4px 0 0 0; font-size: 0.8rem; text-transform: uppercase;">Colegio San Sebastián de Melipilla</p>
        </div>
        <div style="padding: 32px; background-color: #ffffff; color: #1C0A0A;">
            <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">Restablecimiento de credenciales</h2>
            <p style="font-size: 0.9rem;">Estimado(a) <strong>{escape(usuario.usuario_nombre)} {escape(usuario.usuario_apaterno)}</strong>,</p>
            <p style="font-size: 0.9rem;">Hemos recibido una solicitud para recuperar tus credenciales de acceso. Se generó una <strong>contraseña temporal</strong> para que puedas volver a entrar.</p>
            <div style="background-color: #F7F3ED; border-left: 4px solid #D4A017; padding: 14px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; font-size: 0.85rem;">
                    Tu contraseña temporal es: <strong style="font-size: 0.95rem; color: #7B1A1A; font-family: monospace;">{contrasena_temporal}</strong>
                </p>
            </div>
            <p style="font-size: 0.82rem; color: #5C3A2A;">Por seguridad, el sistema te pedirá crear una contraseña nueva y personal apenas inicies sesión.</p>
        </div>
    </div>
    """

    with transaction.atomic():
        usuario.usuario_contrasena = make_password(contrasena_temporal)
        usuario.usuario_primer_ingreso = True
        usuario.usuario_bloqueado = False
        usuario.usuario_intentos_fallidos = 0
        usuario.save(update_fields=[
            'usuario_contrasena',
            'usuario_primer_ingreso',
            'usuario_bloqueado',
            'usuario_intentos_fallidos',
        ])
        SesionActiva.objects.filter(usuario=usuario).delete()

        enviar_correo_html(
            destinatario=usuario.usuario_correo,
            asunto="Recuperación de Contraseña - ConviData",
            html=html_recuperacion_contrasena,
        )

    return True


def login_view(request):
    if request.method == 'POST':
        if 'correo_recuperacion' in request.POST:
            correo_destino = request.POST.get('correo_recuperacion', '').strip()
            try:
                solicitar_recuperacion_contrasena(correo_destino)
                messages.success(
                    request,
                    "Si el correo está registrado y activo, recibirás una contraseña temporal.",
                )
            except Exception:
                logger.exception("Error al enviar correo de recuperación de contraseña.")
                messages.error(
                    request,
                    "No se pudo procesar la solicitud en este momento. Inténtalo nuevamente más tarde.",
                )
            return redirect('login')

        # INICIO DE SESIÓN
        correo_ingresado = request.POST.get('correo', '').strip()
        contrasena_ingresada = request.POST.get('contrasena', '')

        if not correo_ingresado or not contrasena_ingresada:
            messages.error(request, "Ingresa tu correo institucional y contraseña.")
            return redirect('login')

        try:
            with transaction.atomic():
                usuario = (
                    Usuario.objects
                    .select_for_update()
                    .select_related('rol')
                    .get(usuario_correo__iexact=correo_ingresado)
                )

                # Cuenta bloqueada por intentos fallidos -> no se valida contraseña
                if usuario.usuario_bloqueado:
                    messages.error(
                        request,
                        "Cuenta bloqueada. Contacta al Administrador del sistema para restablecer el acceso.",
                    )
                    return redirect('login')

                if check_password(contrasena_ingresada, usuario.usuario_contrasena):
                    if not usuario.usuario_activo:
                        messages.error(
                            request,
                            "Tu cuenta se encuentra inactiva. Contacta al Administrador del sistema.",
                        )
                        return redirect('login')

                    usuario.usuario_intentos_fallidos = 0
                    usuario.usuario_ultimo_acceso = timezone.now()
                    usuario.save(update_fields=['usuario_intentos_fallidos', 'usuario_ultimo_acceso'])
                else:
                    # Incremento atómico de intentos fallidos
                    usuario.usuario_intentos_fallidos = F('usuario_intentos_fallidos') + 1
                    usuario.save(update_fields=['usuario_intentos_fallidos'])
                    usuario.refresh_from_db(fields=['usuario_intentos_fallidos'])

                    if usuario.usuario_intentos_fallidos >= 5:
                        usuario.usuario_bloqueado = True
                        usuario.save(update_fields=['usuario_bloqueado'])
                        messages.error(
                            request,
                            "Cuenta bloqueada. Se detectaron 5 intentos fallidos consecutivos. Contacta al Administrador del sistema.",
                        )
                    else:
                        intentos_restantes = 5 - usuario.usuario_intentos_fallidos
                        messages.error(
                            request,
                            f"Contraseña incorrecta. Te quedan {intentos_restantes} intento(s) antes de que la cuenta se bloquee.",
                        )
                    return redirect('login')

            # Evita session fixation y crea nueva clave de sesión única
            request.session.cycle_key()
            request.session['usuario_id'] = usuario.usuario_id
            request.session['usuario_nombre'] = f"{usuario.usuario_nombre} {usuario.usuario_apaterno}".strip()
            request.session['usuario_rol'] = usuario.rol.rol_nombre
            request.session['usuario_correo'] = usuario.usuario_correo
            request.session['primer_ingreso'] = bool(usuario.usuario_primer_ingreso)
            request.session.save()

            SesionActiva.objects.update_or_create(
                usuario=usuario,
                defaults={
                    'session_key': request.session.session_key,
                    'fecha_inicio': timezone.now(),
                },
            )

            if usuario.rol.rol_nombre == 'Profesor Jefe':
                return redirect('mis_casos_curso')

            return redirect('dashboard')

        except Usuario.DoesNotExist:
            messages.error(
                request,
                "Usuario no existente: el correo ingresado no está registrado en el sistema.",
            )
            return redirect('login')

    return render(request, 'gestion_casos/login.html')


# CIERRE DE SESIÓN
def logout_view(request):
    storage = get_messages(request)
    storage.used = True

    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        SesionActiva.objects.filter(usuario_id=usuario_id).delete()

    request.session.flush()
    return redirect('login')
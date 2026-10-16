"""Auth Controller: inicio y cierre de sesión, credenciales y recuperación de acceso."""

import secrets
import string

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.messages import get_messages
from django.shortcuts import redirect, render
from django.utils import timezone

from ..models import SesionActiva, Usuario
from .email_controller import enviar_correo_html


def login_view(request):
    if request.method == 'POST':
        
        #RECUPERACION CONTRASEÑA CON RESSEND
        if 'correo_recuperacion' in request.POST:
            correo_destino = request.POST.get('correo_recuperacion').strip()
            #login
            try:
                usuario = Usuario.objects.get(usuario_correo=correo_destino)

                # Se genera una contraseña TEMPORAL nueva y aleatoria (nunca se vuelve a
                # mostrar/enviar la contraseña real, ya que ahora se guarda encriptada
                # y ni el propio sistema puede leerla). Se obliga a cambiarla al entrar.
                alfabeto = string.ascii_letters + string.digits
                contrasena_temporal = ''.join(secrets.choice(alfabeto) for _ in range(10))

                usuario.usuario_contrasena = make_password(contrasena_temporal)
                usuario.usuario_primer_ingreso = True
                usuario.usuario_bloqueado = False
                usuario.usuario_intentos_fallidos = 0
                usuario.save()

                html_recuperacion_contraseña = f"""
                <div style="font-family: 'Segoe UI', sans-serif; max-width: 550px; margin: 0 auto; border: 1px solid rgba(123,26,26,0.15); border-radius: 12px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #5A1010 0%, #7B1A1A 100%); padding: 24px; text-align: center; border-bottom: 3px solid #D4A017;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 1.4rem;">ConviData</h1>
                        <p style="color: #F0C030; margin: 4px 0 0 0; font-size: 0.8rem; text-transform: uppercase;">Colegio San Sebastián de Melipilla</p>
                    </div>
                    <div style="padding: 32px; background-color: #ffffff; color: #1C0A0A;">
                        <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">Restablecimiento de Credenciales</h2>
                        <p style="font-size: 0.9rem;">Estimado(a) <strong>{usuario.usuario_nombre} {usuario.usuario_apaterno}</strong>,</p>
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
                
                enviar_correo_html(
                    destinatario=correo_destino,
                    asunto="Recuperación de Contraseña - ConviData",
                    html=html_recuperacion_contraseña,
                )
                
                messages.success(request, f"Se ha enviado un correo con una contraseña temporal a {correo_destino}.")
                return redirect('login')
                
            except Usuario.DoesNotExist:
                messages.error(request, "Usuario no existente: el correo ingresado no está registrado.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error en el servidor de correos: {str(e)}")
                return redirect('login')

        # INICIO SESION
        else:
            correo_ingresado = request.POST.get('correo', '').strip()
            contrasena_ingresada = request.POST.get('contrasena', '')
            
            try:
                # Buscamos al funcionario por su correo real
                usuario = Usuario.objects.get(usuario_correo=correo_ingresado)

                # RF: cuenta bloqueada por intentos fallidos -> ni siquiera se valida la contraseña
                if usuario.usuario_bloqueado:
                    messages.error(request, "Cuenta bloqueada. Contacta al Administrador del sistema para restablecer el acceso.")
                    return redirect('login')

                # Validamos credenciales directo con tu string de contraseña de la BD
                if check_password(contrasena_ingresada, usuario.usuario_contrasena):

                    # RF: no dejar entrar a cuentas marcadas como inactivas
                    if not usuario.usuario_activo:
                        messages.error(request, "Tu cuenta se encuentra inactiva. Contacta al Administrador del sistema.")
                        return redirect('login')

                    usuario.usuario_intentos_fallidos = 0
                    usuario.usuario_ultimo_acceso=timezone.now()
                    usuario.save(update_fields=['usuario_intentos_fallidos', 'usuario_ultimo_acceso'])


                    # Inyectamos las variables obligatorias en la sesión web
                    request.session['usuario_id'] = usuario.usuario_id
                    request.session['usuario_nombre'] = f"{usuario.usuario_nombre} {usuario.usuario_apaterno}"
                    request.session['usuario_rol'] = usuario.rol.rol_nombre
                    request.session['usuario_correo'] = usuario.usuario_correo
                    
                    # CONTROL PARA PRIMER INGRESO
                    try:
                        request.session['primer_ingreso'] = usuario.usuario_primer_ingreso
                    except AttributeError:
                        request.session['primer_ingreso'] = False

                    # SESIÓN ÚNICA: esta sesión pasa a ser la única válida para esta cuenta.
                    # Si esta cuenta estaba abierta en otro dispositivo/navegador, ese quedará invalidado.
                    request.session.save()  # fuerza la creación del session_key si aún no existía
                    SesionActiva.objects.update_or_create(
                        usuario=usuario,
                        defaults={'session_key': request.session.session_key, 'fecha_inicio': timezone.now()}
                    )
                    
                    # El Profesor Jefe no tiene panel general: entra directo a su curso
                    if usuario.rol.rol_nombre == 'Profesor Jefe':
                        return redirect('mis_casos_curso')

                    return redirect('dashboard')
                else:
                    # RF: contraseña incorrecta -> cuenta el intento y bloquea al llegar a 5
                    usuario.usuario_intentos_fallidos += 1

                    if usuario.usuario_intentos_fallidos >= 5:
                        usuario.usuario_bloqueado = True
                        usuario.save(update_fields=['usuario_intentos_fallidos', 'usuario_bloqueado'])
                        messages.error(request, "Cuenta bloqueada. Se detectaron 5 intentos fallidos consecutivos. Contacta al Administrador del sistema.")
                    else:
                        usuario.save(update_fields=['usuario_intentos_fallidos'])
                        intentos_restantes = 5 - usuario.usuario_intentos_fallidos
                        messages.error(request, f"Contraseña incorrecta. Te quedan {intentos_restantes} intento(s) antes de que la cuenta se bloquee.")

                    return redirect('login')
                    
            except Usuario.DoesNotExist:
                messages.error(request, "Usuario no existente: el correo ingresado no está registrado en el sistema.")
                return redirect('login')

    return render(request, 'gestion_casos/login.html')


# CIERRE SESION
def logout_view(request):
    storage = get_messages(request)
    for message in storage:
        pass  

    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        SesionActiva.objects.filter(usuario_id=usuario_id).delete()

    request.session.flush()
    
    return redirect('login')

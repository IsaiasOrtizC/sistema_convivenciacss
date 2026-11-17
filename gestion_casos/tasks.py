Este módulo de tareas de Celery (`tasks.py`) presenta un error de sintaxis, problemas de seguridad en el renderizado HTML y falta de tolerancia a fallos en la cola de correos:

1. **Error de sintaxis y asunto mal formateado en `enviar_alerta_caso_gravisimo`:**
Hay un guion `-` suelto al inicio de la línea del `subject` (que rompe la compilación de Python) y el texto dice `#{caso_id}ConviData` sin separador (`#{caso_id} - ConviData`).
2. **Inyección de HTML (`XSS` en correo):**
Variables como `nombre`, `apaterno`, `contrasena`, `zona` o `tipo_falta` se interpolan directamente en el f-string sin escapar (`html.escape()`). Si un nombre o zona contiene `<` o `&`, rompe la estructura del correo.
3. **Resiliencia en Celery (`autoretry_for`) y consistencia en el remitente (`from`):**
* Las llamadas a APIs externas como Resend pueden fallar temporalmente por límites de tasa (`429`) o cortes de red. Agregar `autoretry_for=(Exception,)` con `retry_backoff=True` evita perder correos importantes.
* Las dos primeras tareas tenían hardcodeado `"onboarding@resend.dev"` mientras que la tercera usaba `settings.RESEND_FROM_EMAIL`. Unificarlo en una función auxiliar `_remitente()` facilita pasar a producción con dominio propio.


4. **Privacidad en múltiples destinatarios:**
En `enviar_alerta_caso_gravisimo`, si `destinatarios` tiene varios encargados, pasar todos en `"to"` expone sus correos entre sí y puede disparar filtros antispam; enviar cada correo individualmente (o usar `"bcc"` cuando haya más de un destinatario) es más limpio y seguro.

### Código optimizado

```python
from html import escape

import resend
from celery import shared_task
from django.conf import settings


def _configurar_resend():
    resend.api_key = settings.RESEND_API_KEY
    return getattr(
        settings,
        "RESEND_FROM_EMAIL",
        "ConviData <onboarding@resend.dev>",
    )


def _plantilla_correo(subtitulo_header, contenido_html):
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Arial, sans-serif;
                max-width: 560px; margin: 0 auto; border: 1px solid rgba(123, 26, 26, 0.16);
                border-radius: 12px; overflow: hidden; background-color: #ffffff; color: #1d1d1f;">
        <div style="background: linear-gradient(90deg, #5A1010 0%, #7B1A1A 100%);
                    padding: 24px; text-align: center; border-bottom: 3px solid #D4A017;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.4rem; letter-spacing: -0.02em;">
                ConviData
            </h1>
            <p style="color: #F0C030; margin: 4px 0 0 0; font-size: 0.78rem;
                      font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">
                {escape(subtitulo_header)}
            </p>
        </div>
        <div style="padding: 30px 32px; line-height: 1.55;">
            {contenido_html}
        </div>
    </div>
    """


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_correo_prueba(destinatario):
    remitente = _configurar_resend()
    cuerpo = """
        <h2 style="font-size: 1.15rem; margin-top: 0; color: #7B1A1A;">Prueba de conexión</h2>
        <p style="font-size: 0.9rem;">Este correo fue enviado mediante Celery y Resend.</p>
        <p style="font-size: 0.9rem; margin-bottom: 0;">La cola de tareas está funcionando correctamente.</p>
    """
    params = {
        "from": remitente,
        "to": [destinatario],
        "subject": "Prueba Celery + Resend - ConviData",
        "html": _plantilla_correo("Colegio San Sebastián de Melipilla", cuerpo),
    }
    return resend.Emails.send(params)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_credenciales_usuario(destinatario, nombre, apaterno, contrasena):
    remitente = _configurar_resend()

    nombre_seguro = escape(f"{nombre} {apaterno}".strip())
    destinatario_seguro = escape(destinatario)
    contrasena_segura = escape(contrasena)

    cuerpo = f"""
        <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">
            Cuenta creada
        </h2>
        <p style="font-size: 0.9rem;">
            Estimado(a) <strong>{nombre_seguro}</strong>,
        </p>
        <p style="font-size: 0.9rem;">
            Se ha creado una cuenta para ti en ConviData.
        </p>
        <div style="background-color: #F7F3ED; border-left: 4px solid #D4A017;
                    padding: 14px 16px; margin: 20px 0; border-radius: 6px;">
            <p style="margin: 0 0 8px 0; font-size: 0.85rem;">
                <strong>Correo:</strong> {destinatario_seguro}
            </p>
            <p style="margin: 0; font-size: 0.85rem;">
                <strong>Contraseña:</strong>
                <span style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                             color: #7B1A1A; font-weight: 700;">
                    {contrasena_segura}
                </span>
            </p>
        </div>
        <p style="font-size: 0.85rem; color: #424245; margin-bottom: 0;">
            Esta contraseña es temporal. Al iniciar sesión por primera vez,
            deberás cambiarla por una contraseña personal.
        </p>
    """

    params = {
        "from": remitente,
        "to": [destinatario],
        "subject": "Tu cuenta de acceso a ConviData",
        "html": _plantilla_correo("Colegio San Sebastián de Melipilla", cuerpo),
    }
    return resend.Emails.send(params)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_alerta_caso_gravisimo(destinatarios, caso_id, fecha, zona, tipo_falta):
    if not destinatarios:
        return None

    remitente = _configurar_resend()
    nivel = "gravísimo" if tipo_falta == "Gravísima" else "grave"

    cuerpo = f"""
        <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">
            Se registró un caso de nivel {escape(nivel)}
        </h2>
        <div style="background-color: #F7F3ED; border-left: 4px solid #D4A017;
                    padding: 14px 16px; margin: 18px 0; border-radius: 6px; font-size: 0.88rem;">
            <p style="margin: 0 0 6px 0;"><strong>Caso:</strong> #{escape(str(caso_id))}</p>
            <p style="margin: 0 0 6px 0;"><strong>Fecha:</strong> {escape(str(fecha))}</p>
            <p style="margin: 0 0 6px 0;"><strong>Zona:</strong> {escape(str(zona))}</p>
            <p style="margin: 0;"><strong>Clasificación:</strong> {escape(str(tipo_falta))}</p>
        </div>
        <p style="font-size: 0.85rem; color: #424245; margin-bottom: 0;">
            Ingresa a ConviData para revisar los antecedentes y realizar el seguimiento correspondiente.
        </p>
    """

    lista_destinatarios = list(destinatarios)
    params = {
        "from": remitente,
        "to": [lista_destinatarios[0]],
        "subject": f"Alerta de caso {nivel} #{caso_id} - ConviData",
        "html": _plantilla_correo("Alerta institucional de convivencia", cuerpo),
    }
    if len(lista_destinatarios) > 1:
        params["bcc"] = lista_destinatarios[1:]

    return resend.Emails.send(params)

```
import resend

from celery import shared_task
from django.conf import settings


@shared_task
def enviar_correo_prueba(destinatario):
    resend.api_key = settings.RESEND_API_KEY

    params = {
        "from": "onboarding@resend.dev",
        "to": [destinatario],
        "subject": "Prueba Celery + Resend - ConviData",
        "html": """
            <h2>ConviData</h2>
            <p>Este correo fue enviado mediante Celery y Resend.</p>
            <p>La cola de tareas está funcionando correctamente.</p>
        """,
    }

    return resend.Emails.send(params)


@shared_task
def enviar_credenciales_usuario(destinatario, nombre, apaterno, contrasena):
    resend.api_key = settings.RESEND_API_KEY

    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 550px;
                margin: 0 auto; border: 1px solid rgba(123,26,26,0.15);
                border-radius: 12px; overflow: hidden;">

        <div style="background: linear-gradient(90deg, #5A1010 0%, #7B1A1A 100%);
                    padding: 24px; text-align: center;
                    border-bottom: 3px solid #D4A017;">

            <h1 style="color: #ffffff; margin: 0; font-size: 1.4rem;">
                ConviData
            </h1>

            <p style="color: #F0C030; margin: 4px 0 0 0;
                      font-size: 0.8rem; text-transform: uppercase;">
                Colegio San Sebastián de Melipilla
            </p>
        </div>

        <div style="padding: 32px; background-color: #ffffff; color: #1C0A0A;">

            <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">
                Cuenta creada
            </h2>

            <p style="font-size: 0.9rem;">
                Estimado(a) <strong>{nombre} {apaterno}</strong>,
            </p>

            <p style="font-size: 0.9rem;">
                Se ha creado una cuenta para ti en ConviData.
            </p>

            <div style="background-color: #F7F3ED;
                        border-left: 4px solid #D4A017;
                        padding: 14px; margin: 20px 0;
                        border-radius: 4px;">

                <p style="margin: 0 0 8px 0; font-size: 0.85rem;">
                    <strong>Correo:</strong> {destinatario}
                </p>

                <p style="margin: 0; font-size: 0.85rem;">
                    <strong>Contraseña:</strong>
                    <span style="font-family: monospace; color: #7B1A1A;">
                        {contrasena}
                    </span>
                </p>
            </div>

            <p style="font-size: 0.85rem;">
                Esta contraseña es temporal. Al iniciar sesión por primera vez,
                deberás cambiarla por una contraseña personal.
            </p>

        </div>
    </div>
    """

    params = {
        "from": "ConviData <onboarding@resend.dev>",
        "to": [destinatario],
        "subject": "Tu cuenta de acceso a ConviData",
        "html": html,
    }

    return resend.Emails.send(params)


@shared_task
def enviar_alerta_caso_gravisimo(destinatarios, caso_id, fecha, zona, tipo_falta):
    resend.api_key = settings.RESEND_API_KEY
    params = {
        "from": getattr(
            settings,
            "RESEND_FROM_EMAIL",
            "ConviData <onboarding@resend.dev>",
        ),
        "to": destinatarios,
        "subject": f"Alerta de caso gravísimo #{caso_id} - ConviData",
        "html": (
            "<div style=\"font-family:Arial,sans-serif;max-width:560px;"
            "margin:0 auto;border:1px solid #eadfda;border-radius:12px;"
            "overflow:hidden;color:#251717\">"
            "<header style=\"padding:20px;background:#7B1A1A;color:white;"
            "border-bottom:3px solid #D4A017\"><h1 style=\"margin:0\">ConviData</h1>"
            "<p style=\"margin:4px 0 0\">Alerta institucional de convivencia</p></header>"
            "<main style=\"padding:24px\"><h2 style=\"color:#7B1A1A\">"
            "Se registró un caso de nivel gravísimo</h2>"
            f"<p><strong>Caso:</strong> #{caso_id}</p>"
            f"<p><strong>Fecha:</strong> {fecha}</p>"
            f"<p><strong>Zona:</strong> {zona}</p>"
            f"<p><strong>Clasificación:</strong> {tipo_falta}</p>"
            "<p>Ingresa a ConviData para revisar los antecedentes y realizar el "
            "seguimiento correspondiente.</p></main></div>"
        ),
    }
    return resend.Emails.send(params)

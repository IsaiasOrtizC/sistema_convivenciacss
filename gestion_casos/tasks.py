"""Tareas asíncronas de notificación por correo para ConviData."""

from html import escape
import os

import resend
from celery import shared_task
from django.conf import settings

CORREO_PRUEBA_RESEND = "matstreaming0752@gmail.com"


def _obtener_api_key() -> str:
    """Obtiene la API key vigente de Resend desde el entorno o settings."""
    return (
        os.getenv("RESEND_API_KEY")
        or getattr(settings, "RESEND_API_KEY", "")
    ).strip()


def _configurar_resend() -> str:
    """Configura la API key de Resend y devuelve el remitente institucional."""
    api_key = _obtener_api_key()
    if api_key:
        resend.api_key = api_key

    remitente = (
        os.getenv("RESEND_FROM_EMAIL")
        or getattr(settings, "RESEND_FROM_EMAIL", "ConviData <onboarding@resend.dev>")
    ).strip()
    return remitente


def _resolver_destinatarios_prueba(destinatarios, remitente: str) -> list[str]:
    """Redirige a la casilla de pruebas cuando se envía desde @resend.dev sin dominio propio."""
    limpios = [d.strip() for d in destinatarios if d and d.strip()]
    if not limpios:
        return []

    # Sin dominio propio verificado en Resend, las pruebas con @resend.dev solo pueden
    # entregarse a la cuenta autorizada de pruebas.
    if remitente.lower().endswith("@resend.dev>"):
        return [CORREO_PRUEBA_RESEND]

    return limpios


def _es_caso_gravisimo(tipo_falta) -> bool:
    """Valida si la clasificación corresponde estrictamente a un caso gravísimo."""
    clasificacion = (str(tipo_falta or "")).strip().lower()
    return clasificacion in {"gravísima", "gravisima"}


def _plantilla_correo(subtitulo_header: str, contenido_html: str) -> str:
    """Envuelve el cuerpo del correo en la plantilla HTML institucional."""
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
def enviar_correo_prueba(destinatario: str):
    """Envía un correo de prueba para verificar la conexión entre Celery y Resend."""
    remitente = _configurar_resend()
    destinos = _resolver_destinatarios_prueba([destinatario], remitente)
    if not destinos:
        return None

    cuerpo = """
        <h2 style="font-size: 1.15rem; margin-top: 0; color: #7B1A1A;">Prueba de conexión</h2>
        <p style="font-size: 0.9rem;">Este correo fue enviado mediante Celery y Resend.</p>
        <p style="font-size: 0.9rem; margin-bottom: 0;">La cola de tareas está funcionando correctamente.</p>
    """
    params = {
        "from": remitente,
        "to": destinos,
        "subject": "Prueba Celery + Resend - ConviData",
        "html": _plantilla_correo("Colegio San Sebastián de Melipilla", cuerpo),
    }
    return resend.Emails.send(params)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_credenciales_usuario(destinatario: str, nombre: str, apaterno: str, contrasena: str):
    """Envía las credenciales temporales a un funcionario recién creado."""
    remitente = _configurar_resend()
    destinos = _resolver_destinatarios_prueba([destinatario], remitente)
    if not destinos:
        return None

    # Se escapan los datos dinámicos para prevenir inyección HTML (XSS) en el correo.
    nombre_seguro = escape(f"{nombre} {apaterno}".strip())
    destinatario_seguro = escape(destinos[0])
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
        "to": destinos,
        "subject": "Tu cuenta de acceso a ConviData",
        "html": _plantilla_correo("Colegio San Sebastián de Melipilla", cuerpo),
    }
    return resend.Emails.send(params)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_alerta_caso_gravisimo(destinatarios, caso_id, fecha, zona, tipo_falta):
    """Notifica por correo a los responsables únicamente cuando el caso es gravísimo."""
    if not destinatarios or not _es_caso_gravisimo(tipo_falta):
        # Si no es gravísimo (por ejemplo, es grave), no se envía correo por Resend.
        return None

    remitente = _configurar_resend()
    lista_destinatarios = _resolver_destinatarios_prueba(destinatarios, remitente)
    if not lista_destinatarios:
        return None

    nivel = "gravísimo"

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

    # Se envía al primer destinatario en `to` y al resto en `bcc` para no exponer correos entre sí.
    params = {
        "from": remitente,
        "to": [lista_destinatarios[0]],
        "subject": f"Alerta de caso {nivel} #{caso_id} - ConviData",
        "html": _plantilla_correo("Alerta institucional de convivencia", cuerpo),
    }
    if len(lista_destinatarios) > 1:
        params["bcc"] = lista_destinatarios[1:]

    return resend.Emails.send(params)
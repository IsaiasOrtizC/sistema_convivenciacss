"""Email Controller: coordina el envío de correos y comunicaciones automáticas."""

import logging
import os

import resend
from django.conf import settings
from django.contrib import messages
from django.db import transaction

from ..trazabilidad import trazar

logger = logging.getLogger(__name__)


def _obtener_api_key() -> str:
    """Obtiene la API key vigente de Resend desde el entorno o settings."""
    return (
        os.getenv("RESEND_API_KEY")
        or getattr(settings, "RESEND_API_KEY", "")
    ).strip()


def _obtener_remitente_por_defecto() -> str:
    """Obtiene el remitente configurado para correos de ConviData."""
    return (
        os.getenv("RESEND_FROM_EMAIL")
        or getattr(settings, "RESEND_FROM_EMAIL", "ConviData <onboarding@resend.dev>")
    ).strip()


@trazar('CONTROLADOR', 'EmailController', 'enviando correo mediante Resend')
def enviar_correo_html(destinatario, asunto, html, remitente=None):
    """Envía de inmediato un correo HTML mediante Resend (soporta str o iterable de correos)."""
    destinatarios = (
        [destinatario.strip()]
        if isinstance(destinatario, str)
        else [correo.strip() for correo in destinatario if correo and correo.strip()]
    )

    if not destinatarios:
        logger.warning("Intento de envío de correo '%s' sin destinatarios válidos.", asunto)
        return None

    api_key = _obtener_api_key()
    if not api_key:
        logger.warning(
            "RESEND_API_KEY no configurada. Correo '%s' para %s omitido.",
            asunto,
            destinatarios,
        )
        return None

    # Se asigna la clave al momento del envío para asegurar que use el valor actual.
    resend.api_key = api_key
    remitente_final = (remitente or _obtener_remitente_por_defecto()).strip()

    return resend.Emails.send({
        "from": remitente_final,
        "to": destinatarios,
        "subject": asunto,
        "html": html,
    })


@trazar('CONTROLADOR', 'EmailController', 'encolando el envío de correo (Celery)')
def programar_tarea_correo(request, tarea, argumentos, mensaje_error):
    """Encola una tarea de Celery tras confirmar la transacción; si no hay broker, ejecuta directo."""
    args_lista = list(argumentos or ())

    def encolar():
        try:
            # Intenta enviar la tarea a la cola de Celery (requiere broker/Redis activo).
            tarea.delay(*args_lista)
        except Exception as exc:
            logger.warning(
                "No se pudo encolar en Celery (%s): %s. Ejecutando %s de forma directa.",
                getattr(tarea, 'name', tarea),
                exc,
                getattr(tarea, 'name', tarea),
            )
            try:
                # Llama a .run (o a la función directa) para evitar que Celery reintente
                # conectarse al result backend de Redis durante una prueba sin broker.
                funcion_directa = getattr(tarea, "run", tarea)
                funcion_directa(*args_lista)
            except Exception:
                logger.exception(
                    "Falló también la ejecución directa de %s.",
                    getattr(tarea, 'name', tarea),
                )
                if request is not None and mensaje_error:
                    try:
                        messages.warning(request, mensaje_error)
                    except Exception:
                        logger.debug("No fue posible adjuntar el mensaje de advertencia al request.")

    transaction.on_commit(encolar)
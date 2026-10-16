"""Email Controller: coordina el envío de correos y comunicaciones automáticas."""

import logging

import resend
from django.conf import settings
from django.contrib import messages
from django.db import transaction

from ..trazabilidad import trazar

logger = logging.getLogger(__name__)


# Configuración global del cliente de Resend (servicio externo de correo)
resend.api_key = getattr(settings, 'RESEND_API_KEY', '')

REMITENTE_POR_DEFECTO = "ConviData <onboarding@resend.dev>"


@trazar('CONTROLADOR', 'EmailController', 'enviando correo mediante Resend')
def enviar_correo_html(destinatario, asunto, html, remitente=REMITENTE_POR_DEFECTO):
    """Envía de inmediato un correo HTML mediante Resend (cliente del servicio externo)."""
    return resend.Emails.send({
        "from": remitente,
        "to": [destinatario],
        "subject": asunto,
        "html": html,
    })



@trazar('CONTROLADOR', 'EmailController', 'encolando el envío de correo (Celery)')
def programar_tarea_correo(request, tarea, argumentos, mensaje_error):
    def encolar():
        try:
            tarea.delay(*argumentos)
        except Exception:
            logger.exception("No se pudo encolar el envío de correo.")
            messages.warning(request, mensaje_error)

    transaction.on_commit(encolar)

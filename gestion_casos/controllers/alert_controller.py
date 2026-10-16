"""Alert Controller: situaciones prioritarias y alertas automáticas."""

import logging
from datetime import timedelta

from django.utils import timezone

from ..models import Caso, HistorialNotificacion, Notificacion, ProfesorJefe, Rol, Usuario
from ..trazabilidad import trazar
from .email_controller import programar_tarea_correo

logger = logging.getLogger(__name__)


@trazar('CONTROLADOR', 'AlertController', 'notificando caso gravísimo a los responsables')
def notificar_caso_gravisimo(request, caso, tipo_falta, lugar):
    destinatarios = list(
        Usuario.objects.filter(
            rol__rol_nombre='Administrador',
            usuario_activo=True,
            usuario_bloqueado=False,
        ).exclude(usuario_correo='').order_by('usuario_id')
    )
    if not destinatarios:
        logger.warning(
            "El caso gravísimo #%s no tiene administradores activos con correo.",
            caso.caso_id,
        )
        return

    for destinatario in destinatarios:
        clave = f'caso_gravisimo:{caso.caso_id}:admin:{destinatario.usuario_id}'
        notificacion, creada = Notificacion.objects.get_or_create(
            evento_clave=clave,
            defaults={
                'usuario': destinatario,
                'notificacion_titulo': f'Caso gravísimo #{caso.caso_id}',
                'notificacion_mensaje': (
                    f'Se registró el caso #{caso.caso_id} como {tipo_falta} '
                    f'en {lugar.lugar_nombre}. Revisa sus antecedentes.'
                ),
                'notificacion_icono': '🚨',
                'caso': caso,
                'evento_tipo': Notificacion.TipoEvento.CASO_CREADO,
            },
        )
        if creada:
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=notificacion.estado,
                cambiado_por_id=request.session['usuario_id'],
                motivo='Alerta creada por el registro de un caso gravísimo.',
            )

    from ..tasks import enviar_alerta_caso_gravisimo

    programar_tarea_correo(
        request,
        enviar_alerta_caso_gravisimo,
        (
            [usuario.usuario_correo for usuario in destinatarios],
            caso.caso_id,
            caso.caso_fecha.strftime('%d/%m/%Y'),
            lugar.lugar_nombre,
            tipo_falta,
        ),
        "El caso se registró, pero no se pudo encolar el correo de alerta a los administradores.",
    )


@trazar('CONTROLADOR', 'AlertController', 'verificando el umbral de casos del curso')
def verificar_alerta_curso_mas_de_10_casos(curso):
    """
    RF-33 / RF-34

    Genera una alerta cuando un curso supera los 10 casos
    durante la semana actual (lunes a domingo).

    La alerta se genera una sola vez por curso y semana.
    """

    if not curso:
        return

    hoy = timezone.localdate()

    # Semana actual: lunes -> domingo
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    # Contar casos distintos asociados al curso.
    total_casos = (
        Caso.objects
        .filter(
            caso_fecha__gte=inicio_semana,
            caso_fecha__lte=fin_semana,
            estudiantes__curso=curso
        )
        .distinct()
        .count()
    )

    # La alerta aparece SOLO cuando supera 10.
    if total_casos <= 10:
        return

    nombre_curso = str(curso)

    titulo = "Alerta: alta cantidad de casos"

    mensaje = (
        f"El curso {nombre_curso} supera los 10 casos de convivencia "
        f"esta semana. Actualmente registra {total_casos} casos."
    )

    # ------------------------------------------------------------
    # RF-33
    # Administrador / Inspector / PConvivencia
    # ------------------------------------------------------------

    roles_alerta = Rol.objects.filter(
        rol_nombre__in=[
            'Administrador',
            'Inspector',
            'PConvivencia'
        ]
    )

    usuarios_generales = Usuario.objects.filter(
        rol__in=roles_alerta,
        usuario_activo=True,
        usuario_bloqueado=False
    )

    # ------------------------------------------------------------
    # RF-34
    # Profesor Jefe del curso
    # ------------------------------------------------------------

    profesor_jefe = (
        ProfesorJefe.objects
        .filter(
            curso=curso,
            usuario__usuario_activo=True,
            usuario__usuario_bloqueado=False
        )
        .select_related('usuario')
        .first()
    )

    usuarios_destino = {
        usuario.usuario_id: usuario
        for usuario in usuarios_generales
    }

    if profesor_jefe and profesor_jefe.usuario:
        usuarios_destino[profesor_jefe.usuario.usuario_id] = (
            profesor_jefe.usuario
        )

    # ------------------------------------------------------------
    # Evitar duplicados:
    # una alerta por curso y semana para cada usuario.
    # ------------------------------------------------------------

    for usuario in usuarios_destino.values():

        ya_existe = Notificacion.objects.filter(
            usuario=usuario,
            notificacion_titulo=titulo,
            notificacion_mensaje__contains=f"curso {nombre_curso}",
            notificacion_fecha__date__gte=inicio_semana,
            notificacion_fecha__date__lte=fin_semana
        ).exists()

        if ya_existe:
            continue

        Notificacion.objects.create(
            usuario=usuario,
            notificacion_titulo=titulo,
            notificacion_mensaje=mensaje,
            notificacion_icono="⚠️"
        )

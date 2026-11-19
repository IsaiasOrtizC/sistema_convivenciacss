"""Alert Controller: situaciones prioritarias y alertas automáticas."""

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from ..models import Caso, HistorialNotificacion, Notificacion, ProfesorJefe, Usuario
from ..trazabilidad import trazar
from .email_controller import programar_tarea_correo

logger = logging.getLogger(__name__)


@trazar('CONTROLADOR', 'AlertController', 'notificando caso grave o gravísimo a los responsables')
def notificar_caso_gravisimo(request, caso, tipo_falta, lugar):
    """Genera alerta interna para casos graves/gravísimos y envía correo solo si es gravísimo."""
    destinatarios = list(
        Usuario.objects.filter(
            rol__rol_nombre='Administrador',
            usuario_activo=True,
            usuario_bloqueado=False,
        ).order_by('usuario_id')
    )
    if not destinatarios:
        logger.warning("El caso %s #%s no tiene administradores activos.", tipo_falta, caso.caso_id)
        return

    es_gravisimo = (str(tipo_falta or "")).strip().lower() in {'gravísima', 'gravisima'}
    nivel = 'gravísimo' if es_gravisimo else 'grave'

    # 1. Registra la notificación en el sistema para administradores activos.
    for destinatario in destinatarios:
        clave = f'caso_prioritario:{caso.caso_id}:admin:{destinatario.usuario_id}'
        notificacion, creada = Notificacion.objects.get_or_create(
            evento_clave=clave,
            defaults={
                'usuario': destinatario,
                'notificacion_titulo': f'Caso {nivel} #{caso.caso_id}',
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
            usuario_actual = getattr(request, 'user', None)
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=notificacion.estado,
                cambiado_por_id=(
                    usuario_actual.pk
                    if usuario_actual and usuario_actual.is_authenticated
                    else request.session.get('usuario_id')
                ),
                motivo=f'Alerta creada por el registro de un caso {nivel}.',
            )

    # 2. El correo externo por Resend se dispara únicamente cuando el caso es gravísimo.
    if not es_gravisimo:
        return

    destinatarios_correo = [
        usuario.usuario_correo for usuario in destinatarios
        if usuario.usuario_correo
    ]
    if not destinatarios_correo:
        logger.warning(
            "El caso %s #%s no tiene administradores activos con correo.",
            tipo_falta,
            caso.caso_id,
        )
        return

    from ..tasks import enviar_alerta_caso_gravisimo

    programar_tarea_correo(
        request,
        enviar_alerta_caso_gravisimo,
        (
            destinatarios_correo,
            caso.caso_id,
            caso.caso_fecha.strftime('%d/%m/%Y'),
            lugar.lugar_nombre,
            tipo_falta,
        ),
        f"El caso {nivel} se registró, pero no se pudo encolar el correo de alerta a los administradores.",
    )


@trazar('CONTROLADOR', 'AlertController', 'verificando el umbral de casos del curso por tramos de 10')
def verificar_alerta_curso_mas_de_10_casos(curso):
    """
    RF-33 / RF-34

    - Dispara una alerta al superar 10, 20, 30... casos en la semana actual (lunes a domingo).
    - Destinatarios exclusivos: 'PConvivencia' y Profesor(es) Jefe(s) del curso.
    - No repite alertas dentro del mismo tramo de 10.
    - Al avanzar a un nuevo tramo (ej. caso #21), elimina las notificaciones
      de tramos anteriores de ese curso/semana que ya estén resueltas o leídas.
    """
    if not curso:
        return

    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    total_casos = (
        Caso.objects
        .filter(
            caso_fecha__gte=inicio_semana,
            caso_fecha__lte=fin_semana,
            estudiantes__curso=curso,
        )
        .distinct()
        .count()
    )

    # Tramo 0: 1..10 | Tramo 1: 11..20 (>10) | Tramo 2: 21..30 (>20) | etc.
    tramo_actual = (total_casos - 1) // 10
    if tramo_actual < 1:
        return

    umbral_superado = tramo_actual * 10
    prefijo_semana = f"umbral_curso:{curso.curso_id}:semana:{inicio_semana.isoformat()}:"
    clave_tramo_actual = f"{prefijo_semana}tramo:{tramo_actual}:"

    # 1. Eliminar notificaciones de tramos anteriores ya resueltas (estado cambiado) o marcadas como leídas.
    estado_inicial = Notificacion.Estado.values[0]
    Notificacion.objects.filter(
        evento_clave__startswith=prefijo_semana
    ).exclude(
        evento_clave__startswith=clave_tramo_actual
    ).filter(
        ~Q(estado=estado_inicial) | Q(notificacion_leido=True)
    ).delete()

    # 2. Destinatarios exclusivos: PConvivencia + Profesor Jefe del curso.
    usuarios_convivencia = Usuario.objects.filter(
        rol__rol_nombre__iexact='PConvivencia',
        usuario_activo=True,
        usuario_bloqueado=False,
    )

    profesores_jefe = (
        ProfesorJefe.objects
        .filter(
            curso=curso,
            usuario__usuario_activo=True,
            usuario__usuario_bloqueado=False,
        )
        .select_related('usuario')
    )

    usuarios_destino = {
        usuario.usuario_id: usuario
        for usuario in usuarios_convivencia
    }
    for pj in profesores_jefe:
        if pj.usuario:
            usuarios_destino[pj.usuario.usuario_id] = pj.usuario

    if not usuarios_destino:
        logger.warning(
            "El curso %s superó %s casos semanales, pero no tiene PConvivencia ni Profesor Jefe activo.",
            curso,
            umbral_superado,
        )
        return

    nombre_curso = str(curso)
    titulo = f"Alerta: más de {umbral_superado} casos en la semana"
    mensaje = (
        f"El curso {nombre_curso} superó el umbral de {umbral_superado} casos "
        f"de convivencia esta semana (actualmente registra {total_casos} casos)."
    )

    # 3. Crear alerta única por tramo y destinatario.
    for usuario in usuarios_destino.values():
        clave = f"{clave_tramo_actual}usuario:{usuario.usuario_id}"
        notificacion, creada = Notificacion.objects.get_or_create(
            evento_clave=clave,
            defaults={
                'usuario': usuario,
                'notificacion_titulo': titulo,
                'notificacion_mensaje': mensaje,
                'notificacion_icono': '⚠️',
            },
        )
        if creada:
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=notificacion.estado,
                cambiado_por=usuario,
                motivo=(
                    f"Alerta automática generada al superar {umbral_superado} casos "
                    f"semanales en el curso {nombre_curso}."
                ),
            )
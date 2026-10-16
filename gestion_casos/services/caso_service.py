"""CasoService: lógica de negocio para registrar, consultar y filtrar casos."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils.dateparse import parse_date

from ..controllers.alert_controller import (
    notificar_caso_gravisimo,
    verificar_alerta_curso_mas_de_10_casos,
)
from ..models import (
    Caso,
    Curso,
    Estudiante,
    HistorialNotificacion,
    HistorialUsuario,
    Notificacion,
    _quitar_tildes,
)
from ..reglamento import evaluar_reglas_para_caso
from ..trazabilidad import trazar


@trazar('SERVICE', 'CasoService', nivel_min=2)
def identificador_estudiante(estudiante):
    return estudiante.estudiante_identificador or f'Estudiante #{estudiante.estudiante_id}'


# FORMULARIO DE REGISTRAR CASO
@trazar('SERVICE', 'CasoService', 'validando datos y registrando el caso')
def crear_caso_persistido(
    request,
    usuario_instancia,
    fecha,
    titulo,
    descripcion_cuerpo,
    evidencia,
    lugar_instancia,
    tipo_falta,
    estudiantes_data,
):
    nuevo_caso = Caso.objects.create(
        caso_fecha=fecha,
        caso_descripcion=f"[{titulo}] - {descripcion_cuerpo}",
        evidencia=evidencia,
        lugar=lugar_instancia,
        usuario=usuario_instancia,
    )
    identificadores_involucrados = []
    estudiantes_involucrados = []
    cursos_alerta_ids = set()

    for datos in estudiantes_data:
        nom_clean = datos['nombre'].strip()
        apat_clean = datos['apellido_paterno'].strip()
        amat_clean = datos['apellido_materno'].strip()
        curso_instancia = Curso.objects.get(pk=datos['curso_id'])
        cursos_alerta_ids.add(curso_instancia.curso_id)
        estudiante_id = datos.get('estudiante_id')

        if estudiante_id:
            try:
                estudiante_instancia = Estudiante.objects.get(
                    pk=estudiante_id,
                    estudiante_activo=True,
                )
            except Estudiante.DoesNotExist:
                if Estudiante.objects.filter(pk=estudiante_id).exists():
                    raise ValidationError(
                        "No se pueden asociar alumnos inactivos a casos nuevos."
                    )
                estudiante_instancia, _ = Estudiante.objects.get_or_create(
                    estudiante_nombre=nom_clean,
                    estudiante_apaterno=apat_clean,
                    estudiante_amaterno=amat_clean,
                    curso=curso_instancia,
                )
        else:
            estudiante_instancia, _ = Estudiante.objects.get_or_create(
                estudiante_nombre=nom_clean,
                estudiante_apaterno=apat_clean,
                estudiante_amaterno=amat_clean,
                curso=curso_instancia,
            )

        if estudiante_instancia.curso_id != curso_instancia.curso_id:
            raise ValidationError(
                "El curso del estudiante seleccionado no coincide con el formulario."
            )
        if not estudiante_instancia.estudiante_activo:
            raise ValidationError(
                "No se pueden asociar alumnos inactivos a casos nuevos."
            )

        numero_lista = datos.get('numero_lista')
        if numero_lista is not None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE estudiante SET estudiante_numero_lista = %s "
                    "WHERE estudiante_id = %s",
                    [numero_lista, estudiante_instancia.estudiante_id],
                )
            estudiante_instancia.estudiante_numero_lista = numero_lista

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO involucran (estudiante_id, caso_id, tipo_falta)
                VALUES (%s, %s, %s)
                """,
                [
                    estudiante_instancia.estudiante_id,
                    nuevo_caso.caso_id,
                    tipo_falta,
                ],
            )

        identificadores_involucrados.append(
            identificador_estudiante(estudiante_instancia)
        )
        estudiantes_involucrados.append(estudiante_instancia)

    for curso_id_alerta in cursos_alerta_ids:
        verificar_alerta_curso_mas_de_10_casos(
            Curso.objects.get(pk=curso_id_alerta)
        )

    evaluar_reglas_para_caso(
        nuevo_caso,
        estudiantes_involucrados,
        usuario_instancia,
    )

    lista_identificadores = ", ".join(identificadores_involucrados)
    notificacion_nueva, notificacion_creada = Notificacion.objects.get_or_create(
        evento_clave=(
            f'caso_creado:{nuevo_caso.caso_id}:'
            f'usuario:{usuario_instancia.usuario_id}'
        ),
        defaults={
            'usuario': usuario_instancia,
            'notificacion_titulo': 'Nuevo caso registrado',
            'notificacion_mensaje': (
                f"Se registró el caso #{nuevo_caso.caso_id} para "
                f"{lista_identificadores} en la zona "
                f"{lugar_instancia.lugar_nombre}."
            ),
            'notificacion_icono': '🚨',
            'caso': nuevo_caso,
            'evento_tipo': Notificacion.TipoEvento.CASO_CREADO,
        },
    )
    if notificacion_creada:
        HistorialNotificacion.objects.create(
            notificacion=notificacion_nueva,
            estado=notificacion_nueva.estado,
            cambiado_por=usuario_instancia,
            motivo='Notificación creada al registrar un caso.',
        )

    if _quitar_tildes(tipo_falta.casefold()) == 'gravisima':
        notificar_caso_gravisimo(
            request,
            nuevo_caso,
            tipo_falta,
            lugar_instancia,
        )

    HistorialUsuario.objects.create(
        usuario=usuario_instancia,
        historial_accion="Creación",
        historial_detalle=(
            f"Registró exitosamente el caso #{nuevo_caso.caso_id} "
            f"con {len(estudiantes_involucrados)} estudiante(s): "
            + ", ".join(
                f"{estudiante.estudiante_nombre} "
                f"{estudiante.estudiante_apaterno} "
                f"{estudiante.estudiante_amaterno}"
                for estudiante in estudiantes_involucrados
            )
            + "."
        ),
    )
    return nuevo_caso


# ============================================================
#  RF-40: DESCARGA DE CASOS DEL CURSO (PROFESOR JEFE)
# ============================================================

@trazar('SERVICE', 'CasoService', 'consulta base de los casos del curso', nivel_min=2)
def _obtener_casos_del_curso(curso):
    """Devuelve una lista de diccionarios con los datos de los casos de un curso,
    listos para mostrarse en pantalla o exportarse a PDF/XLSX."""
    casos_qs = Caso.objects.filter(estudiantes__curso=curso).distinct().select_related('lugar').order_by('-caso_fecha')

    resultado = []
    for caso in casos_qs:
        texto_completo = caso.caso_descripcion or ""
        titulo = ""
        descripcion = texto_completo
        if "]" in texto_completo and "-" in texto_completo:
            partes = texto_completo.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()
            descripcion = partes[1].strip()

        # OJO: la tabla 'involucran' no tiene columna 'id', por eso se consulta
        # con SQL directo en vez del ORM (igual que en el resto del sistema).
        nombres_alumnos = []
        tipo_falta = ""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s",
                [caso.caso_id]
            )
            filas_involucrados = cursor.fetchall()

        for estudiante_id, tf in filas_involucrados:
            try:
                est = Estudiante.objects.get(pk=estudiante_id)
                nombres_alumnos.append(
                    f"{est.estudiante_nombre} {est.estudiante_apaterno} {est.estudiante_amaterno}"
                )
            except Estudiante.DoesNotExist:
                pass
            tipo_falta = tf

        resultado.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'descripcion': descripcion,
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else '',
            'tipo_falta': tipo_falta,
            'alumnos': ", ".join(nombres_alumnos),
        })
    return resultado


@trazar('SERVICE', 'CasoService', 'consultando los casos del curso con los filtros')
def filtrar_casos_del_curso(request, curso):
    desde_raw = request.GET.get('fecha_desde', '').strip()
    hasta_raw = request.GET.get('fecha_hasta', '').strip()
    gravedad = request.GET.get('gravedad', '').strip()
    desde = parse_date(desde_raw) if desde_raw else None
    hasta = parse_date(hasta_raw) if hasta_raw else None
    if desde_raw and not desde:
        messages.warning(request, "La fecha inicial no es válida y se ignoró.")
    if hasta_raw and not hasta:
        messages.warning(request, "La fecha final no es válida y se ignoró.")
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde
        messages.warning(request, "Las fechas estaban invertidas; se intercambiaron para aplicar el filtro.")

    casos = _obtener_casos_del_curso(curso)
    if desde:
        casos = [caso for caso in casos if caso['fecha'] and caso['fecha'] >= desde]
    if hasta:
        casos = [caso for caso in casos if caso['fecha'] and caso['fecha'] <= hasta]
    if gravedad in ('Leve', 'Grave', 'Gravísima'):
        casos = [caso for caso in casos if caso['tipo_falta'] == gravedad]
    else:
        gravedad = ''
    return casos, {
        'fecha_desde': desde.isoformat() if desde else '',
        'fecha_hasta': hasta.isoformat() if hasta else '',
        'gravedad': gravedad,
    }

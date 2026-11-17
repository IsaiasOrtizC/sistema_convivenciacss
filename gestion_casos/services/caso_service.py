"""CasoService: lógica de negocio para registrar, consultar y filtrar casos."""

from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection, transaction
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

PRIORIDAD_GRAVEDAD = {'Gravísima': 3, 'Grave': 2, 'Leve': 1}


@trazar('SERVICE', 'CasoService', nivel_min=2)
def identificador_estudiante(estudiante):
    return estudiante.estudiante_identificador or f'Estudiante #{estudiante.estudiante_id}'


def _extraer_titulo_y_cuerpo(texto_completo, caso_id):
    texto = texto_completo or ''
    if ']' in texto and '-' in texto:
        partes = texto.split('] -', 1)
        titulo = partes[0].replace('[', '').strip()
        descripcion = partes[1].strip()
        return (titulo or f'Caso #{caso_id}', descripcion)
    return (texto or f'Caso #{caso_id}', texto)


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
    with transaction.atomic():
        nuevo_caso = Caso.objects.create(
            caso_fecha=fecha,
            caso_descripcion=f"[{titulo}] - {descripcion_cuerpo}",
            evidencia=evidencia,
            lugar=lugar_instancia,
            usuario=usuario_instancia,
        )

        # Precarga de cursos involucrados en 1 sola query
        cursos_ids_req = {datos['curso_id'] for datos in estudiantes_data}
        cursos_map = Curso.objects.in_bulk(cursos_ids_req)

        identificadores_involucrados = []
        estudiantes_involucrados = []
        cursos_alerta = {}
        relaciones_involucran = []

        for datos in estudiantes_data:
            nom_clean = datos['nombre'].strip()
            apat_clean = datos['apellido_paterno'].strip()
            amat_clean = datos['apellido_materno'].strip()
            curso_instancia = cursos_map.get(datos['curso_id'])
            if not curso_instancia:
                raise Curso.DoesNotExist(f"Curso {datos['curso_id']} no encontrado.")

            cursos_alerta[curso_instancia.curso_id] = curso_instancia
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
            if numero_lista is not None and estudiante_instancia.estudiante_numero_lista != numero_lista:
                Estudiante.objects.filter(pk=estudiante_instancia.estudiante_id).update(
                    estudiante_numero_lista=numero_lista
                )
                estudiante_instancia.estudiante_numero_lista = numero_lista

            relaciones_involucran.append(
                (estudiante_instancia.estudiante_id, nuevo_caso.caso_id, tipo_falta)
            )
            identificadores_involucrados.append(identificador_estudiante(estudiante_instancia))
            estudiantes_involucrados.append(estudiante_instancia)

        if relaciones_involucran:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO involucran (estudiante_id, caso_id, tipo_falta)
                    VALUES (%s, %s, %s)
                    """,
                    relaciones_involucran,
                )

        for curso_obj in cursos_alerta.values():
            verificar_alerta_curso_mas_de_10_casos(curso_obj)

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

        if _quitar_tildes(tipo_falta.casefold()) in ('grave', 'gravisima'):
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
def _obtener_casos_del_curso(curso, fecha_desde=None, fecha_hasta=None):
    """Devuelve una lista de diccionarios con los datos de los casos exclusivos de un curso,
    listos para mostrarse en pantalla o exportarse a PDF/XLSX."""
    casos_qs = Caso.objects.filter(estudiantes__curso=curso)
    if fecha_desde:
        casos_qs = casos_qs.filter(caso_fecha__gte=fecha_desde)
    if fecha_hasta:
        casos_qs = casos_qs.filter(caso_fecha__lte=fecha_hasta)

    casos_lista = list(casos_qs.distinct().select_related('lugar').order_by('-caso_fecha'))
    if not casos_lista:
        return []

    caso_ids = [c.caso_id for c in casos_lista]
    placeholders = ','.join(['%s'] * len(caso_ids))

    # Una sola consulta en lote para traer involucrados, nombres y cursos
    involucrados_por_caso = defaultdict(list)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT i.caso_id, i.tipo_falta, e.curso_id,
                   e.estudiante_nombre, e.estudiante_apaterno, e.estudiante_amaterno
            FROM involucran i
            INNER JOIN estudiante e ON e.estudiante_id = i.estudiante_id
            WHERE i.caso_id IN ({placeholders})
            """,
            caso_ids,
        )
        for cid, tf, est_curso_id, nom, apat, amat in cursor.fetchall():
            nombre_completo = f"{nom} {apat} {amat}".strip()
            involucrados_por_caso[cid].append((est_curso_id, tf, nombre_completo))

    resultado = []
    for caso in casos_lista:
        filas = involucrados_por_caso.get(caso.caso_id, [])
        if not filas or any(est_curso_id != curso.pk for est_curso_id, _, _ in filas):
            continue

        nombres_alumnos = []
        tipo_falta = ''
        for _, tf, nombre_completo in filas:
            nombres_alumnos.append(nombre_completo)
            if PRIORIDAD_GRAVEDAD.get(tf, 0) >= PRIORIDAD_GRAVEDAD.get(tipo_falta, 0):
                tipo_falta = tf or tipo_falta

        titulo, descripcion = _extraer_titulo_y_cuerpo(caso.caso_descripcion, caso.caso_id)
        resultado.append({
            'caso_id': caso.caso_id,
            'titulo': titulo,
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

    casos = _obtener_casos_del_curso(curso, fecha_desde=desde, fecha_hasta=hasta)
    if gravedad in ('Leve', 'Grave', 'Gravísima'):
        casos = [caso for caso in casos if caso['tipo_falta'] == gravedad]
    else:
        gravedad = ''

    return casos, {
        'fecha_desde': desde.isoformat() if desde else '',
        'fecha_hasta': hasta.isoformat() if hasta else '',
        'gravedad': gravedad,
    }
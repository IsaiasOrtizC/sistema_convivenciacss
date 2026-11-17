"""Cálculo de las estadísticas del panel (gráficos, tabla de datos y filtros)."""

from collections import defaultdict
from datetime import date

from django.db import connection
from django.db.models import Count, Value
from django.db.models.functions import Concat, ExtractMonth
from django.utils import timezone

from ..models import Caso, Estudiante
from ..trazabilidad import trazar

PRIORIDAD_GRAVEDAD = {'Gravísima': 3, 'Grave': 2, 'Leve': 1}


def _fecha_anio_anterior(fecha):
    try:
        return fecha.replace(year=fecha.year - 1)
    except ValueError:
        return fecha.replace(year=fecha.year - 1, day=28)


def _parse_fecha_segura(valor, fallback):
    if not valor:
        return fallback
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return fallback


def _calcular_ids_casos(fecha_desde, fecha_hasta, curso_id, lugar_id, gravedad):
    """Devuelve la lista de caso_id que cumplen con los filtros dados."""
    qs = Caso.objects.filter(caso_fecha__gte=fecha_desde, caso_fecha__lte=fecha_hasta)

    if curso_id:
        qs = qs.filter(estudiantes__curso_id=curso_id)
    if lugar_id:
        qs = qs.filter(lugar_id=lugar_id)
    if gravedad:
        qs = qs.filter(estudiantes__involucran__tipo_falta=gravedad)

    return list(qs.distinct().values_list('caso_id', flat=True))


@trazar('SERVICE', 'EstadisticaService', 'calculando estadísticas con los filtros aplicados')
def obtener_datos_estadisticas(request):
    """Calcula todos los datos (KPIs, series de gráficos y tabla) según los
    filtros de la request. Usada por la vista de la página, la API JSON y las
    exportaciones PDF/XLSX, para que todas muestren siempre lo mismo."""
    hoy = timezone.localdate()
    anio_actual = hoy.year

    filtro_gravedad = request.GET.get('gravedad', '').strip()
    filtro_curso_id = request.GET.get('curso', '').strip()
    filtro_lugar_id = request.GET.get('zona', '').strip()

    fecha_desde_obj = _parse_fecha_segura(
        request.GET.get('fecha_desde', '').strip(),
        date(anio_actual, 1, 1),
    )
    fecha_hasta_obj = _parse_fecha_segura(
        request.GET.get('fecha_hasta', '').strip(),
        date(anio_actual, 12, 31),
    )
    filtro_fecha_desde = fecha_desde_obj.isoformat()
    filtro_fecha_hasta = fecha_hasta_obj.isoformat()

    caso_ids = _calcular_ids_casos(
        filtro_fecha_desde,
        filtro_fecha_hasta,
        filtro_curso_id,
        filtro_lugar_id,
        filtro_gravedad,
    )
    total_casos = len(caso_ids)

    # ---- Por gravedad (tipo de caso) ----
    dict_gravedad = {'Leve': 0, 'Grave': 0, 'Gravísima': 0}
    if caso_ids:
        placeholders = ','.join(['%s'] * len(caso_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT tipo_falta, COUNT(DISTINCT caso_id) FROM involucran WHERE caso_id IN ({placeholders}) GROUP BY tipo_falta",
                caso_ids,
            )
            for tipo_falta, total in cursor.fetchall():
                if tipo_falta in dict_gravedad:
                    dict_gravedad[tipo_falta] = total

    gravedad_labels = list(dict_gravedad.keys())
    gravedad_data = list(dict_gravedad.values())
    tipo_caso_top = (
        max(dict_gravedad, key=dict_gravedad.get)
        if max(dict_gravedad.values(), default=0) > 0
        else "N/A"
    )

    # ---- Por curso ----
    conteo_cursos = (
        Estudiante.objects.filter(involucran__caso_id__in=caso_ids)
        .exclude(curso__isnull=True)
        .annotate(nombre_completo_curso=Concat('curso__curso_grado', Value(' '), 'curso__curso_letra'))
        .values('nombre_completo_curso')
        .annotate(total=Count('involucran__caso_id', distinct=True))
        .order_by('-total')[:8]
    )
    cursos_labels = [item['nombre_completo_curso'].strip() for item in conteo_cursos]
    cursos_data = [item['total'] for item in conteo_cursos]
    curso_top = cursos_labels[0] if cursos_labels else "N/A"

    # ---- Por zona del colegio (lugar) ----
    conteo_zonas = (
        Caso.objects.filter(caso_id__in=caso_ids)
        .values('lugar__lugar_nombre')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total')[:8]
    )
    zonas_labels = [item['lugar__lugar_nombre'] or "No especificado" for item in conteo_zonas]
    zonas_data = [item['total'] for item in conteo_zonas]
    zona_top = zonas_labels[0] if zonas_labels else "N/A"

    # ---- Evolución mensual (tendencia) ----
    conteo_mensual = (
        Caso.objects.filter(caso_id__in=caso_ids)
        .annotate(mes=ExtractMonth('caso_fecha'))
        .values('mes')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('mes')
    )
    dict_meses = {i: 0 for i in range(1, 13)}
    for item in conteo_mensual:
        if item['mes']:
            dict_meses[item['mes']] = item['total']
    meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    mensual_data = [dict_meses[i] for i in range(1, 13)]

    # ---- Variación % vs el mismo periodo del año anterior ----
    fecha_desde_anterior = _fecha_anio_anterior(fecha_desde_obj)
    fecha_hasta_anterior = _fecha_anio_anterior(fecha_hasta_obj)
    ids_anterior = _calcular_ids_casos(
        fecha_desde_anterior.isoformat(),
        fecha_hasta_anterior.isoformat(),
        filtro_curso_id,
        filtro_lugar_id,
        filtro_gravedad,
    )
    total_anterior = len(ids_anterior)
    if total_anterior > 0:
        variacion_pct = round(((total_casos - total_anterior) / total_anterior) * 100, 1)
    elif total_casos > 0:
        variacion_pct = 100.0
    else:
        variacion_pct = 0.0

    # ---- Tabla de datos en lote (1 sola consulta para relaciones + cursos, sin N+1) ----
    cursos_por_caso = defaultdict(set)
    gravedad_por_caso = {}

    if caso_ids:
        involucrados = (
            Estudiante.objects.filter(involucran__caso_id__in=caso_ids)
            .values_list(
                'involucran__caso_id',
                'involucran__tipo_falta',
                'curso__curso_grado',
                'curso__curso_letra',
            )
        )
        for cid, tipo_falta, grado, letra in involucrados:
            if grado and letra:
                cursos_por_caso[cid].add(f"{grado} {letra}".strip())

            actual = gravedad_por_caso.get(cid, '')
            if PRIORIDAD_GRAVEDAD.get(tipo_falta, 0) >= PRIORIDAD_GRAVEDAD.get(actual, 0):
                gravedad_por_caso[cid] = tipo_falta or actual

    tabla_datos = []
    casos_detalle = (
        Caso.objects.filter(caso_id__in=caso_ids)
        .select_related('lugar')
        .order_by('-caso_fecha')
    )
    for caso in casos_detalle:
        texto = caso.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()

        cursos_set = cursos_por_caso.get(caso.caso_id)
        tabla_datos.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'fecha': caso.caso_fecha,
            'cursos': ", ".join(sorted(cursos_set)) if cursos_set else "Sin curso",
            'zona': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'gravedad': gravedad_por_caso.get(caso.caso_id, ""),
        })

    return {
        'total_casos': total_casos,
        'curso_top': curso_top,
        'tipo_caso_top': tipo_caso_top,
        'zona_top': zona_top,
        'variacion_pct': variacion_pct,
        'gravedad_labels': gravedad_labels,
        'gravedad_data': gravedad_data,
        'cursos_labels': cursos_labels,
        'cursos_data': cursos_data,
        'zonas_labels': zonas_labels,
        'zonas_data': zonas_data,
        'meses_labels': meses_labels,
        'mensual_data': mensual_data,
        'tabla_datos': tabla_datos,
        'filtros': {
            'gravedad': filtro_gravedad,
            'curso': filtro_curso_id,
            'zona': filtro_lugar_id,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
    }
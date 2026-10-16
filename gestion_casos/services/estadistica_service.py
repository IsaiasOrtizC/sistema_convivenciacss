"""Cálculo de las estadísticas del panel (gráficos, tabla de datos y filtros)."""

from django.db import connection
from django.db.models import Count, Value
from django.db.models.functions import Concat, ExtractMonth
from django.utils import timezone

from ..models import Caso, Estudiante
from ..trazabilidad import trazar


def _calcular_ids_casos(fecha_desde, fecha_hasta, curso_id, lugar_id, gravedad):
    """Devuelve la lista de caso_id que cumplen con los filtros dados."""
    qs = Caso.objects.filter(caso_fecha__gte=fecha_desde, caso_fecha__lte=fecha_hasta)
    
    if curso_id:
        qs = qs.filter(estudiantes__curso_id=curso_id)
    if lugar_id:
        qs = qs.filter(lugar_id=lugar_id)
        
    ids = list(qs.distinct().values_list('caso_id', flat=True))

    if gravedad and ids:
        placeholders = ','.join(['%s'] * len(ids))
        query = f"SELECT DISTINCT caso_id FROM involucran WHERE tipo_falta = %s AND caso_id IN ({placeholders})"
        params = [gravedad] + ids
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            ids = [row[0] for row in cursor.fetchall()]

    return ids


@trazar('SERVICE', 'EstadisticaService', 'calculando estadísticas con los filtros aplicados')
def obtener_datos_estadisticas(request):
    """Calcula todos los datos (KPIs, series de gráficos y tabla) según los
    filtros de la request. Usada por la vista de la página, la API JSON y las
    exportaciones PDF/XLSX, para que todas muestren siempre lo mismo."""
    anio_actual = timezone.localdate().year

    filtro_gravedad = request.GET.get('gravedad', '').strip()
    filtro_curso_id = request.GET.get('curso', '').strip()
    filtro_lugar_id = request.GET.get('zona', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip() or f"{anio_actual}-01-01"
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip() or f"{anio_actual}-12-31"

    caso_ids = _calcular_ids_casos(filtro_fecha_desde, filtro_fecha_hasta, filtro_curso_id, filtro_lugar_id, filtro_gravedad)
    total_casos = len(caso_ids)

    # ---- Por gravedad (tipo de caso) ----
    dict_gravedad = {'Leve': 0, 'Grave': 0, 'Gravísima': 0}
    if caso_ids:
        placeholders = ','.join(['%s'] * len(caso_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT tipo_falta, COUNT(DISTINCT caso_id) FROM involucran WHERE caso_id IN ({placeholders}) GROUP BY tipo_falta",
                caso_ids
            )
            for tipo_falta, total in cursor.fetchall():
                if tipo_falta in dict_gravedad:
                    dict_gravedad[tipo_falta] = total
    gravedad_labels = list(dict_gravedad.keys())
    gravedad_data = list(dict_gravedad.values())
    tipo_caso_top = max(dict_gravedad, key=dict_gravedad.get) if max(dict_gravedad.values(), default=0) > 0 else "N/A"

    # ---- Por curso ----
    conteo_cursos = Estudiante.objects.filter(involucran__caso_id__in=caso_ids).exclude(curso__isnull=True)\
        .annotate(nombre_completo_curso=Concat('curso__curso_grado', Value(' '), 'curso__curso_letra'))\
        .values('nombre_completo_curso')\
        .annotate(total=Count('involucran__caso_id', distinct=True))\
        .order_by('-total')[:8]
    cursos_labels = [item['nombre_completo_curso'].strip() for item in conteo_cursos]
    cursos_data = [item['total'] for item in conteo_cursos]
    curso_top = cursos_labels[0] if cursos_labels else "N/A"

    # ---- Por zona del colegio (lugar) ----
    conteo_zonas = Caso.objects.filter(caso_id__in=caso_ids).values('lugar__lugar_nombre')\
        .annotate(total=Count('caso_id', distinct=True)).order_by('-total')[:8]
    zonas_labels = [item['lugar__lugar_nombre'] or "No especificado" for item in conteo_zonas]
    zonas_data = [item['total'] for item in conteo_zonas]
    zona_top = zonas_labels[0] if zonas_labels else "N/A"

    # ---- Evolución mensual (tendencia) ----
    conteo_mensual = Caso.objects.filter(caso_id__in=caso_ids)\
        .annotate(mes=ExtractMonth('caso_fecha')).values('mes')\
        .annotate(total=Count('caso_id', distinct=True)).order_by('mes')
    dict_meses = {i: 0 for i in range(1, 13)}
    for item in conteo_mensual:
        dict_meses[item['mes']] = item['total']
    meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    mensual_data = [dict_meses[i] for i in range(1, 13)]

    # ---- Variación % vs el mismo periodo del año anterior (con los mismos filtros de curso/zona/gravedad) ----
    anio_comparado = int(filtro_fecha_desde[:4])
    anio_anterior = anio_comparado - 1
    ids_anterior = _calcular_ids_casos(f"{anio_anterior}-01-01", f"{anio_anterior}-12-31", filtro_curso_id, filtro_lugar_id, filtro_gravedad)
    total_anterior = len(ids_anterior)
    if total_anterior > 0:
        variacion_pct = round(((total_casos - total_anterior) / total_anterior) * 100, 1)
    elif total_casos > 0:
        variacion_pct = 100.0
    else:
        variacion_pct = 0.0

    # ---- Tabla de datos (detalle de los casos filtrados, usada en pantalla y en las exportaciones) ----
    tabla_datos = []
    casos_detalle = Caso.objects.filter(caso_id__in=caso_ids).select_related('lugar').order_by('-caso_fecha')
    for caso in casos_detalle:
        texto = caso.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()

        with connection.cursor() as cursor:
            cursor.execute("SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s", [caso.caso_id])
            filas = cursor.fetchall()

        cursos_del_caso = set()
        gravedad_caso = ""
        for est_id, tf in filas:
            gravedad_caso = tf
            try:
                est = Estudiante.objects.select_related('curso').get(pk=est_id)
                if est.curso:
                    cursos_del_caso.add(f"{est.curso.curso_grado} {est.curso.curso_letra}")
            except Estudiante.DoesNotExist:
                pass

        tabla_datos.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'fecha': caso.caso_fecha,
            'cursos': ", ".join(sorted(cursos_del_caso)) if cursos_del_caso else "Sin curso",
            'zona': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'gravedad': gravedad_caso,
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
        }
    }

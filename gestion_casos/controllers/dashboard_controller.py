"""Dashboard Controller: resumen principal, indicadores y panel."""

import json
from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from ..models import Caso, Involucran
from ..trazabilidad import trazar
from .auth_casos_controller import bloquear_si_profesor_jefe


def _extraer_titulo_caso(caso):
    texto = caso.caso_descripcion or ''
    if '] -' in texto:
        titulo = texto.split('] -', 1)[0].replace('[', '').strip()
        if titulo:
            return titulo
    return f'Caso #{caso.caso_id}'


@trazar('CONTROLLER', 'DashboardController', 'calculando indicadores y resumen del panel')
def obtener_datos_dashboard(request):
    # CONTADOR GLOBAL DE CASOS Y DESGLOSE POR GRAVEDAD (1 sola consulta agrupada)
    total_casos = Caso.objects.count()
    conteo_por_gravedad = dict(
        Involucran.objects
        .values('tipo_falta')
        .annotate(total=Count('caso_id', distinct=True))
        .values_list('tipo_falta', 'total')
    )
    casos_leves = conteo_por_gravedad.get('Leve', 0)
    casos_graves = conteo_por_gravedad.get('Grave', 0)
    casos_gravisimas = conteo_por_gravedad.get('Gravísima', 0)

    # VENTANA DE ÚLTIMOS 30 DÍAS VS PERIODO ANTERIOR
    hoy = timezone.localdate()
    fecha_inicio = hoy - timedelta(days=29)
    fecha_inicio_anterior = fecha_inicio - timedelta(days=30)
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)

    casos_periodo = Caso.objects.filter(caso_fecha__range=(fecha_inicio, hoy))
    total_casos_periodo = casos_periodo.count()
    total_casos_periodo_anterior = Caso.objects.filter(
        caso_fecha__range=(fecha_inicio_anterior, fecha_fin_anterior)
    ).count()

    if total_casos_periodo_anterior:
        variacion_periodo = round(
            (total_casos_periodo - total_casos_periodo_anterior)
            / total_casos_periodo_anterior * 100,
            1,
        )
    else:
        variacion_periodo = 100.0 if total_casos_periodo else 0.0

    # CASOS POR ZONA EN EL PERIODO
    casos_por_zona = list(
        casos_periodo.values('lugar__lugar_nombre')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'lugar__lugar_nombre')
    )

    zonas_labels = []
    zonas_data = []
    casos_por_zona_lista = []
    for registro in casos_por_zona:
        nombre_zona = registro['lugar__lugar_nombre'] or 'No asignado'
        zonas_labels.append(nombre_zona)
        zonas_data.append(registro['total'])
        casos_por_zona_lista.append({
            'nombre': nombre_zona,
            'total': registro['total'],
        })

    # INDICADORES DESTACADOS DEL PERIODO
    resumen_tipo = (
        Involucran.objects
        .filter(caso__caso_fecha__range=(fecha_inicio, hoy))
        .exclude(tipo_falta='')
        .values('tipo_falta')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'tipo_falta')
        .first()
    )
    resumen_curso = (
        casos_periodo
        .filter(estudiantes__curso__isnull=False)
        .values(
            'estudiantes__curso__curso_grado',
            'estudiantes__curso__curso_letra',
        )
        .annotate(total=Count('caso_id', distinct=True))
        .order_by(
            '-total',
            'estudiantes__curso__curso_grado',
            'estudiantes__curso__curso_letra',
        )
        .first()
    )

    curso_mas_incidentes = (
        f"{resumen_curso['estudiantes__curso__curso_grado']} "
        f"{resumen_curso['estudiantes__curso__curso_letra']}".strip()
        if resumen_curso else 'Sin datos'
    )
    tipo_falta_frecuente = (
        resumen_tipo['tipo_falta'] if resumen_tipo else 'Sin datos'
    )
    zona_mas_conflictos = (
        casos_por_zona_lista[0]['nombre'] if casos_por_zona_lista else 'Sin datos'
    )

    # LISTADO PAGINADO DE INCIDENTES RECIENTES
    casos_query = Caso.objects.select_related('lugar').order_by(
        '-caso_fecha', '-caso_id',
    )
    pagina_casos = Paginator(casos_query, 10).get_page(
        request.GET.get('pagina'),
    )

    lista_casos_dashboard = [
        {
            'id': caso.caso_id,
            'titulo': _extraer_titulo_caso(caso),
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No asignado',
        }
        for caso in pagina_casos
    ]

    return {
        'total_casos': total_casos,
        'casos_leves': casos_leves,
        'casos_graves': casos_graves,
        'casos_gravisimas': casos_gravisimas,
        'casos_recientes': lista_casos_dashboard,
        'pagina_casos': pagina_casos,
        'casos_periodo': total_casos_periodo,
        'curso_mas_incidentes': curso_mas_incidentes,
        'tipo_falta_frecuente': tipo_falta_frecuente,
        'zona_mas_conflictos': zona_mas_conflictos,
        'variacion_periodo': variacion_periodo,
        'zonas_labels_json': json.dumps(zonas_labels),
        'zonas_data_json': json.dumps(zonas_data),
        'casos_por_zona': casos_por_zona_lista,
    }


def dashboard_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    # El Profesor Jefe no ve el panel general: se le redirige directo a su curso
    redireccion = bloquear_si_profesor_jefe(request)
    if redireccion:
        return redireccion

    context = obtener_datos_dashboard(request)
    return render(request, 'gestion_casos/dashboard.html', context)
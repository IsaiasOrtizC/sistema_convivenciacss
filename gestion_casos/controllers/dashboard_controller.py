"""Dashboard Controller: resumen principal, indicadores y panel."""

import json
from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from ..models import Caso, Involucran
from .auth_casos_controller import bloquear_si_profesor_jefe


def dashboard_view(request):
    # 1. Seguridad: Validar que el usuario haya iniciado sesión
    if 'usuario_id' not in request.session:
        return redirect('login')

    # El Profesor Jefe no ve el panel general: se le redirige directo a su curso
    redireccion = bloquear_si_profesor_jefe(request)
    if redireccion:
        return redireccion

    # CONTADOR DE CASOS
    total_casos = Caso.objects.count()
    casos_leves = Involucran.objects.filter(tipo_falta='Leve').values('caso_id').distinct().count()
    casos_graves = Involucran.objects.filter(tipo_falta='Grave').values('caso_id').distinct().count()
    casos_gravisimas = Involucran.objects.filter(tipo_falta='Gravísima').values('caso_id').distinct().count()

    hoy = timezone.localdate()
    fecha_inicio = hoy - timedelta(days=29)
    fecha_inicio_anterior = fecha_inicio - timedelta(days=30)
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    casos_periodo = Caso.objects.filter(caso_fecha__range=(fecha_inicio, hoy))
    total_casos_periodo = casos_periodo.count()
    total_casos_periodo_anterior = Caso.objects.filter(
        caso_fecha__range=(fecha_inicio_anterior, fecha_fin_anterior)
    ).count()

    # CASOS POR ZONA
    casos_por_zona = list(
        casos_periodo.values('lugar__lugar_nombre')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'lugar__lugar_nombre')
    )

    zonas_labels = []
    zonas_data = []
    for registro in casos_por_zona:
        nombre_zona = registro['lugar__lugar_nombre'] if registro['lugar__lugar_nombre'] else "No asignado"
        zonas_labels.append(nombre_zona)
        zonas_data.append(registro['total'])

    resumen_tipo = (
        Involucran.objects.filter(caso__caso_fecha__range=(fecha_inicio, hoy))
        .values('tipo_falta')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'tipo_falta')
        .first()
    )
    resumen_curso = (
        casos_periodo.values(
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
    if total_casos_periodo_anterior:
        variacion_periodo = round(
            (total_casos_periodo - total_casos_periodo_anterior)
            / total_casos_periodo_anterior * 100,
            1,
        )
    else:
        variacion_periodo = 100.0 if total_casos_periodo else 0.0

    curso_mas_incidentes = (
        f"{resumen_curso['estudiantes__curso__curso_grado']} "
        f"{resumen_curso['estudiantes__curso__curso_letra']}"
        if resumen_curso else "Sin datos"
    )
    tipo_falta_frecuente = (
        resumen_tipo['tipo_falta'] if resumen_tipo else "Sin datos"
    )
    zona_mas_conflictos = (
        (casos_por_zona[0]['lugar__lugar_nombre'] or "No asignado")
        if casos_por_zona else "Sin datos"
    )

    # El listado completo se pagina y prioriza los incidentes más recientes.
    casos_query = Caso.objects.select_related('lugar').order_by(
        '-caso_fecha', '-caso_id',
    )
    pagina_casos = Paginator(casos_query, 10).get_page(
        request.GET.get('pagina'),
    )

    # PARA VER EL TITULO DEL CASO
    lista_casos_dashboard = []
    for caso in pagina_casos:
        texto_completo = caso.caso_descripcion if caso.caso_descripcion else ""
        
        if "]" in texto_completo and "-" in texto_completo:
            partes = texto_completo.split("] -", 1)
            titulo_limpio = partes[0].replace("[", "").strip()
        else:
            titulo_limpio = f"Caso #{caso.caso_id}"
        lista_casos_dashboard.append({
            'id': caso.caso_id,
            'titulo': titulo_limpio,
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No asignado"
        })

    
    context = {
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
    }
    
    return render(request, 'gestion_casos/dashboard.html', context)

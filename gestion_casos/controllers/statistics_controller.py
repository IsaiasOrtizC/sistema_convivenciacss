"""Statistics Controller: presentación de tendencias, cantidades y estados."""

import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ..models import Curso, Lugar
from ..permissions import tiene_acceso_estadisticas
from ..services.estadistica_service import obtener_datos_estadisticas


def estadisticas_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not tiene_acceso_estadisticas(request):
        messages.error(request, "Acceso denegado: Esta sección es exclusiva para Administrador, Inspector o Convivencia Escolar.")
        return redirect('dashboard')

    datos = obtener_datos_estadisticas(request)

    context = {
        'datos_json': json.dumps(datos, default=str),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra'),
        'zonas': Lugar.objects.all().order_by('lugar_nombre'),
        'filtros': datos['filtros'],
    }
    return render(request, 'gestion_casos/estadisticas.html', context)


def estadisticas_datos_view(request):
    """API JSON usada por el frontend para refrescar los gráficos automáticamente
    cuando se cambian los filtros, sin recargar la página (RF-30)."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if not tiene_acceso_estadisticas(request):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    datos = obtener_datos_estadisticas(request)
    return JsonResponse(datos, safe=False)

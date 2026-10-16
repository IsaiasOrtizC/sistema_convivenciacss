"""Buscador global de la barra superior (alumnos y casos)."""

from django.db.models import Q
from django.http import JsonResponse

from ..models import Caso, Estudiante, Usuario, _quitar_tildes

# ============================================================
#  BÚSQUEDA GLOBAL (lupa en la barra superior)
# ============================================================

def busqueda_global_view(request):
    """API JSON para el buscador global de la barra superior (alumnos, casos y funcionarios).
    Ignora tildes y mayúsculas/minúsculas en ambos lados (lo que se busca y lo guardado)."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    # El Profesor Jefe no tiene acceso al buscador global (solo ve su propio curso)
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    query = request.GET.get('q', '').strip()
    resultado = {'estudiantes': [], 'casos': [], 'usuarios': []}

    if len(query) < 2:
        return JsonResponse(resultado)

    # Se le quitan las tildes al término buscado, para que coincida sin importar
    # si el usuario escribe "jose" o "josé" (el campo también se compara sin tildes,
    # vía la extensión 'unaccent' de PostgreSQL con el lookup __unaccent).
    query_normalizada = _quitar_tildes(query)

    # ---- Alumnos ----
    estudiantes = Estudiante.objects.select_related('curso').filter(
        Q(estudiante_nombre__unaccent__icontains=query_normalizada) |
        Q(estudiante_apaterno__unaccent__icontains=query_normalizada) |
        Q(estudiante_amaterno__unaccent__icontains=query_normalizada) |
        Q(estudiante_identificador__icontains=query.upper())
    )[:8]
    for e in estudiantes:
        resultado['estudiantes'].append({
            'id': e.estudiante_id,
            'nombre_completo': f"{e.estudiante_nombre} {e.estudiante_apaterno} {e.estudiante_amaterno}",
            'curso': f"{e.curso.curso_grado} {e.curso.curso_letra}" if e.curso else "Sin curso asignado",
        })

    # ---- Casos ----
    casos = Caso.objects.filter(
        caso_descripcion__unaccent__icontains=query_normalizada
    ).select_related('lugar').order_by('-caso_fecha')[:8]
    for c in casos:
        texto = c.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()
        resultado['casos'].append({
            'id': c.caso_id,
            'titulo': titulo if titulo else f"Caso #{c.caso_id}",
            'fecha': c.caso_fecha.strftime('%d/%m/%Y') if c.caso_fecha else '',
            'lugar': c.lugar.lugar_nombre if c.lugar else 'No especificado',
        })

    # ---- Funcionarios (Profesor Jefe, Inspector, Administrador, Convivencia) ----
    usuarios = Usuario.objects.select_related('rol').filter(
        Q(usuario_nombre__unaccent__icontains=query_normalizada) |
        Q(usuario_apaterno__unaccent__icontains=query_normalizada) |
        Q(usuario_amaterno__unaccent__icontains=query_normalizada) |
        Q(usuario_correo__icontains=query)
    )[:6]
    for u in usuarios:
        resultado['usuarios'].append({
            'id': u.usuario_id,
            'nombre_completo': f"{u.usuario_nombre} {u.usuario_apaterno} {u.usuario_amaterno}",
            'correo': u.usuario_correo,
            'rol': u.rol.rol_nombre if u.rol else '',
        })

    return JsonResponse(resultado)

"""Buscador global de la barra superior (alumnos, casos y funcionarios)."""

from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.urls import reverse

from ..models import Caso, Estudiante, Usuario, _quitar_tildes
from ..trazabilidad import trazar


@trazar('CONTROLADOR', 'BusquedaController', 'ejecutando búsqueda global')
def busqueda_global_view(request):
    """API JSON para el buscador global de la barra superior (alumnos, casos y funcionarios).
    Ignora tildes y mayúsculas/minúsculas tanto en el término buscado como en los registros."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    rol_usuario = (request.session.get('usuario_rol') or '').strip()
    if 'profesor' in rol_usuario.casefold():
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    query = request.GET.get('q', '').strip()[:80]
    resultado = {'estudiantes': [], 'casos': [], 'usuarios': []}

    if len(query) < 2:
        return JsonResponse(resultado)

    query_normalizada = _quitar_tildes(query)
    rut_normalizado = query.upper().replace('.', '').strip()

    # ---- Alumnos ----
    estudiantes = (
        Estudiante.objects
        .select_related('curso')
        .annotate(
            nombre_completo_db=Concat(
                'estudiante_nombre',
                Value(' '),
                'estudiante_apaterno',
                Value(' '),
                'estudiante_amaterno',
            )
        )
        .filter(
            Q(nombre_completo_db__unaccent__icontains=query_normalizada)
            | Q(estudiante_identificador__icontains=rut_normalizado)
        )
        .order_by('estudiante_apaterno', 'estudiante_nombre')[:8]
    )
    for e in estudiantes:
        resultado['estudiantes'].append({
            'id': e.estudiante_id,
            'nombre_completo': f"{e.estudiante_nombre} {e.estudiante_apaterno} {e.estudiante_amaterno}".strip(),
            'curso': f"{e.curso.curso_grado} {e.curso.curso_letra}".strip() if e.curso else "Sin curso asignado",
            'url': reverse('detalle_estudiante', args=[e.estudiante_id]),
        })

    # ---- Casos (por #ID, descripción o alumno involucrado) ----
    filtro_casos = (
        Q(caso_descripcion__unaccent__icontains=query_normalizada)
        | Q(estudiantes__estudiante_nombre__unaccent__icontains=query_normalizada)
        | Q(estudiantes__estudiante_apaterno__unaccent__icontains=query_normalizada)
    )
    codigo_numerico = query.lstrip('#').strip()
    if codigo_numerico.isdigit():
        filtro_casos |= Q(caso_id=int(codigo_numerico))

    casos = (
        Caso.objects
        .filter(filtro_casos)
        .select_related('lugar')
        .distinct()
        .order_by('-caso_fecha', '-caso_id')[:8]
    )
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
            'url': reverse('detalle_caso', args=[c.caso_id]),
        })

    # ---- Funcionarios activos ----
    usuarios = (
        Usuario.objects
        .select_related('rol')
        .annotate(
            nombre_completo_db=Concat(
                'usuario_nombre',
                Value(' '),
                'usuario_apaterno',
                Value(' '),
                'usuario_amaterno',
            )
        )
        .filter(usuario_activo=True)
        .filter(
            Q(nombre_completo_db__unaccent__icontains=query_normalizada)
            | Q(usuario_correo__icontains=query)
        )
        .order_by('usuario_apaterno', 'usuario_nombre')[:6]
    )
    for u in usuarios:
        resultado['usuarios'].append({
            'id': u.usuario_id,
            'nombre_completo': f"{u.usuario_nombre} {u.usuario_apaterno} {u.usuario_amaterno}".strip(),
            'correo': u.usuario_correo,
            'rol': u.rol.rol_nombre if u.rol else '',
            'url': f"{reverse('gestion_de_usuarios')}?q={u.usuario_correo}",
        })

    return JsonResponse(resultado)
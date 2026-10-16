"""Auth casos: autoriza consultas y modificaciones de casos según el rol."""

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from ..models import Caso, Estudiante, ProfesorJefe
from ..trazabilidad import trazar


# ES LA PANTALLA DE INICIO
@trazar('CONTROLADOR', 'AuthCasosController', 'verificando si es Profesor Jefe', nivel_min=2)
def bloquear_si_profesor_jefe(request, mensaje=None):
    """Helper de seguridad: el Profesor Jefe solo debe acceder a 'Mi Curso',
    su Perfil, Configuración y Documentos. Se usa al inicio de las demás
    vistas para bloquearlo y redirigirlo a su propia sección."""
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        if mensaje:
            messages.error(request, mensaje)
        return redirect('mis_casos_curso')
    return None


@trazar('CONTROLADOR', 'AuthCasosController', 'verificando permiso de edición del caso', nivel_min=2)
def puede_editar_caso(rol, caso, momento=None):
    if rol == 'Administrador':
        return True
    if rol not in ('Inspector', 'PConvivencia') or not caso.caso_creado_en:
        return False
    diferencia = (momento or timezone.now()) - caso.caso_creado_en
    return timedelta(0) <= diferencia <= timedelta(hours=48)


@trazar('CONTROLADOR', 'AuthCasosController', 'validando el curso del Profesor Jefe', nivel_min=2)
def validar_profesor_jefe(request):
    """Valida sesión + rol + curso asignado. Devuelve el objeto Curso o None si algo falla."""
    if 'usuario_id' not in request.session:
        return None
    if request.session.get('usuario_rol', '') != 'Profesor Jefe':
        return None
    try:
        profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
    except ProfesorJefe.DoesNotExist:
        return None
    if not profesor.curso:
        return None
    return profesor.curso


@trazar('CONTROLADOR', 'AuthCasosController', 'validando acceso a la exportación del caso', nivel_min=2)
def validar_acceso_exportacion_caso(request, caso_id):
    if 'usuario_id' not in request.session:
        return None
    rol = request.session.get('usuario_rol')
    if rol not in ('Administrador', 'Inspector', 'PConvivencia', 'Profesor Jefe'):
        messages.error(request, "Acceso denegado: no tienes permisos para descargar este caso.")
        return None
    caso = get_object_or_404(
        Caso.objects.select_related('lugar'),
        pk=caso_id,
    )
    if rol == 'Profesor Jefe':
        curso = validar_profesor_jefe(request)
        if not curso or not Estudiante.objects.filter(
            involucran__caso_id=caso_id,
            curso=curso,
        ).exists():
            messages.error(request, "Acceso denegado: ese caso no corresponde a tu curso.")
            return None
    return caso

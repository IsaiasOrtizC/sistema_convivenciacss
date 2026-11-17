"""Auth casos: autoriza consultas y modificaciones de casos según el rol."""

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from ..models import Caso, Estudiante, ProfesorJefe, Usuario
from ..trazabilidad import trazar


def _es_rol_profesor(rol):
    return 'profesor' in (rol or '').strip().casefold()


def _usuario_sesion_habilitado(usuario_id):
    if not usuario_id:
        return False
    return Usuario.objects.filter(
        pk=usuario_id,
        usuario_activo=True,
        usuario_bloqueado=False,
    ).exists()


# PANTALLA DE INICIO Y RESTRICCIÓN DE ROL
@trazar('CONTROLADOR', 'AuthCasosController', 'verificando si es Profesor Jefe', nivel_min=2)
def bloquear_si_profesor_jefe(request, mensaje=None):
    """Helper de seguridad: el Profesor Jefe solo debe acceder a 'Mi Curso',
    su Perfil, Configuración y Documentos. Se usa al inicio de las demás
    vistas para bloquearlo y redirigirlo a su propia sección."""
    if _es_rol_profesor(request.session.get('usuario_rol')):
        if mensaje:
            messages.error(request, mensaje)
        return redirect('mis_casos_curso')
    return None


@trazar('CONTROLADOR', 'AuthCasosController', 'verificando permiso de edición del caso', nivel_min=2)
def puede_editar_caso(rol, caso, momento=None):
    if rol == 'Administrador':
        return True
    if rol not in ('Inspector', 'PConvivencia') or not caso or not caso.caso_creado_en:
        return False
    diferencia = (momento or timezone.now()) - caso.caso_creado_en
    return timedelta(0) <= diferencia <= timedelta(hours=48)


@trazar('CONTROLADOR', 'AuthCasosController', 'verificando permiso de eliminación del caso', nivel_min=2)
def puede_eliminar_caso(rol, caso, momento=None):
    if rol == 'Administrador':
        return True
    if rol != 'Inspector' or not caso or not caso.caso_creado_en:
        return False
    diferencia = (momento or timezone.now()) - caso.caso_creado_en
    return timedelta(0) <= diferencia <= timedelta(hours=12)


@trazar('CONTROLADOR', 'AuthCasosController', 'validando el curso del Profesor Jefe', nivel_min=2)
def validar_profesor_jefe(request):
    """Valida sesión + cuenta activa + rol + curso asignado. Devuelve el objeto Curso o None."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    if not _es_rol_profesor(request.session.get('usuario_rol')):
        return None

    profesor = (
        ProfesorJefe.objects
        .select_related('curso')
        .filter(
            usuario_id=usuario_id,
            usuario__usuario_activo=True,
            usuario__usuario_bloqueado=False,
            curso__isnull=False,
        )
        .first()
    )
    return profesor.curso if profesor else None


@trazar('CONTROLADOR', 'AuthCasosController', 'verificando visibilidad del caso para el curso', nivel_min=2)
def caso_visible_para_curso(caso_o_id, curso):
    """Comprueba que el caso tenga estudiantes involucrados y todos pertenezcan al curso dado."""
    if not curso or not caso_o_id:
        return False
    caso_id = caso_o_id.pk if isinstance(caso_o_id, Caso) else caso_o_id
    cursos_involucrados = set(
        Estudiante.objects
        .filter(involucran__caso_id=caso_id)
        .values_list('curso_id', flat=True)
        .distinct()
    )
    return cursos_involucrados == {curso.pk}


@trazar('CONTROLADOR', 'AuthCasosController', 'validando acceso a la exportación del caso', nivel_min=2)
def validar_acceso_exportacion_caso(request, caso_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None

    rol = (request.session.get('usuario_rol') or '').strip()
    es_profesor = _es_rol_profesor(rol)
    if rol not in ('Administrador', 'Inspector', 'PConvivencia') and not es_profesor:
        messages.error(request, "Acceso denegado: no tienes permisos para descargar este caso.")
        return None

    if not _usuario_sesion_habilitado(usuario_id):
        messages.error(request, "Tu cuenta se encuentra inactiva o bloqueada.")
        return None

    caso = get_object_or_404(
        Caso.objects.select_related('lugar'),
        pk=caso_id,
    )

    if es_profesor:
        curso = validar_profesor_jefe(request)
        if not caso_visible_para_curso(caso, curso):
            messages.error(request, "Acceso denegado: ese caso no corresponde a tu curso.")
            return None

    return caso
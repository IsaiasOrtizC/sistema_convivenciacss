"""User Controller: crear, consultar, modificar, desbloquear, activar o desactivar usuarios y consultar su historial de acciones."""

import logging
import secrets
import string

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from ..models import (
    Administrador,
    Curso,
    HistorialUsuario,
    Inspector,
    PConvivencia,
    ProfesorJefe,
    Rol,
    SesionActiva,
    Usuario,
    _quitar_tildes,
)
from ..trazabilidad import traza_consulta
from .email_controller import programar_tarea_correo

logger = logging.getLogger(__name__)


def _sincronizar_subtipo_rol(usuario_obj, rol_instancia, curso_instancia=None):
    """Mantiene sincronizada la tabla específica del rol del funcionario."""
    Administrador.objects.filter(usuario=usuario_obj).delete()
    Inspector.objects.filter(usuario=usuario_obj).delete()
    PConvivencia.objects.filter(usuario=usuario_obj).delete()
    ProfesorJefe.objects.filter(usuario=usuario_obj).delete()

    nombre = usuario_obj.usuario_nombre
    apaterno = usuario_obj.usuario_apaterno
    amaterno = usuario_obj.usuario_amaterno

    if rol_instancia.rol_nombre == 'Administrador':
        Administrador.objects.create(
            usuario=usuario_obj,
            admin_nombre=nombre,
            admin_apaterno=apaterno,
            admin_amaterno=amaterno,
        )
    elif rol_instancia.rol_nombre == 'Inspector':
        Inspector.objects.create(
            usuario=usuario_obj,
            inspector_nombre=nombre,
            inspector_apaterno=apaterno,
            inspector_amaterno=amaterno,
        )
    elif rol_instancia.rol_nombre == 'PConvivencia':
        PConvivencia.objects.create(
            usuario=usuario_obj,
            convivencia_nombre=nombre,
            convivencia_apaterno=apaterno,
            convivencia_amaterno=amaterno,
        )
    elif rol_instancia.rol_nombre == 'Profesor Jefe':
        ProfesorJefe.objects.create(
            usuario=usuario_obj,
            curso=curso_instancia,
            profesor_nombre=nombre,
            profesor_apaterno=apaterno,
            profesor_amaterno=amaterno,
        )


def _registrar_auditoria(admin_id, accion, detalle):
    if not admin_id:
        return
    admin_instancia = Usuario.objects.filter(pk=admin_id).first()
    if admin_instancia:
        HistorialUsuario.objects.create(
            usuario=admin_instancia,
            historial_accion=accion,
            historial_detalle=detalle,
        )


# GESTION USUARIOS
def gestion_de_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    admin_id = request.session.get('usuario_id')

    # NUEVO USUARIO
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')

        try:
            validate_email(correo)
            if not (nombre and apaterno and amaterno):
                messages.error(request, "Completa los nombres y apellidos del funcionario.")
                return redirect('gestion_de_usuarios')

            if Usuario.objects.filter(usuario_correo__iexact=correo).exists():
                messages.error(request, f"El correo {correo} ya se encuentra registrado.")
                return redirect('gestion_de_usuarios')

            rol_instancia = Rol.objects.get(pk=rol_id)

            curso_instancia = None
            if rol_instancia.rol_nombre == 'Profesor Jefe':
                if not curso_id:
                    messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                    return redirect('gestion_de_usuarios')
                curso_instancia = Curso.objects.get(pk=curso_id)
                if ProfesorJefe.objects.filter(curso=curso_instancia).exists():
                    messages.error(
                        request,
                        f"El curso {curso_instancia} ya tiene un Profesor Jefe asignado.",
                    )
                    return redirect('gestion_de_usuarios')

            contrasena_temporal = _generar_contrasena_temporal()
            with transaction.atomic():
                nuevo_usuario = Usuario.objects.create(
                    usuario_nombre=nombre,
                    usuario_apaterno=apaterno,
                    usuario_amaterno=amaterno,
                    usuario_correo=correo,
                    usuario_contrasena=make_password(contrasena_temporal),
                    usuario_primer_ingreso=True,
                    rol=rol_instancia,
                )
                _sincronizar_subtipo_rol(nuevo_usuario, rol_instancia, curso_instancia)
                _registrar_auditoria(
                    admin_id,
                    'Creación',
                    f"Creó al funcionario {nombre} {apaterno} ({correo}) con rol {rol_instancia.rol_nombre}.",
                )

                from ..tasks import enviar_credenciales_usuario

                programar_tarea_correo(
                    request,
                    enviar_credenciales_usuario,
                    (correo, nombre, apaterno, contrasena_temporal),
                    "La cuenta se creó, pero no se pudo encolar el correo con la contraseña temporal. Contacta al administrador del sistema.",
                )

            messages.success(
                request,
                f"Funcionario {nombre} {apaterno} creado. Se enviará una contraseña temporal a su correo institucional.",
            )
            return redirect('gestion_de_usuarios')

        except ValidationError:
            messages.error(request, "Ingresa un correo institucional válido.")
        except (Rol.DoesNotExist, Curso.DoesNotExist):
            messages.error(request, "El rol o curso seleccionado no existe.")
        except Exception:
            logger.exception("No se pudo crear el usuario institucional.")
            messages.error(request, "Ocurrió un error al intentar registrar al usuario.")

    # Filtros combinables (nombre, rol, estado de cuenta, fecha de último acceso)
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_rol_id = request.GET.get('rol', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    traza_consulta(
        'usuarios', nombre=filtro_nombre, rol=filtro_rol_id, estado=filtro_estado,
        desde=filtro_fecha_desde, hasta=filtro_fecha_hasta,
    )

    usuarios_registrados = (
        Usuario.objects
        .select_related('rol', 'profesorjefe', 'profesorjefe__curso')
        .all()
        .order_by('usuario_apaterno', 'usuario_nombre')
    )

    if filtro_nombre:
        for termino in filtro_nombre.split():
            nombre_normalizado = _quitar_tildes(termino)
            usuarios_registrados = usuarios_registrados.filter(
                Q(usuario_nombre__unaccent__icontains=nombre_normalizado)
                | Q(usuario_apaterno__unaccent__icontains=nombre_normalizado)
                | Q(usuario_amaterno__unaccent__icontains=nombre_normalizado)
                | Q(usuario_correo__icontains=termino)
            )

    if filtro_rol_id and filtro_rol_id.isdigit():
        usuarios_registrados = usuarios_registrados.filter(rol_id=int(filtro_rol_id))

    if filtro_estado == 'activo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=True)
    elif filtro_estado == 'inactivo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=False)

    desde_dt = parse_date(filtro_fecha_desde) if filtro_fecha_desde else None
    hasta_dt = parse_date(filtro_fecha_hasta) if filtro_fecha_hasta else None
    if desde_dt:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__gte=desde_dt)
    if hasta_dt:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__lte=hasta_dt)

    roles_disponibles = Rol.objects.all().order_by('rol_nombre')
    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    context = {
        'usuarios': usuarios_registrados,
        'usuario_actual_id': admin_id,
        'roles': roles_disponibles,
        'cursos': cursos_disponibles,
        'filtros': {
            'nombre': filtro_nombre,
            'rol': filtro_rol_id,
            'estado': filtro_estado,
            'fecha_desde': desde_dt.isoformat() if desde_dt else '',
            'fecha_hasta': hasta_dt.isoformat() if hasta_dt else '',
        },
        'hay_filtros_activos': bool(
            filtro_nombre or filtro_rol_id or filtro_estado or desde_dt or hasta_dt
        ),
    }
    return render(request, 'gestion_casos/gestion_de_usuarios.html', context)


# SELECCIÓN MÚLTIPLE DE USUARIOS PARA DESACTIVAR O ELIMINAR (solo Administrador)
def acciones_masivas_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_usuarios')

    accion = request.POST.get('accion', '')
    if accion not in ('desactivar', 'eliminar'):
        messages.error(request, "Acción no válida.")
        return redirect('gestion_de_usuarios')

    ids = [int(x) for x in request.POST.getlist('usuarios_seleccionados') if x.isdigit()]
    if not ids:
        messages.warning(request, "Debes seleccionar al menos un usuario.")
        return redirect('gestion_de_usuarios')

    admin_id = request.session.get('usuario_id')
    omitido_propio = admin_id in ids
    lista = list(Usuario.objects.filter(pk__in=ids).exclude(pk=admin_id))
    if not lista:
        messages.warning(request, "No se puede aplicar la acción sobre tu propia cuenta.")
        return redirect('gestion_de_usuarios')

    nombres = [f"{u.usuario_nombre} {u.usuario_apaterno} (#{u.usuario_id})" for u in lista]
    ids_objetivo = [u.usuario_id for u in lista]

    try:
        with transaction.atomic():
            if accion == 'desactivar':
                Usuario.objects.filter(pk__in=ids_objetivo).update(usuario_activo=False)
                SesionActiva.objects.filter(usuario_id__in=ids_objetivo).delete()
                accion_hist, verbo_msg = "Desactivación masiva", "desactivado(s)"
            else:
                SesionActiva.objects.filter(usuario_id__in=ids_objetivo).delete()
                Usuario.objects.filter(pk__in=ids_objetivo).delete()
                accion_hist, verbo_msg = "Eliminación masiva", "eliminado(s)"

            _registrar_auditoria(
                admin_id,
                accion_hist,
                f"{accion_hist} de {len(lista)} usuario(s): " + ", ".join(nombres) + ".",
            )

        mensaje = f"{len(lista)} usuario(s) {verbo_msg} exitosamente."
        if omitido_propio:
            mensaje += " Tu propia cuenta fue omitida."
        messages.success(request, mensaje)
    except Exception:
        logger.exception("Error al ejecutar acción masiva de usuarios (%s).", accion)
        messages.error(request, "Ocurrió un error al procesar la acción masiva.")

    return redirect('gestion_de_usuarios')


def editar_usuario_view(request, usuario_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    admin_id = request.session.get('usuario_id')
    usuario_editar = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        contrasena = request.POST.get('contrasena', '').strip()
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')
        cuenta_activa = request.POST.get('activo') == 'on'

        if usuario_editar.usuario_id == admin_id and not cuenta_activa:
            messages.error(request, "No puedes desactivar tu propia cuenta de Administrador.")
            return redirect('gestion_de_usuarios')

        try:
            validate_email(correo)
            if not (nombre and apaterno and amaterno):
                messages.error(request, "Completa los nombres y apellidos del funcionario.")
                return redirect('gestion_de_usuarios')

            if Usuario.objects.filter(usuario_correo__iexact=correo).exclude(pk=usuario_id).exists():
                messages.error(request, f"El correo {correo} ya está en uso por otro funcionario.")
                return redirect('gestion_de_usuarios')

            rol_instancia = Rol.objects.get(pk=rol_id)

            curso_instancia = None
            if rol_instancia.rol_nombre == 'Profesor Jefe':
                if not curso_id:
                    messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                    return redirect('gestion_de_usuarios')
                curso_instancia = Curso.objects.get(pk=curso_id)
                if (
                    ProfesorJefe.objects
                    .filter(curso=curso_instancia)
                    .exclude(usuario=usuario_editar)
                    .exists()
                ):
                    messages.error(
                        request,
                        f"El curso {curso_instancia} ya tiene otro Profesor Jefe asignado.",
                    )
                    return redirect('gestion_de_usuarios')

            with transaction.atomic():
                usuario_editar.usuario_nombre = nombre
                usuario_editar.usuario_apaterno = apaterno
                usuario_editar.usuario_amaterno = amaterno
                usuario_editar.usuario_correo = correo
                usuario_editar.rol = rol_instancia
                usuario_editar.usuario_activo = cuenta_activa
                usuario_editar.usuario_bloqueado = False
                usuario_editar.usuario_intentos_fallidos = 0
                if contrasena:
                    usuario_editar.usuario_contrasena = make_password(contrasena)
                usuario_editar.save()

                if not cuenta_activa:
                    SesionActiva.objects.filter(usuario=usuario_editar).delete()

                _sincronizar_subtipo_rol(usuario_editar, rol_instancia, curso_instancia)
                _registrar_auditoria(
                    admin_id,
                    'Modificación',
                    f"Actualizó los datos de {nombre} {apaterno} (#{usuario_editar.usuario_id}, rol {rol_instancia.rol_nombre}).",
                )

            messages.success(request, f"Funcionario {nombre} {apaterno} actualizado exitosamente.")

        except ValidationError:
            messages.error(request, "Ingresa un correo institucional válido.")
        except (Rol.DoesNotExist, Curso.DoesNotExist):
            messages.error(request, "El rol o curso seleccionado no existe.")
        except Exception:
            logger.exception("Error al actualizar al usuario %s.", usuario_id)
            messages.error(request, "Ocurrió un error al actualizar al usuario.")

    return redirect('gestion_de_usuarios')


def desbloquear_usuario_view(request, usuario_id):
    """Permite al Administrador desbloquear una cuenta bloqueada por intentos fallidos."""
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_usuarios')

    usuario_desbloquear = get_object_or_404(Usuario, pk=usuario_id)
    with transaction.atomic():
        usuario_desbloquear.usuario_bloqueado = False
        usuario_desbloquear.usuario_intentos_fallidos = 0
        usuario_desbloquear.save(update_fields=['usuario_bloqueado', 'usuario_intentos_fallidos'])
        _registrar_auditoria(
            request.session.get('usuario_id'),
            'Modificación',
            f"Desbloqueó la cuenta de {usuario_desbloquear.usuario_nombre} {usuario_desbloquear.usuario_apaterno} (#{usuario_desbloquear.usuario_id}).",
        )

    messages.success(
        request,
        f"La cuenta de {usuario_desbloquear.usuario_nombre} {usuario_desbloquear.usuario_apaterno} fue desbloqueada exitosamente.",
    )
    return redirect('gestion_de_usuarios')


# HISTORIAL DE ACCIONES USUARIOS
def historial_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    filtro_usuario = request.GET.get('usuario', '').strip()
    filtro_busqueda = request.GET.get('busqueda', '').strip()
    filtro_accion = request.GET.get('accion', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    traza_consulta(
        'el historial de usuarios', usuario=filtro_usuario, busqueda=filtro_busqueda,
        accion=filtro_accion, desde=filtro_fecha_desde, hasta=filtro_fecha_hasta,
    )

    base_qs = HistorialUsuario.objects.select_related('usuario')
    total_registros = base_qs.count()
    registros_auditoria = base_qs.order_by('-historial_fecha')

    if filtro_usuario:
        for termino in filtro_usuario.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(usuario__usuario_nombre__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_apaterno__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_amaterno__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_correo__icontains=termino)
            )

    if filtro_busqueda:
        for termino in filtro_busqueda.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(historial_detalle__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_nombre__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_apaterno__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_amaterno__unaccent__icontains=termino_norm)
            )

    if filtro_accion:
        registros_auditoria = registros_auditoria.filter(historial_accion=filtro_accion)

    fecha_desde = parse_date(filtro_fecha_desde) if filtro_fecha_desde else None
    fecha_hasta = parse_date(filtro_fecha_hasta) if filtro_fecha_hasta else None

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
        messages.warning(request, "La fecha 'desde' era posterior a 'hasta'; se invirtieron para aplicar el filtro.")

    if fecha_desde:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__gte=fecha_desde)
    if fecha_hasta:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__lte=fecha_hasta)

    filtro_fecha_desde = fecha_desde.isoformat() if fecha_desde else ''
    filtro_fecha_hasta = fecha_hasta.isoformat() if fecha_hasta else ''

    acciones_disponibles = (
        HistorialUsuario.objects.order_by('historial_accion')
        .values_list('historial_accion', flat=True).distinct()
    )
    usuarios_historial = (
        Usuario.objects.filter(historial_acciones__isnull=False)
        .distinct().order_by('usuario_apaterno', 'usuario_nombre')
    )

    context = {
        'historial': registros_auditoria,
        'total_registros': total_registros,
        'acciones_disponibles': acciones_disponibles,
        'usuarios_historial': usuarios_historial,
        'filtros': {
            'usuario': filtro_usuario,
            'busqueda': filtro_busqueda,
            'accion': filtro_accion,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(
            filtro_usuario or filtro_busqueda or filtro_accion
            or filtro_fecha_desde or filtro_fecha_hasta
        ),
    }
    return render(request, 'gestion_casos/historial_de_usuarios.html', context)


def _generar_contrasena_temporal():
    alfabeto = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabeto) for _ in range(14))
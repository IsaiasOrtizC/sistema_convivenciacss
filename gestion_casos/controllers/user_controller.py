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

from ..models import (
    Administrador,
    Curso,
    HistorialUsuario,
    Inspector,
    PConvivencia,
    ProfesorJefe,
    Rol,
    Usuario,
    _quitar_tildes,
)
from ..trazabilidad import traza_consulta
from .email_controller import programar_tarea_correo

logger = logging.getLogger(__name__)


# GESTION USUARIOS
def gestion_de_usuarios_view(request):
    #VERIFICA SI ES ADMON
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    # NUEVO USUARIO
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')  # Solo se usa si el rol es "Profesor Jefe"

        try:
            validate_email(correo)
            if not (nombre and apaterno and amaterno):
                messages.error(request, "Completa los nombres y apellidos del funcionario.")
                return redirect('gestion_de_usuarios')

            #PARA VER SI EL CORREO EXISTE
            if Usuario.objects.filter(usuario_correo=correo).exists():
                messages.error(request, f"El correo {correo} ya se encuentra registrado.")
            else:
                rol_instancia = Rol.objects.get(pk=rol_id)

                # Si el rol es Profesor Jefe, el curso es obligatorio antes de crear nada
                curso_instancia = None
                if rol_instancia.rol_nombre == 'Profesor Jefe':
                    if not curso_id:
                        messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                        return redirect('gestion_de_usuarios')
                    curso_instancia = Curso.objects.get(pk=curso_id)

                contrasena_temporal = _generar_contrasena_temporal()
                with transaction.atomic():
                    nuevo_usuario = Usuario(
                        usuario_nombre=nombre,
                        usuario_apaterno=apaterno,
                        usuario_amaterno=amaterno,
                        usuario_correo=correo,
                        usuario_contrasena=make_password(contrasena_temporal),
                        usuario_primer_ingreso=True,
                        rol=rol_instancia
                    )
                    nuevo_usuario.save()

                    # Crea también el registro específico según el rol asignado
                    if rol_instancia.rol_nombre == 'Administrador':
                        Administrador.objects.create(
                            usuario=nuevo_usuario, admin_nombre=nombre,
                            admin_apaterno=apaterno, admin_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'Inspector':
                        Inspector.objects.create(
                            usuario=nuevo_usuario, inspector_nombre=nombre,
                            inspector_apaterno=apaterno, inspector_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'PConvivencia':
                        PConvivencia.objects.create(
                            usuario=nuevo_usuario, convivencia_nombre=nombre,
                            convivencia_apaterno=apaterno, convivencia_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'Profesor Jefe':
                        ProfesorJefe.objects.create(
                            usuario=nuevo_usuario, curso=curso_instancia,
                            profesor_nombre=nombre, profesor_apaterno=apaterno,
                            profesor_amaterno=amaterno
                        )

                    from ..tasks import enviar_credenciales_usuario

                    programar_tarea_correo(
                        request,
                        enviar_credenciales_usuario,
                        (correo, nombre, apaterno, contrasena_temporal),
                        "La cuenta se creó, pero no se pudo encolar el correo con la contraseña temporal. Contacta al administrador del sistema.",
                    )

                messages.success(request, f"Funcionario {nombre} {apaterno} creado. Se enviará una contraseña temporal a su correo institucional.")
                return redirect('gestion_de_usuarios')

        except ValidationError:
            messages.error(request, "Ingresa un correo institucional válido.")
        except Exception as e:
            logger.exception("No se pudo crear el usuario institucional.")
            messages.error(request, "Ocurrió un error al intentar registrar al usuario.")

    
    # RF: filtros combinables (nombre, rol, estado de cuenta, fecha de último acceso)
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_rol_id = request.GET.get('rol', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    traza_consulta(
        'usuarios', nombre=filtro_nombre, rol=filtro_rol_id, estado=filtro_estado,
        desde=filtro_fecha_desde, hasta=filtro_fecha_hasta,
    )

    usuarios_registrados = Usuario.objects.select_related('rol', 'profesorjefe').all().order_by('usuario_apaterno')

    if filtro_nombre:
        nombre_normalizado = _quitar_tildes(filtro_nombre)
        usuarios_registrados = usuarios_registrados.filter(
            Q(usuario_nombre__unaccent__icontains=nombre_normalizado) |
            Q(usuario_apaterno__unaccent__icontains=nombre_normalizado) |
            Q(usuario_amaterno__unaccent__icontains=nombre_normalizado) |
            Q(usuario_correo__icontains=filtro_nombre)
        )

    if filtro_rol_id:
        usuarios_registrados = usuarios_registrados.filter(rol_id=filtro_rol_id)

    if filtro_estado == 'activo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=True)
    elif filtro_estado == 'inactivo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=False)

    if filtro_fecha_desde:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__gte=filtro_fecha_desde)

    if filtro_fecha_hasta:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__lte=filtro_fecha_hasta)

    roles_disponibles = Rol.objects.all().order_by('rol_nombre')
    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    context = {
        'usuarios': usuarios_registrados,
        'usuario_actual_id': request.session.get('usuario_id'),
        'roles': roles_disponibles,
        'cursos': cursos_disponibles,
        'filtros': {
            'nombre': filtro_nombre,
            'rol': filtro_rol_id,
            'estado': filtro_estado,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(filtro_nombre or filtro_rol_id or filtro_estado or filtro_fecha_desde or filtro_fecha_hasta),
    }
    return render(request, 'gestion_casos/gestion_de_usuarios.html', context)


# RF: SELECCIÓN MÚLTIPLE DE USUARIOS PARA DESACTIVAR O ELIMINAR (solo Administrador)
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

    # El Administrador no puede desactivarse ni eliminarse a sí mismo
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
                accion_hist, verbo_msg = "Desactivación masiva", "desactivado(s)"
            else:
                # Django aplica los on_delete definidos en models.py (CASCADE / SET_NULL)
                Usuario.objects.filter(pk__in=ids_objetivo).delete()
                accion_hist, verbo_msg = "Eliminación masiva", "eliminado(s)"

            admin_instancia = Usuario.objects.filter(pk=admin_id).first()
            if admin_instancia:
                HistorialUsuario.objects.create(
                    usuario=admin_instancia,
                    historial_accion=accion_hist,
                    historial_detalle=f"{accion_hist} de {len(lista)} usuario(s): " + ", ".join(nombres) + "."
                )

        mensaje = f"{len(lista)} usuario(s) {verbo_msg} exitosamente."
        if omitido_propio:
            mensaje += " Tu propia cuenta fue omitida."
        messages.success(request, mensaje)
    except Exception as e:
        messages.error(request, f"Ocurrió un error al procesar la acción masiva: {str(e)}")

    return redirect('gestion_de_usuarios')


def editar_usuario_view(request, usuario_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    usuario_editar = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        contrasena = request.POST.get('contrasena', '').strip()  # Vacío = mantener la actual
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')  # Solo se usa si el rol es "Profesor Jefe"
        cuenta_activa = request.POST.get('activo') == 'on'  # checkbox: presente = activo

        try:
            # Verifica que el correo no pertenezca a OTRO usuario (excluyéndose a sí mismo)
            if Usuario.objects.filter(usuario_correo=correo).exclude(pk=usuario_id).exists():
                messages.error(request, f"El correo {correo} ya está en uso por otro funcionario.")
                return redirect('gestion_de_usuarios')

            rol_instancia = Rol.objects.get(pk=rol_id)

            curso_instancia = None
            if rol_instancia.rol_nombre == 'Profesor Jefe':
                if not curso_id:
                    messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                    return redirect('gestion_de_usuarios')
                curso_instancia = Curso.objects.get(pk=curso_id)

            with transaction.atomic():
                usuario_editar.usuario_nombre = nombre
                usuario_editar.usuario_apaterno = apaterno
                usuario_editar.usuario_amaterno = amaterno
                usuario_editar.usuario_correo = correo
                usuario_editar.rol = rol_instancia
                usuario_editar.usuario_activo = cuenta_activa
                # Si el Administrador edita y guarda al funcionario, se considera revisado:
                # se desbloquea la cuenta y se reinicia el contador de intentos fallidos.
                usuario_editar.usuario_bloqueado = False
                usuario_editar.usuario_intentos_fallidos = 0
                if contrasena:
                    usuario_editar.usuario_contrasena = make_password(contrasena)
                usuario_editar.save()

                # Se limpian los registros de subtipo anteriores (pudo haber cambiado de rol)
                # y se recrea el correspondiente al rol actual, para mantener todo sincronizado.
                Administrador.objects.filter(usuario=usuario_editar).delete()
                Inspector.objects.filter(usuario=usuario_editar).delete()
                PConvivencia.objects.filter(usuario=usuario_editar).delete()
                ProfesorJefe.objects.filter(usuario=usuario_editar).delete()

                if rol_instancia.rol_nombre == 'Administrador':
                    Administrador.objects.create(
                        usuario=usuario_editar, admin_nombre=nombre,
                        admin_apaterno=apaterno, admin_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'Inspector':
                    Inspector.objects.create(
                        usuario=usuario_editar, inspector_nombre=nombre,
                        inspector_apaterno=apaterno, inspector_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'PConvivencia':
                    PConvivencia.objects.create(
                        usuario=usuario_editar, convivencia_nombre=nombre,
                        convivencia_apaterno=apaterno, convivencia_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'Profesor Jefe':
                    ProfesorJefe.objects.create(
                        usuario=usuario_editar, curso=curso_instancia,
                        profesor_nombre=nombre, profesor_apaterno=apaterno,
                        profesor_amaterno=amaterno
                    )

            messages.success(request, f"Funcionario {nombre} {apaterno} actualizado exitosamente.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al actualizar al usuario: {str(e)}")

    return redirect('gestion_de_usuarios')


def desbloquear_usuario_view(request, usuario_id):
    """RF: permite al Administrador desbloquear en un solo clic una cuenta
    que quedó bloqueada por 5 intentos fallidos de inicio de sesión."""
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    usuario_desbloquear = get_object_or_404(Usuario, pk=usuario_id)
    usuario_desbloquear.usuario_bloqueado = False
    usuario_desbloquear.usuario_intentos_fallidos = 0
    usuario_desbloquear.save(update_fields=['usuario_bloqueado', 'usuario_intentos_fallidos'])

    messages.success(request, f"La cuenta de {usuario_desbloquear.usuario_nombre} {usuario_desbloquear.usuario_apaterno} fue desbloqueada exitosamente.")
    return redirect('gestion_de_usuarios')


# HISTORIAL DE ACCIONES USUARIOS
def historial_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    from django.utils.dateparse import parse_date

    # Filtros combinables: usuario responsable, tipo de acción y rango de fechas
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

    # Usuario responsable: cada palabra escrita debe coincidir con nombre, apellidos o correo
    if filtro_usuario:
        for termino in filtro_usuario.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(usuario__usuario_nombre__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_apaterno__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_amaterno__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_correo__icontains=termino)
            )

    if filtro_busqueda:
        for termino in filtro_busqueda.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(historial_detalle__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_nombre__icontains=termino)
                | Q(usuario__usuario_apaterno__icontains=termino)
                | Q(usuario__usuario_amaterno__icontains=termino)
            )

    # Tipo de acción
    if filtro_accion:
        registros_auditoria = registros_auditoria.filter(historial_accion=filtro_accion)

    # Rango de fechas (se ignoran valores con formato inválido)
    def _fecha_valida(texto):
        if not texto:
            return None
        try:
            return parse_date(texto)
        except ValueError:
            return None

    fecha_desde = _fecha_valida(filtro_fecha_desde)
    fecha_hasta = _fecha_valida(filtro_fecha_hasta)

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
        messages.warning(request, "La fecha 'desde' era posterior a 'hasta'; se invirtieron para aplicar el filtro.")

    if fecha_desde:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__gte=fecha_desde)
    if fecha_hasta:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__lte=fecha_hasta)

    filtro_fecha_desde = fecha_desde.isoformat() if fecha_desde else ''
    filtro_fecha_hasta = fecha_hasta.isoformat() if fecha_hasta else ''

    # Opciones de los filtros (solo lo que realmente existe en la bitácora)
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

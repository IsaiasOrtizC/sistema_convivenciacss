"""Controlador de casos: listado, registro, detalle, edición, eliminación, solicitudes pendientes y casos del curso."""

import logging
import os
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.dateparse import parse_date

from ..models import (
    Caso,
    Curso,
    Estudiante,
    HistorialNotificacion,
    HistorialUsuario,
    Involucran,
    Lugar,
    Notificacion,
    ProfesorJefe,
    SolicitudCaso,
    Usuario,
)
from ..permissions import ROLES_APROBACION_CASOS
from ..reglamento import evaluar_reglas_para_caso
from ..services.caso_service import crear_caso_persistido, filtrar_casos_del_curso
from .auth_casos_controller import (
    bloquear_si_profesor_jefe,
    puede_editar_caso,
    validar_profesor_jefe,
)

logger = logging.getLogger(__name__)


# HISTORIAL DE CASOS
def historial_casos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    redireccion = bloquear_si_profesor_jefe(request, "Acceso denegado: como Profesor Jefe, solo puedes ver los casos de tu curso.")
    if redireccion:
        return redireccion

    # RF-13: parámetros de búsqueda y filtros (vienen por GET, así se puede compartir/recargar la URL filtrada)
    busqueda = request.GET.get('q', '').strip()
    filtro_curso_id = request.GET.get('curso', '').strip()
    filtro_gravedad = request.GET.get('gravedad', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    casos_query = Caso.objects.all().select_related('lugar').order_by('-caso_fecha', '-caso_id')

    if busqueda:
        casos_query = casos_query.filter(caso_descripcion__icontains=busqueda)

    if filtro_curso_id:
        casos_query = casos_query.filter(estudiantes__curso_id=filtro_curso_id).distinct()

    if filtro_fecha_desde:
        casos_query = casos_query.filter(caso_fecha__gte=filtro_fecha_desde)

    if filtro_fecha_hasta:
        casos_query = casos_query.filter(caso_fecha__lte=filtro_fecha_hasta)

    if filtro_gravedad:
        # 'tipo_falta' vive en la tabla 'involucran', que no tiene columna 'id',
        # por eso se consulta con SQL directo (igual que en el resto del sistema).
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT caso_id FROM involucran WHERE tipo_falta = %s", [filtro_gravedad])
            ids_con_gravedad = [fila[0] for fila in cursor.fetchall()]
        casos_query = casos_query.filter(caso_id__in=ids_con_gravedad)

    lista_casos_formateada = []

    rol_usuario = request.session.get('usuario_rol', '')
    ahora = timezone.now()

    for caso in casos_query:
        titulo = "Sin título"
        descripcion_limpia = caso.caso_descripcion if caso.caso_descripcion else ""
        
        if descripcion_limpia.startswith('['):
            try:
                partes = descripcion_limpia.split('] - ', 1)
                if len(partes) == 2:
                    titulo = partes[0].replace('[', '')
                    descripcion_limpia = partes[1]
            except Exception:
                pass
        else:
            titulo = descripcion_limpia[:40] + "..." if len(descripcion_limpia) > 40 else descripcion_limpia

        # RF-52 / RF-53: ¿este usuario puede eliminar este caso?
        puede_eliminar = False
        if rol_usuario == 'Administrador':
            puede_eliminar = True
        elif rol_usuario == 'Inspector':
            if caso.caso_creado_en and (ahora - caso.caso_creado_en) <= timedelta(hours=12):
                puede_eliminar = True

        lista_casos_formateada.append({
            'caso_id': caso.caso_id,
            'titulo': titulo,
            'descripcion': descripcion_limpia,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'fecha': caso.caso_fecha,
            'usuario_id': caso.usuario_id,
            'puede_eliminar': puede_eliminar,
            'puede_editar': puede_editar_caso(rol_usuario, caso, ahora),
        })

    total_casos_filtrados = len(lista_casos_formateada)

    # Paginación: 10 casos por página, con indicador y flechas Anterior/Siguiente
    paginador = Paginator(lista_casos_formateada, 10)
    numero_pagina = request.GET.get('pagina')
    pagina_casos = paginador.get_page(numero_pagina)

    context = {
        'casos': pagina_casos,  # Page object: iterable + .has_next, .has_previous, .number, etc.
        'total_casos': total_casos_filtrados,  # RF-46 (cuenta TODOS los resultados, no solo los de esta página)
        'mostrar_contador': rol_usuario in ('Administrador', 'Inspector', 'PConvivencia'),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra'),
        'filtros': {
            'q': busqueda,
            'curso': filtro_curso_id,
            'gravedad': filtro_gravedad,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(busqueda or filtro_curso_id or filtro_gravedad or filtro_fecha_desde or filtro_fecha_hasta),
    }
    return render(request, 'gestion_casos/historial_casos.html', context)


def registrar_caso_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    es_profesor_jefe = request.session.get('usuario_rol') == 'Profesor Jefe'
    curso_profesor = validar_profesor_jefe(request) if es_profesor_jefe else None
    if es_profesor_jefe and not curso_profesor:
        messages.error(
            request,
            "No se encontró un curso asignado para tu cuenta de Profesor Jefe.",
        )
        return redirect('mis_casos_curso')
    if not es_profesor_jefe:
        redireccion = bloquear_si_profesor_jefe(
            request,
            "Acceso denegado: como Profesor Jefe solo puedes reportar casos de tu curso.",
        )
        if redireccion:
            return redireccion

    # ZONA HORARIA LOCAL
    fecha_hoy = timezone.localdate().strftime('%Y-%m-%d')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        fecha = request.POST.get('fecha')
        lugar_id = request.POST.get('lugar')
        descripcion_cuerpo = request.POST.get('descripcion')
        tipo_falta = request.POST.get('tipo_falta')
        
        # CAPTURA DE ARREGLOS PARA MÚLTIPLES ESTUDIANTES Y NÚMERO DE LISTA
        nombres = request.POST.getlist('alumno_nombre[]')
        apaternos = request.POST.getlist('alumno_apaterno[]')
        amaternos = request.POST.getlist('alumno_amaterno[]')
        num_listas = request.POST.getlist('alumno_num_lista[]')
        cursos_ids = request.POST.getlist('curso[]')
        # Si el usuario eligió un alumno ya existente desde el buscador, viene su ID aquí.
        # Si está vacío, significa que se debe crear un alumno nuevo con los datos tipeados.
        estudiantes_ids = request.POST.getlist('estudiante_id[]')

        fecha_validada = parse_date(fecha) if fecha else None
        if not fecha_validada or fecha_validada > timezone.localdate():
            messages.error(
                request,
                "La fecha del caso debe ser válida y no puede ser posterior al día de hoy.",
            )
            return redirect('registrar_caso')
        if (
            not titulo
            or len(titulo.strip()) > 180
            or not descripcion_cuerpo
            or tipo_falta not in ('Leve', 'Grave', 'Gravísima')
        ):
            messages.error(
                request,
                "Completa el título, la descripción y una clasificación de gravedad válida.",
            )
            return redirect('registrar_caso')

        listas_estudiantes = (
            nombres, apaternos, amaternos, num_listas, cursos_ids, estudiantes_ids,
        )
        if not nombres or any(len(lista) != len(nombres) for lista in listas_estudiantes):
            messages.error(request, "Completa los datos de todos los estudiantes involucrados.")
            return redirect('registrar_caso')

        foto_adjunta = request.FILES.get('evidencia_foto')
        nombre_foto_guardado = None
        if foto_adjunta:
            extension = os.path.splitext(foto_adjunta.name)[1].lower()
            extensiones_permitidas = {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
                '.png', '.jpg', '.jpeg',
            }
            if extension not in extensiones_permitidas:
                messages.error(
                    request,
                    "Adjunta un documento PDF, Word, Excel, texto o una imagen válida.",
                )
                return redirect('registrar_caso')
            if foto_adjunta.size > 20 * 1024 * 1024:
                messages.error(request, "El archivo adjunto supera el límite de 20 MB.")
                return redirect('registrar_caso')

        if foto_adjunta:
            try:
                nombre_seguro = os.path.basename(foto_adjunta.name)
                nombre_foto_guardado = default_storage.save(
                    f'evidencias/{nombre_seguro}',
                    foto_adjunta,
                )
            except Exception:
                logger.exception("No se pudo guardar la evidencia adjunta del caso.")
                messages.error(
                    request,
                    "No se pudo guardar el archivo adjunto. Intenta nuevamente.",
                )
                return redirect('registrar_caso')

        estudiantes_data = []
        try:
            for nom, apat, amat, num_lista, curso_id, estudiante_id in zip(
                nombres, apaternos, amaternos, num_listas, cursos_ids, estudiantes_ids,
            ):
                if not nom.strip() or not apat.strip() or not curso_id:
                    raise ValidationError(
                        "Completa nombre, apellido y curso de cada estudiante."
                    )
                curso_id = int(curso_id)
                if es_profesor_jefe and curso_id != curso_profesor.pk:
                    raise ValidationError(
                        "Solo puedes reportar estudiantes de tu curso asignado."
                    )
                if num_lista and not num_lista.isdigit():
                    raise ValidationError(
                        "El número de lista debe ser un número entero."
                    )
                estudiante_id_valido = int(estudiante_id) if estudiante_id else None
                nombre_final = nom.strip()
                apellido_paterno_final = apat.strip()
                apellido_materno_final = amat.strip()
                numero_lista_final = int(num_lista) if num_lista else None
                if es_profesor_jefe and estudiante_id_valido:
                    estudiante_existente = Estudiante.objects.filter(
                        pk=estudiante_id_valido,
                        curso_id=curso_profesor.pk,
                        estudiante_activo=True,
                    ).first()
                    if not estudiante_existente:
                        raise ValidationError(
                            "El estudiante seleccionado no pertenece a tu curso o está inactivo."
                        )
                    nombre_final = estudiante_existente.estudiante_nombre
                    apellido_paterno_final = estudiante_existente.estudiante_apaterno
                    apellido_materno_final = estudiante_existente.estudiante_amaterno
                    numero_lista_final = estudiante_existente.estudiante_numero_lista
                estudiantes_data.append({
                    'nombre': nombre_final,
                    'apellido_paterno': apellido_paterno_final,
                    'apellido_materno': apellido_materno_final,
                    'numero_lista': numero_lista_final,
                    'curso_id': curso_id,
                    'estudiante_id': estudiante_id_valido,
                })
        except (ValueError, ValidationError) as error:
            if nombre_foto_guardado:
                default_storage.delete(nombre_foto_guardado)
            messages.error(request, str(error))
            return redirect('registrar_caso')

        if es_profesor_jefe:
            try:
                with transaction.atomic():
                    solicitud = SolicitudCaso.objects.create(
                        solicitante=Usuario.objects.get(
                            pk=request.session['usuario_id']
                        ),
                        lugar=Lugar.objects.get(pk=lugar_id),
                        fecha_evento=fecha,
                        titulo=(titulo or '').strip(),
                        descripcion=(descripcion_cuerpo or '').strip(),
                        tipo_falta=tipo_falta or '',
                        evidencia=nombre_foto_guardado or '',
                        estudiantes=estudiantes_data,
                    )
                messages.success(
                    request,
                    f"El caso quedó en espera de revisión (solicitud #{solicitud.pk}).",
                )
                return redirect('mis_casos_curso')
            except Exception:
                if nombre_foto_guardado:
                    default_storage.delete(nombre_foto_guardado)
                logger.exception("No se pudo guardar la solicitud de caso del profesor.")
                messages.error(
                    request,
                    "No se pudo enviar el caso para revisión. Intenta nuevamente.",
                )
                return redirect('registrar_caso')

        try:
            with transaction.atomic():
                lugar_instancia = Lugar.objects.get(pk=lugar_id)
                usuario_id_sesion = request.session.get('usuario_id')
                usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion)
                nuevo_caso = crear_caso_persistido(
                    request,
                    usuario_instancia,
                    fecha,
                    titulo,
                    descripcion_cuerpo,
                    nombre_foto_guardado,
                    lugar_instancia,
                    tipo_falta,
                    estudiantes_data,
                )

            messages.success(request, f"Caso registrado exitosamente por {usuario_instancia.usuario_nombre}.")
            return redirect('historial_casos')
            
        except Exception as e:
            messages.error(request, f"Hubo un problema al registrar en PostgreSQL: {str(e)}")
            return redirect('registrar_caso')

    lugares = Lugar.objects.all().order_by('lugar_nombre')
    cursos = Curso.objects.filter(pk=curso_profesor.pk) if curso_profesor else Curso.objects.all()
    cursos = cursos.order_by('curso_grado', 'curso_letra')
    estudiantes_existentes = Estudiante.objects.filter(
        estudiante_activo=True
    ).select_related('curso').order_by(
        'estudiante_apaterno', 'estudiante_amaterno', 'estudiante_nombre'
    )
    if curso_profesor:
        estudiantes_existentes = estudiantes_existentes.filter(curso=curso_profesor)
    
    context = {
        'lugares': lugares,
        'cursos': cursos,
        'fecha_hoy': fecha_hoy,
        'estudiantes_existentes': estudiantes_existentes,
        'requiere_aprobacion': es_profesor_jefe,
    }
    return render(request, 'gestion_casos/registrar_caso.html', context)


def solicitudes_casos_pendientes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') not in ROLES_APROBACION_CASOS:
        return HttpResponseForbidden(
            "No tienes permisos para revisar solicitudes de casos."
        )

    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        decision = request.POST.get('decision')
        comentario = request.POST.get('comentario', '').strip()
        if decision not in ('aprobar', 'rechazar'):
            messages.error(request, "La decisión de revisión no es válida.")
            return redirect('solicitudes_casos_pendientes')

        mensaje_resultado = ''
        try:
            with transaction.atomic():
                solicitud = get_object_or_404(
                    SolicitudCaso.objects.select_for_update(),
                    pk=solicitud_id,
                )
                if solicitud.estado != SolicitudCaso.Estado.PENDIENTE:
                    messages.warning(
                        request,
                        "Esta solicitud ya fue revisada por otro usuario.",
                    )
                    return redirect('solicitudes_casos_pendientes')

                revisor = Usuario.objects.get(pk=request.session['usuario_id'])
                if decision == 'aprobar':
                    estudiantes_data = solicitud.estudiantes
                    if not estudiantes_data:
                        raise ValidationError(
                            "La solicitud no contiene estudiantes involucrados."
                        )
                    if solicitud.solicitante and solicitud.solicitante.rol.rol_nombre == 'Profesor Jefe':
                        perfil_profesor = ProfesorJefe.objects.select_related(
                            'curso'
                        ).filter(usuario_id=solicitud.solicitante_id).first()
                        curso_profesor = (
                            perfil_profesor.curso if perfil_profesor else None
                        )
                        if not curso_profesor or any(
                            int(estudiante['curso_id']) != curso_profesor.pk
                            for estudiante in estudiantes_data
                        ):
                            raise ValidationError(
                                "El curso asignado al profesor cambió; no se puede aprobar "
                                "esta solicitud hasta corregir su información."
                            )

                    caso = crear_caso_persistido(
                        request,
                        solicitud.solicitante or revisor,
                        solicitud.fecha_evento,
                        solicitud.titulo,
                        solicitud.descripcion,
                        solicitud.evidencia,
                        solicitud.lugar,
                        solicitud.tipo_falta,
                        estudiantes_data,
                    )
                    solicitud.estado = SolicitudCaso.Estado.APROBADA
                    solicitud.comentario_revision = comentario
                    mensaje_resultado = (
                        f"Solicitud aprobada. El caso #{caso.caso_id} ya está registrado."
                    )
                else:
                    solicitud.estado = SolicitudCaso.Estado.RECHAZADA
                    solicitud.comentario_revision = comentario or "Solicitud rechazada."
                    mensaje_resultado = "La solicitud fue rechazada."

                solicitud.revisada_por = revisor
                solicitud.revisada_en = timezone.now()
                solicitud.save(update_fields=[
                    'estado',
                    'comentario_revision',
                    'revisada_por',
                    'revisada_en',
                ])
                HistorialUsuario.objects.create(
                    usuario=revisor,
                    historial_accion=(
                        "Aprobación de caso"
                        if decision == 'aprobar'
                        else "Rechazo de caso"
                    ),
                    historial_detalle=(
                        f"Revisó la solicitud #{solicitud.pk} del Profesor Jefe "
                        f"{solicitud.solicitante.usuario_nombre if solicitud.solicitante else 'sin usuario'}: "
                        f"{solicitud.get_estado_display()}."
                    ),
                )
            messages.success(request, mensaje_resultado)
        except (SolicitudCaso.DoesNotExist, Usuario.DoesNotExist):
            messages.error(request, "No se encontró la solicitud o el usuario revisor.")
        except ValidationError as error:
            messages.error(request, str(error))
        except Exception:
            logger.exception("No se pudo completar la revisión de la solicitud de caso.")
            messages.error(
                request,
                "No se pudo completar la revisión; la solicitud permanece sin cambios.",
            )
        return redirect('solicitudes_casos_pendientes')

    solicitudes = list(SolicitudCaso.objects.select_related(
        'solicitante__rol', 'lugar', 'revisada_por',
    ).filter(estado=SolicitudCaso.Estado.PENDIENTE))
    cursos = Curso.objects.in_bulk({
        estudiante['curso_id']
        for solicitud in solicitudes
        for estudiante in solicitud.estudiantes
    })
    elementos_solicitud = []
    for solicitud in solicitudes:
        estudiantes = []
        for estudiante in solicitud.estudiantes:
            curso = cursos.get(estudiante['curso_id'])
            estudiantes.append({
                **estudiante,
                'curso': (
                    f"{curso.curso_grado} {curso.curso_letra}"
                    if curso else "Curso no disponible"
                ),
            })
        elementos_solicitud.append({
            'solicitud': solicitud,
            'estudiantes': estudiantes,
            'evidencia_url': (
                default_storage.url(solicitud.evidencia)
                if solicitud.evidencia
                and default_storage.exists(solicitud.evidencia)
                else ''
            ),
        })
    return render(
        request,
        'gestion_casos/solicitudes_casos_pendientes.html',
        {'solicitudes': elementos_solicitud},
    )


# DETALLE DE CASO
def detalle_caso_view(request, caso_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    caso = get_object_or_404(Caso.objects.select_related('lugar', 'usuario'), pk=caso_id)

    # El Profesor Jefe solo puede ver el detalle si el caso pertenece a un alumno de SU curso
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        try:
            profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
        except ProfesorJefe.DoesNotExist:
            messages.error(request, "Acceso denegado.")
            return redirect('mis_casos_curso')

        pertenece_a_su_curso = Estudiante.objects.filter(
            involucran__caso_id=caso_id, curso=profesor.curso
        ).exists()

        if not pertenece_a_su_curso:
            messages.error(request, "Acceso denegado: ese caso no corresponde a los alumnos de tu curso.")
            return redirect('mis_casos_curso')

    titulo = "Sin título"
    descripcion_limpia = caso.caso_descripcion if caso.caso_descripcion else ""
    if descripcion_limpia.startswith('['):
        try:
            partes = descripcion_limpia.split('] - ', 1)
            if len(partes) == 2:
                titulo = partes[0].replace('[', '')
                descripcion_limpia = partes[1]
        except Exception:
            pass
    else:
        titulo = descripcion_limpia[:40] + "..." if len(descripcion_limpia) > 40 else descripcion_limpia

    # 🌟 DEFINIMOS LAS VARIABLES ANTES DEL BUCLE/SQL PARA EVITAR EL ERROR DE PYLANCE
    relaciones = []
    tipo_falta = "No especificado"

    query_sql = """
        SELECT e.estudiante_nombre, e.estudiante_apaterno, e.estudiante_amaterno, 
               e.estudiante_numero_lista, cu.curso_grado, cu.curso_letra, i.tipo_falta
        FROM involucran i
        INNER JOIN estudiante e ON i.estudiante_id = e.estudiante_id
        INNER JOIN curso cu ON e.curso_id = cu.curso_id
        WHERE i.caso_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_sql, [caso_id])
        rows = cursor.fetchall()
        
        for row in rows:
            tipo_falta = row[6]  # 🌟 Se actualiza con el valor real traído desde la BD
            relaciones.append({
                'estudiante': {
                    'estudiante_nombre': row[0],
                    'estudiante_apaterno': row[1],
                    'estudiante_amaterno': row[2],
                    'estudiante_numero_lista': row[3],
                    'curso': {
                        'curso_grado': row[4],
                        'curso_letra': row[5]
                    }
                }
            })

    es_mi_caso = False
    if caso.usuario and caso.usuario.usuario_id == request.session.get('usuario_id'):
        es_mi_caso = True

    evidencia_url = ''
    evidencia_es_imagen = False
    if caso.evidencia:
        nombre_evidencia = caso.evidencia
        extension_evidencia = os.path.splitext(nombre_evidencia)[1].lower()
        evidencia_es_imagen = extension_evidencia in {'.png', '.jpg', '.jpeg'}
        if default_storage.exists(nombre_evidencia):
            evidencia_url = default_storage.url(nombre_evidencia)
        else:
            evidencia_url = static(
                nombre_evidencia
                if nombre_evidencia.startswith('evidencias/')
                else f'evidencias/{nombre_evidencia}'
            )

    context = {
        'caso': caso,
        'titulo': titulo,
        'descripcion': descripcion_limpia,
        'tipo_falta': tipo_falta,
        'relaciones': relaciones,
        'es_mi_caso': es_mi_caso,
        'puede_editar': puede_editar_caso(
            request.session.get('usuario_rol', ''),
            caso,
        ),
        'nombre_foto': caso.evidencia, 
        'evidencia_url': evidencia_url,
        'evidencia_es_imagen': evidencia_es_imagen,
    }
    return render(request, 'gestion_casos/detalle_caso.html', context)


# editar un caso
def editar_caso_view(request, caso_id):
    # 1. Seguridad: Validar sesión activa
    if 'usuario_id' not in request.session:
        return redirect('login')

    redireccion = bloquear_si_profesor_jefe(request, "Acceso denegado: como Profesor Jefe no puedes editar casos.")
    if redireccion:
        return redireccion

    usuario_id_sesion = request.session.get('usuario_id')
    usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion)

    # 2. Rescatar el caso o lanzar error 404 si no existe
    caso = get_object_or_404(Caso, pk=caso_id)
    creador_caso = caso.usuario
    usuario_id_sesion = request.session['usuario_id']
    rol_usuario = request.session.get('usuario_rol', '')

    if not puede_editar_caso(rol_usuario, caso):
        if rol_usuario == 'Administrador':
            messages.error(request, "No fue posible validar el plazo de edición del caso.")
        elif rol_usuario in ('Inspector', 'PConvivencia'):
            messages.error(
                request,
                "Solo puedes editar casos dentro de las 48 horas desde su creación.",
            )
        else:
            messages.error(request, "Acceso denegado: no tienes permisos para editar este caso.")
        return redirect('historial_casos')

    # 4. Obtener TODOS los estudiantes involucrados en el caso (antes traía solo 1 con LIMIT 1)
    query_estudiantes = """
        SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s
    """
    lista_ids_involucrados = []
    tipo_falta_actual = ""
    with connection.cursor() as cursor:
        cursor.execute(query_estudiantes, [caso.caso_id])
        filas = cursor.fetchall()
        for fila in filas:
            lista_ids_involucrados.append(fila[0])
            tipo_falta_actual = fila[1]  # la severidad es a nivel de caso, igual para todos

    estudiantes_qs = Estudiante.objects.filter(estudiante_id__in=lista_ids_involucrados).select_related('curso')
    estudiantes_dict = {e.estudiante_id: e for e in estudiantes_qs}
    estudiantes_involucrados = [estudiantes_dict[eid] for eid in lista_ids_involucrados if eid in estudiantes_dict]

    # 5. Procesar el envío del formulario (POST)
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion_cuerpo = request.POST.get('descripcion')
        lugar_id = request.POST.get('lugar')
        tipo_falta = request.POST.get('tipo_falta')

        # Ahora vienen como listas, un valor por cada alumno del formulario
        estudiante_ids = request.POST.getlist('estudiante_id[]')
        nombres = request.POST.getlist('alumno_nombre[]')
        apaternos = request.POST.getlist('alumno_apaterno[]')
        amaternos = request.POST.getlist('alumno_amaterno[]')
        cursos_ids = request.POST.getlist('curso[]')

        try:
            with transaction.atomic():
                # Actualizar datos del Caso
                caso.caso_descripcion = f"[{titulo}] - {descripcion_cuerpo}"
                caso.lugar = Lugar.objects.get(pk=lugar_id)
                caso.save()

                # Actualizar datos de cada alumno involucrado
                for est_id, nom, apat, amat, c_id in zip(estudiante_ids, nombres, apaternos, amaternos, cursos_ids):
                    estudiante_obj = Estudiante.objects.get(pk=est_id)
                    estudiante_obj.estudiante_nombre = nom.strip()
                    estudiante_obj.estudiante_apaterno = apat.strip()
                    estudiante_obj.estudiante_amaterno = amat.strip()
                    estudiante_obj.curso = Curso.objects.get(pk=c_id)
                    estudiante_obj.save()

                    # Actualizar el tipo de falta en la tabla intermedia nativa
                    query_update_intermedia = """
                        UPDATE involucran SET tipo_falta = %s WHERE caso_id = %s AND estudiante_id = %s
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(query_update_intermedia, [tipo_falta, caso.caso_id, est_id])

                evaluar_reglas_para_caso(
                    caso,
                    estudiantes_involucrados,
                    usuario_instancia,
                    evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    fecha_evento=timezone.now(),
                )

                # Notificar al creador si otro usuario modificó el caso
                if creador_caso and creador_caso.usuario_id != usuario_instancia.usuario_id:
                    notificacion_modificacion = Notificacion.objects.create(
                        usuario=creador_caso,
                        notificacion_titulo="Caso actualizado",
                        notificacion_mensaje=(
                            f"El caso #{caso.caso_id} fue modificado por "
                            f"{usuario_instancia.usuario_nombre} "
                            f"{usuario_instancia.usuario_apaterno}."
                        ),
                        notificacion_icono="✏️",
                        caso=caso,
                        evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    )
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion_modificacion,
                        estado=notificacion_modificacion.estado,
                        cambiado_por=usuario_instancia,
                        motivo='Notificación creada al modificar un caso.',
                    )

                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Modificación",
                    historial_detalle=(
                        f"Modificó los registros del caso #{caso.caso_id}. "
                        "Estudiantes: "
                        + ", ".join(
                            f"{estudiante.estudiante_nombre} "
                            f"{estudiante.estudiante_apaterno} "
                            f"{estudiante.estudiante_amaterno}"
                            for estudiante in estudiantes_involucrados
                        )
                        + "."
                    )
                )

            messages.success(request, f"El caso #{caso.caso_id} ha sido modificado exitosamente.")
            return redirect('historial_casos')

        except Exception as e:
            messages.error(request, f"Error al procesar la edición: {str(e)}")

    # 6. Preparar los datos pre-cargados para el formulario (GET)
    # Separamos el título de la descripción para rellenar los inputs limpios
    texto_completo = caso.caso_descripcion if caso.caso_descripcion else ""
    titulo_preparado = ""
    descripcion_preparada = texto_completo
    if "]" in texto_completo and "-" in texto_completo:
        partes = texto_completo.split("] -", 1)
        titulo_preparado = partes[0].replace("[", "").strip()
        descripcion_preparada = partes[1].strip()

    context = {
        'caso': caso,
        'titulo_actual': titulo_preparado,
        'descripcion_actual': descripcion_preparada,
        'tipo_falta_actual': tipo_falta_actual,
        'estudiantes': estudiantes_involucrados,   # <-- ahora es una lista, no un solo objeto
        'lugares': Lugar.objects.all().order_by('lugar_nombre'),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra')
    }
    return render(request, 'gestion_casos/editar_caso.html', context)


def eliminar_caso_view(request, caso_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    caso = get_object_or_404(Caso, pk=caso_id)
    rol_usuario = request.session.get('usuario_rol', '')

    puede_eliminar = False
    if rol_usuario == 'Administrador':
        puede_eliminar = True
    elif rol_usuario == 'Inspector':
        if caso.caso_creado_en and (timezone.now() - caso.caso_creado_en) <= timedelta(hours=12):
            puede_eliminar = True
        else:
            messages.error(request, "Como Inspector, solo puedes eliminar un caso dentro de las primeras 12 horas desde su creación.")
            return redirect('historial_casos')

    if not puede_eliminar:
        messages.error(request, "Acceso denegado: no tienes permisos para eliminar este caso.")
        return redirect('historial_casos')

    try:
        usuario_id_sesion = request.session.get('usuario_id')
        usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion) if usuario_id_sesion else None

        with transaction.atomic():
            caso_id_eliminado = caso.caso_id
            creador = caso.usuario
            if (
                creador
                and creador.usuario_id != usuario_instancia.usuario_id
            ):
                clave = (
                    f'caso_eliminado:{caso_id_eliminado}:'
                    f'creador:{creador.usuario_id}'
                )
                notificacion, creada = Notificacion.objects.get_or_create(
                    evento_clave=clave,
                    defaults={
                        'usuario': creador,
                        'notificacion_titulo': 'Caso eliminado',
                        'notificacion_mensaje': (
                            f'El caso #{caso_id_eliminado} que registraste fue '
                            'eliminado por otro usuario.'
                        ),
                        'notificacion_icono': '🗑️',
                    },
                )
                if creada:
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion,
                        estado=notificacion.estado,
                        cambiado_por=usuario_instancia,
                        motivo='Notificación creada al eliminar un caso de otro usuario.',
                    )
            caso.delete()  # El CASCADE elimina también sus filas en 'involucran'

            if usuario_instancia:
                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Eliminación",
                    historial_detalle=f"Eliminó el caso #{caso_id_eliminado} de la bitácora de convivencia."
                )

        messages.success(request, f"El caso #{caso_id_eliminado} fue eliminado exitosamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar el caso: {str(e)}")

    return redirect('historial_casos')


# ELIMINAR UN ALUMNO DE UN CASO (botón "✕" en la pantalla de edición)
def eliminar_estudiante_caso_view(request, caso_id, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    caso = get_object_or_404(Caso, pk=caso_id)
    rol_usuario = request.session.get('usuario_rol', '')
    if not puede_editar_caso(rol_usuario, caso):
        if rol_usuario in ('Inspector', 'PConvivencia'):
            messages.error(
                request,
                "Solo puedes editar casos dentro de las 48 horas desde su creación.",
            )
        else:
            messages.error(
                request,
                "Acceso denegado: no tienes permisos para editar este caso.",
            )
        return redirect('historial_casos')

    # No permitir dejar un caso sin ningún alumno involucrado
    total_involucrados = Involucran.objects.filter(caso_id=caso_id).count()
    if total_involucrados <= 1:
        messages.error(request, "No puedes eliminar al único alumno involucrado en este caso.")
        return redirect('editar_caso', caso_id=caso_id)

    Involucran.objects.filter(caso_id=caso_id, estudiante_id=estudiante_id).delete()
    messages.success(request, "Alumno eliminado del caso correctamente.")
    return redirect('editar_caso', caso_id=caso_id)


def mis_casos_curso_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_rol', '') != 'Profesor Jefe':
        messages.error(request, "Acceso denegado: Esta sección es exclusiva para el Profesor Jefe de un curso.")
        return redirect('dashboard')

    try:
        profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
    except ProfesorJefe.DoesNotExist:
        messages.error(request, "No se encontró un perfil de Profesor Jefe asociado a tu cuenta.")
        return redirect('dashboard')

    if not profesor.curso:
        messages.error(request, "No tienes un curso asignado actualmente. Contacta al Administrador.")
        return redirect('dashboard')

    casos_del_curso, filtros = filtrar_casos_del_curso(request, profesor.curso)
    from urllib.parse import urlencode
    filtros_query = urlencode({key: value for key, value in filtros.items() if value})

    context = {
        'curso': profesor.curso,
        'casos': casos_del_curso,
        'total_casos': len(casos_del_curso),
        'solicitudes_caso': SolicitudCaso.objects.filter(
            solicitante_id=request.session['usuario_id'],
        ).select_related('lugar', 'revisada_por')[:10],
        'filtros': filtros,
        'filtros_query': filtros_query,
    }
    return render(request, 'gestion_casos/mis_casos_curso.html', context)

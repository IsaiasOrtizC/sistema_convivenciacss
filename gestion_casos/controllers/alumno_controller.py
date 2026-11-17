"""Alumno Controller: consulta y administración de alumnos y sus antecedentes."""

import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import load_workbook

from ..models import (
    Caso,
    Curso,
    Estudiante,
    HistorialImportacionEstudiantes,
    HistorialUsuario,
    Involucran,
    Usuario,
    _quitar_tildes,
)
from ..trazabilidad import traza_consulta

logger = logging.getLogger(__name__)

MAX_EXCEL_BYTES = 5 * 1024 * 1024  # 5 MB


def _registrar_auditoria_alumno(admin_id, accion, detalle):
    if not admin_id:
        return
    admin = Usuario.objects.filter(pk=admin_id).first()
    if admin:
        HistorialUsuario.objects.create(
            usuario=admin,
            historial_accion=accion,
            historial_detalle=detalle,
        )


def _parsear_numero_lista(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if not texto.isdigit():
        raise ValidationError("El N° de lista debe ser un número entero entre 1 y 99.")
    numero = int(texto)
    if not (1 <= numero <= 99):
        raise ValidationError("El N° de lista debe estar entre 1 y 99.")
    return numero


def gestion_de_estudiantes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    admin_id = request.session.get('usuario_id')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        curso_id = request.POST.get('curso')
        numero_lista_raw = request.POST.get('numero_lista', '')

        try:
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError("Completa los nombres y apellidos del alumno.")
            if correo:
                validate_email(correo)

            curso_instancia = Curso.objects.get(pk=curso_id)
            numero_lista_val = _parsear_numero_lista(numero_lista_raw)

            if numero_lista_val and _numero_lista_ya_usado(curso_instancia, numero_lista_val):
                messages.error(
                    request,
                    f"Ya existe un alumno con el N° de lista {numero_lista_val} en {curso_instancia}. "
                    f"El número de lista debe ser único dentro del mismo curso.",
                )
                return redirect('gestion_de_alumnos')

            with transaction.atomic():
                nuevo_estudiante = Estudiante(
                    estudiante_nombre=nombre,
                    estudiante_apaterno=apaterno,
                    estudiante_amaterno=amaterno,
                    estudiante_correo=correo or None,
                    curso=curso_instancia,
                    estudiante_numero_lista=numero_lista_val,
                )
                nuevo_estudiante.save()
                _registrar_auditoria_alumno(
                    admin_id,
                    'Creación',
                    f"Registró al estudiante {nombre} {apaterno} {amaterno} en {curso_instancia}.",
                )

            if nuevo_estudiante.estudiante_identificador:
                messages.success(
                    request,
                    f"Alumno(a) {nombre} {apaterno} registrado(a) exitosamente. "
                    f"Identificador asignado: {nuevo_estudiante.estudiante_identificador}",
                )
            else:
                messages.warning(
                    request,
                    f"Alumno(a) {nombre} {apaterno} registrado(a), pero no se pudo generar su "
                    f"identificador único (revisa que el N° de lista y el curso sean válidos).",
                )
            return redirect('gestion_de_alumnos')

        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no existe.")
        except IntegrityError:
            messages.error(
                request,
                "Ya existe un estudiante con el mismo identificador único en ese curso y número de lista.",
            )
        except Exception:
            logger.exception("Error registrando alumno %s %s", nombre, apaterno)
            messages.error(request, "No fue posible registrar al alumno. Revisa el curso y vuelve a intentarlo.")

    # Filtros combinables: búsqueda por texto, curso, N° de lista y estado
    filtro_busqueda = request.GET.get('busqueda', '').strip()
    filtro_curso = request.GET.get('curso', '').strip()
    filtro_lista = request.GET.get('numero_lista', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    traza_consulta(
        'alumnos', busqueda=filtro_busqueda, curso=filtro_curso,
        n_lista=filtro_lista, estado=filtro_estado,
    )

    estudiantes_registrados = (
        Estudiante.objects
        .select_related('curso')
        .all()
        .order_by(
            'curso__curso_grado',
            'curso__curso_letra',
            'estudiante_apaterno',
            'estudiante_nombre',
        )
    )

    if filtro_busqueda:
        for termino in filtro_busqueda.split():
            termino_norm = _quitar_tildes(termino)
            estudiantes_registrados = estudiantes_registrados.filter(
                Q(estudiante_nombre__unaccent__icontains=termino_norm)
                | Q(estudiante_apaterno__unaccent__icontains=termino_norm)
                | Q(estudiante_amaterno__unaccent__icontains=termino_norm)
                | Q(estudiante_identificador__icontains=termino_norm.upper())
            )

    if filtro_curso.isdigit():
        estudiantes_registrados = estudiantes_registrados.filter(curso_id=int(filtro_curso))
    else:
        filtro_curso = ''

    if filtro_lista.isdigit():
        estudiantes_registrados = estudiantes_registrados.filter(estudiante_numero_lista=int(filtro_lista))
    else:
        filtro_lista = ''

    if filtro_estado in ('activo', 'inactivo'):
        estudiantes_registrados = estudiantes_registrados.filter(
            estudiante_activo=(filtro_estado == 'activo')
        )
    else:
        filtro_estado = ''

    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    parametros = {
        k: val
        for k, val in (
            ('busqueda', filtro_busqueda),
            ('curso', filtro_curso),
            ('numero_lista', filtro_lista),
            ('estado', filtro_estado),
        )
        if val
    }
    querystring_filtros = ('&' + urlencode(parametros)) if parametros else ''

    paginador = Paginator(estudiantes_registrados, 10)
    pagina_estudiantes = paginador.get_page(request.GET.get('pagina'))

    context = {
        'estudiantes': pagina_estudiantes,
        'cursos': cursos_disponibles,
        'filtros': {
            'busqueda': filtro_busqueda,
            'curso': filtro_curso,
            'numero_lista': filtro_lista,
            'estado': filtro_estado,
        },
        'hay_filtros_activos': bool(parametros),
        'querystring_filtros': querystring_filtros,
        'historial_importaciones': HistorialImportacionEstudiantes.objects.all()[:10],
    }
    return render(request, 'gestion_casos/gestion_de_estudiantes.html', context)


# ============================================================
#  RF-70: IMPORTACIÓN MASIVA DE ALUMNOS DESDE EXCEL (.XLSX)
# ============================================================

def importar_estudiantes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    if request.method != 'POST' or not request.FILES.get('archivo_excel'):
        messages.error(request, "Debes seleccionar un archivo Excel (.xlsx) para importar.")
        return redirect('gestion_de_alumnos')

    archivo = request.FILES['archivo_excel']

    if not archivo.name.lower().endswith('.xlsx'):
        messages.error(request, "El archivo debe estar en formato .xlsx.")
        return redirect('gestion_de_alumnos')

    if archivo.size > MAX_EXCEL_BYTES:
        messages.error(request, "El archivo Excel supera el tamaño máximo permitido (5 MB).")
        return redirect('gestion_de_alumnos')

    try:
        libro = load_workbook(archivo, read_only=True, data_only=True)
        hoja = libro.active
    except Exception:
        logger.exception("No se pudo abrir el archivo Excel %s.", archivo.name)
        messages.error(request, "No se pudo leer el archivo. Verifica que sea un Excel (.xlsx) válido.")
        return redirect('gestion_de_alumnos')

    # Precarga en memoria para evitar consultas N+1 por fila
    cursos_mapa = {
        (c.curso_grado.strip().casefold(), c.curso_letra.strip().casefold()): c
        for c in Curso.objects.all()
    }
    listas_ocupadas = set(
        Estudiante.objects
        .filter(estudiante_numero_lista__isnull=False)
        .values_list('curso_id', 'estudiante_numero_lista')
    )
    alumnos_existentes = {
        (
            _quitar_tildes(n).strip().casefold(),
            _quitar_tildes(ap).strip().casefold(),
            _quitar_tildes(am).strip().casefold(),
            c_id,
        )
        for n, ap, am, c_id in Estudiante.objects.values_list(
            'estudiante_nombre',
            'estudiante_apaterno',
            'estudiante_amaterno',
            'curso_id',
        )
    }

    creados = 0
    omitidos = 0
    errores = []
    alumnos_agregados = []
    duplicados_detectados = []

    try:
        for num_fila, fila in enumerate(hoja.iter_rows(min_row=2, max_col=6, values_only=True), start=2):
            if not fila or all(c is None or str(c).strip() == '' for c in fila):
                continue

            try:
                nombre = str(fila[0]).strip() if fila[0] is not None else ''
                apaterno = str(fila[1]).strip() if fila[1] is not None else ''
                amaterno = str(fila[2]).strip() if fila[2] is not None else ''
                valor_curso_grado = fila[3]
                curso_letra = str(fila[4]).strip() if fila[4] is not None else ''
                valor_numero_lista = fila[5] if len(fila) > 5 else None

                if not (nombre and apaterno and amaterno and valor_curso_grado is not None and curso_letra):
                    errores.append(f"Fila {num_fila}: faltan datos obligatorios.")
                    omitidos += 1
                    continue

                if isinstance(valor_curso_grado, (int, float)):
                    curso_grado = f"{int(valor_curso_grado)}° Medio"
                else:
                    texto_grado = str(valor_curso_grado).strip()
                    curso_grado = f"{texto_grado}° Medio" if texto_grado.isdigit() else texto_grado

                curso_instancia = cursos_mapa.get(
                    (curso_grado.casefold(), curso_letra.casefold())
                )
                if not curso_instancia:
                    errores.append(f"Fila {num_fila}: el curso '{curso_grado} {curso_letra}' no existe en el sistema.")
                    omitidos += 1
                    continue

                clave_alumno = (
                    _quitar_tildes(nombre).casefold(),
                    _quitar_tildes(apaterno).casefold(),
                    _quitar_tildes(amaterno).casefold(),
                    curso_instancia.curso_id,
                )
                if clave_alumno in alumnos_existentes:
                    omitidos += 1
                    duplicado = f"{nombre} {apaterno} {amaterno} ({curso_instancia})"
                    duplicados_detectados.append(duplicado)
                    errores.append(f"Fila {num_fila}: {duplicado} ya existía, se omitió.")
                    continue

                numero_lista = None
                if isinstance(valor_numero_lista, (int, float)):
                    cand = int(valor_numero_lista)
                    if 1 <= cand <= 99:
                        numero_lista = cand
                elif isinstance(valor_numero_lista, str) and valor_numero_lista.strip().isdigit():
                    cand = int(valor_numero_lista.strip())
                    if 1 <= cand <= 99:
                        numero_lista = cand

                if numero_lista and (curso_instancia.curso_id, numero_lista) in listas_ocupadas:
                    errores.append(
                        f"Fila {num_fila}: el N° de lista {numero_lista} ya está en uso en {curso_instancia}. "
                        f"Se registró sin número de lista asignado."
                    )
                    numero_lista = None

                estudiante = Estudiante(
                    estudiante_nombre=nombre,
                    estudiante_apaterno=apaterno,
                    estudiante_amaterno=amaterno,
                    curso=curso_instancia,
                    estudiante_numero_lista=numero_lista,
                )
                estudiante.save()

                alumnos_existentes.add(clave_alumno)
                if numero_lista:
                    listas_ocupadas.add((curso_instancia.curso_id, numero_lista))

                creados += 1
                alumnos_agregados.append(f"{nombre} {apaterno} {amaterno} ({curso_instancia})")

            except Exception:
                logger.exception("Error importando alumno desde fila %s del archivo %s", num_fila, archivo.name)
                errores.append(f"Fila {num_fila}: error inesperado al procesar la fila.")
                omitidos += 1
    finally:
        libro.close()

    try:
        usuario_importador = Usuario.objects.only('usuario_correo').get(
            pk=request.session['usuario_id']
        )
        HistorialImportacionEstudiantes.objects.create(
            archivo=archivo.name[:255],
            usuario_id_importo=usuario_importador.pk,
            usuario_correo_importo=usuario_importador.usuario_correo,
            alumnos_agregados=alumnos_agregados,
            duplicados_detectados=duplicados_detectados,
            filas_omitidas=omitidos,
        )
        _registrar_auditoria_alumno(
            usuario_importador.pk,
            'Importación',
            f"Importó {creados} estudiante(s) desde '{archivo.name}' ({omitidos} omitido(s)).",
        )
    except Exception:
        logger.exception("No fue posible registrar la auditoría de importación de alumnos")
        messages.error(
            request,
            "La importación se procesó, pero no se pudo guardar su registro de auditoría. Contacta al administrador.",
        )

    if creados > 0:
        messages.success(
            request,
            f"Importación completada: {creados} alumno(s) nuevo(s) registrado(s), {omitidos} fila(s) omitida(s).",
        )
    else:
        messages.warning(
            request,
            f"No se registró ningún alumno nuevo. {omitidos} fila(s) omitida(s) o con datos repetidos.",
        )

    if errores:
        detalle = " | ".join(errores[:8])
        if len(errores) > 8:
            detalle += f" ... y {len(errores) - 8} fila(s) más con problemas."
        messages.error(request, f"Detalle de filas no importadas: {detalle}")

    return redirect('gestion_de_alumnos')


def editar_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    admin_id = request.session.get('usuario_id')
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        curso_id = request.POST.get('curso')
        numero_lista_raw = request.POST.get('numero_lista', '')

        try:
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError("Completa los nombres y apellidos del alumno.")
            if correo:
                validate_email(correo)

            curso_instancia = Curso.objects.get(pk=curso_id)
            numero_lista_val = _parsear_numero_lista(numero_lista_raw)

            if numero_lista_val and _numero_lista_ya_usado(
                curso_instancia,
                numero_lista_val,
                excluir_estudiante_id=estudiante.estudiante_id,
            ):
                messages.error(
                    request,
                    f"Ya existe OTRO alumno con el N° de lista {numero_lista_val} en {curso_instancia}. "
                    f"El número de lista debe ser único dentro del mismo curso.",
                )
                return redirect('gestion_de_alumnos')

            with transaction.atomic():
                estudiante.estudiante_nombre = nombre
                estudiante.estudiante_apaterno = apaterno
                estudiante.estudiante_amaterno = amaterno
                estudiante.estudiante_correo = correo or None
                estudiante.curso = curso_instancia
                estudiante.estudiante_numero_lista = numero_lista_val
                if numero_lista_val is None:
                    estudiante.estudiante_identificador = None
                estudiante.save()

                _registrar_auditoria_alumno(
                    admin_id,
                    'Modificación',
                    f"Actualizó al estudiante #{estudiante.estudiante_id} ({nombre} {apaterno} - {curso_instancia}).",
                )

            messages.success(request, f"Alumno(a) {nombre} {apaterno} actualizado(a) exitosamente.")
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Curso.DoesNotExist:
            messages.error(request, "El curso seleccionado no existe.")
        except IntegrityError:
            messages.error(
                request,
                "Ya existe otro estudiante con el mismo identificador único en ese curso.",
            )
        except Exception:
            logger.exception("Error actualizando estudiante %s", estudiante_id)
            messages.error(request, "No fue posible actualizar al alumno. Revisa los datos ingresados.")

    return redirect('gestion_de_alumnos')


def eliminar_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_alumnos')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    with transaction.atomic():
        estudiante.estudiante_activo = False
        estudiante.save(update_fields=['estudiante_activo'])
        _registrar_auditoria_alumno(
            request.session.get('usuario_id'),
            'Modificación',
            f"Desactivó al estudiante #{estudiante.estudiante_id} ({estudiante.nombre_completo}).",
        )

    messages.success(
        request,
        f"El alumno {estudiante.estudiante_nombre} {estudiante.estudiante_apaterno} fue desactivado. "
        "Sus datos y antecedentes se conservaron.",
    )
    return redirect('gestion_de_alumnos')


def cambiar_estado_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_alumnos')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    with transaction.atomic():
        estudiante.estudiante_activo = not estudiante.estudiante_activo
        estudiante.save(update_fields=['estudiante_activo'])
        estado = 'activado' if estudiante.estudiante_activo else 'desactivado'
        _registrar_auditoria_alumno(
            request.session.get('usuario_id'),
            'Modificación',
            f"Estado de estudiante #{estudiante.estudiante_id} ({estudiante.nombre_completo}) cambiado a {estado}.",
        )

    messages.success(
        request,
        f"El alumno {estudiante.estudiante_nombre} {estudiante.estudiante_apaterno} fue {estado}.",
    )
    return redirect('gestion_de_alumnos')


def detalle_estudiante_view(request, estudiante_id):
    """Ficha de un alumno: sus datos + todos los casos en los que ha estado involucrado."""
    if 'usuario_id' not in request.session:
        return redirect('login')

    if 'profesor' in (request.session.get('usuario_rol') or '').casefold():
        messages.error(request, "Acceso denegado.")
        return redirect('mis_casos_curso')

    estudiante = get_object_or_404(Estudiante.objects.select_related('curso'), pk=estudiante_id)

    participaciones = (
        Involucran.objects
        .filter(estudiante_id=estudiante_id)
        .select_related('caso', 'caso__lugar')
        .order_by('-caso__caso_fecha', '-caso__caso_id')
    )

    casos_detalle = []
    conteo_gravedad = {'Leve': 0, 'Grave': 0, 'Gravísima': 0}

    for inv in participaciones:
        caso = inv.caso
        texto = caso.caso_descripcion or ''
        titulo = texto
        if '] -' in texto:
            titulo = texto.split('] -', 1)[0].replace('[', '').strip()

        gravedad_caso = inv.tipo_falta or ''
        if gravedad_caso in conteo_gravedad:
            conteo_gravedad[gravedad_caso] += 1

        casos_detalle.append({
            'caso_id': caso.caso_id,
            'titulo': titulo or f"Caso #{caso.caso_id}",
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'gravedad': gravedad_caso,
        })

    prioridad_gravedad = {'Gravísima': 0, 'Grave': 1, 'Leve': 2}
    casos_detalle.sort(key=lambda c: prioridad_gravedad.get(c['gravedad'], 3))

    total_casos = len(casos_detalle)

    # Semáforo automático según puntaje ponderado: Leve = 1, Grave = 3, Gravísima = 5
    puntaje = (
        (conteo_gravedad['Leve'] * 1)
        + (conteo_gravedad['Grave'] * 3)
        + (conteo_gravedad['Gravísima'] * 5)
    )

    if puntaje >= 10:
        estado_clave = 'alerta'
        estado_texto = 'Alerta: requiere intervención'
        estado_detalle = (
            'Este alumno acumula una cantidad importante de faltas graves o gravísimas. '
            'Se recomienda intervención prioritaria de Convivencia Escolar.'
        )
    elif puntaje >= 5:
        estado_clave = 'atencion'
        estado_texto = 'Requiere atención'
        estado_detalle = (
            'El alumno tiene antecedentes que ameritan seguimiento cercano, '
            'aunque no son motivo de alarma todavía.'
        )
    elif puntaje >= 1:
        estado_clave = 'seguimiento'
        estado_texto = 'Bajo seguimiento'
        estado_detalle = (
            'El alumno tiene antecedentes leves registrados. '
            'No requiere acción urgente, pero conviene monitorear.'
        )
    else:
        estado_clave = 'sin_incidencias'
        estado_texto = 'Sin incidencias'
        estado_detalle = 'Este alumno no tiene casos de convivencia registrados en el sistema.'

    context = {
        'estudiante': estudiante,
        'casos': casos_detalle,
        'total_casos': total_casos,
        'conteo_gravedad': conteo_gravedad,
        'puntaje_riesgo': puntaje,
        'estado_clave': estado_clave,
        'estado_texto': estado_texto,
        'estado_detalle': estado_detalle,
    }
    return render(request, 'gestion_casos/detalle_estudiante.html', context)


def _numero_lista_ya_usado(curso, numero_lista, excluir_estudiante_id=None):
    """Verifica si otro alumno del MISMO curso ya tiene ese número de lista."""
    if not numero_lista or not curso:
        return False
    qs = Estudiante.objects.filter(curso=curso, estudiante_numero_lista=numero_lista)
    if excluir_estudiante_id:
        qs = qs.exclude(pk=excluir_estudiante_id)
    return qs.exists()
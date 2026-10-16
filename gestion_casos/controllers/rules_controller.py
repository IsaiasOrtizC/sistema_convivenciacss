"""Rules Controller: reglas de negocio, revisión de disposiciones y versiones del reglamento."""

import hashlib

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from ..models import DocumentoInstitucional, HistorialUsuario, ReglaInstitucional, VersionReglamento


def crear_regla_manual_view(request, version_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede crear o revisar reglas.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    version = get_object_or_404(
        VersionReglamento.objects.select_related('documento'),
        pk=version_id,
        documento__estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
    )
    if version.estado == VersionReglamento.Estado.VIGENTE:
        messages.error(request, "Una versión vigente es inmutable. Sube una nueva versión para revisarla.")
        return redirect('gestion_documentos')
    evidencia = request.POST.get('evidencia_textual', '').strip()
    if not evidencia or evidencia not in version.documento.texto_extraido:
        messages.error(request, "La cita debe coincidir con texto extraído del documento.")
        return redirect('gestion_documentos')

    pagina = request.POST.get('pagina', '').strip()
    referencia = f'Página {pagina}' if pagina.isdigit() else ''
    regla = ReglaInstitucional.objects.create(
        version=version,
        titulo=request.POST.get('titulo', '').strip()[:180] or evidencia[:180],
        evidencia_textual=evidencia,
        referencia_origen=referencia,
        hash_origen=hashlib.sha256(
            f'manual\0{version.pk}\0{referencia}\0{evidencia}'.encode('utf-8')
        ).hexdigest(),
    )
    HistorialUsuario.objects.create(
        usuario_id=request.session['usuario_id'],
        historial_accion='Creación',
        historial_detalle=f'Creó una propuesta de regla para la versión {version.pk}.',
    )
    messages.success(request, "Propuesta creada; completa sus campos y revísala antes de aprobarla.")
    return redirect('gestion_documentos')


def revisar_regla_view(request, regla_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede revisar reglas.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    regla = get_object_or_404(ReglaInstitucional, pk=regla_id)
    if regla.version.estado == VersionReglamento.Estado.VIGENTE:
        messages.error(request, "Una versión vigente es inmutable. Sube una nueva versión para cambiar sus reglas.")
        return redirect('gestion_documentos')
    estado = request.POST.get('estado', '')
    activador = request.POST.get('activador', '')
    tipo_medida = request.POST.get('tipo_medida', regla.tipo_medida)
    titulo = request.POST.get('titulo', '').strip()
    categoria = request.POST.get('categoria_falta', '').strip()
    accion = request.POST.get('accion_requerida', '').strip()
    responsable = request.POST.get('responsable_rol', '').strip()
    umbral_raw = request.POST.get('umbral_casos', '').strip()
    umbral_anotaciones_raw = request.POST.get('umbral_anotaciones', '').strip()
    plazo_raw = request.POST.get('plazo_dias', '').strip()
    plazo_desde = request.POST.get(
        'plazo_desde', ReglaInstitucional.ReferenciaPlazo.SIN_DEFINIR,
    )
    if estado not in ReglaInstitucional.Estado.values:
        messages.error(request, "Selecciona un estado de revisión válido.")
        return redirect('gestion_documentos')
    if activador not in ReglaInstitucional.Activador.values:
        messages.error(request, "Selecciona un tipo de condición válido.")
        return redirect('gestion_documentos')
    if tipo_medida not in ReglaInstitucional.TipoMedida.values:
        messages.error(request, "Selecciona un tipo de disposición válido.")
        return redirect('gestion_documentos')
    if responsable and responsable not in ReglaInstitucional.RolResponsable.values:
        messages.error(request, "Selecciona un responsable válido.")
        return redirect('gestion_documentos')
    if plazo_desde not in ReglaInstitucional.ReferenciaPlazo.values:
        messages.error(request, "Selecciona un inicio de plazo válido.")
        return redirect('gestion_documentos')

    try:
        umbral = int(umbral_raw) if umbral_raw else None
        umbral_anotaciones = (
            int(umbral_anotaciones_raw) if umbral_anotaciones_raw else None
        )
        if (
            umbral_anotaciones is None
            and regla.unidad_umbral == ReglaInstitucional.UnidadUmbral.ANOTACIONES
        ):
            umbral_anotaciones = regla.cantidad_minima
        plazo = int(plazo_raw) if plazo_raw else None
    except ValueError:
        messages.error(request, "El umbral y el plazo deben ser números enteros.")
        return redirect('gestion_documentos')
    if (
        (umbral is not None and not 1 <= umbral <= 10000)
        or (
            umbral_anotaciones is not None
            and not 1 <= umbral_anotaciones <= 10000
        )
        or (plazo is not None and not 0 <= plazo <= 3650)
    ):
        messages.error(request, "El umbral o el plazo están fuera del rango permitido.")
        return redirect('gestion_documentos')
    if activador == ReglaInstitucional.Activador.UMBRAL_CASOS and umbral is None:
        messages.error(request, "La condición por umbral requiere un número de casos.")
        return redirect('gestion_documentos')
    if plazo_desde == ReglaInstitucional.ReferenciaPlazo.EVENTO and plazo is None:
        messages.error(request, "Define los días del plazo antes de calcular su vencimiento.")
        return redirect('gestion_documentos')
    if estado == ReglaInstitucional.Estado.APROBADA and (
        not regla.evidencia_textual.strip()
        or not (
            categoria
            or regla.conducta_condicion.strip()
            or regla.medida_asociada.strip()
        )
        or (
            not regla.solo_presentacion
            and (not categoria or not accion)
        )
    ):
        messages.error(
            request,
            "Para aprobar, completa la disposición, su evidencia y los campos "
            "requeridos por su modalidad.",
        )
        return redirect('gestion_documentos')
    if (
        estado == ReglaInstitucional.Estado.APROBADA
        and regla.solo_presentacion
        and (
            tipo_medida == ReglaInstitucional.TipoMedida.NO_CLASIFICADA
            or not regla.version_fuente.strip()
            or not regla.titulo_fuente.strip()
            or not regla.seccion_fuente.strip()
            or not regla.pagina_impresa
            or not regla.pagina_pdf
        )
    ):
        messages.error(
            request,
            "Para aprobar una disposición de solo presentación, completa su tipo "
            "y referencia verificable de versión, sección y páginas.",
        )
        return redirect('gestion_documentos')

    with transaction.atomic():
        if titulo:
            regla.titulo = titulo[:180]
        regla.tipo_medida = tipo_medida
        regla.categoria_falta = categoria[:100]
        regla.activador = activador
        regla.umbral_casos = (
            umbral if activador == ReglaInstitucional.Activador.UMBRAL_CASOS else None
        )
        regla.umbral_anotaciones = umbral_anotaciones
        regla.accion_requerida = accion
        regla.requiere_citacion_apoderado = request.POST.get('requiere_citacion') == 'on'
        regla.plazo_dias = plazo
        regla.plazo_desde = plazo_desde
        regla.responsable_rol = responsable
        regla.estado = estado
        regla.revisada_por_id = request.session['usuario_id']
        regla.revisada_en = timezone.now()
        regla.save(update_fields=[
            'titulo', 'tipo_medida', 'categoria_falta', 'activador', 'umbral_casos', 'accion_requerida',
            'umbral_anotaciones', 'requiere_citacion_apoderado', 'plazo_dias',
            'plazo_desde', 'responsable_rol',
            'estado', 'revisada_por', 'revisada_en',
        ])
        HistorialUsuario.objects.create(
            usuario_id=request.session['usuario_id'],
            historial_accion='Modificación',
            historial_detalle=(
                f'Revisó la regla {regla.pk}: '
                f'{regla.get_estado_display()} ({regla.referencia_origen or "sin referencia"}).'
            ),
        )
    messages.success(request, "La revisión de la regla quedó registrada.")
    return redirect('gestion_documentos')


def activar_version_reglamento_view(request, version_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede activar una versión.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    with transaction.atomic():
        version = get_object_or_404(
            VersionReglamento.objects.select_for_update().select_related('documento'),
            pk=version_id,
        )
        reglas_aprobadas = list(
            version.reglas.filter(estado=ReglaInstitucional.Estado.APROBADA)
        )
        if (
            version.documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
            or not reglas_aprobadas
            or any(not regla.puede_activarse() for regla in reglas_aprobadas)
        ):
            messages.error(
                request,
                "No se puede activar: el documento debe estar procesado y debe existir "
                "al menos una disposición aprobada con evidencia y datos suficientes.",
            )
            return redirect('gestion_documentos')

        VersionReglamento.objects.filter(estado=VersionReglamento.Estado.VIGENTE).exclude(
            pk=version.pk
        ).update(estado=VersionReglamento.Estado.REEMPLAZADA)
        version.estado = VersionReglamento.Estado.VIGENTE
        version.activada_en = timezone.now()
        version.activada_por_id = request.session['usuario_id']
        version.save(update_fields=['estado', 'activada_en', 'activada_por'])
        HistorialUsuario.objects.create(
            usuario_id=request.session['usuario_id'],
            historial_accion='Modificación',
            historial_detalle=f'Activó la versión {version.pk} del reglamento institucional.',
        )
    messages.success(request, "La versión aprobada ahora está vigente.")
    return redirect('gestion_documentos')

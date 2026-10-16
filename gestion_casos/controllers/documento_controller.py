"""Controlador de documentos: carga, reprocesamiento y eliminación del reglamento y los protocolos institucionales."""

import hashlib
import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from ..models import (
    DocumentoInstitucional,
    HistorialUsuario,
    Notificacion,
    ReglaInstitucional,
    Usuario,
    VersionReglamento,
)
from ..reglamento import ErrorProcesamientoPDF, extraer_paginas_pdf, guardar_candidatas

logger = logging.getLogger(__name__)


# ============================================================
#  DOCUMENTOS INSTITUCIONALES (Reglamento Interno / Protocolos)
# ============================================================

def gestion_documentos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    rol_usuario = request.session.get('usuario_rol', '')
    es_administrador = rol_usuario == 'Administrador'

    if request.method == 'POST':
        if not es_administrador:
            messages.error(request, "Acceso denegado: Solo un Administrador puede subir documentos.")
            return redirect('gestion_documentos')

        tipo_documento = request.POST.get('tipo_documento')
        titulo = request.POST.get('titulo', '').strip()
        archivo = request.FILES.get('archivo')

        if tipo_documento not in ('Reglamento', 'Protocolo'):
            messages.error(request, "Debes seleccionar una categoría válida para el documento.")
            return redirect('gestion_documentos')

        if not archivo:
            messages.error(request, "Debes seleccionar un archivo para subir.")
            return redirect('gestion_documentos')

        if not archivo.name.lower().endswith('.pdf'):
            messages.error(request, "Solo se permiten archivos PDF.")
            return redirect('gestion_documentos')

        limite_bytes = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
        if not archivo.size:
            messages.error(request, "El archivo PDF está vacío.")
            return redirect('gestion_documentos')
        if archivo.size > limite_bytes:
            messages.error(
                request,
                f"El archivo supera el tamaño máximo permitido "
                f"({limite_bytes // (1024 * 1024)} MB).",
            )
            return redirect('gestion_documentos')

        tipo_mime = getattr(archivo, 'content_type', '')
        if tipo_mime not in ('', 'application/pdf', 'application/octet-stream'):
            messages.error(request, "El tipo de contenido del archivo no corresponde a un PDF.")
            return redirect('gestion_documentos')

        contenido = archivo.read()
        archivo.seek(0)
        if not contenido.startswith(b'%PDF-'):
            messages.error(request, "El contenido del archivo no es un PDF válido.")
            return redirect('gestion_documentos')

        try:
            usuario_instancia = Usuario.objects.get(pk=request.session['usuario_id'])
            documento = DocumentoInstitucional.objects.create(
                tipo_documento=tipo_documento,
                titulo=titulo if titulo else archivo.name,
                archivo=archivo,
                usuario=usuario_instancia,
                estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.PROCESANDO,
                checksum_sha256=hashlib.sha256(contenido).hexdigest(),
            )
        except Exception as error:
            logger.error(
                "Error al almacenar un documento institucional (%s).",
                type(error).__name__,
            )
            messages.error(request, "No se pudo almacenar el documento. Revisa la configuración de Cloudinary.")
            return redirect('gestion_documentos')

        try:
            candidatas_count = _procesar_documento_institucional(
                documento,
                contenido,
                usuario_instancia,
            )
            if tipo_documento == 'Reglamento':
                messages.success(
                    request,
                    f"Reglamento almacenado y procesado. "
                    f"Se detectaron {candidatas_count} propuestas, todas pendientes de revisión.",
                )
            else:
                messages.success(request, "Documento institucional almacenado y procesado.")
        except ErrorProcesamientoPDF as error:
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = str(error)
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            messages.error(request, str(error))
        except Exception as error:
            logger.error(
                "Error al extraer texto del documento institucional %s (%s).",
                documento.documento_id,
                type(error).__name__,
            )
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = (
                'Ocurrió un error interno durante la extracción. '
                'Revisa el archivo y vuelve a intentarlo.'
            )
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            messages.error(request, documento.error_procesamiento)

        return redirect('gestion_documentos')

    context = {
        'reglamentos': DocumentoInstitucional.objects.filter(
            tipo_documento='Reglamento',
        ).annotate(
            version_count=Count('versiones_reglamento', distinct=True),
            rule_count=Count('versiones_reglamento__reglas', distinct=True),
        ),
        'protocolos': DocumentoInstitucional.objects.filter(
            tipo_documento='Protocolo',
        ).annotate(
            version_count=Count('versiones_reglamento', distinct=True),
            rule_count=Count('versiones_reglamento__reglas', distinct=True),
        ),
        'es_administrador': es_administrador,
        'versiones_reglamento': VersionReglamento.objects.select_related(
            'documento', 'creada_por', 'activada_por',
        ).prefetch_related('reglas').order_by('-creada_en'),
        'puede_revisar_reglas': es_administrador,
        'estados_regla': ReglaInstitucional.Estado.choices,
        'activadores_regla': ReglaInstitucional.Activador.choices,
        'tipos_medida': ReglaInstitucional.TipoMedida.choices,
        'roles_responsables': ReglaInstitucional.RolResponsable.choices,
        'referencias_plazo': ReglaInstitucional.ReferenciaPlazo.choices,
        'limite_pdf_mb': getattr(
            settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024
        ) // (1024 * 1024),
    }
    return render(request, 'gestion_casos/gestion_documentos.html', context)


def reprocesar_documento_view(request, documento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede reprocesar documentos.")
    if request.method != 'POST':
        return HttpResponseForbidden("El reprocesamiento requiere una solicitud POST.")

    documento = get_object_or_404(DocumentoInstitucional, pk=documento_id)
    if documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.ERROR:
        messages.error(request, "Solo se pueden reprocesar documentos que estén en estado de error.")
        return redirect('gestion_documentos')

    documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.PROCESANDO
    documento.error_procesamiento = ''
    documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
    limite_bytes = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
    try:
        with documento.archivo.open('rb') as archivo:
            contenido = archivo.read(limite_bytes + 1)
        if len(contenido) > limite_bytes:
            raise ErrorProcesamientoPDF(
                f'El PDF supera el límite de {limite_bytes // (1024 * 1024)} MB.'
            )
        if not contenido.startswith(b'%PDF-'):
            raise ErrorProcesamientoPDF("El archivo almacenado no contiene un PDF válido.")

        propuestas = _procesar_documento_institucional(
            documento,
            contenido,
            Usuario.objects.get(pk=request.session['usuario_id']),
        )
        mensaje = "Documento reprocesado correctamente."
        if documento.tipo_documento == 'Reglamento':
            if propuestas:
                mensaje += (
                    f" Se crearon {propuestas} propuestas nuevas, pendientes de revisión."
                )
            else:
                mensaje += " Se conservaron las versiones y reglas existentes."
        messages.success(request, mensaje)
    except ErrorProcesamientoPDF as error:
        documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
        documento.error_procesamiento = str(error)
        documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
        messages.error(request, str(error))
    except Exception as error:
        logger.error(
            "Error al reprocesar documento institucional %s (%s).",
            documento.documento_id,
            type(error).__name__,
        )
        documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
        documento.error_procesamiento = (
            'Ocurrió un error interno durante el reprocesamiento. '
            'Comprueba el almacenamiento y la configuración del servidor.'
        )
        documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
        messages.error(request, documento.error_procesamiento)
    return redirect('gestion_documentos')


def eliminar_documento_view(request, documento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('gestion_documentos')
    if request.method != 'POST':
        return HttpResponseForbidden("La eliminación requiere una solicitud POST.")

    try:
        with transaction.atomic():
            documento = (
                DocumentoInstitucional.objects.select_for_update()
                .filter(pk=documento_id)
                .first()
            )
            if documento is None:
                messages.info(
                    request,
                    "El documento ya no existe; puede que se haya eliminado "
                    "desde otra sesión. Actualiza la página para ver el listado vigente.",
                )
                return redirect('gestion_documentos')

            documento_id_auditoria = documento.pk
            titulo = documento.titulo
            nombre_archivo = documento.archivo.name
            almacenamiento = documento.archivo.storage
            cantidad_versiones = documento.versiones_reglamento.count()
            cantidad_reglas = ReglaInstitucional.objects.filter(
                version__documento=documento,
            ).count()

            Notificacion.objects.filter(
                Q(regla__version__documento=documento)
                | Q(version_reglamento__documento=documento)
            ).update(
                notificacion_titulo='Disposición reglamentaria retirada',
                notificacion_mensaje=(
                    'La disposición vinculada a esta notificación fue retirada '
                    'al reemplazar el documento. No utilices la orientación anterior; '
                    'solicita revisión del personal autorizado.'
                ),
                regla=None,
                version_reglamento=None,
            )
            HistorialUsuario.objects.create(
                usuario_id=request.session['usuario_id'],
                historial_accion='Eliminación',
                historial_detalle=(
                    f'Eliminó el documento institucional "{titulo}" '
                    f'(ID {documento.pk}), junto con {cantidad_versiones} versión(es) '
                    f'y {cantidad_reglas} propuesta(s) asociada(s).'
                ),
            )
            documento.delete()
    except Exception:
        logger.exception(
            "Error al eliminar el documento institucional %s.", documento_id,
        )
        messages.error(
            request,
            "No se pudo eliminar el documento y sus propuestas. No se confirmó "
            "la eliminación del archivo.",
        )
        return redirect('gestion_documentos')

    try:
        if nombre_archivo:
            almacenamiento.delete(nombre_archivo)
    except Exception:
        logger.exception(
            "El registro del documento %s se eliminó, pero falló la limpieza del archivo.",
            documento_id_auditoria,
        )
        messages.warning(
            request,
            "El documento y sus versiones/propuestas se eliminaron, pero el archivo "
            "almacenado no pudo limpiarse. Contacta al Administrador del sistema.",
        )
    else:
        messages.success(
            request,
            f"Se eliminó «{titulo}» junto con {cantidad_versiones} versión(es) "
            f"y {cantidad_reglas} propuesta(s). Ya puedes subir el reglamento de reemplazo.",
        )

    return redirect('gestion_documentos')


def _procesar_documento_institucional(documento, contenido, usuario):
    paginas = extraer_paginas_pdf(contenido)
    documento.texto_extraido = '\n\n'.join(paginas)
    documento.numero_paginas = len(paginas)
    documento.error_procesamiento = ''
    documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
    documento.save(update_fields=[
        'texto_extraido', 'numero_paginas', 'error_procesamiento',
        'estado_procesamiento',
    ])

    if documento.tipo_documento != 'Reglamento':
        return 0
    if VersionReglamento.objects.filter(documento=documento).exists():
        return 0

    ultimo_numero = (
        VersionReglamento.objects.filter(documento__tipo_documento='Reglamento')
        .order_by('-numero')
        .values_list('numero', flat=True)
        .first()
        or 0
    )
    with transaction.atomic():
        version = VersionReglamento.objects.create(
            documento=documento,
            numero=ultimo_numero + 1,
            creada_por=usuario,
        )
        candidatas = guardar_candidatas(version, paginas)
    return len(candidatas)

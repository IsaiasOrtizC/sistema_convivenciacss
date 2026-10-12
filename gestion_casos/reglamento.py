import importlib
import os
import re
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pypdf import PdfReader

from .models import (
    AccionSeguimiento,
    Caso,
    HistorialAccionSeguimiento,
    HistorialNotificacion,
    HistorialSeguimientoCaso,
    Involucran,
    Notificacion,
    ReglaInstitucional,
    SeguimientoCaso,
    Estudiante,
    Usuario,
)


class ErrorProcesamientoPDF(ValueError):
    """Error validado que puede explicarse al usuario sin exponer detalles internos."""


class PDFRequiereOCR(ErrorProcesamientoPDF):
    pass


class DependenciaOCRNoDisponible(PDFRequiereOCR):
    pass


class OCRSinResultados(PDFRequiereOCR):
    pass


def _limite(nombre, predeterminado):
    return getattr(settings, nombre, predeterminado)


def _caracteres_utiles(texto):
    return sum(caracter.isalnum() for caracter in texto)


def _cargar_dependencias_ocr():
    try:
        fitz = importlib.import_module('pymupdf')
        pytesseract = importlib.import_module('pytesseract')
        from PIL import Image
    except ImportError as error:
        raise DependenciaOCRNoDisponible(
            'Falta una biblioteca de OCR. Instala las dependencias del proyecto '
            'con "pip install -r requirements.txt".'
        ) from error

    comando = _limite('TESSERACT_CMD', '')
    if comando:
        pytesseract.pytesseract.tesseract_cmd = comando

    tessdata = _limite('TESSDATA_PREFIX', '')
    if tessdata:
        os.environ['TESSDATA_PREFIX'] = tessdata
    try:
        idiomas = pytesseract.get_languages()
    except pytesseract.pytesseract.TesseractNotFoundError as error:
        raise DependenciaOCRNoDisponible(
            'No se encontró Tesseract. Instala el ejecutable del sistema y '
            'configura TESSERACT_CMD si no está en PATH.'
        ) from error
    except pytesseract.pytesseract.TesseractError as error:
        if _falta_idioma_espanol(str(error)):
            raise DependenciaOCRNoDisponible(
                'No está instalado el idioma español (spa) de Tesseract. '
                'Instala spa.traineddata y configura TESSDATA_PREFIX.'
            ) from error
        raise ErrorProcesamientoPDF(
            'Tesseract no pudo iniciarse. Comprueba su instalación y configuración.'
        ) from error

    if 'spa' not in idiomas:
        raise DependenciaOCRNoDisponible(
            'No está instalado el idioma español (spa) de Tesseract. '
            'Instala spa.traineddata y configura TESSDATA_PREFIX.'
        )
    return fitz, pytesseract, Image, ''


def _falta_idioma_espanol(mensaje):
    mensaje = mensaje.casefold()
    return any(
        indicio in mensaje
        for indicio in (
            'spa.traineddata',
            'failed loading language',
            'error opening data file',
            'could not initialize tesseract',
        )
    )


def _texto_ocr(pytesseract, imagen, config):
    try:
        return pytesseract.image_to_string(
            imagen,
            lang='spa',
            config=config,
            timeout=_limite('REGLAMENTO_OCR_TIMEOUT_SECONDS', 30),
        )
    except pytesseract.pytesseract.TesseractNotFoundError as error:
        raise DependenciaOCRNoDisponible(
            'No se encontró Tesseract. Instala el ejecutable del sistema y '
            'configura TESSERACT_CMD si no está en PATH.'
        ) from error
    except pytesseract.pytesseract.TesseractError as error:
        if _falta_idioma_espanol(str(error)):
            raise DependenciaOCRNoDisponible(
                'No está instalado el idioma español (spa) de Tesseract. '
                'Instala spa.traineddata y configura TESSDATA_PREFIX.'
            ) from error
        raise ErrorProcesamientoPDF(
            'Tesseract no pudo procesar una página del documento.'
        ) from error
    except RuntimeError as error:
        raise ErrorProcesamientoPDF(
            'El OCR excedió el tiempo máximo permitido para una página.'
        ) from error


def extraer_paginas_pdf(contenido):
    if not contenido:
        raise ErrorProcesamientoPDF('El archivo PDF está vacío.')
    limite_bytes = _limite('REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
    if len(contenido) > limite_bytes:
        raise ErrorProcesamientoPDF(
            f'El PDF supera el límite de {limite_bytes // (1024 * 1024)} MB.'
        )
    if not contenido.startswith(b'%PDF-'):
        raise ErrorProcesamientoPDF('El archivo no tiene una cabecera PDF válida.')

    max_paginas = _limite('REGLAMENTO_PDF_MAX_PAGES', 500)
    min_texto_pagina = _limite('REGLAMENTO_PDF_MIN_TEXT_CHARS', 30)
    min_texto_documento = _limite('REGLAMENTO_PDF_MIN_USEFUL_CHARS', 30)
    try:
        lector = PdfReader(BytesIO(contenido), strict=False)
        if lector.is_encrypted:
            raise ErrorProcesamientoPDF('El PDF está protegido y no se puede procesar.')
        if not lector.pages:
            raise ErrorProcesamientoPDF('El PDF no contiene páginas para procesar.')
        if len(lector.pages) > max_paginas:
            unidad = 'página' if max_paginas == 1 else 'páginas'
            raise ErrorProcesamientoPDF(
                f'El PDF supera el límite de {max_paginas} {unidad}.'
            )
        paginas = [pagina.extract_text() or '' for pagina in lector.pages]
    except ErrorProcesamientoPDF:
        raise
    except Exception as error:
        raise ErrorProcesamientoPDF(
            'No se pudo leer el PDF. Comprueba que el archivo no esté dañado.'
        ) from error

    indices_ocr = [
        indice for indice, texto in enumerate(paginas)
        if _caracteres_utiles(texto) < min_texto_pagina
    ]
    if indices_ocr:
        max_paginas_ocr = _limite('REGLAMENTO_OCR_MAX_PAGES', 50)
        if len(indices_ocr) > max_paginas_ocr:
            raise ErrorProcesamientoPDF(
                'El documento supera el límite de páginas que se pueden procesar '
                f'por OCR ({max_paginas_ocr}).'
            )
        try:
            fitz, pytesseract, Image, config = _cargar_dependencias_ocr()
            with fitz.open(stream=contenido, filetype='pdf') as documento:
                if documento.page_count != len(paginas):
                    raise ErrorProcesamientoPDF(
                        'No se pudo preparar el PDF para el reconocimiento de texto.'
                    )
                dpi = _limite('REGLAMENTO_OCR_DPI', 200)
                for indice in indices_ocr:
                    pagina = documento.load_page(indice)
                    pixmap = pagina.get_pixmap(
                        dpi=dpi,
                        colorspace=fitz.csGRAY,
                        alpha=False,
                    )
                    with Image.open(BytesIO(pixmap.tobytes('png'))) as imagen:
                        texto_ocr = _texto_ocr(pytesseract, imagen, config)
                    if _caracteres_utiles(texto_ocr) < min_texto_pagina:
                        raise OCRSinResultados(
                            'El OCR no obtuvo texto utilizable en una o más páginas. '
                            'Comprueba que el documento sea legible y que tenga '
                            'instalado el idioma español (spa).'
                        )
                    if _caracteres_utiles(texto_ocr) > _caracteres_utiles(paginas[indice]):
                        paginas[indice] = texto_ocr
        except ErrorProcesamientoPDF:
            raise
        except Exception as error:
            raise ErrorProcesamientoPDF(
                'No se pudo preparar una página para OCR. Comprueba que el PDF '
                'no esté dañado y que PyMuPDF esté instalado correctamente.'
            ) from error

    if sum(_caracteres_utiles(texto) for texto in paginas) < min_texto_documento:
        raise OCRSinResultados(
            'No se obtuvo texto utilizable del PDF. Comprueba que las páginas '
            'sean legibles y que Tesseract tenga instalado el idioma español (spa).'
        )
    return paginas


def detectar_reglas_candidatas(paginas):
    """No infiere reglas desde párrafos arbitrarios ni desde fragmentos del PDF."""
    return []


@transaction.atomic
def guardar_candidatas(version, paginas):
    creadas = []
    for datos in detectar_reglas_candidatas(paginas):
        regla, creada = ReglaInstitucional.objects.get_or_create(
            version=version,
            hash_origen=datos['hash_origen'],
            defaults=datos,
        )
        if creada:
            creadas.append(regla)
    return creadas


def _identificador_visual(estudiante):
    if estudiante.estudiante_identificador:
        return estudiante.estudiante_identificador
    return f'Estudiante #{estudiante.estudiante_id}'


def _responsable_regla(regla, actor):
    if regla.responsable_rol:
        responsable = (
            Usuario.objects.filter(
                rol__rol_nombre=regla.responsable_rol,
                usuario_activo=True,
            )
            .order_by('usuario_id')
            .first()
        )
        if responsable:
            return responsable
    return actor


@transaction.atomic
def evaluar_reglas_para_caso(
    caso: Caso,
    estudiantes,
    actor: Usuario,
    evento_tipo=Notificacion.TipoEvento.CASO_CREADO,
    fecha_evento=None,
):
    """Evalúa solo reglas activas y aprobadas contra los eventos ya persistidos."""
    activas = ReglaInstitucional.objects.filter(
        estado=ReglaInstitucional.Estado.APROBADA,
        version__estado='vigente',
        solo_presentacion=False,
    ).exclude(activador=ReglaInstitucional.Activador.MANUAL).select_related(
        'version', 'version__documento',
    )
    momento_evento = fecha_evento or caso.caso_creado_en or timezone.now()
    fecha_evento_local = timezone.localtime(momento_evento).date()
    notificaciones_creadas = 0

    for estudiante in estudiantes:
        seguimiento, seguimiento_creado = SeguimientoCaso.objects.get_or_create(
            caso=caso,
            estudiante=estudiante,
        )
        if seguimiento_creado:
            HistorialSeguimientoCaso.objects.create(
                seguimiento=seguimiento,
                estado=seguimiento.estado,
                cambiado_por=actor,
                motivo='Seguimiento creado al registrar o actualizar un caso.',
            )
        for regla in activas:
            if not regla.categoria_falta or not regla.accion_requerida.strip():
                continue
            tiene_categoria = Involucran.objects.filter(
                caso_id=caso.caso_id,
                estudiante_id=estudiante.estudiante_id,
                tipo_falta__iexact=regla.categoria_falta,
            ).exists()
            if not tiene_categoria:
                continue

            if regla.activador == ReglaInstitucional.Activador.UMBRAL_CASOS:
                if not regla.umbral_casos:
                    continue
                total = Involucran.objects.filter(
                    estudiante_id=estudiante.estudiante_id,
                    tipo_falta__iexact=regla.categoria_falta,
                ).values('caso_id').distinct().count()
                if total < regla.umbral_casos:
                    continue

            clave = (
                f'{evento_tipo}:caso:{caso.caso_id}:'
                f'estudiante:{estudiante.estudiante_id}:regla:{regla.pk}'
            )
            responsable = _responsable_regla(regla, actor)
            fecha_limite = (
                fecha_evento_local + timedelta(days=regla.plazo_dias)
                if (
                    regla.plazo_dias is not None
                    and regla.plazo_desde == ReglaInstitucional.ReferenciaPlazo.EVENTO
                )
                else None
            )
            texto_mensaje = regla.accion_requerida.strip()
            if regla.requiere_citacion_apoderado:
                texto_mensaje += ' También requiere citar al apoderado.'
            notificacion, creada = Notificacion.objects.get_or_create(
                evento_clave=clave,
                defaults={
                    'usuario': responsable,
                    'responsable': responsable,
                    'notificacion_titulo': (
                        f'Orientación reglamentaria · {regla.categoria_falta}'
                    ),
                    'notificacion_mensaje': (
                        f'{_identificador_visual(estudiante)}: {texto_mensaje}'
                    ),
                    'notificacion_icono': '🔔',
                    'regla': regla,
                    'version_reglamento': regla.version,
                    'caso': caso,
                    'estudiante': estudiante,
                    'evento_tipo': evento_tipo,
                    'fecha_limite': fecha_limite,
                },
            )
            if not creada:
                continue

            notificaciones_creadas += 1
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=notificacion.estado,
                cambiado_por=actor,
                motivo='Notificación creada por una regla institucional aprobada.',
            )
            acciones_requeridas = [regla.accion_requerida.strip()]
            if regla.requiere_citacion_apoderado:
                acciones_requeridas.append('Citar al apoderado')
            for numero_accion, titulo_accion in enumerate(acciones_requeridas, start=1):
                accion, accion_creada = AccionSeguimiento.objects.get_or_create(
                    clave_idempotencia=f'{clave}:accion:{numero_accion}',
                    defaults={
                        'seguimiento': seguimiento,
                        'regla': regla,
                        'notificacion': notificacion,
                        'titulo': titulo_accion[:180],
                        'responsable': responsable,
                        'responsable_rol': regla.responsable_rol,
                        'fecha_limite': fecha_limite,
                    },
                )
                if accion_creada:
                    HistorialAccionSeguimiento.objects.create(
                        accion=accion,
                        estado=accion.estado,
                        cambiado_por=actor,
                        motivo='Acción creada por una regla institucional aprobada.',
                    )

    return notificaciones_creadas

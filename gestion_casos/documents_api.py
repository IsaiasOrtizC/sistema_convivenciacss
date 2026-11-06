"""JWT endpoints for institutional documents and reviewed rule versions."""

import hashlib
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DocumentoInstitucional,
    HistorialUsuario,
    Notificacion,
    ReglaInstitucional,
    Usuario,
    VersionReglamento,
)
from .reglamento import ErrorProcesamientoPDF
from .controllers.documento_controller import _procesar_documento_institucional

logger = logging.getLogger(__name__)


def _es_administrador(request):
    return request.user.rol.rol_nombre == 'Administrador'


def _datos_regla(regla):
    return {
        'id': regla.pk,
        'titulo': regla.titulo,
        'categoria_falta': regla.categoria_falta,
        'activador': regla.activador,
        'umbral_casos': regla.umbral_casos,
        'umbral_anotaciones': regla.umbral_anotaciones,
        'conducta_condicion': regla.conducta_condicion,
        'unidad_umbral': regla.unidad_umbral,
        'cantidad_minima': regla.cantidad_minima,
        'estado_cantidad': regla.estado_cantidad,
        'accion_requerida': regla.accion_requerida,
        'medida_asociada': regla.medida_asociada,
        'tipo_medida': regla.tipo_medida,
        'duracion_minima_dias': regla.duracion_minima_dias,
        'duracion_maxima_dias': regla.duracion_maxima_dias,
        'unidad_duracion': regla.unidad_duracion,
        'condiciones': regla.condiciones,
        'excepciones': regla.excepciones,
        'requiere_citacion_apoderado': regla.requiere_citacion_apoderado,
        'solo_presentacion': regla.solo_presentacion,
        'plazo_dias': regla.plazo_dias,
        'plazo_desde': regla.plazo_desde,
        'responsable_rol': regla.responsable_rol,
        'evidencia_textual': regla.evidencia_textual,
        'referencia_origen': regla.referencia_origen,
        'titulo_fuente': regla.titulo_fuente,
        'version_fuente': regla.version_fuente,
        'seccion_fuente': regla.seccion_fuente,
        'pagina_impresa': regla.pagina_impresa,
        'pagina_pdf': regla.pagina_pdf,
        'pagina_impresa_hasta': regla.pagina_impresa_hasta,
        'pagina_pdf_hasta': regla.pagina_pdf_hasta,
        'estado': regla.estado,
        'puede_activarse': regla.puede_activarse(),
    }


class DocumentosAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get(self, request):
        documentos = []
        versiones = []
        for documento in DocumentoInstitucional.objects.select_related(
            'usuario',
        ).order_by('-fecha_subida'):
            documentos.append({
                'id': documento.pk,
                'tipo': documento.tipo_documento,
                'titulo': documento.titulo,
                'archivo_url': documento.archivo.url if documento.archivo else '',
                'fecha_subida': documento.fecha_subida.isoformat(),
                'subido_por': (
                    f'{documento.usuario.usuario_nombre} '
                    f'{documento.usuario.usuario_apaterno}'
                    if documento.usuario else 'Usuario eliminado'
                ),
                'estado_procesamiento': documento.estado_procesamiento,
                'error_procesamiento': documento.error_procesamiento,
                'numero_paginas': documento.numero_paginas,
            })
            for version in documento.versiones_reglamento.prefetch_related(
                'reglas',
            ).order_by('-creada_en'):
                versiones.append({
                    'id': version.pk,
                    'documento_id': documento.pk,
                    'documento_titulo': documento.titulo,
                    'numero': version.numero,
                    'estado': version.estado,
                    'creada_en': version.creada_en.isoformat(),
                    'reglas': [
                        _datos_regla(regla)
                        for regla in version.reglas.all()
                    ],
                    'puede_activar': (
                        documento.estado_procesamiento
                        == DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
                        and any(
                            regla.estado == ReglaInstitucional.Estado.APROBADA
                            and regla.puede_activarse()
                            for regla in version.reglas.all()
                        )
                    ),
                })
        return Response({
            'documentos': documentos,
            'versiones': versiones,
            'puede_administrar': _es_administrador(request),
            'limite_pdf_mb': getattr(
                settings,
                'REGLAMENTO_PDF_MAX_BYTES',
                20 * 1024 * 1024,
            ) // (1024 * 1024),
            'opciones': {
                'estados_regla': [
                    {'valor': value, 'etiqueta': label}
                    for value, label in ReglaInstitucional.Estado.choices
                ],
                'activadores': [
                    {'valor': value, 'etiqueta': label}
                    for value, label in ReglaInstitucional.Activador.choices
                ],
                'tipos_medida': [
                    {'valor': value, 'etiqueta': label}
                    for value, label in ReglaInstitucional.TipoMedida.choices
                ],
                'roles_responsables': [
                    {'valor': value, 'etiqueta': label}
                    for value, label in ReglaInstitucional.RolResponsable.choices
                ],
                'referencias_plazo': [
                    {'valor': value, 'etiqueta': label}
                    for value, label in ReglaInstitucional.ReferenciaPlazo.choices
                ],
            },
        })

    def post(self, request, documento_id=None):
        if documento_id is not None:
            return self.post_action(request, documento_id)
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede subir documentos.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        tipo = request.data.get('tipo_documento')
        titulo = request.data.get('titulo', '')
        archivo = request.FILES.get('archivo')
        if tipo not in ('Reglamento', 'Protocolo'):
            return Response(
                {'detail': 'Selecciona una categoría de documento válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not archivo or not archivo.name.lower().endswith('.pdf'):
            return Response(
                {'detail': 'Selecciona un archivo PDF válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limite = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
        if not archivo.size or archivo.size > limite:
            return Response(
                {'detail': f'El PDF debe pesar entre 1 byte y {limite // (1024 * 1024)} MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mime = getattr(archivo, 'content_type', '')
        if mime not in ('', 'application/pdf', 'application/octet-stream'):
            return Response(
                {'detail': 'El archivo seleccionado no es un PDF.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contenido = archivo.read()
        archivo.seek(0)
        if not contenido.startswith(b'%PDF-'):
            return Response(
                {'detail': 'El contenido del archivo no corresponde a un PDF válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            documento = DocumentoInstitucional.objects.create(
                tipo_documento=tipo,
                titulo=(titulo.strip() or archivo.name)[:150],
                archivo=archivo,
                usuario=request.user,
                estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.PROCESANDO,
                checksum_sha256=hashlib.sha256(contenido).hexdigest(),
            )
        except Exception:
            logger.exception('No se pudo almacenar el documento institucional vía API.')
            return Response(
                {'detail': 'No se pudo almacenar el documento. Revisa el almacenamiento.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        try:
            propuestas = _procesar_documento_institucional(
                documento,
                contenido,
                request.user,
            )
            return Response(
                {
                    'id': documento.pk,
                    'propuestas': propuestas,
                    'mensaje': 'El documento fue almacenado y procesado.',
                },
                status=status.HTTP_201_CREATED,
            )
        except ErrorProcesamientoPDF as error:
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = str(error)
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            return Response(
                {'detail': str(error), 'documento_id': documento.pk},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.exception(
                'No se pudo procesar el documento institucional %s.',
                documento.pk,
            )
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = (
                'Ocurrió un error interno durante la extracción. '
                'Revisa el archivo y vuelve a intentarlo.'
            )
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            return Response(
                {
                    'detail': documento.error_procesamiento,
                    'documento_id': documento.pk,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post_action(self, request, documento_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede gestionar documentos.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        documento = get_object_or_404(DocumentoInstitucional, pk=documento_id)
        if request.data.get('accion') != 'reprocesar':
            return Response(
                {'detail': 'La acción solicitada no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.ERROR:
            return Response(
                {'detail': 'Solo se pueden reprocesar documentos con error.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.PROCESANDO
        documento.error_procesamiento = ''
        documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
        limite = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
        try:
            with documento.archivo.open('rb') as archivo:
                contenido = archivo.read(limite + 1)
            if len(contenido) > limite or not contenido.startswith(b'%PDF-'):
                raise ErrorProcesamientoPDF('El PDF almacenado no es válido o supera el límite.')
            propuestas = _procesar_documento_institucional(
                documento,
                contenido,
                request.user,
            )
            return Response({
                'propuestas': propuestas,
                'mensaje': 'El documento fue reprocesado correctamente.',
            })
        except ErrorProcesamientoPDF as error:
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = str(error)
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception('No se pudo reprocesar el documento %s vía API.', documento_id)
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = 'No se pudo procesar el documento almacenado.'
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            return Response(
                {'detail': documento.error_procesamiento},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, documento_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede eliminar documentos.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            with transaction.atomic():
                documento = get_object_or_404(
                    DocumentoInstitucional.objects.select_for_update(),
                    pk=documento_id,
                )
                archivo = documento.archivo.name
                storage = documento.archivo.storage
                title = documento.titulo
                versiones = documento.versiones_reglamento.count()
                reglas = ReglaInstitucional.objects.filter(
                    version__documento=documento,
                ).count()
                Notificacion.objects.filter(
                    Q(regla__version__documento=documento)
                    | Q(version_reglamento__documento=documento)
                ).update(
                    notificacion_titulo='Disposición reglamentaria retirada',
                    notificacion_mensaje=(
                        'La disposición vinculada a esta notificación fue retirada '
                        'al reemplazar el documento. Solicita revisión al personal autorizado.'
                    ),
                    regla=None,
                    version_reglamento=None,
                )
                HistorialUsuario.objects.create(
                    usuario=request.user,
                    historial_accion='Eliminación',
                    historial_detalle=(
                        f'Eliminó el documento institucional "{title}" '
                        f'(ID {documento.pk}), con {versiones} versión(es) '
                        f'y {reglas} propuesta(s).'
                    ),
                )
                documento.delete()
            try:
                if archivo:
                    storage.delete(archivo)
            except Exception:
                logger.exception('El documento %s se eliminó, pero falló la limpieza del archivo.', documento_id)
                return Response({
                    'mensaje': 'Se eliminó el registro, pero el archivo almacenado no pudo limpiarse.',
                    'advertencia': True,
                })
            return Response({'mensaje': f'Se eliminó {title} y su contenido asociado.'})
        except Exception:
            logger.exception('No se pudo eliminar el documento %s vía API.', documento_id)
            return Response(
                {'detail': 'No se pudo eliminar el documento y sus versiones.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VersionReglamentoAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def post(self, request, version_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede crear propuestas de reglas.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        version = get_object_or_404(
            VersionReglamento.objects.select_related('documento'),
            pk=version_id,
            documento__estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
        )
        if version.estado == VersionReglamento.Estado.VIGENTE:
            return Response(
                {'detail': 'Una versión vigente es inmutable; sube una nueva versión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        evidencia = request.data.get('evidencia_textual', '')
        if not isinstance(evidencia, str) or not evidencia.strip() or evidencia not in version.documento.texto_extraido:
            return Response(
                {'detail': 'La cita debe coincidir con texto extraído del documento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pagina = request.data.get('pagina')
        referencia = f'Página {pagina}' if isinstance(pagina, int) and pagina > 0 else ''
        regla = ReglaInstitucional.objects.create(
            version=version,
            titulo=(request.data.get('titulo', '').strip() or evidencia[:180])[:180],
            evidencia_textual=evidencia,
            referencia_origen=referencia,
            hash_origen=hashlib.sha256(
                f'manual\0{version.pk}\0{referencia}\0{evidencia}'.encode('utf-8')
            ).hexdigest(),
        )
        HistorialUsuario.objects.create(
            usuario=request.user,
            historial_accion='Creación',
            historial_detalle=f'Creó una propuesta de regla para la versión {version.pk}.',
        )
        return Response(
            {'regla': _datos_regla(regla)},
            status=status.HTTP_201_CREATED,
        )


class ReglaInstitucionalAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def patch(self, request, regla_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede revisar reglas.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        regla = get_object_or_404(
            ReglaInstitucional.objects.select_related('version'),
            pk=regla_id,
        )
        if regla.version.estado == VersionReglamento.Estado.VIGENTE:
            return Response(
                {'detail': 'Una versión vigente es inmutable.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        datos = request.data
        estado = datos.get('estado')
        activador = datos.get('activador')
        tipo_medida = datos.get('tipo_medida', regla.tipo_medida)
        plazo_desde = datos.get(
            'plazo_desde',
            ReglaInstitucional.ReferenciaPlazo.SIN_DEFINIR,
        )
        responsable = datos.get('responsable_rol', '')
        if estado not in ReglaInstitucional.Estado.values:
            return Response({'detail': 'Selecciona un estado de revisión válido.'}, status=400)
        if activador not in ReglaInstitucional.Activador.values:
            return Response({'detail': 'Selecciona una condición válida.'}, status=400)
        if tipo_medida not in ReglaInstitucional.TipoMedida.values:
            return Response({'detail': 'Selecciona un tipo de disposición válido.'}, status=400)
        if responsable and responsable not in ReglaInstitucional.RolResponsable.values:
            return Response({'detail': 'Selecciona un responsable válido.'}, status=400)
        if plazo_desde not in ReglaInstitucional.ReferenciaPlazo.values:
            return Response({'detail': 'Selecciona un inicio de plazo válido.'}, status=400)
        try:
            umbral = int(datos['umbral_casos']) if datos.get('umbral_casos') not in (None, '') else None
            umbral_anotaciones = int(datos['umbral_anotaciones']) if datos.get('umbral_anotaciones') not in (None, '') else None
            plazo = int(datos['plazo_dias']) if datos.get('plazo_dias') not in (None, '') else None
        except (TypeError, ValueError):
            return Response({'detail': 'Umbrales y plazos deben ser números enteros.'}, status=400)
        if (
            (umbral is not None and not 1 <= umbral <= 10000)
            or (umbral_anotaciones is not None and not 1 <= umbral_anotaciones <= 10000)
            or (plazo is not None and not 0 <= plazo <= 3650)
        ):
            return Response({'detail': 'El umbral o plazo está fuera del rango permitido.'}, status=400)
        if activador == ReglaInstitucional.Activador.UMBRAL_CASOS and umbral is None:
            return Response({'detail': 'La condición por umbral requiere un número de casos.'}, status=400)
        if plazo_desde == ReglaInstitucional.ReferenciaPlazo.EVENTO and plazo is None:
            return Response({'detail': 'Define los días del plazo.'}, status=400)

        titulo = datos.get('titulo', regla.titulo)
        categoria = datos.get('categoria_falta', '')
        accion = datos.get('accion_requerida', '')
        if not all(isinstance(value, str) for value in (titulo, categoria, accion)):
            return Response({'detail': 'Los campos de revisión deben ser texto.'}, status=400)
        if estado == ReglaInstitucional.Estado.APROBADA and (
            not regla.evidencia_textual.strip()
            or not (
                categoria.strip()
                or regla.conducta_condicion.strip()
                or regla.medida_asociada.strip()
            )
            or (not regla.solo_presentacion and (not categoria.strip() or not accion.strip()))
        ):
            return Response(
                {'detail': 'Completa la disposición y evidencia antes de aprobar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if estado == ReglaInstitucional.Estado.APROBADA and regla.solo_presentacion and (
            tipo_medida == ReglaInstitucional.TipoMedida.NO_CLASIFICADA
            or not regla.version_fuente.strip()
            or not regla.titulo_fuente.strip()
            or not regla.seccion_fuente.strip()
            or not regla.pagina_impresa
            or not regla.pagina_pdf
        ):
            return Response(
                {'detail': 'Completa tipo y referencia verificable para aprobar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            regla.titulo = titulo.strip()[:180] or regla.titulo
            regla.tipo_medida = tipo_medida
            regla.categoria_falta = categoria.strip()[:100]
            regla.activador = activador
            regla.umbral_casos = (
                umbral if activador == ReglaInstitucional.Activador.UMBRAL_CASOS else None
            )
            regla.umbral_anotaciones = umbral_anotaciones
            regla.accion_requerida = accion.strip()
            regla.requiere_citacion_apoderado = datos.get('requiere_citacion_apoderado') is True
            regla.plazo_dias = plazo
            regla.plazo_desde = plazo_desde
            regla.responsable_rol = responsable
            regla.estado = estado
            regla.revisada_por = request.user
            regla.revisada_en = timezone.now()
            regla.save(update_fields=[
                'titulo', 'tipo_medida', 'categoria_falta', 'activador',
                'umbral_casos', 'accion_requerida', 'umbral_anotaciones',
                'requiere_citacion_apoderado', 'plazo_dias', 'plazo_desde',
                'responsable_rol', 'estado', 'revisada_por', 'revisada_en',
            ])
            HistorialUsuario.objects.create(
                usuario=request.user,
                historial_accion='Modificación',
                historial_detalle=(
                    f'Revisó la regla {regla.pk}: {regla.get_estado_display()} '
                    f'({regla.referencia_origen or "sin referencia"}).'
                ),
            )
        return Response({'regla': _datos_regla(regla)})


class ActivarVersionReglamentoAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, version_id):
        if not _es_administrador(request):
            return Response(
                {'detail': 'Solo un Administrador puede activar una versión.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        with transaction.atomic():
            version = get_object_or_404(
                VersionReglamento.objects.select_for_update().select_related('documento'),
                pk=version_id,
            )
            reglas = list(
                version.reglas.filter(estado=ReglaInstitucional.Estado.APROBADA)
            )
            if (
                version.documento.estado_procesamiento
                != DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
                or not reglas
                or any(not regla.puede_activarse() for regla in reglas)
            ):
                return Response(
                    {
                        'detail': (
                            'No se puede activar: el documento debe estar procesado '
                            'y debe existir una disposición aprobada y completa.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            VersionReglamento.objects.filter(
                estado=VersionReglamento.Estado.VIGENTE,
            ).exclude(pk=version.pk).update(
                estado=VersionReglamento.Estado.REEMPLAZADA,
            )
            version.estado = VersionReglamento.Estado.VIGENTE
            version.activada_en = timezone.now()
            version.activada_por = request.user
            version.save(update_fields=['estado', 'activada_en', 'activada_por'])
            HistorialUsuario.objects.create(
                usuario=request.user,
                historial_accion='Modificación',
                historial_detalle=f'Activó la versión {version.pk} del reglamento institucional.',
            )
        return Response({'mensaje': 'La versión aprobada ahora está vigente.'})

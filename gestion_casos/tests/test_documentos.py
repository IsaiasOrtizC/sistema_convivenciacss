"""Carga de documentos institucionales (reglamento y protocolos)."""

from contextlib import nullcontext
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase
from gestion_casos.controllers.documento_controller import gestion_documentos_view
from gestion_casos.models import DocumentoInstitucional, VersionReglamento
from gestion_casos.reglamento import DependenciaOCRNoDisponible
from reportlab.pdfgen import canvas


class ReglamentoUploadViewTests(SimpleTestCase):
    def make_pdf(self, text=None):
            contenido = BytesIO()
            documento = canvas.Canvas(contenido)
            if text:
                documento.drawString(72, 720, text)
            documento.save()
            return contenido.getvalue()

    def make_pdf_pages(self, texts):
            contenido = BytesIO()
            documento = canvas.Canvas(contenido)
            for text in texts:
                if text:
                    documento.drawString(72, 720, text)
                documento.showPage()
            documento.save()
            return contenido.getvalue()

    def make_upload_request(self, filename, contents, content_type='application/pdf'):
        request = RequestFactory().post(
            '/documentos/',
            data={
                'tipo_documento': 'Reglamento',
                'titulo': 'Reglamento de prueba',
                'archivo': SimpleUploadedFile(
                    filename, contents, content_type=content_type,
                ),
            },
        )
        request.session = {'usuario_id': 1, 'usuario_rol': 'Administrador'}
        return request

    def test_upload_rejects_non_pdf_extension_before_storage(self):
        request = self.make_upload_request('document.exe', b'not pdf')
        with (
            patch('gestion_casos.controllers.documento_controller.messages.error'),
            patch.object(DocumentoInstitucional.objects, 'create') as create_doc,
        ):
            response = gestion_documentos_view(request)
        self.assertEqual(response.status_code, 302)
        create_doc.assert_not_called()

    def test_valid_rule_pdf_is_stored_processed_and_versioned(self):
        pdf = self.make_pdf('Norma institucional general.')
        request = self.make_upload_request('reglamento.pdf', pdf)
        documento = SimpleNamespace(
            documento_id=10,
            tipo_documento='Reglamento',
            estado_procesamiento='procesando',
            error_procesamiento='',
            texto_extraido='',
            numero_paginas=None,
            save=lambda **kwargs: None,
        )
        version = SimpleNamespace(pk=4)
        with (
            patch('gestion_casos.controllers.documento_controller.Usuario.objects.get', return_value=object()),
            patch.object(DocumentoInstitucional.objects, 'create', return_value=documento),
            patch.object(VersionReglamento.objects, 'filter') as versiones,
            patch.object(VersionReglamento.objects, 'create', return_value=version) as create_version,
            patch('gestion_casos.controllers.documento_controller.guardar_candidatas', return_value=[]),
            patch(
                'gestion_casos.controllers.documento_controller.extraer_paginas_pdf',
                return_value=['Norma institucional general.'],
            ),
            patch('gestion_casos.controllers.documento_controller.transaction.atomic', return_value=nullcontext()),
            patch('gestion_casos.controllers.documento_controller.messages.success'),
        ):
            versiones.return_value.exists.return_value = False
            versiones.return_value.order_by.return_value.values_list.return_value.first.return_value = 0
            response = gestion_documentos_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            documento.estado_procesamiento,
            DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
        )
        self.assertIn('Norma institucional general.', documento.texto_extraido)
        create_version.assert_called_once()

    def test_scanned_rule_pdf_is_stored_with_explicit_ocr_error(self):
        request = self.make_upload_request('escaneado.pdf', self.make_pdf_pages([None]))
        documento = SimpleNamespace(
            documento_id=11,
            estado_procesamiento='procesando',
            error_procesamiento='',
            save=lambda **kwargs: None,
        )
        with (
            patch('gestion_casos.controllers.documento_controller.Usuario.objects.get', return_value=object()),
            patch.object(DocumentoInstitucional.objects, 'create', return_value=documento),
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                side_effect=DependenciaOCRNoDisponible(
                    'No se encontró Tesseract en el entorno de prueba.'
                ),
            ),
            patch('gestion_casos.controllers.documento_controller.messages.error'),
        ):
            response = gestion_documentos_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            documento.estado_procesamiento,
            DocumentoInstitucional.EstadoProcesamiento.ERROR,
        )
        self.assertIn('No se encontró Tesseract', documento.error_procesamiento)

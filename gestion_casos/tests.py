from contextlib import nullcontext
from io import BytesIO
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TransactionTestCase, override_settings
from django.template.loader import render_to_string
from django.utils import timezone
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
from rest_framework.test import APIClient

from gestion_casos.reglamento import (
    DependenciaOCRNoDisponible,
    ErrorProcesamientoPDF,
    OCRSinResultados,
    detectar_reglas_candidatas,
    extraer_paginas_pdf,
)
from gestion_casos.reglamento_2026 import (
    DISPOSICIONES_REGLAMENTO_2026,
    REFERENCIAS_TITULOS_2026,
    VERSION_FUENTE_REGLAMENTO_2026,
)
from gestion_casos.views import (
    activar_version_reglamento_view,
    cambiar_estado_notificacion_view,
    cerrar_seguimiento_view,
    eliminar_caso_view,
    descargar_caso_pdf_view,
    descargar_caso_xlsx_view,
    cambiar_estado_estudiante_view,
    eliminar_estudiante_view,
    gestion_datos_publicos_view,
    eliminar_documento_view,
    gestion_documentos_view,
    marcar_notificacion_leida_view,
    _mensaje_notificacion_seguro,
    _url_caso_notificacion,
    _filtrar_casos_del_curso,
    _puede_editar_caso,
    _notificar_caso_gravisimo,
    _procesar_documento_institucional,
    _regla_notificacion_operativa,
    notificaciones_view,
    reprocesar_documento_view,
    revisar_regla_view,
    seguimiento_view,
)
from gestion_casos.models import (
    AccionSeguimiento, Administrador, DocumentoInstitucional, Inspector,
    Notificacion, PConvivencia, ProfesorJefe, ReglaInstitucional, Caso, Curso,
    Estudiante, HistorialUsuario, Involucran, Lugar, Rol, SeguimientoCaso,
    SolicitudCaso, Usuario, VersionReglamento,
)
from gestion_casos.reglamento import evaluar_reglas_para_caso


class DashboardRequirementsTests(SimpleTestCase):
    def test_dashboard_shows_period_summary_and_case_pagination(self):
        request = RequestFactory().get('/dashboard/')
        request.session = {
            'usuario_id': 1,
            'usuario_nombre': 'Administradora',
            'usuario_correo': 'admin@colegio.cl',
            'usuario_rol': 'Administrador',
        }
        request.user = AnonymousUser()
        request._messages = []

        contenido = render_to_string(
            'gestion_casos/dashboard.html',
            {
                'total_casos': 11,
                'casos_leves': 2,
                'casos_graves': 3,
                'casos_gravisimas': 1,
                'casos_recientes': [{
                    'id': 11,
                    'titulo': 'Caso reciente',
                    'fecha': None,
                    'lugar': 'Patio',
                }],
                'pagina_casos': Paginator(list(range(11)), 10).get_page(2),
                'casos_periodo': 4,
                'curso_mas_incidentes': '3° Medio A',
                'tipo_falta_frecuente': 'Grave',
                'zona_mas_conflictos': 'Patio',
                'variacion_periodo': 25.0,
                'zonas_labels_json': '[]',
                'zonas_data_json': '[]',
            },
            request=request,
        )

        self.assertIn('Resumen de los últimos 30 días', contenido)
        self.assertIn('Curso con más incidentes', contenido)
        self.assertIn('Tipo de falta más frecuente', contenido)
        self.assertIn('Zona con más conflictos', contenido)
        self.assertIn('Variación del período', contenido)
        self.assertIn('Página 2 de 2', contenido)
        self.assertIn('href="?pagina=1"', contenido)
        self.assertIn('11 casos', contenido)


class RemainingFunctionalRequirementTests(SimpleTestCase):
    def test_case_edit_permission_obeys_role_and_48_hour_boundary(self):
        creado = timezone.now()
        caso = SimpleNamespace(caso_creado_en=creado)

        self.assertTrue(_puede_editar_caso('Administrador', caso, creado + timedelta(days=5)))
        self.assertTrue(
            _puede_editar_caso('Inspector', caso, creado + timedelta(hours=48))
        )
        self.assertFalse(
            _puede_editar_caso('Inspector', caso, creado + timedelta(hours=48, seconds=1))
        )
        self.assertFalse(_puede_editar_caso('Profesor Jefe', caso, creado))

    @patch('gestion_casos.views._obtener_casos_del_curso')
    def test_teacher_filters_are_shared_with_case_exports(self, obtener_casos):
        obtener_casos.return_value = [
            {'caso_id': 1, 'fecha': date(2026, 1, 2), 'tipo_falta': 'Leve'},
            {'caso_id': 2, 'fecha': date(2026, 1, 8), 'tipo_falta': 'Grave'},
            {'caso_id': 3, 'fecha': date(2026, 1, 9), 'tipo_falta': 'Gravísima'},
        ]
        request = RequestFactory().get(
            '/mis-casos-curso/?fecha_desde=2026-01-05&fecha_hasta=2026-01-10&gravedad=Grave'
        )
        request._messages = Mock()

        casos, filtros = _filtrar_casos_del_curso(request, object())

        self.assertEqual([caso['caso_id'] for caso in casos], [2])
        self.assertEqual(filtros, {
            'fecha_desde': '2026-01-05',
            'fecha_hasta': '2026-01-10',
            'gravedad': 'Grave',
        })

    @patch('gestion_casos.views._datos_reporte_caso')
    @patch('gestion_casos.views._validar_acceso_exportacion_caso')
    def test_individual_case_exports_produce_pdf_and_safe_xlsx(
        self, validar_acceso, obtener_datos
    ):
        validar_acceso.return_value = object()
        obtener_datos.return_value = {
            'id': 31,
            'titulo': '=1+1',
            'descripcion': 'Relato del caso',
            'fecha': date(2026, 1, 2),
            'lugar': 'Patio',
            'involucrados': [{
                'identificador': 'AB013MA',
                'nombre': 'Ana Alvarez',
                'curso': '3° Medio A',
                'tipo_falta': 'Grave',
            }],
        }

        response_pdf = descargar_caso_pdf_view(
            RequestFactory().get('/casos/31/pdf/'), 31
        )
        response_xlsx = descargar_caso_xlsx_view(
            RequestFactory().get('/casos/31/xlsx/'), 31
        )

        self.assertEqual(response_pdf['Content-Type'], 'application/pdf')
        self.assertTrue(response_pdf.content.startswith(b'%PDF'))
        libro = load_workbook(BytesIO(response_xlsx.content), data_only=False)
        self.assertEqual(libro['Caso']['B3'].value, "'=1+1")
        self.assertEqual(libro['Estudiantes']['B2'].value, 'Ana Alvarez')

    @patch('gestion_casos.views.get_object_or_404')
    def test_deactivating_student_preserves_the_student_and_case_history(
        self, get_object
    ):
        student = SimpleNamespace(
            estudiante_nombre='Ana',
            estudiante_apaterno='Alvarez',
            estudiante_activo=True,
            save=Mock(),
        )
        get_object.return_value = student
        request = RequestFactory().post('/administracion/alumnos/eliminar/9/')
        request.session = {'usuario_id': 1, 'usuario_rol': 'Administrador'}
        request._messages = Mock()

        response = eliminar_estudiante_view(request, 9)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(student.estudiante_activo)
        student.save.assert_called_once_with(update_fields=['estudiante_activo'])

    @patch('gestion_casos.views.get_object_or_404')
    @patch('gestion_casos.views.Usuario.objects.filter')
    def test_profile_update_validates_and_saves_public_account_data(
        self, usuario_filter, get_object
    ):
        user = SimpleNamespace(
            pk=4,
            usuario_nombre='Antes',
            usuario_apaterno='Apellido',
            usuario_amaterno='Materno',
            usuario_correo='antes@colegio.cl',
            save=Mock(),
        )
        get_object.return_value = user
        usuario_filter.return_value.exclude.return_value.exists.return_value = False
        request = RequestFactory().post('/mis-datos/perfil/', {
            'nombre': 'Ana',
            'apaterno': 'Alvarez',
            'amaterno': 'Paz',
            'correo': 'ana@colegio.cl',
        })
        request.session = {'usuario_id': 4}
        request._messages = Mock()

        response = gestion_datos_publicos_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.usuario_nombre, 'Ana')
        self.assertEqual(user.usuario_correo, 'ana@colegio.cl')
        user.save.assert_called_once()
        self.assertEqual(request.session['usuario_nombre'], 'Ana Alvarez')


class EmptyQuerySet(list):
    def select_related(self, *args, **kwargs):
        return self

    def prefetch_related(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def order_by(self, *args, **kwargs):
        return self


class ReglamentoPDFTests(SimpleTestCase):
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

    def ocr_dependencies(self):
        import pymupdf
        import pytesseract
        from PIL import Image

        return pymupdf, pytesseract, Image, ''

    def test_extracts_text_from_selectable_pdf(self):
        with patch(
            'gestion_casos.reglamento._cargar_dependencias_ocr',
            side_effect=AssertionError('No se debe iniciar OCR para texto suficiente.'),
        ):
            paginas = extraer_paginas_pdf(
                self.make_pdf(
                    'Al alcanzar 3 anotaciones leves se debe citar al apoderado en 5 días.'
                )
            )
        self.assertIn('3 anotaciones leves', paginas[0])

    def test_scanned_pdf_uses_spanish_ocr(self):
        with (
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                return_value=self.ocr_dependencies(),
            ),
            patch(
                'pytesseract.image_to_string',
                return_value='El reglamento establece una norma escolar clara.',
            ) as ocr,
        ):
            paginas = extraer_paginas_pdf(self.make_pdf_pages([None]))
        self.assertIn('norma escolar', paginas[0])
        self.assertEqual(ocr.call_args.kwargs['lang'], 'spa')

    def test_mixed_pdf_uses_text_layer_and_ocr_per_page(self):
        texto_original = 'Página con texto seleccionable de este reglamento escolar.'
        texto_escaneado = 'Página escaneada con una segunda regla escolar.'
        contenido = self.make_pdf_pages([texto_original, None])
        with (
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                return_value=self.ocr_dependencies(),
            ),
            patch('pytesseract.image_to_string', return_value=texto_escaneado),
        ):
            paginas = extraer_paginas_pdf(contenido)
        self.assertIn('texto seleccionable', paginas[0])
        self.assertIn('segunda regla', paginas[1])

    def test_ocr_without_usable_results_is_an_error(self):
        with (
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                return_value=self.ocr_dependencies(),
            ),
            patch('pytesseract.image_to_string', return_value=''),
            self.assertRaisesRegex(OCRSinResultados, 'OCR no obtuvo texto utilizable'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages([None]))

    def test_mixed_pdf_fails_if_an_ocr_page_has_no_usable_text(self):
        contenido = self.make_pdf_pages([
            'Esta página tiene texto seleccionable suficiente para extracción.',
            None,
        ])
        with (
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                return_value=self.ocr_dependencies(),
            ),
            patch('pytesseract.image_to_string', return_value=''),
            self.assertRaisesRegex(OCRSinResultados, 'una o más páginas'),
        ):
            extraer_paginas_pdf(contenido)

    def test_missing_python_ocr_dependency_is_reported(self):
        with (
            patch(
                'gestion_casos.reglamento.importlib.import_module',
                side_effect=ModuleNotFoundError("No module named 'pymupdf'"),
            ),
            self.assertRaisesRegex(DependenciaOCRNoDisponible, 'pip install'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages([None]))

    def test_missing_tesseract_executable_is_reported(self):
        import pytesseract

        error = pytesseract.pytesseract.TesseractNotFoundError()
        with (
            patch('pytesseract.get_languages', side_effect=error),
            self.assertRaisesRegex(DependenciaOCRNoDisponible, 'No se encontró Tesseract'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages([None]))

    def test_missing_spanish_tesseract_language_is_reported(self):
        import pytesseract

        with (
            patch('pytesseract.get_languages', return_value=['eng']),
            self.assertRaisesRegex(DependenciaOCRNoDisponible, 'idioma español'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages([None]))

    def test_rejects_non_pdf_payload(self):
        with self.assertRaises(ErrorProcesamientoPDF):
            extraer_paginas_pdf(b'<html>not a PDF</html>')

    def test_rejects_empty_and_oversized_pdf(self):
        with self.assertRaisesRegex(ErrorProcesamientoPDF, 'está vacío'):
            extraer_paginas_pdf(b'')
        with override_settings(REGLAMENTO_PDF_MAX_BYTES=10):
            with self.assertRaisesRegex(ErrorProcesamientoPDF, 'supera el límite'):
                extraer_paginas_pdf(b'%PDF-0123456789')

    def test_rejects_pdf_over_configured_page_limit(self):
        with (
            override_settings(REGLAMENTO_PDF_MAX_PAGES=1),
            self.assertRaisesRegex(ErrorProcesamientoPDF, 'supera el límite de 1 página'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages(['Página uno.', 'Página dos.']))

    def test_rejects_more_ocr_pages_than_configured_without_running_ocr(self):
        with (
            override_settings(REGLAMENTO_OCR_MAX_PAGES=1),
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                side_effect=AssertionError('No se debe superar el límite OCR.'),
            ),
            self.assertRaisesRegex(ErrorProcesamientoPDF, 'límite de páginas'),
        ):
            extraer_paginas_pdf(self.make_pdf_pages([None, None]))

    def test_arbitrary_pdf_paragraphs_do_not_become_rule_proposals(self):
        self.assertEqual(
            detectar_reglas_candidatas([
                'Al alcanzar 3 anotaciones leves se debe citar al apoderado en 5 días.',
                'Ante una falta grave, la dirección revisará la situación.',
                'El título del capítulo menciona las faltas.',
            ]),
            [],
        )


class DisposicionesVerificadas2026Tests(SimpleTestCase):
    def setUp(self):
        self.reglas = {
            regla['clave']: regla
            for regla in DISPOSICIONES_REGLAMENTO_2026
        }

    def test_classification_definitions_are_explicit_and_traceable(self):
        for clave, categoria, cita in (
            (
                'clasificacion-leve',
                'Leve',
                'que no afectan a otros miembros de la comunidad educativa.',
            ),
            (
                'clasificacion-grave',
                'Grave',
                'deterioren intencionalmente la infraestructura o materiales del establecimiento.',
            ),
            (
                'clasificacion-gravisima',
                'Gravísima',
                'También aquellas acciones que constituyan delito.',
            ),
        ):
            regla = self.reglas[clave]
            self.assertEqual(regla['categoria_falta'], categoria)
            self.assertIn(cita, regla['evidencia_textual'])
            self.assertEqual(regla['pagina_impresa'], 48)
            self.assertEqual(regla['pagina_pdf'], 49)
            self.assertEqual(
                regla['estado_cantidad'],
                ReglaInstitucional.EstadoCantidad.NO_APLICA,
            )
        self.assertIn('no traer la agenda', self.reglas['clasificacion-leve']['conducta_condicion'])
        self.assertIn('fumar dentro del Colegio', self.reglas['clasificacion-grave']['conducta_condicion'])
        self.assertIn('portar o tener armas', self.reglas['clasificacion-gravisima']['conducta_condicion'])
        self.assertEqual(
            (
                self.reglas['clasificacion-leve']['pagina_impresa_hasta'],
                self.reglas['clasificacion-leve']['pagina_pdf_hasta'],
            ),
            (52, 53),
        )

    def test_only_explicit_annotation_thresholds_are_loaded(self):
        tres = self.reglas['leve-tres-anotaciones']
        cinco = self.reglas['leve-cinco-anotaciones']
        self.assertEqual(
            (tres['cantidad_minima'], tres['unidad_umbral']),
            (3, ReglaInstitucional.UnidadUmbral.ANOTACIONES),
        )
        self.assertEqual(
            (cinco['cantidad_minima'], cinco['unidad_umbral']),
            (5, ReglaInstitucional.UnidadUmbral.ANOTACIONES),
        )
        self.assertNotIn(
            ReglaInstitucional.UnidadUmbral.FALTAS,
            [tres['unidad_umbral'], cinco['unidad_umbral']],
        )
        self.assertNotIn('umbral_casos', tres)
        self.assertNotIn('umbral_casos', cinco)
        self.assertEqual(
            tres['medida_asociada'],
            'Conversación del Profesor Jefe con el alumno; registrar la entrevista '
            'y firma en el formato respectivo.',
        )
        self.assertIn('Citación del Profesor Jefe al apoderado', cinco['medida_asociada'])
        self.assertEqual(
            tres['tipo_medida'],
            ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
        )

    def test_annotation_threshold_boundary_scenarios_are_descriptive_only(self):
        reglas_por_umbral = {
            regla['cantidad_minima']: regla
            for regla in self.reglas.values()
            if regla.get('unidad_umbral') == ReglaInstitucional.UnidadUmbral.ANOTACIONES
        }
        escenarios = (
            (2, set()),
            (3, {'leve-tres-anotaciones'}),
            (4, {'leve-tres-anotaciones'}),
            (5, {'leve-tres-anotaciones', 'leve-cinco-anotaciones'}),
        )
        for cantidad, esperadas in escenarios:
            with self.subTest(cantidad=cantidad):
                candidatas = {
                    regla['clave']
                    for umbral, regla in reglas_por_umbral.items()
                    if cantidad >= umbral
                }
                self.assertEqual(candidatas, esperadas)
        self.assertEqual(
            {
                clave: reglas_por_umbral[umbral]['medida_asociada']
                for umbral, clave in (
                    (3, 'leve-tres-anotaciones'),
                    (5, 'leve-cinco-anotaciones'),
                )
            },
            {
                'leve-tres-anotaciones':
                    self.reglas['leve-tres-anotaciones']['medida_asociada'],
                'leve-cinco-anotaciones':
                    self.reglas['leve-cinco-anotaciones']['medida_asociada'],
            },
        )

    def test_suspension_durations_and_exceptions_are_explicit(self):
        grave = self.reglas['grave-suspension']
        gravisima = self.reglas['gravisima-suspension']
        preventiva = self.reglas['gravisima-separacion-preventiva']
        self.assertEqual(
            (grave['duracion_minima_dias'], grave['duracion_maxima_dias']),
            (2, 3),
        )
        self.assertEqual(
            (gravisima['duracion_minima_dias'], gravisima['duracion_maxima_dias']),
            (3, 5),
        )
        self.assertEqual(
            (preventiva['duracion_minima_dias'], preventiva['duracion_maxima_dias']),
            (3, 5),
        )
        self.assertIn('riesgo', gravisima['excepciones'])
        self.assertIn('antes de concluir el debido proceso', preventiva['condiciones'])
        self.assertIn('cinco días hábiles', self.reglas['suspension-limite-general']['evidencia_textual'])
        self.assertEqual(
            self.reglas['suspension-limite-general']['unidad_duracion'],
            ReglaInstitucional.UnidadDuracion.DIAS_HABILES,
        )
        self.assertEqual(self.reglas['suspension-limite-general']['duracion_maxima_dias'], 5)
        self.assertIn('prorrogar una vez por igual periodo', self.reglas['suspension-limite-general']['evidencia_textual'])
        self.assertIn(
            'prorrogarse por cinco días adicionales',
            gravisima['evidencia_textual'],
        )
        self.assertNotEqual(
            (
                self.reglas['suspension-limite-general']['duracion_maxima_dias'],
                self.reglas['suspension-limite-general']['unidad_duracion'],
            ),
            (
                gravisima['duracion_maxima_dias'],
                gravisima['unidad_duracion'],
            ),
        )
        self.assertIn('requiere revisión humana', self.reglas['suspension-limite-general']['excepciones'])
        self.assertEqual(
            preventiva['tipo_medida'],
            ReglaInstitucional.TipoMedida.PREVENTIVA,
        )
        self.assertEqual(
            gravisima['tipo_medida'],
            ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
        )

    def test_existing_catalog_is_typed_without_adding_new_dispositions(self):
        self.assertEqual(len(self.reglas), 13)
        self.assertEqual(
            {regla['tipo_medida'] for regla in DISPOSICIONES_REGLAMENTO_2026},
            {
                ReglaInstitucional.TipoMedida.CLASIFICACION,
                ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
                ReglaInstitucional.TipoMedida.PREVENTIVA,
            },
        )
        self.assertNotIn('dialogo-formativo', self.reglas)
        self.assertNotIn('accion-reparacion', self.reglas)
        self.assertNotIn('resolucion-alternativa-conflictos', self.reglas)

    def test_unspecified_repetition_is_not_given_a_numeric_threshold(self):
        regla = self.reglas['condicionalidad-reiteracion']
        self.assertEqual(
            regla['estado_cantidad'],
            ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
        )
        self.assertNotIn('cantidad_minima', regla)
        self.assertIn('No se define cuántas', regla['excepciones'])

    def test_documentary_evidence_and_reviewable_source_are_required(self):
        self.assertTrue(DISPOSICIONES_REGLAMENTO_2026)
        for regla in DISPOSICIONES_REGLAMENTO_2026:
            self.assertTrue(regla['evidencia_textual'])
            self.assertTrue(regla['seccion_fuente'].startswith('XVIII'))
            self.assertTrue(regla['tipo_medida'])
            self.assertEqual(regla['version_fuente'], VERSION_FUENTE_REGLAMENTO_2026)
            self.assertEqual(regla['pagina_pdf'], regla['pagina_impresa'] + 1)
        self.assertEqual(
            {regla['pagina_impresa'] for regla in DISPOSICIONES_REGLAMENTO_2026},
            {48, 50, 51, 52, 53, 54, 55},
        )
        self.assertEqual(
            REFERENCIAS_TITULOS_2026['IX']['pagina_impresa'],
            32,
        )
        self.assertEqual(REFERENCIAS_TITULOS_2026['IX']['pagina_pdf'], 33)
        self.assertEqual(
            REFERENCIAS_TITULOS_2026['pagina_impresa_34']['titulo'],
            'USO DEL UNIFORME Y LA PRESENTACIÓN PERSONAL DE LOS ALUMNOS',
        )
        self.assertEqual(REFERENCIAS_TITULOS_2026['XVIII']['pagina_impresa'], 48)
        self.assertEqual(REFERENCIAS_TITULOS_2026['XVIII']['pagina_pdf'], 49)
        self.assertEqual(REFERENCIAS_TITULOS_2026['XVIII']['ultima_pagina_impresa'], 57)
        self.assertEqual(REFERENCIAS_TITULOS_2026['XVIII']['ultima_pagina_pdf'], 58)

    def test_catalogued_rules_have_explicit_amount_states_and_no_case_count_inference(self):
        claves = [regla['clave'] for regla in DISPOSICIONES_REGLAMENTO_2026]
        citas = [regla['evidencia_textual'] for regla in DISPOSICIONES_REGLAMENTO_2026]
        self.assertEqual(len(claves), len(set(claves)))
        self.assertEqual(len(citas), len(set(citas)))
        for regla in DISPOSICIONES_REGLAMENTO_2026:
            self.assertTrue(regla['evidencia_textual'])
            self.assertIn(
                regla['estado_cantidad'],
                (
                    ReglaInstitucional.EstadoCantidad.DEFINIDA,
                    ReglaInstitucional.EstadoCantidad.NO_ESPECIFICADA,
                    ReglaInstitucional.EstadoCantidad.NO_APLICA,
                ),
            )
            self.assertNotIn('umbral_casos', regla)


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
            patch('gestion_casos.views.messages.error'),
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
            patch('gestion_casos.views.Usuario.objects.get', return_value=object()),
            patch.object(DocumentoInstitucional.objects, 'create', return_value=documento),
            patch.object(VersionReglamento.objects, 'filter') as versiones,
            patch.object(VersionReglamento.objects, 'create', return_value=version) as create_version,
            patch('gestion_casos.views.guardar_candidatas', return_value=[]),
            patch(
                'gestion_casos.views.extraer_paginas_pdf',
                return_value=['Norma institucional general.'],
            ),
            patch('gestion_casos.views.transaction.atomic', return_value=nullcontext()),
            patch('gestion_casos.views.messages.success'),
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
            patch('gestion_casos.views.Usuario.objects.get', return_value=object()),
            patch.object(DocumentoInstitucional.objects, 'create', return_value=documento),
            patch(
                'gestion_casos.reglamento._cargar_dependencias_ocr',
                side_effect=DependenciaOCRNoDisponible(
                    'No se encontró Tesseract en el entorno de prueba.'
                ),
            ),
            patch('gestion_casos.views.messages.error'),
        ):
            response = gestion_documentos_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            documento.estado_procesamiento,
            DocumentoInstitucional.EstadoProcesamiento.ERROR,
        )
        self.assertIn('No se encontró Tesseract', documento.error_procesamiento)


class SeguimientoPermissionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request_with_role(self, role, method='get', path='/seguimiento/'):
        request = getattr(self.factory, method)(path, data={})
        request.session = {'usuario_id': 1, 'usuario_rol': role}
        return request

    def test_teacher_is_denied_notifications_and_followup(self):
        request = self.request_with_role('Profesor Jefe', path='/notificaciones/')
        self.assertEqual(notificaciones_view(request).status_code, 403)

    def test_document_reprocessing_requires_admin_post(self):
        request = self.request_with_role('Inspector', method='post')
        self.assertEqual(reprocesar_documento_view(request, 1).status_code, 403)
        request = self.request_with_role('Administrador')
        self.assertEqual(reprocesar_documento_view(request, 1).status_code, 403)

    def test_document_deletion_removes_proposals_and_invalidates_old_notifications(self):
        request = self.request_with_role(
            'Administrador', method='post', path='/documentos/eliminar/1/'
        )
        document = SimpleNamespace(
            pk=1,
            titulo='Reglamento anterior',
            versiones_reglamento=SimpleNamespace(count=Mock(return_value=2)),
            archivo=SimpleNamespace(
                name='documentos/reglamento.pdf',
                storage=SimpleNamespace(delete=Mock()),
            ),
            delete=Mock(),
        )
        notification_queryset = SimpleNamespace(update=Mock())
        rule_queryset = SimpleNamespace(count=Mock(return_value=316))
        document_queryset = SimpleNamespace(first=Mock(return_value=document))
        locked_documents = SimpleNamespace(
            filter=Mock(return_value=document_queryset),
        )
        with (
            patch('gestion_casos.views.transaction.atomic', return_value=nullcontext()),
            patch(
                'gestion_casos.views.DocumentoInstitucional.objects.select_for_update',
                return_value=locked_documents,
            ),
            patch(
                'gestion_casos.views.Notificacion.objects.filter',
                return_value=notification_queryset,
            ),
            patch(
                'gestion_casos.views.ReglaInstitucional.objects.filter',
                return_value=rule_queryset,
            ),
            patch('gestion_casos.views.HistorialUsuario.objects.create') as audit_log,
            patch('gestion_casos.views.messages.success') as success_message,
        ):
            response = eliminar_documento_view(request, 1)

        self.assertEqual(response.status_code, 302)
        notification_queryset.update.assert_called_once()
        self.assertIsNone(notification_queryset.update.call_args.kwargs['regla'])
        self.assertIsNone(
            notification_queryset.update.call_args.kwargs['version_reglamento']
        )
        self.assertIn('316 propuesta(s)', audit_log.call_args.kwargs['historial_detalle'])
        document.delete.assert_called_once()
        document.archivo.storage.delete.assert_called_once_with(
            'documentos/reglamento.pdf'
        )
        self.assertIn('316 propuesta(s)', success_message.call_args.args[1])

    def test_deleting_missing_document_returns_to_list_with_message(self):
        request = self.request_with_role(
            'Administrador', method='post', path='/documentos/eliminar/6/'
        )
        document_queryset = SimpleNamespace(first=Mock(return_value=None))
        locked_documents = SimpleNamespace(
            filter=Mock(return_value=document_queryset),
        )
        with (
            patch('gestion_casos.views.transaction.atomic', return_value=nullcontext()),
            patch(
                'gestion_casos.views.DocumentoInstitucional.objects.select_for_update',
                return_value=locked_documents,
            ),
            patch('gestion_casos.views.messages.info') as info_message,
        ):
            response = eliminar_documento_view(request, 6)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/documentos/')
        info_message.assert_called_once()

    def test_document_deletion_confirmation_is_rendered_by_the_page(self):
        rendered = render_to_string(
            'gestion_casos/gestion_documentos.html',
            {
                'es_administrador': True,
                'reglamentos': [],
                'protocolos': [],
                'versiones_reglamento': [],
            },
            request=self.factory.get('/documentos/'),
        )
        self.assertIn('id="deleteDocumentDialog"', rendered)
        self.assertIn('Eliminar documento y propuestas', rendered)
        self.assertNotIn('confirm(', rendered)

    def test_inspector_cannot_close_followup(self):
        request = self.request_with_role(
            'Inspector', method='post', path='/seguimiento/casos/1/estudiantes/1/cerrar/'
        )
        self.assertEqual(cerrar_seguimiento_view(request, 1, 1).status_code, 403)

    def test_non_admin_cannot_review_or_activate_rules(self):
        for role in ('PConvivencia', 'Inspector', 'Profesor Jefe'):
            with self.subTest(role=role):
                request = self.request_with_role(role, method='post')
                self.assertEqual(revisar_regla_view(request, 1).status_code, 403)
                self.assertEqual(activar_version_reglamento_view(request, 1).status_code, 403)

    def test_inspector_cannot_change_notification_state(self):
        request = self.request_with_role('Inspector', method='post', path='/notificaciones/1/estado/')
        self.assertEqual(cambiar_estado_notificacion_view(request, 1).status_code, 403)

    def test_admin_and_convivencia_can_open_notification_module(self):
        for role in ('Administrador', 'PConvivencia', 'Inspector'):
            with self.subTest(role=role):
                request = self.request_with_role(role, path='/notificaciones/')
                with (
                    patch.object(Notificacion.objects, 'filter', return_value=EmptyQuerySet()),
                    patch('gestion_casos.views._obtener_filas_seguimiento', return_value=[]),
                    patch('gestion_casos.views.render', return_value=HttpResponse('ok')),
                ):
                    response = notificaciones_view(request)
                self.assertEqual(response.status_code, 200)

    def test_legacy_followup_url_redirects_to_notifications_section(self):
        request = self.request_with_role('Inspector')
        response = seguimiento_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/notificaciones/#seguimiento')

    def test_repeating_the_same_notification_state_is_a_noop(self):
        request = self.request_with_role(
            'Administrador', method='post', path='/notificaciones/2/estado/'
        )
        request.POST = {'estado': Notificacion.Estado.ESPERA, 'motivo': 'Sin cambios'}
        same_state = SimpleNamespace(estado=Notificacion.Estado.ESPERA)
        with patch('gestion_casos.views.get_object_or_404', return_value=same_state):
            response = cambiar_estado_notificacion_view(request, 2)
        self.assertEqual(response.status_code, 302)

    def test_event_and_action_idempotency_keys_are_database_unique(self):
        self.assertTrue(Notificacion._meta.get_field('evento_clave').unique)
        self.assertTrue(AccionSeguimiento._meta.get_field('clave_idempotencia').unique)

    def test_rule_starts_pending_and_cannot_activate_without_review_fields(self):
        rule = ReglaInstitucional(
            version_id=1,
            titulo='Regla propuesta',
            evidencia_textual='Cita del documento',
            hash_origen='0' * 64,
        )
        self.assertEqual(rule.estado, ReglaInstitucional.Estado.PENDIENTE)
        self.assertFalse(rule.puede_activarse())

    def test_annotation_rule_cannot_be_automated_from_case_events(self):
        rule = ReglaInstitucional(
            version_id=1,
            titulo='Umbral de anotaciones',
            categoria_falta='Leve',
            activador=ReglaInstitucional.Activador.UMBRAL_CASOS,
            umbral_casos=3,
            accion_requerida='Revisar la situación',
            evidencia_textual='Al alcanzar 3 anotaciones leves, revisar.',
            hash_origen='1' * 64,
        )
        self.assertFalse(rule.puede_activarse())

    def test_presentation_disposition_needs_typed_and_traceable_source(self):
        rule = ReglaInstitucional(
            version_id=1,
            titulo='Disposición informativa',
            categoria_falta='Grave',
            tipo_medida=ReglaInstitucional.TipoMedida.SANCION_DISCIPLINARIA,
            solo_presentacion=True,
            medida_asociada='Suspensión para revisión humana.',
            evidencia_textual='Cita textual del Reglamento.',
            titulo_fuente='Título XVIII',
            version_fuente=VERSION_FUENTE_REGLAMENTO_2026,
            seccion_fuente='XVIII, C)',
            pagina_impresa=53,
            pagina_pdf=54,
            hash_origen='2' * 64,
        )
        self.assertTrue(rule.puede_activarse())
        rule.version_fuente = ''
        self.assertFalse(rule.puede_activarse())

    def test_legacy_case_notification_message_is_redacted_in_general_listing(self):
        notification = SimpleNamespace(
            notificacion_titulo='Nueva Bitácora Registrada',
            notificacion_mensaje='Caso asociado a: Nombre Apellido.',
        )
        self.assertNotIn(
            'Nombre Apellido',
            _mensaje_notificacion_seguro(notification),
        )

    def test_legacy_case_notification_links_to_cases_from_its_date(self):
        notification = SimpleNamespace(
            caso_id=None,
            notificacion_titulo='Nueva Bitácora Registrada',
            notificacion_fecha=timezone.make_aware(
                datetime(2026, 10, 12, 12, 30)
            ),
        )
        self.assertEqual(
            _url_caso_notificacion(notification),
            '/casos/?fecha_desde=2026-10-12&fecha_hasta=2026-10-12',
        )

    def test_case_notification_message_is_safe_and_regulation_rule_must_be_current(self):
        notification = SimpleNamespace(
            notificacion_titulo='Nuevo caso registrado',
            evento_tipo=Notificacion.TipoEvento.CASO_CREADO,
            notificacion_mensaje='Caso asociado a: Nombre Apellido.',
        )
        self.assertNotIn(
            'Nombre Apellido',
            _mensaje_notificacion_seguro(notification),
        )

        current_rule = SimpleNamespace(
            estado=ReglaInstitucional.Estado.APROBADA,
            version=SimpleNamespace(estado=VersionReglamento.Estado.VIGENTE),
            solo_presentacion=False,
            activador=ReglaInstitucional.Activador.NUEVO_CASO,
            accion_requerida='Revisar antecedentes con el estudiante.',
        )
        self.assertTrue(_regla_notificacion_operativa(current_rule))
        current_rule.activador = ReglaInstitucional.Activador.MANUAL
        self.assertFalse(_regla_notificacion_operativa(current_rule))
        current_rule.activador = ReglaInstitucional.Activador.NUEVO_CASO
        current_rule.solo_presentacion = True
        self.assertFalse(_regla_notificacion_operativa(current_rule))
        current_rule.solo_presentacion = False
        current_rule.estado = ReglaInstitucional.Estado.PENDIENTE
        self.assertFalse(_regla_notificacion_operativa(current_rule))
        current_rule.estado = ReglaInstitucional.Estado.APROBADA
        current_rule.version.estado = 'archivada'
        self.assertFalse(_regla_notificacion_operativa(current_rule))

    def test_notification_template_links_case_and_discloses_rule_evidence(self):
        regla = SimpleNamespace(
            evidencia_textual='Evidencia textual de la disposición.',
            titulo_fuente='Reglamento Interno 2026',
            seccion_fuente='Título XVIII, sección C',
            pagina_impresa=53,
            pagina_pdf=54,
        )
        notification = SimpleNamespace(
            notificacion_id=7,
            notificacion_titulo='Orientación reglamentaria',
            notificacion_mensaje='Revisar el caso conforme al procedimiento.',
            notificacion_fecha=timezone.now(),
            notificacion_leido=False,
            evento_tipo=Notificacion.TipoEvento.CASO_CREADO,
            caso_id=42,
            categoria_falta='Grave',
            categoria_css='grave',
            regla_operativa=True,
            regla=regla,
            estado=Notificacion.Estado.ESPERA,
            get_estado_display=lambda: 'En espera de resolución',
            fecha_limite=None,
            version_reglamento=SimpleNamespace(numero=1),
            historial_estados=SimpleNamespace(all=lambda: []),
        )
        rendered = render_to_string(
            'gestion_casos/notificaciones.html',
            {
                'notificaciones': [notification],
                'puede_gestionar': False,
                'estados_notificacion': [],
                'hoy': timezone.localdate(),
                'filas_seguimiento': [],
                'filtro_estado': '',
            },
            request=RequestFactory().get('/notificaciones/'),
        )

        self.assertIn('href="/casos/42/"', rendered)
        self.assertIn('Revisar el caso conforme al procedimiento.', rendered)
        self.assertIn('Evidencia textual de la disposición.', rendered)
        self.assertIn('Título XVIII, sección C', rendered)
        self.assertNotIn('Gestionar estado', rendered)


class PersistentRuleEvaluationTests(TransactionTestCase):
    unmanaged_models = (
        Rol, Usuario, Curso, Estudiante, Lugar, Caso, Involucran,
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in cls.unmanaged_models:
                    schema_editor.create_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()

    @classmethod
    def tearDownClass(cls):
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in reversed(cls.unmanaged_models):
                    schema_editor.delete_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()
        super().tearDownClass()

    def setUp(self):
        with connection.cursor() as cursor:
            for table in (
                'involucran', 'caso', 'estudiante', 'curso', 'lugar', 'usuario', 'rol',
            ):
                cursor.execute(f'DELETE FROM {table}')
        self.role = Rol.objects.create(rol_nombre='PConvivencia')
        self.user = Usuario.objects.create(
            usuario_nombre='Equipo',
            usuario_apaterno='Convivencia',
            usuario_amaterno='',
            usuario_correo='convivencia@example.test',
            usuario_contrasena='not-a-real-password',
            rol=self.role,
        )
        self.course = Curso.objects.create(curso_grado='3° Básica', curso_letra='A')
        self.student = Estudiante.objects.create(
            estudiante_nombre='Estudiante',
            estudiante_apaterno='Ejemplo',
            estudiante_amaterno='',
            curso=self.course,
            estudiante_numero_lista=5,
        )
        self.place = Lugar.objects.create(lugar_nombre='Patio')
        self.case = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Descripción de prueba',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=self.case,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        self.document = DocumentoInstitucional.objects.create(
            tipo_documento='Reglamento',
            titulo='Reglamento de prueba',
            archivo='',
            usuario=self.user,
            estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
            texto_extraido='Ante una falta leve, realizar seguimiento.',
        )
        self.version = VersionReglamento.objects.create(
            documento=self.document,
            numero=1,
            estado=VersionReglamento.Estado.VIGENTE,
            creada_por=self.user,
        )
        self.rule = ReglaInstitucional.objects.create(
            version=self.version,
            titulo='Seguimiento de falta leve',
            categoria_falta='Leve',
            activador=ReglaInstitucional.Activador.UMBRAL_CASOS,
            umbral_casos=1,
            accion_requerida='Realizar seguimiento',
            plazo_dias=2,
            plazo_desde=ReglaInstitucional.ReferenciaPlazo.EVENTO,
            responsable_rol=ReglaInstitucional.RolResponsable.CONVIVENCIA,
            evidencia_textual='Ante una falta leve, realizar seguimiento.',
            referencia_origen='Página 1',
            estado=ReglaInstitucional.Estado.APROBADA,
            hash_origen='a' * 64,
        )

    def test_approved_rule_generates_persistent_notification_once_per_event(self):
        primero = evaluar_reglas_para_caso(
            self.case, [self.student], self.user,
        )
        segundo = evaluar_reglas_para_caso(
            self.case, [self.student], self.user,
        )
        momento_actualizacion = timezone.now() + timedelta(days=5)
        tercero = evaluar_reglas_para_caso(
            self.case,
            [self.student],
            self.user,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
            fecha_evento=momento_actualizacion,
        )
        cuarto = evaluar_reglas_para_caso(
            self.case,
            [self.student],
            self.user,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
            fecha_evento=momento_actualizacion,
        )
        self.assertEqual((primero, segundo, tercero, cuarto), (1, 0, 1, 0))

        notificacion = Notificacion.objects.get(
            regla=self.rule,
            evento_tipo=Notificacion.TipoEvento.CASO_CREADO,
        )
        self.assertEqual(notificacion.version_reglamento, self.version)
        self.assertEqual(notificacion.regla.evidencia_textual, self.rule.evidencia_textual)
        self.assertEqual(notificacion.evento_tipo, Notificacion.TipoEvento.CASO_CREADO)
        self.assertEqual(notificacion.estado, Notificacion.Estado.ESPERA)
        self.assertEqual(
            notificacion.fecha_limite,
            timezone.localdate() + timedelta(days=2),
        )
        self.assertEqual(
            AccionSeguimiento.objects.filter(
                seguimiento__caso=self.case,
                regla=self.rule,
            ).count(),
            2,
        )
        self.assertEqual(notificacion.historial_estados.count(), 1)
        actualizacion = Notificacion.objects.get(
            regla=self.rule,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
        )
        self.assertEqual(
            actualizacion.fecha_limite,
            timezone.localtime(momento_actualizacion).date() + timedelta(days=2),
        )

    def test_presentation_only_rule_is_never_applied_automatically(self):
        self.rule.solo_presentacion = True
        self.rule.medida_asociada = 'Suspensión solo para revisión humana.'
        self.rule.save(update_fields=['solo_presentacion', 'medida_asociada'])

        self.assertEqual(
            evaluar_reglas_para_caso(self.case, [self.student], self.user),
            0,
        )
        self.assertEqual(Notificacion.objects.count(), 0)
        self.assertEqual(AccionSeguimiento.objects.count(), 0)

    def test_annotation_evidence_cannot_trigger_case_automation(self):
        self.rule.evidencia_textual = 'Al alcanzar 3 anotaciones leves, revisar.'
        self.rule.umbral_anotaciones = 3
        self.rule.save(update_fields=['evidencia_textual', 'umbral_anotaciones'])
        self.assertFalse(self.rule.puede_activarse())

    def test_annotation_threshold_can_be_explicitly_mapped_to_case_count(self):
        self.rule.activador = ReglaInstitucional.Activador.UMBRAL_CASOS
        self.rule.umbral_casos = 3
        self.rule.umbral_anotaciones = 3
        self.rule.unidad_umbral = ReglaInstitucional.UnidadUmbral.ANOTACIONES
        self.rule.cantidad_minima = 3
        self.rule.evidencia_textual = 'Al alcanzar 3 anotaciones leves, revisar.'
        self.rule.save(update_fields=[
            'activador',
            'umbral_casos',
            'umbral_anotaciones',
            'unidad_umbral',
            'cantidad_minima',
            'evidencia_textual',
        ])
        self.assertTrue(self.rule.puede_activarse())

    def test_three_and_five_annotation_thresholds_use_distinct_cases_by_severity(self):
        self.rule.estado = ReglaInstitucional.Estado.RECHAZADA
        self.rule.save(update_fields=['estado'])
        reglas_umbral = {}
        for umbral in (3, 5):
            reglas_umbral[umbral] = ReglaInstitucional.objects.create(
                version=self.version,
                titulo=f'Revisión humana al alcanzar {umbral} anotaciones leves',
                categoria_falta='Leve',
                activador=ReglaInstitucional.Activador.UMBRAL_CASOS,
                umbral_casos=umbral,
                umbral_anotaciones=umbral,
                unidad_umbral=ReglaInstitucional.UnidadUmbral.ANOTACIONES,
                cantidad_minima=umbral,
                estado_cantidad=ReglaInstitucional.EstadoCantidad.DEFINIDA,
                accion_requerida=(
                    'Presentar la disposición y su evidencia al personal autorizado; '
                    'no aplicar una sanción automáticamente.'
                ),
                evidencia_textual=f'{umbral} anotaciones negativas por faltas leves.',
                referencia_origen='Título XVIII, 3.A',
                estado=ReglaInstitucional.Estado.APROBADA,
                hash_origen=f'{umbral}' * 64,
            )
            self.assertTrue(reglas_umbral[umbral].puede_activarse())

        for categoria in ('Grave', 'Gravísima'):
            caso_otra_gravedad = Caso.objects.create(
                caso_fecha=timezone.localdate(),
                caso_descripcion=(
                    f'[Registro] - Caso {categoria} no suma anotaciones leves'
                ),
                usuario=self.user,
                lugar=self.place,
            )
            Involucran.objects.create(
                caso=caso_otra_gravedad,
                estudiante=self.student,
                tipo_falta=categoria,
            )
            evaluar_reglas_para_caso(
                caso_otra_gravedad,
                [self.student],
                self.user,
            )
        self.assertEqual(Notificacion.objects.count(), 0)

        caso_dos = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Segunda falta leve',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=caso_dos,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        evaluar_reglas_para_caso(caso_dos, [self.student], self.user)
        evaluar_reglas_para_caso(
            caso_dos,
            [self.student],
            self.user,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
        )
        self.assertEqual(Notificacion.objects.count(), 0)

        caso_tres = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Tercera falta leve',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=caso_tres,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        evaluar_reglas_para_caso(caso_tres, [self.student], self.user)
        self.assertTrue(
            Notificacion.objects.filter(regla=reglas_umbral[3]).exists()
        )
        self.assertFalse(
            Notificacion.objects.filter(regla=reglas_umbral[5]).exists()
        )
        notificacion_umbral_3 = Notificacion.objects.get(
            regla=reglas_umbral[3],
            caso=caso_tres,
        )
        self.assertEqual(
            notificacion_umbral_3.regla.evidencia_textual,
            '3 anotaciones negativas por faltas leves.',
        )
        self.assertIn('no aplicar una sanción automáticamente', notificacion_umbral_3.notificacion_mensaje)

        caso_cuatro = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Cuarta falta leve',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=caso_cuatro,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        evaluar_reglas_para_caso(caso_cuatro, [self.student], self.user)
        self.assertFalse(
            Notificacion.objects.filter(regla=reglas_umbral[5]).exists()
        )

        caso_cinco = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Quinta falta leve',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=caso_cinco,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        evaluar_reglas_para_caso(caso_cinco, [self.student], self.user)
        self.assertTrue(
            Notificacion.objects.filter(
                regla=reglas_umbral[5],
                caso=caso_cinco,
            ).exists()
        )
        self.assertEqual(
            Involucran.objects.filter(
                estudiante=self.student,
                tipo_falta='Leve',
            ).values('caso_id').distinct().count(),
            5,
        )

    def test_case_threshold_counts_distinct_cases_not_update_events(self):
        self.rule.umbral_casos = 2
        self.rule.save(update_fields=['umbral_casos'])

        creadas = evaluar_reglas_para_caso(
            self.case, [self.student], self.user,
            evento_tipo=Notificacion.TipoEvento.CASO_CREADO,
        )
        actualizadas = evaluar_reglas_para_caso(
            self.case, [self.student], self.user,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
            fecha_evento=timezone.now() + timedelta(days=1),
        )
        self.assertEqual((creadas, actualizadas), (0, 0))
        self.assertEqual(
            Involucran.objects.filter(
                estudiante=self.student,
                tipo_falta='Leve',
            ).values('caso_id').distinct().count(),
            1,
        )
        self.assertEqual(Notificacion.objects.count(), 0)

        segundo_caso = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Registro] - Segundo caso de prueba',
            usuario=self.user,
            lugar=self.place,
        )
        Involucran.objects.create(
            caso=segundo_caso,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        self.assertEqual(
            evaluar_reglas_para_caso(segundo_caso, [self.student], self.user),
            1,
        )

    def test_pending_rule_does_not_affect_operational_case_evaluation(self):
        self.rule.estado = ReglaInstitucional.Estado.PENDIENTE
        self.rule.save(update_fields=['estado'])

        self.assertEqual(
            evaluar_reglas_para_caso(self.case, [self.student], self.user),
            0,
        )
        self.assertEqual(Notificacion.objects.count(), 0)
        self.assertEqual(AccionSeguimiento.objects.count(), 0)

    def test_review_preserves_catalogued_annotation_threshold(self):
        self.version.estado = VersionReglamento.Estado.BORRADOR
        self.version.save(update_fields=['estado'])
        for cantidad, clave in (
            (3, 'leve-tres-anotaciones'),
            (5, 'leve-cinco-anotaciones'),
        ):
            with self.subTest(cantidad=cantidad):
                disposicion = next(
                    item for item in DISPOSICIONES_REGLAMENTO_2026
                    if item['clave'] == clave
                )
                regla = ReglaInstitucional.objects.create(
                    version=self.version,
                    titulo=disposicion['titulo'],
                    categoria_falta=disposicion['categoria_falta'],
                    tipo_medida=disposicion['tipo_medida'],
                    activador=ReglaInstitucional.Activador.MANUAL,
                    solo_presentacion=True,
                    unidad_umbral=disposicion['unidad_umbral'],
                    cantidad_minima=cantidad,
                    estado_cantidad=disposicion['estado_cantidad'],
                    medida_asociada=disposicion['medida_asociada'],
                    evidencia_textual=disposicion['evidencia_textual'],
                    titulo_fuente='Título XVIII',
                    version_fuente=VERSION_FUENTE_REGLAMENTO_2026,
                    seccion_fuente=disposicion['seccion_fuente'],
                    pagina_impresa=disposicion['pagina_impresa'],
                    pagina_pdf=disposicion['pagina_pdf'],
                    estado=ReglaInstitucional.Estado.PENDIENTE,
                    hash_origen=f'{cantidad}' * 64,
                )
                request = RequestFactory().post(
                    f'/documentos/reglas/{regla.pk}/revisar/',
                    {
                        'titulo': regla.titulo,
                        'estado': ReglaInstitucional.Estado.APROBADA,
                        'tipo_medida': regla.tipo_medida,
                        'activador': ReglaInstitucional.Activador.MANUAL,
                        'categoria_falta': regla.categoria_falta,
                        'umbral_casos': '',
                        'umbral_anotaciones': '',
                        'accion_requerida': '',
                        'plazo_dias': '',
                        'plazo_desde': ReglaInstitucional.ReferenciaPlazo.SIN_DEFINIR,
                        'responsable_rol': '',
                    },
                )
                request.session = {
                    'usuario_id': self.user.pk,
                    'usuario_rol': 'Administrador',
                }
                with patch('gestion_casos.views.messages.success'):
                    response = revisar_regla_view(request, regla.pk)

                self.assertEqual(response.status_code, 302)
                regla.refresh_from_db()
                self.assertEqual(regla.cantidad_minima, cantidad)
                self.assertEqual(regla.umbral_anotaciones, cantidad)
                self.assertTrue(regla.puede_activarse())

    def test_reprocessing_preserves_existing_versions_and_approved_rules(self):
        texto_nuevo = 'Texto de reglamento recuperado mediante OCR.'
        with patch(
            'gestion_casos.views.extraer_paginas_pdf',
            return_value=[texto_nuevo],
        ):
            propuestas = _procesar_documento_institucional(
                self.document,
                b'%PDF-contenido-de-prueba',
                self.user,
            )
        self.assertEqual(propuestas, 0)
        self.document.refresh_from_db()
        self.version.refresh_from_db()
        self.rule.refresh_from_db()
        self.assertEqual(self.document.texto_extraido, texto_nuevo)
        self.assertEqual(VersionReglamento.objects.filter(documento=self.document).count(), 1)
        self.assertEqual(self.version.estado, VersionReglamento.Estado.VIGENTE)
        self.assertEqual(self.rule.estado, ReglaInstitucional.Estado.APROBADA)
        self.assertEqual(self.rule.evidencia_textual, 'Ante una falta leve, realizar seguimiento.')

    def test_pending_rule_requires_admin_review_before_version_activation(self):
        self.rule.estado = ReglaInstitucional.Estado.PENDIENTE
        self.rule.save(update_fields=['estado'])
        self.version.estado = VersionReglamento.Estado.BORRADOR
        self.version.save(update_fields=['estado'])
        admin_role = Rol.objects.create(rol_nombre='Administrador')
        admin = Usuario.objects.create(
            usuario_nombre='Admin',
            usuario_apaterno='Prueba',
            usuario_amaterno='',
            usuario_correo='admin@example.test',
            usuario_contrasena='not-a-real-password',
            rol=admin_role,
        )
        data = {
            'titulo': self.rule.titulo,
            'estado': ReglaInstitucional.Estado.APROBADA,
            'activador': ReglaInstitucional.Activador.MANUAL,
            'categoria_falta': 'Leve',
            'umbral_casos': '',
            'umbral_anotaciones': '',
            'accion_requerida': 'Realizar seguimiento',
            'plazo_dias': '',
            'plazo_desde': ReglaInstitucional.ReferenciaPlazo.SIN_DEFINIR,
            'responsable_rol': '',
        }
        request = RequestFactory().post('/documentos/reglas/1/revisar/', data)
        request.session = {'usuario_id': admin.pk, 'usuario_rol': 'Administrador'}
        with patch('gestion_casos.views.messages.success'):
            response = revisar_regla_view(request, self.rule.pk)
        self.assertEqual(response.status_code, 302)
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.estado, ReglaInstitucional.Estado.APROBADA)

        request = RequestFactory().post('/documentos/versiones/1/activar/')
        request.session = {'usuario_id': admin.pk, 'usuario_rol': 'Administrador'}
        with patch('gestion_casos.views.messages.success'):
            response = activar_version_reglamento_view(request, self.version.pk)
        self.assertEqual(response.status_code, 302)
        self.version.refresh_from_db()
        self.assertEqual(self.version.estado, VersionReglamento.Estado.VIGENTE)

    def test_pending_rule_does_not_generate_notifications(self):
        self.rule.estado = ReglaInstitucional.Estado.PENDIENTE
        self.rule.save(update_fields=['estado'])
        self.assertEqual(
            evaluar_reglas_para_caso(self.case, [self.student], self.user),
            0,
        )
        self.assertEqual(Notificacion.objects.count(), 0)

    def test_reading_notification_does_not_resolve_or_remove_it(self):
        evaluar_reglas_para_caso(self.case, [self.student], self.user)
        notification = Notificacion.objects.get(regla=self.rule)
        request = RequestFactory().post(f'/notificaciones/{notification.pk}/leer/')
        request.session = {'usuario_id': self.user.pk, 'usuario_rol': 'Inspector'}
        response = marcar_notificacion_leida_view(request, notification.pk)
        self.assertEqual(response.status_code, 302)
        notification.refresh_from_db()
        self.assertTrue(notification.notificacion_leido)
        self.assertEqual(notification.estado, Notificacion.Estado.ESPERA)
        self.assertTrue(Notificacion.objects.filter(pk=notification.pk).exists())

    def test_progress_uses_real_required_actions_and_case_closure_is_audited(self):
        evaluar_reglas_para_caso(self.case, [self.student], self.user)
        seguimiento = SeguimientoCaso.objects.get(caso=self.case, estudiante=self.student)
        accion = seguimiento.acciones.get()
        self.assertEqual(seguimiento.porcentaje_avance, 0)

        accion.estado = AccionSeguimiento.Estado.COMPLETADA
        accion.completada_en = timezone.now()
        accion.save(update_fields=['estado', 'completada_en'])
        self.assertEqual(seguimiento.porcentaje_avance, 100)

        request = RequestFactory().post(
            '/seguimiento/casos/1/estudiantes/1/cerrar/',
            {'motivo': 'Acciones verificadas'},
        )
        request.session = {'usuario_id': self.user.pk, 'usuario_rol': 'PConvivencia'}
        response = cerrar_seguimiento_view(request, self.case.pk, self.student.pk)
        self.assertEqual(response.status_code, 302)
        seguimiento.refresh_from_db()
        self.assertEqual(seguimiento.estado, SeguimientoCaso.Estado.SOLUCIONADO)
        self.assertEqual(seguimiento.historial.count(), 2)
        notificacion = Notificacion.objects.get(regla=self.rule)
        self.assertEqual(notificacion.estado, Notificacion.Estado.SOLUCIONADO)
        self.assertEqual(notificacion.historial_estados.count(), 2)


class JwtApiTests(TransactionTestCase):
    unmanaged_models = (
        Rol, Curso, Usuario, Estudiante, Lugar, Caso, Involucran,
        Administrador, Inspector, PConvivencia, ProfesorJefe,
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in cls.unmanaged_models:
                    schema_editor.create_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()

    @classmethod
    def tearDownClass(cls):
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in reversed(cls.unmanaged_models):
                    schema_editor.delete_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()
        super().tearDownClass()

    def setUp(self):
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM usuario')
            cursor.execute('DELETE FROM rol')
        self.role = Rol.objects.create(rol_nombre='PConvivencia')
        self.user = Usuario.objects.create(
            usuario_nombre='Equipo',
            usuario_apaterno='Convivencia',
            usuario_amaterno='',
            usuario_correo='convivencia@example.test',
            usuario_contrasena=make_password('ConviData-segura-2026'),
            usuario_primer_ingreso=False,
            rol=self.role,
        )
        self.client = APIClient()

    def test_profile_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/me/')
        self.assertEqual(response.status_code, 401)

    def test_temporary_password_accounts_cannot_obtain_tokens(self):
        self.user.usuario_primer_ingreso = True
        self.user.save(update_fields=['usuario_primer_ingreso'])

        response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_token_authenticates_user_and_returns_identity_and_role(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.assertEqual(token_response.status_code, 200)
        self.assertIn('access', token_response.data)
        self.assertIn('refresh', token_response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        response = self.client.get('/api/v1/me/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': self.user.pk,
            'nombre': 'Equipo',
            'apellido_paterno': 'Convivencia',
            'apellido_materno': '',
            'correo': 'convivencia@example.test',
            'rol': 'PConvivencia',
        })

    def test_refresh_endpoint_issues_an_access_token(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        refresh_response = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': token_response.data['refresh']},
            format='json',
        )

        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn('access', refresh_response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh_response.data['access']}"
        )
        self.assertEqual(self.client.get('/api/v1/me/').status_code, 200)

    def test_invalid_passwords_reach_the_existing_account_lock_threshold(self):
        for _ in range(5):
            response = self.client.post(
                '/api/auth/token/',
                {
                    'correo': self.user.usuario_correo,
                    'contrasena': 'incorrecta',
                },
                format='json',
            )
            self.assertEqual(response.status_code, 401)

        self.user.refresh_from_db()
        self.assertTrue(self.user.usuario_bloqueado)
        response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_refresh_and_access_are_rejected_after_account_is_deactivated(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.user.usuario_activo = False
        self.user.save(update_fields=['usuario_activo'])

        refresh_response = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': token_response.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, 403)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        self.assertEqual(self.client.get('/api/v1/me/').status_code, 401)


class CaseApprovalWorkflowTests(TransactionTestCase):
    unmanaged_models = (
        Rol, Curso, Usuario, Estudiante, Lugar, Caso, Involucran, ProfesorJefe,
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in cls.unmanaged_models:
                    schema_editor.create_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()

    @classmethod
    def tearDownClass(cls):
        constraints_were_enabled = connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                for model in reversed(cls.unmanaged_models):
                    schema_editor.delete_model(model)
        finally:
            if constraints_were_enabled:
                connection.enable_constraint_checking()
        super().tearDownClass()

    def setUp(self):
        with connection.cursor() as cursor:
            for table in (
                'involucran', 'caso', 'estudiante', 'profesorjefe',
                'usuario', 'lugar', 'curso', 'rol',
            ):
                cursor.execute(f'DELETE FROM {table}')

        self.teacher_role = Rol.objects.create(rol_nombre='Profesor Jefe')
        self.reviewer_role = Rol.objects.create(rol_nombre='Inspector')
        self.course = Curso.objects.create(
            curso_grado='3° Básica',
            curso_letra='A',
        )
        self.other_course = Curso.objects.create(
            curso_grado='3° Básica',
            curso_letra='B',
        )
        self.teacher = Usuario.objects.create(
            usuario_nombre='Profesora',
            usuario_apaterno='Curso',
            usuario_amaterno='',
            usuario_correo='profesora@example.test',
            usuario_contrasena='not-a-real-password',
            usuario_primer_ingreso=False,
            rol=self.teacher_role,
        )
        self.reviewer = Usuario.objects.create(
            usuario_nombre='Inspector',
            usuario_apaterno='Revisor',
            usuario_amaterno='',
            usuario_correo='inspector@example.test',
            usuario_contrasena='not-a-real-password',
            usuario_primer_ingreso=False,
            rol=self.reviewer_role,
        )
        ProfesorJefe.objects.create(
            profesor_nombre='Profesora',
            profesor_apaterno='Curso',
            profesor_amaterno='',
            curso=self.course,
            usuario=self.teacher,
        )
        self.student = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Ejemplo',
            estudiante_amaterno='',
            curso=self.course,
            estudiante_numero_lista=4,
        )
        self.place = Lugar.objects.create(lugar_nombre='Patio')

    def _set_session(self, client, usuario, rol):
        session = client.session
        session['usuario_id'] = usuario.pk
        session['usuario_rol'] = rol
        session['usuario_nombre'] = usuario.usuario_nombre
        session['primer_ingreso'] = False
        session.save()

    def _submit_report(self, course_id=None, student_id=None, new_student=False):
        self._set_session(self.client, self.teacher, 'Profesor Jefe')
        return self.client.post('/casos/nuevo/', {
            'titulo': 'Conflicto en recreo',
            'fecha': timezone.localdate().isoformat(),
            'lugar': self.place.pk,
            'descripcion': 'Descripción de prueba del incidente.',
            'tipo_falta': 'Leve',
            'alumno_nombre[]': ['Bruno' if new_student else 'Ana'],
            'alumno_apaterno[]': ['Nuevo' if new_student else 'Ejemplo'],
            'alumno_amaterno[]': [''],
            'alumno_num_lista[]': ['8' if new_student else '4'],
            'curso[]': [course_id or self.course.pk],
            'estudiante_id[]': [
                '' if new_student else student_id or self.student.pk
            ],
        })

    def test_teacher_submission_stays_out_of_case_and_student_tables_until_approved(self):
        response = self._submit_report()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/mis-casos-curso/')
        self.assertEqual(SolicitudCaso.objects.count(), 1)
        solicitud = SolicitudCaso.objects.get()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.PENDIENTE)
        self.assertEqual(Caso.objects.count(), 0)
        self.assertEqual(Involucran.objects.count(), 0)
        self.assertEqual(Estudiante.objects.count(), 1)
        self.assertContains(
            self.client.get('/mis-casos-curso/'),
            'En espera de revisión',
        )

    def test_teacher_form_is_available_but_limited_to_assigned_course(self):
        self._set_session(self.client, self.teacher, 'Profesor Jefe')

        response = self.client.get('/casos/nuevo/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El reporte será enviado a revisión')
        self.assertContains(response, '3° Básica A')
        self.assertNotContains(response, '3° Básica B')
        self.assertContains(
            response,
            'accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg"',
        )

    def test_non_admin_can_read_user_history(self):
        HistorialUsuario.objects.create(
            usuario=self.teacher,
            historial_accion='Creación',
            historial_detalle='Registró el caso #42 para Ana Ejemplo.',
        )
        self._set_session(self.client, self.teacher, 'Profesor Jefe')

        response = self.client.get('/modulo-admin/historial-usuarios/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registró el caso #42')
        self.assertContains(response, 'Historial de usuarios')

    def test_inspector_cannot_remove_a_student_after_case_edit_deadline(self):
        caso = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Caso con dos alumnos] - Descripción.',
            caso_creado_en=timezone.now() - timedelta(hours=48, seconds=1),
            usuario=self.teacher,
            lugar=self.place,
        )
        segundo_estudiante = Estudiante.objects.create(
            estudiante_nombre='Bruno',
            estudiante_apaterno='Ejemplo',
            estudiante_amaterno='',
            curso=self.course,
            estudiante_numero_lista=5,
        )
        Involucran.objects.create(
            caso=caso,
            estudiante=self.student,
            tipo_falta='Leve',
        )
        Involucran.objects.create(
            caso=caso,
            estudiante=segundo_estudiante,
            tipo_falta='Leve',
        )
        self._set_session(self.client, self.reviewer, 'Inspector')

        response = self.client.post(
            f'/casos/editar/{caso.pk}/eliminar_estudiante/{segundo_estudiante.pk}/'
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Involucran.objects.filter(caso=caso).count(), 2)

    def test_deleting_case_notifies_its_original_creator(self):
        caso = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Caso eliminado] - Descripción.',
            usuario=self.teacher,
            lugar=self.place,
        )
        self._set_session(self.client, self.reviewer, 'Inspector')

        response = self.client.post(f'/casos/eliminar/{caso.pk}/')

        self.assertEqual(response.status_code, 302)
        notification = Notificacion.objects.get(
            usuario=self.teacher,
            notificacion_titulo='Caso eliminado',
        )
        self.assertIn(f'caso #{caso.pk}', notification.notificacion_mensaje)

    @patch('gestion_casos.tasks.enviar_alerta_caso_gravisimo.delay')
    def test_gravisimo_case_notifies_admin_and_queues_email(self, send_email):
        admin_role = Rol.objects.create(rol_nombre='Administrador')
        admin = Usuario.objects.create(
            usuario_nombre='Admin',
            usuario_apaterno='ConviData',
            usuario_amaterno='',
            usuario_correo='admin@example.test',
            usuario_contrasena='not-a-real-password',
            usuario_primer_ingreso=False,
            rol=admin_role,
        )
        caso = Caso.objects.create(
            caso_fecha=timezone.localdate(),
            caso_descripcion='[Caso gravísimo] - Descripción.',
            usuario=self.teacher,
            lugar=self.place,
        )
        request = RequestFactory().post('/casos/nuevo/')
        request.session = {'usuario_id': self.teacher.pk}

        _notificar_caso_gravisimo(request, caso, 'Gravísima', self.place)

        self.assertTrue(
            Notificacion.objects.filter(
                usuario=admin,
                caso=caso,
                notificacion_titulo=f'Caso gravísimo #{caso.pk}',
            ).exists()
        )
        send_email.assert_called_once()

    def test_approving_submission_creates_case_and_marks_request_approved(self):
        self._submit_report()
        solicitud = SolicitudCaso.objects.get()
        self._set_session(self.client, self.reviewer, 'Inspector')

        queue_response = self.client.get('/casos/pendientes/')
        self.assertEqual(queue_response.status_code, 200)
        self.assertContains(queue_response, 'Conflicto en recreo')
        self.assertContains(queue_response, 'Ana Ejemplo')

        response = self.client.post('/casos/pendientes/', {
            'solicitud_id': solicitud.pk,
            'decision': 'aprobar',
            'comentario': 'Revisado y aprobado.',
        })

        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.APROBADA)
        self.assertEqual(solicitud.revisada_por_id, self.reviewer.pk)
        self.assertEqual(Caso.objects.count(), 1)
        self.assertEqual(Involucran.objects.count(), 1)
        caso = Caso.objects.get()
        self.assertEqual(caso.usuario_id, self.teacher.pk)
        self.assertEqual(caso.caso_descripcion, '[Conflicto en recreo] - Descripción de prueba del incidente.')

    def test_new_student_is_not_created_until_the_teacher_report_is_approved(self):
        self._submit_report(new_student=True)

        self.assertEqual(Estudiante.objects.count(), 1)
        solicitud = SolicitudCaso.objects.get()
        self._set_session(self.client, self.reviewer, 'Inspector')
        self.client.post('/casos/pendientes/', {
            'solicitud_id': solicitud.pk,
            'decision': 'aprobar',
        })

        self.assertEqual(Estudiante.objects.count(), 2)
        self.assertTrue(
            Estudiante.objects.filter(
                estudiante_nombre='Bruno',
                estudiante_apaterno='Nuevo',
                curso=self.course,
            ).exists()
        )

    def test_rejected_submission_never_creates_a_case(self):
        self._submit_report()
        solicitud = SolicitudCaso.objects.get()
        self._set_session(self.client, self.reviewer, 'PConvivencia')

        response = self.client.post('/casos/pendientes/', {
            'solicitud_id': solicitud.pk,
            'decision': 'rechazar',
            'comentario': 'Faltan antecedentes.',
        })

        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.RECHAZADA)
        self.assertEqual(Caso.objects.count(), 0)

    def test_teacher_cannot_submit_a_case_for_another_course(self):
        response = self._submit_report(course_id=self.other_course.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SolicitudCaso.objects.count(), 0)
        self.assertEqual(Caso.objects.count(), 0)

    def test_teacher_cannot_access_approval_queue(self):
        self._set_session(self.client, self.teacher, 'Profesor Jefe')

        response = self.client.get('/casos/pendientes/')

        self.assertEqual(response.status_code, 403)

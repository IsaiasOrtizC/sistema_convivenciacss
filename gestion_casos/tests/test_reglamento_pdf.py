"""Lectura de PDF, OCR y disposiciones verificadas del reglamento."""

from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from gestion_casos.models import ReglaInstitucional
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
from reportlab.pdfgen import canvas


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
        pass

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

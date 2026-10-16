"""Requisitos funcionales del panel, exportaciones y perfil."""

from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone
from gestion_casos.controllers.alumno_controller import eliminar_estudiante_view
from gestion_casos.controllers.auth_casos_controller import puede_editar_caso
from gestion_casos.controllers.profile_controller import gestion_datos_publicos_view
from gestion_casos.controllers.report_controller import (
    descargar_caso_pdf_view,
    descargar_caso_xlsx_view,
)
from gestion_casos.services.caso_service import filtrar_casos_del_curso
from openpyxl import load_workbook


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

        self.assertTrue(puede_editar_caso('Administrador', caso, creado + timedelta(days=5)))
        self.assertTrue(
            puede_editar_caso('Inspector', caso, creado + timedelta(hours=48))
        )
        self.assertFalse(
            puede_editar_caso('Inspector', caso, creado + timedelta(hours=48, seconds=1))
        )
        self.assertFalse(puede_editar_caso('Profesor Jefe', caso, creado))

    @patch('gestion_casos.services.caso_service._obtener_casos_del_curso')
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

        casos, filtros = filtrar_casos_del_curso(request, object())

        self.assertEqual([caso['caso_id'] for caso in casos], [2])
        self.assertEqual(filtros, {
            'fecha_desde': '2026-01-05',
            'fecha_hasta': '2026-01-10',
            'gravedad': 'Grave',
        })

    @patch('gestion_casos.controllers.report_controller.datos_reporte_caso')
    @patch('gestion_casos.controllers.report_controller.validar_acceso_exportacion_caso')
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

    @patch('gestion_casos.controllers.alumno_controller.get_object_or_404')
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

    @patch('gestion_casos.controllers.profile_controller.get_object_or_404')
    @patch('gestion_casos.controllers.profile_controller.Usuario.objects.filter')
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

"""API REST con autenticación JWT."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.core.paginator import Paginator
from django.test import TransactionTestCase
from gestion_casos.models import (
    Administrador,
    Caso,
    Curso,
    Estudiante,
    Inspector,
    Involucran,
    Lugar,
    Notificacion,
    PConvivencia,
    ProfesorJefe,
    Rol,
    SolicitudCaso,
    Usuario,
)
from rest_framework.test import APIClient


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
            cursor.execute('DELETE FROM solicitud_caso')
            cursor.execute('DELETE FROM profesorjefe')
            cursor.execute('DELETE FROM involucran')
            cursor.execute('DELETE FROM caso')
            cursor.execute('DELETE FROM estudiante')
            cursor.execute('DELETE FROM usuario')
            cursor.execute('DELETE FROM rol')
            cursor.execute('DELETE FROM curso')
            cursor.execute('DELETE FROM lugar')
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

    def test_dashboard_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 401)

    def test_statistics_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/estadisticas/')
        self.assertEqual(response.status_code, 401)

    def test_statistics_endpoint_returns_data_and_filter_options(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        datos = {
            'total_casos': 0,
            'curso_top': 'N/A',
            'tipo_caso_top': 'N/A',
            'zona_top': 'N/A',
            'variacion_pct': 0.0,
            'gravedad_labels': ['Leve', 'Grave', 'Gravísima'],
            'gravedad_data': [0, 0, 0],
            'cursos_labels': [],
            'cursos_data': [],
            'zonas_labels': [],
            'zonas_data': [],
            'meses_labels': [],
            'mensual_data': [],
            'tabla_datos': [],
            'filtros': {
                'gravedad': '',
                'curso': '',
                'zona': '',
                'fecha_desde': '2026-01-01',
                'fecha_hasta': '2026-12-31',
            },
        }

        with patch(
            'gestion_casos.api.obtener_datos_estadisticas',
            return_value=datos,
        ):
            response = self.client.get('/api/v1/estadisticas/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_casos'], 0)
        self.assertEqual(response.data['cursos_opciones'], [{
            'id': curso.pk,
            'nombre': '3° Medio A',
        }])
        self.assertEqual(response.data['zonas_opciones'], [{
            'id': lugar.pk,
            'nombre': 'Patio',
        }])

    def test_teacher_cannot_access_statistics_api(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/estadisticas/')

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_global_search_api(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/busqueda/?q=ana')

        self.assertEqual(response.status_code, 403)

    def test_teacher_can_read_and_acknowledge_personal_notifications(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        notification = Notificacion.objects.create(
            usuario=self.user,
            notificacion_titulo='Alerta semanal',
            notificacion_mensaje='El curso superó diez casos.',
            notificacion_icono='⚠️',
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        list_response = self.client.get('/api/v1/notificaciones/')
        read_response = self.client.post(
            f'/api/v1/notificaciones/{notification.pk}/',
            {'accion': 'leer'},
            format='json',
        )
        status_response = self.client.post(
            f'/api/v1/notificaciones/{notification.pk}/',
            {'accion': 'estado', 'estado': 'revision', 'motivo': 'Revisión'},
            format='json',
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data['notificaciones']), 1)
        self.assertFalse(list_response.data['puede_gestionar'])
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(status_response.status_code, 403)

    def test_course_history_api_rejects_non_teacher_role(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/mi-curso/')

        self.assertEqual(response.status_code, 403)

    def test_teacher_course_history_returns_assigned_course_and_report_list(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        ProfesorJefe.objects.create(
            profesor_nombre='Equipo',
            profesor_apaterno='Convivencia',
            profesor_amaterno='',
            curso=curso,
            usuario=self.user,
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/mi-curso/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['curso']['nombre'], '3° Medio A')
        self.assertEqual(response.data['casos'], [])
        self.assertEqual(response.data['solicitudes'], [])

    def test_document_upload_is_restricted_to_administrators(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.post('/api/v1/documentos/', {}, format='json')

        self.assertEqual(response.status_code, 403)

    def test_cases_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/casos/')
        self.assertEqual(response.status_code, 401)

    def test_case_form_options_require_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/casos/formulario/')
        self.assertEqual(response.status_code, 401)

    def test_case_form_options_return_places_courses_and_active_students(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='',
            curso=curso,
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/casos/formulario/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['lugares'], [{
            'id': lugar.pk,
            'nombre': 'Patio',
        }])
        self.assertEqual(response.data['cursos'], [{
            'id': curso.pk,
            'nombre': '3° Medio A',
        }])
        self.assertEqual(response.data['estudiantes'][0]['id'], estudiante.pk)
        self.assertFalse(response.data['requiere_aprobacion'])

    def test_case_registration_rejects_missing_student_data(self):
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.post(
            '/api/v1/casos/nuevo/',
            {
                'titulo': 'Caso de prueba',
                'descripcion': 'Descripción suficiente.',
                'fecha': '2026-10-26',
                'lugar_id': str(lugar.pk),
                'tipo_falta': 'Leve',
                'estudiantes': [],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Agrega al menos un estudiante involucrado.')

    def test_case_registration_calls_existing_case_service(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        payload = {
            'titulo': 'Caso de prueba',
            'descripcion': 'Descripción suficiente.',
            'fecha': '2026-10-26',
            'lugar_id': lugar.pk,
            'tipo_falta': 'Leve',
            'estudiantes': [{
                'nombre': 'Ana',
                'apellido_paterno': 'Pérez',
                'apellido_materno': '',
                'numero_lista': None,
                'curso_id': curso.pk,
                'estudiante_id': None,
            }],
        }

        with patch(
            'gestion_casos.api.crear_caso_persistido',
            return_value=SimpleNamespace(pk=42),
        ) as crear_caso:
            response = self.client.post(
                '/api/v1/casos/nuevo/',
                payload,
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['id'], 42)
        crear_caso.assert_called_once()

    def test_teacher_case_registration_creates_pending_approval_request(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        ProfesorJefe.objects.create(
            profesor_nombre='Equipo',
            profesor_apaterno='Convivencia',
            profesor_amaterno='',
            curso=curso,
            usuario=self.user,
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        payload = {
            'titulo': 'Reporte de curso',
            'descripcion': 'Descripción suficiente.',
            'fecha': '2026-10-26',
            'lugar_id': lugar.pk,
            'tipo_falta': 'Leve',
            'estudiantes': [{
                'nombre': 'Ana',
                'apellido_paterno': 'Pérez',
                'apellido_materno': '',
                'numero_lista': 4,
                'curso_id': curso.pk,
                'estudiante_id': None,
            }],
        }

        response = self.client.post(
            '/api/v1/casos/nuevo/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        solicitud = SolicitudCaso.objects.get()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.PENDIENTE)
        self.assertEqual(solicitud.estudiantes[0]['curso_id'], curso.pk)
        self.assertEqual(Caso.objects.count(), 0)

    def test_pending_case_requests_require_authentication_and_approval_role(self):
        response = self.client.get('/api/v1/casos/pendientes/')
        self.assertEqual(response.status_code, 401)

        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        response = self.client.get('/api/v1/casos/pendientes/')
        self.assertEqual(response.status_code, 403)

    def test_pending_case_requests_include_student_and_course_details(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        solicitud = SolicitudCaso.objects.create(
            solicitante=self.user,
            lugar=lugar,
            fecha_evento=date(2026, 10, 26),
            titulo='Reporte de curso',
            descripcion='Descripción del reporte.',
            tipo_falta='Leve',
            estudiantes=[{
                'nombre': 'Ana',
                'apellido_paterno': 'Pérez',
                'apellido_materno': '',
                'curso_id': curso.pk,
            }],
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/casos/pendientes/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['solicitudes']), 1)
        resultado = response.data['solicitudes'][0]
        self.assertEqual(resultado['id'], solicitud.pk)
        self.assertEqual(resultado['fecha'], '2026-10-26')
        self.assertEqual(resultado['solicitante'], 'Equipo Convivencia')
        self.assertEqual(resultado['estudiantes'][0]['curso'], '3° Medio A')
        self.assertEqual(resultado['evidencia_url'], '')

    def test_rejecting_pending_case_records_review_and_comment(self):
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        solicitud = SolicitudCaso.objects.create(
            solicitante=self.user,
            lugar=lugar,
            fecha_evento=date(2026, 10, 26),
            titulo='Reporte de curso',
            descripcion='Descripción del reporte.',
            tipo_falta='Leve',
            estudiantes=[{'curso_id': 1}],
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.post(
            f'/api/v1/casos/pendientes/{solicitud.pk}/',
            {'decision': 'rechazar', 'comentario': 'Faltan antecedentes.'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.RECHAZADA)
        self.assertEqual(solicitud.comentario_revision, 'Faltan antecedentes.')
        self.assertEqual(solicitud.revisada_por_id, self.user.pk)

        response = self.client.post(
            f'/api/v1/casos/pendientes/{solicitud.pk}/',
            {'decision': 'aprobar'},
            format='json',
        )
        self.assertEqual(response.status_code, 409)

    def test_approving_pending_case_uses_existing_case_service(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        teacher_role = Rol.objects.create(rol_nombre='Profesor Jefe')
        teacher = Usuario.objects.create(
            usuario_nombre='Ana',
            usuario_apaterno='Profesora',
            usuario_amaterno='',
            usuario_correo='profesora@example.test',
            usuario_contrasena=make_password('temporal'),
            usuario_primer_ingreso=False,
            rol=teacher_role,
        )
        ProfesorJefe.objects.create(
            profesor_nombre='Ana',
            profesor_apaterno='Profesora',
            profesor_amaterno='',
            curso=curso,
            usuario=teacher,
        )
        solicitud = SolicitudCaso.objects.create(
            solicitante=teacher,
            lugar=lugar,
            fecha_evento=date(2026, 10, 26),
            titulo='Reporte de curso',
            descripcion='Descripción del reporte.',
            tipo_falta='Leve',
            estudiantes=[{
                'nombre': 'Ana',
                'apellido_paterno': 'Pérez',
                'apellido_materno': '',
                'curso_id': curso.pk,
            }],
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        with patch(
            'gestion_casos.api.crear_caso_persistido',
            return_value=SimpleNamespace(pk=51),
        ) as crear_caso:
            response = self.client.post(
                f'/api/v1/casos/pendientes/{solicitud.pk}/',
                {'decision': 'aprobar', 'comentario': 'Revisado.'},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['caso_id'], 51)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCaso.Estado.APROBADA)
        self.assertEqual(solicitud.comentario_revision, 'Revisado.')
        crear_caso.assert_called_once()

    def test_notifications_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/notificaciones/')
        self.assertEqual(response.status_code, 401)

    def test_follow_up_endpoint_requires_a_valid_bearer_token(self):
        response = self.client.get('/api/v1/seguimiento/')
        self.assertEqual(response.status_code, 401)

    def test_teacher_can_access_personal_notifications_but_not_manage_them(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        notification = Notificacion.objects.create(
            usuario=self.user,
            notificacion_titulo='Alerta de prueba',
            notificacion_mensaje='Alerta del curso.',
            notificacion_icono='⚠️',
        )

        list_response = self.client.get('/api/v1/notificaciones/')
        action_response = self.client.post(
            f'/api/v1/notificaciones/{notification.pk}/',
            {'accion': 'estado', 'estado': 'revision', 'motivo': 'Prueba'},
            format='json',
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(action_response.status_code, 403)

    def test_teacher_cannot_access_follow_up_api(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        list_response = self.client.get('/api/v1/seguimiento/')
        update_response = self.client.post(
            '/api/v1/seguimiento/acciones/1/',
            {'estado': 'completada', 'motivo': 'Cierre de prueba.'},
            format='json',
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)

    def test_cases_endpoint_returns_paginated_cases_and_courses(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Incidente] - Descripción del caso',
            lugar=lugar,
            usuario=self.user,
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/casos/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resultados'], [{
            'id': caso.pk,
            'titulo': 'Incidente',
            'descripcion': 'Descripción del caso',
            'lugar': 'Patio',
            'fecha': '2026-10-26',
            'usuario_id': self.user.pk,
        }])
        self.assertEqual(response.data['cursos'], [{
            'id': curso.pk,
            'nombre': '3° Medio A',
        }])
        self.assertEqual(response.data['total'], 1)
        self.assertFalse(response.data['tiene_siguiente'])

    def test_case_detail_endpoint_returns_details_and_edit_permissions(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='López',
            curso=curso,
        )
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Conflicto] - Descripción detallada.',
            usuario=self.user,
            lugar=lugar,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO involucran (estudiante_id, caso_id, tipo_falta) '
                'VALUES (%s, %s, %s)',
                [estudiante.pk, caso.pk, 'Grave'],
            )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get(f'/api/v1/casos/{caso.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['titulo'], 'Conflicto')
        self.assertEqual(response.data['descripcion'], 'Descripción detallada.')
        self.assertTrue(response.data['puede_editar'])
        self.assertEqual(response.data['estudiantes'][0]['curso'], '3° Medio A')
        self.assertEqual(response.data['estudiantes'][0]['tipo_falta'], 'Grave')

    def test_case_detail_forbids_teacher_without_course_assignment(self):
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Conflicto] - Descripción.',
            usuario=self.user,
            lugar=lugar,
        )
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get(f'/api/v1/casos/{caso.pk}/')

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_view_or_export_shared_case_from_other_course(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        curso_a = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        curso_b = Curso.objects.create(curso_grado='3° Medio', curso_letra='B')
        ProfesorJefe.objects.create(
            profesor_nombre='Equipo',
            profesor_apaterno='Convivencia',
            profesor_amaterno='',
            curso=curso_a,
            usuario=self.user,
        )
        estudiante_a = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='López',
            curso=curso_a,
        )
        estudiante_b = Estudiante.objects.create(
            estudiante_nombre='Benjamín',
            estudiante_apaterno='Gómez',
            estudiante_amaterno='Díaz',
            curso=curso_b,
        )
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Conflicto] - Descripción compartida.',
            usuario=self.user,
            lugar=Lugar.objects.create(lugar_nombre='Patio'),
        )
        with connection.cursor() as cursor:
            cursor.executemany(
                'INSERT INTO involucran (estudiante_id, caso_id, tipo_falta) '
                'VALUES (%s, %s, %s)',
                [
                    [estudiante_a.pk, caso.pk, 'Grave'],
                    [estudiante_b.pk, caso.pk, 'Grave'],
                ],
            )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        detalle = self.client.get(f'/api/v1/casos/{caso.pk}/')
        exportacion = self.client.get(
            f'/api/v1/casos/{caso.pk}/exportar/xlsx/'
        )
        historial = self.client.get('/api/v1/mi-curso/')

        self.assertEqual(detalle.status_code, 403)
        self.assertEqual(exportacion.status_code, 403)
        self.assertEqual(historial.status_code, 200)
        self.assertEqual(historial.data['casos'], [])

    def test_case_edit_endpoint_updates_case_and_involvement(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='López',
            curso=curso,
        )
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Original] - Descripción.',
            usuario=self.user,
            lugar=lugar,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO involucran (estudiante_id, caso_id, tipo_falta) '
                'VALUES (%s, %s, %s)',
                [estudiante.pk, caso.pk, 'Leve'],
            )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        with patch('gestion_casos.api.evaluar_reglas_para_caso'):
            response = self.client.put(
                f'/api/v1/casos/{caso.pk}/',
                {
                    'titulo': 'Actualizado',
                    'descripcion': 'Descripción actualizada.',
                    'lugar_id': lugar.pk,
                    'tipo_falta': 'Grave',
                    'estudiantes': [{
                        'id': estudiante.pk,
                        'nombre': 'Ana María',
                        'apellido_paterno': 'Pérez',
                        'apellido_materno': 'López',
                        'curso_id': curso.pk,
                    }],
                },
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        caso.refresh_from_db()
        estudiante.refresh_from_db()
        self.assertEqual(caso.caso_descripcion, '[Actualizado] - Descripción actualizada.')
        self.assertEqual(estudiante.estudiante_nombre, 'Ana María')
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT tipo_falta FROM involucran WHERE caso_id = %s',
                [caso.pk],
            )
            self.assertEqual(cursor.fetchone()[0], 'Grave')

    def test_user_admin_api_forbids_non_admin_and_lists_admin_users(self):
        response = self.client.get('/api/v1/admin/usuarios/')
        self.assertEqual(response.status_code, 401)

        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        forbidden_response = self.client.get('/api/v1/admin/usuarios/')
        self.assertEqual(forbidden_response.status_code, 403)

        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        response = self.client.get('/api/v1/admin/usuarios/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['resultados'][0]['rol'], 'Administrador')

    def test_student_admin_api_creates_filters_and_updates_students(self):
        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        response = self.client.post(
            '/api/v1/admin/estudiantes/',
            {
                'nombre': 'Ana',
                'apellido_paterno': 'Pérez',
                'apellido_materno': 'López',
                'correo': 'ana@example.test',
                'curso_id': curso.pk,
                'numero_lista': 4,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        estudiante_id = response.data['estudiante']['id']
        self.assertEqual(response.data['estudiante']['identificador'], 'AP043MA')
        response = self.client.get('/api/v1/admin/estudiantes/?busqueda=Ana')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)

        response = self.client.patch(
            f'/api/v1/admin/estudiantes/{estudiante_id}/',
            {'activo': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['estudiante']['activo'])

    def test_cases_endpoint_forbids_teacher_role(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get('/api/v1/casos/')

        self.assertEqual(response.status_code, 403)

    def test_cases_endpoint_applies_search_course_severity_and_date_filters(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='',
            curso=curso,
        )
        caso = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Incidente] - Descripción del caso',
            lugar=lugar,
            usuario=self.user,
        )
        Involucran.objects.create(
            estudiante=estudiante,
            caso=caso,
            tipo_falta='Grave',
        )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.get(
            '/api/v1/casos/',
            {
                'q': 'Descripción',
                'curso': curso.pk,
                'gravedad': 'Grave',
                'fecha_desde': '2026-10-01',
                'fecha_hasta': '2026-10-31',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([resultado['id'] for resultado in response.data['resultados']], [caso.pk])

    def test_dashboard_endpoint_returns_dashboard_metrics_and_pagination(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        datos_dashboard = {
            'total_casos': 14,
            'casos_leves': 4,
            'casos_graves': 3,
            'casos_gravisimas': 1,
            'casos_periodo': 5,
            'curso_mas_incidentes': '3° Medio A',
            'tipo_falta_frecuente': 'Grave',
            'zona_mas_conflictos': 'Patio',
            'variacion_periodo': 25.0,
            'casos_por_zona': [{'nombre': 'Patio', 'total': 3}],
            'casos_recientes': [{
                'id': 14,
                'titulo': 'Incidente reciente',
                'fecha': date(2026, 10, 26),
                'lugar': 'Patio',
            }],
            'pagina_casos': Paginator(range(11), 10).get_page(1),
        }

        with patch(
            'gestion_casos.api.obtener_datos_dashboard',
            return_value=datos_dashboard,
        ):
            response = self.client.get('/api/v1/dashboard/?pagina=1')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['metricas'], {
            'total_casos': 14,
            'casos_leves': 4,
            'casos_graves': 3,
            'casos_gravisimas': 1,
        })
        self.assertEqual(response.data['periodo']['zonas'], [
            {'nombre': 'Patio', 'total': 3},
        ])
        self.assertEqual(response.data['casos'], {
            'resultados': [{
                'id': 14,
                'titulo': 'Incidente reciente',
                'fecha': '2026-10-26',
                'lugar': 'Patio',
            }],
            'pagina': 1,
            'total_paginas': 2,
            'total': 11,
            'tiene_anterior': False,
            'tiene_siguiente': True,
        })

    def test_dashboard_endpoint_forbids_teacher_role(self):
        self.role.rol_nombre = 'Profesor Jefe'
        self.role.save(update_fields=['rol_nombre'])
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'ConviData-segura-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        with patch('gestion_casos.api.obtener_datos_dashboard') as obtener_datos:
            response = self.client.get('/api/v1/dashboard/')

        self.assertEqual(response.status_code, 403)
        obtener_datos.assert_not_called()

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

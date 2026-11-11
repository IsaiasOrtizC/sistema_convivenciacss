"""API REST con autenticación JWT."""

from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.core.paginator import Paginator
from django.test import TransactionTestCase
from resend.exceptions import ResendError
from gestion_casos.models import (
    Administrador,
    Caso,
    Curso,
    DocumentoInstitucional,
    Estudiante,
    HistorialUsuario,
    HistorialImportacionEstudiantes,
    Inspector,
    Involucran,
    Lugar,
    Notificacion,
    PConvivencia,
    ProfesorJefe,
    ReglaInstitucional,
    Rol,
    SolicitudCaso,
    Usuario,
    VersionReglamento,
    _quitar_tildes,
)
from rest_framework.test import APIClient
from openpyxl import Workbook


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
        connection.ensure_connection()
        connection.connection.create_function(
            'UNACCENT',
            1,
            lambda value: _quitar_tildes(value) if value is not None else None,
        )
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

    @patch('gestion_casos.api.solicitar_recuperacion_contrasena')
    def test_password_recovery_returns_generic_confirmation(self, solicitar_recuperacion):
        response = self.client.post(
            '/api/auth/password-recovery/',
            {'correo': 'missing@example.test'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Si el correo está registrado', response.data['mensaje'])
        solicitar_recuperacion.assert_called_once_with('missing@example.test')

    def test_password_recovery_rejects_invalid_email(self):
        response = self.client.post(
            '/api/auth/password-recovery/',
            {'correo': 'no-es-un-correo'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Ingresa una dirección de correo válida.')

    @patch('gestion_casos.controllers.auth_controller.enviar_correo_html')
    def test_password_recovery_sends_temporary_password_and_unlocks_user(self, enviar_correo):
        self.user.usuario_bloqueado = True
        self.user.usuario_intentos_fallidos = 5
        self.user.save(update_fields=['usuario_bloqueado', 'usuario_intentos_fallidos'])
        password_original = self.user.usuario_contrasena

        response = self.client.post(
            '/api/auth/password-recovery/',
            {'correo': self.user.usuario_correo},
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.usuario_primer_ingreso)
        self.assertFalse(self.user.usuario_bloqueado)
        self.assertEqual(self.user.usuario_intentos_fallidos, 0)
        self.assertNotEqual(self.user.usuario_contrasena, password_original)
        enviar_correo.assert_called_once()

    @patch('gestion_casos.controllers.auth_controller.enviar_correo_html')
    def test_password_recovery_does_not_change_password_if_email_fails(self, enviar_correo):
        enviar_correo.side_effect = ResendError(
            400,
            'validation_error',
            'No se pudo enviar',
            'Verifica la configuración de correo.',
        )
        password_original = self.user.usuario_contrasena

        response = self.client.post(
            '/api/auth/password-recovery/',
            {'correo': self.user.usuario_correo},
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.user.usuario_contrasena, password_original)
        self.assertFalse(self.user.usuario_primer_ingreso)

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

    def test_notifications_are_limited_to_the_authenticated_user(self):
        another_user = Usuario.objects.create(
            usuario_nombre='Otro',
            usuario_apaterno='Usuario',
            usuario_amaterno='',
            usuario_correo='otro@example.test',
            usuario_contrasena=make_password('ConviData-segura-2026'),
            usuario_primer_ingreso=False,
            rol=self.role,
        )
        document = DocumentoInstitucional.objects.create(
            tipo_documento='Reglamento',
            titulo='Reglamento de prueba',
            archivo='',
            usuario=another_user,
            estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
            texto_extraido='Disposición de prueba.',
        )
        version = VersionReglamento.objects.create(
            documento=document,
            numero=1,
            estado=VersionReglamento.Estado.VIGENTE,
            creada_por=another_user,
        )
        rule = ReglaInstitucional.objects.create(
            version=version,
            titulo='Regla de prueba',
            evidencia_textual='Disposición de prueba.',
            hash_origen='b' * 64,
        )
        own_notification = Notificacion.objects.create(
            usuario=self.user,
            notificacion_titulo='Aviso propio',
            notificacion_mensaje='Aviso del usuario autenticado.',
        )
        other_notification = Notificacion.objects.create(
            usuario=another_user,
            notificacion_titulo='Aviso ajeno',
            notificacion_mensaje='Aviso asignado a otro usuario.',
            regla=rule,
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
            f'/api/v1/notificaciones/{other_notification.pk}/',
            {'accion': 'leer'},
            format='json',
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in list_response.data['notificaciones']],
            [own_notification.pk],
        )
        self.assertEqual(read_response.status_code, 404)
        other_notification.refresh_from_db()
        self.assertFalse(other_notification.notificacion_leido)

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
            'puede_editar': True,
            'puede_eliminar': False,
        }])
        self.assertEqual(response.data['cursos'], [{
            'id': curso.pk,
            'nombre': '3° Medio A',
        }])
        self.assertEqual(response.data['total'], 1)
        self.assertFalse(response.data['tiene_siguiente'])

        self.role.rol_nombre = 'Inspector'
        self.role.save(update_fields=['rol_nombre'])
        inspector_response = self.client.get('/api/v1/casos/')
        self.assertTrue(inspector_response.data['resultados'][0]['puede_editar'])
        self.assertTrue(inspector_response.data['resultados'][0]['puede_eliminar'])

        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        admin_response = self.client.get('/api/v1/casos/')
        self.assertTrue(admin_response.data['resultados'][0]['puede_editar'])
        self.assertTrue(admin_response.data['resultados'][0]['puede_eliminar'])

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

    def test_editing_and_deleting_another_users_case_notifies_its_creator(self):
        inspector_role = Rol.objects.create(rol_nombre='Inspector')
        inspector = Usuario.objects.create(
            usuario_nombre='Inspector',
            usuario_apaterno='Colegio',
            usuario_amaterno='',
            usuario_correo='inspector@example.test',
            usuario_contrasena=make_password('ConviData-inspector-2026'),
            usuario_primer_ingreso=False,
            rol=inspector_role,
        )
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='López',
            curso=curso,
        )
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso_editado = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Original] - Descripción.',
            usuario=self.user,
            lugar=lugar,
        )
        caso_eliminado = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Eliminar] - Descripción.',
            usuario=self.user,
            lugar=lugar,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO involucran (estudiante_id, caso_id, tipo_falta) '
                'VALUES (%s, %s, %s)',
                [estudiante.pk, caso_editado.pk, 'Leve'],
            )
        token_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': inspector.usuario_correo,
                'contrasena': 'ConviData-inspector-2026',
            },
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        with patch('gestion_casos.api.evaluar_reglas_para_caso'):
            response_edit = self.client.put(
                f'/api/v1/casos/{caso_editado.pk}/',
                {
                    'titulo': 'Actualizado',
                    'descripcion': 'Descripción actualizada.',
                    'lugar_id': lugar.pk,
                    'tipo_falta': 'Grave',
                    'estudiantes': [{
                        'id': estudiante.pk,
                        'nombre': 'Ana',
                        'apellido_paterno': 'Pérez',
                        'apellido_materno': 'López',
                        'curso_id': curso.pk,
                    }],
                },
                format='json',
            )
        response_delete = self.client.delete(
            f'/api/v1/casos/{caso_eliminado.pk}/',
        )

        self.assertEqual(response_edit.status_code, 200)
        self.assertEqual(response_delete.status_code, 200)
        self.assertTrue(Notificacion.objects.filter(
            usuario=self.user,
            caso=caso_editado,
            evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
        ).exists())
        self.assertTrue(Notificacion.objects.filter(
            usuario=self.user,
            evento_clave=f'caso_eliminado:{caso_eliminado.pk}:creador:{self.user.pk}',
        ).exists())

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

    def test_user_admin_search_matches_names_without_accents(self):
        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        self.user.usuario_nombre = 'José'
        self.user.save(update_fields=['usuario_nombre'])
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

        response = self.client.get('/api/v1/admin/usuarios/?nombre=Jose')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['resultados'][0]['nombre'], 'José')

    def test_user_admin_api_filters_locked_accounts(self):
        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        locked_user = Usuario.objects.create(
            usuario_nombre='Bloqueado',
            usuario_apaterno='Funcionario',
            usuario_amaterno='',
            usuario_correo='bloqueado@example.test',
            usuario_contrasena=make_password('Clave-segura-2026'),
            usuario_primer_ingreso=False,
            usuario_bloqueado=True,
            rol=self.role,
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

        response = self.client.get('/api/v1/admin/usuarios/?estado=bloqueado')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in response.data['resultados']],
            [locked_user.pk],
        )

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
        accented_search = self.client.get(
            '/api/v1/admin/estudiantes/?busqueda=Perez'
        )
        self.assertEqual(accented_search.status_code, 200)
        self.assertEqual(accented_search.data['total'], 1)

        response = self.client.patch(
            f'/api/v1/admin/estudiantes/{estudiante_id}/',
            {'activo': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['estudiante']['activo'])

        response = self.client.put(
            f'/api/v1/admin/estudiantes/{estudiante_id}/',
            {
                'nombre': 'Ana María',
                'apellido_paterno': 'Pérez',
                'apellido_materno': 'López',
                'correo': 'ana@example.test',
                'curso_id': curso.pk,
                'numero_lista': 4,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['estudiante']['activo'])
        self.assertEqual(response.data['estudiante']['nombre'], 'Ana María')

    def test_student_admin_rejects_duplicate_zero_list_number(self):
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
        payload = {
            'nombre': 'Ana',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'López',
            'curso_id': curso.pk,
            'numero_lista': 0,
        }

        first_response = self.client.post(
            '/api/v1/admin/estudiantes/',
            payload,
            format='json',
        )
        second_response = self.client.post(
            '/api/v1/admin/estudiantes/',
            {
                **payload,
                'nombre': 'Bruno',
                'apellido_paterno': 'González',
            },
            format='json',
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)
        self.assertIn('número de lista', second_response.data['detail'])

    def test_student_import_detects_duplicate_zero_list_number_and_logs_it(self):
        self.role.rol_nombre = 'Administrador'
        self.role.save(update_fields=['rol_nombre'])
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Pérez',
            estudiante_amaterno='López',
            estudiante_numero_lista=0,
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
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append([
            'Nombres', 'Apellido paterno', 'Apellido materno',
            'Grado', 'Paralelo', 'Número de lista',
        ])
        worksheet.append(['Bruno', 'González', 'Soto', '3° Medio', 'A', 0])
        content = BytesIO()
        workbook.save(content)

        response = self.client.post(
            '/api/v1/admin/estudiantes/',
            {
                'archivo_excel': SimpleUploadedFile(
                    'alumnos.xlsx',
                    content.getvalue(),
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    ),
                ),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(any('número de lista duplicado' in error for error in response.data['errores']))
        imported = Estudiante.objects.get(estudiante_nombre='Bruno')
        self.assertIsNone(imported.estudiante_numero_lista)
        import_record = HistorialImportacionEstudiantes.objects.get()
        self.assertEqual(import_record.archivo, 'alumnos.xlsx')
        self.assertEqual(import_record.alumnos_agregados, [
            'Bruno González Soto (3° Medio A)',
        ])

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

    def test_cases_endpoint_can_filter_cases_by_creator(self):
        otro_usuario = Usuario.objects.create(
            usuario_nombre='Otro',
            usuario_apaterno='Inspector',
            usuario_amaterno='',
            usuario_correo='otro-inspector@example.test',
            usuario_contrasena=make_password('Otra-clave-segura-2026'),
            usuario_primer_ingreso=False,
            rol=self.role,
        )
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso_del_usuario = Caso.objects.create(
            caso_fecha=date(2026, 10, 26),
            caso_descripcion='[Caso del funcionario] - Descripción.',
            lugar=lugar,
            usuario=otro_usuario,
        )
        Caso.objects.create(
            caso_fecha=date(2026, 10, 27),
            caso_descripcion='[Caso diferente] - Descripción.',
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

        response = self.client.get(
            '/api/v1/casos/',
            {'usuario': str(otro_usuario.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in response.data['resultados']],
            [caso_del_usuario.pk],
        )

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
        self.assertEqual(response.data['code'], 'password_change_required')

    def test_temporary_password_must_be_changed_before_login(self):
        self.user.usuario_primer_ingreso = True
        self.user.save(update_fields=['usuario_primer_ingreso'])

        response = self.client.post(
            '/api/auth/required-password-change/',
            {
                'correo': self.user.usuario_correo,
                'contrasena_actual': 'ConviData-segura-2026',
                'contrasena_nueva': 'Nueva-clave-segura-2026',
            },
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.usuario_primer_ingreso)
        login_response = self.client.post(
            '/api/auth/token/',
            {
                'correo': self.user.usuario_correo,
                'contrasena': 'Nueva-clave-segura-2026',
            },
            format='json',
        )
        self.assertEqual(login_response.status_code, 200)

    def test_required_password_change_rejects_wrong_temporary_password(self):
        self.user.usuario_primer_ingreso = True
        self.user.save(update_fields=['usuario_primer_ingreso'])

        response = self.client.post(
            '/api/auth/required-password-change/',
            {
                'correo': self.user.usuario_correo,
                'contrasena_actual': 'incorrecta',
                'contrasena_nueva': 'Nueva-clave-segura-2026',
            },
            format='json',
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(self.user.usuario_primer_ingreso)

    def test_login_distinguishes_unknown_user_and_wrong_password(self):
        unknown_user = self.client.post(
            '/api/auth/token/',
            {'correo': 'inexistente@example.test', 'contrasena': 'clave'},
            format='json',
        )
        wrong_password = self.client.post(
            '/api/auth/token/',
            {'correo': self.user.usuario_correo, 'contrasena': 'incorrecta'},
            format='json',
        )

        self.assertEqual(unknown_user.status_code, 401)
        self.assertEqual(unknown_user.data['detail'], 'Usuario no existente.')
        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(wrong_password.data['detail'], 'Contraseña incorrecta.')

    def test_user_history_is_scoped_to_authenticated_user(self):
        other_user = Usuario.objects.create(
            usuario_nombre='Otro',
            usuario_apaterno='Funcionario',
            usuario_amaterno='',
            usuario_correo='otro@example.test',
            usuario_contrasena=make_password('Otra-clave-segura-2026'),
            usuario_primer_ingreso=False,
            rol=self.role,
        )
        HistorialUsuario.objects.create(
            usuario=self.user,
            historial_accion='Edición',
            historial_detalle='Actualizó su perfil.',
        )
        HistorialUsuario.objects.create(
            usuario=other_user,
            historial_accion='Creación',
            historial_detalle='Dato de otro funcionario.',
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

        response = self.client.get('/api/v1/admin/historial-usuarios/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['resultados'][0]['detalle'], 'Actualizó su perfil.')
        self.assertEqual(response.data['usuarios'], [])

    def test_case_history_can_filter_one_student_and_order_by_severity(self):
        curso = Curso.objects.create(curso_grado='3° Medio', curso_letra='A')
        estudiante = Estudiante.objects.create(
            estudiante_nombre='Ana',
            estudiante_apaterno='Ejemplo',
            estudiante_amaterno='',
            estudiante_correo='ana@example.test',
            estudiante_activo=True,
            curso=curso,
            estudiante_numero_lista=1,
            estudiante_identificador='AE013MA',
        )
        lugar = Lugar.objects.create(lugar_nombre='Patio')
        caso_grave = Caso.objects.create(
            caso_fecha=date(2026, 5, 2),
            caso_descripcion='[Caso grave] - Descripción grave.',
            lugar=lugar,
            usuario=self.user,
        )
        caso_leve = Caso.objects.create(
            caso_fecha=date(2026, 5, 1),
            caso_descripcion='[Caso leve] - Descripción leve.',
            lugar=lugar,
            usuario=self.user,
        )
        Involucran.objects.create(
            estudiante=estudiante,
            caso=caso_grave,
            tipo_falta='Grave',
        )
        Involucran.objects.create(
            estudiante=estudiante,
            caso=caso_leve,
            tipo_falta='Leve',
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
            {'estudiante': str(estudiante.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in response.data['resultados']],
            [caso_leve.pk, caso_grave.pk],
        )

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
        for attempt in range(5):
            response = self.client.post(
                '/api/auth/token/',
                {
                    'correo': self.user.usuario_correo,
                    'contrasena': 'incorrecta',
                },
                format='json',
            )
            self.assertEqual(response.status_code, 403 if attempt == 4 else 401)
        self.assertEqual(response.data['detail'], 'Cuenta bloqueada.')

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
        self.assertEqual(response.data['detail'], 'Cuenta bloqueada.')

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

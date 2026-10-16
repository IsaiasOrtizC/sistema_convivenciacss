"""API REST con autenticación JWT."""

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test import TransactionTestCase
from gestion_casos.models import (
    Administrador,
    Caso,
    Curso,
    Estudiante,
    Inspector,
    Involucran,
    Lugar,
    PConvivencia,
    ProfesorJefe,
    Rol,
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

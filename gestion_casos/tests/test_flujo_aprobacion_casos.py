"""Registro de casos y flujo de aprobación de solicitudes."""

from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import RequestFactory, TransactionTestCase
from django.utils import timezone
from gestion_casos.controllers.alert_controller import notificar_caso_gravisimo
from gestion_casos.models import (
    Caso,
    Curso,
    Estudiante,
    HistorialUsuario,
    Involucran,
    Lugar,
    Notificacion,
    ProfesorJefe,
    Rol,
    SolicitudCaso,
    Usuario,
)


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

        notificar_caso_gravisimo(request, caso, 'Gravísima', self.place)

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

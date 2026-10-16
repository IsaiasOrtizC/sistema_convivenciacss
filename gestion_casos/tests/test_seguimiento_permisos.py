"""Permisos de seguimiento, notificaciones y eliminación de documentos."""

from contextlib import nullcontext
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone
from gestion_casos.controllers.documento_controller import (
    eliminar_documento_view,
    reprocesar_documento_view,
)
from gestion_casos.controllers.notification_controller import (
    _mensaje_notificacion_seguro,
    _regla_notificacion_operativa,
    _url_caso_notificacion,
    cambiar_estado_notificacion_view,
    notificaciones_view,
)
from gestion_casos.controllers.rules_controller import (
    activar_version_reglamento_view,
    revisar_regla_view,
)
from gestion_casos.controllers.seguimiento_controller import (
    cerrar_seguimiento_view,
    seguimiento_view,
)
from gestion_casos.models import (
    AccionSeguimiento,
    Notificacion,
    ReglaInstitucional,
    VersionReglamento,
)
from gestion_casos.reglamento_2026 import VERSION_FUENTE_REGLAMENTO_2026

from .helpers import EmptyQuerySet


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
            patch('gestion_casos.controllers.documento_controller.transaction.atomic', return_value=nullcontext()),
            patch(
                'gestion_casos.controllers.documento_controller.DocumentoInstitucional.objects.select_for_update',
                return_value=locked_documents,
            ),
            patch(
                'gestion_casos.controllers.documento_controller.Notificacion.objects.filter',
                return_value=notification_queryset,
            ),
            patch(
                'gestion_casos.controllers.documento_controller.ReglaInstitucional.objects.filter',
                return_value=rule_queryset,
            ),
            patch('gestion_casos.controllers.documento_controller.HistorialUsuario.objects.create') as audit_log,
            patch('gestion_casos.controllers.documento_controller.messages.success') as success_message,
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
            patch('gestion_casos.controllers.documento_controller.transaction.atomic', return_value=nullcontext()),
            patch(
                'gestion_casos.controllers.documento_controller.DocumentoInstitucional.objects.select_for_update',
                return_value=locked_documents,
            ),
            patch('gestion_casos.controllers.documento_controller.messages.info') as info_message,
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
                    patch('gestion_casos.controllers.notification_controller.obtener_filas_seguimiento', return_value=[]),
                    patch('gestion_casos.controllers.notification_controller.render', return_value=HttpResponse('ok')),
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
        with patch('gestion_casos.controllers.notification_controller.get_object_or_404', return_value=same_state):
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

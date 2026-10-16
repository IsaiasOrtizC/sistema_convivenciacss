"""Evaluación y revisión persistente de las reglas del reglamento."""

from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import RequestFactory, TransactionTestCase
from django.utils import timezone
from gestion_casos.controllers.documento_controller import _procesar_documento_institucional
from gestion_casos.controllers.notification_controller import marcar_notificacion_leida_view
from gestion_casos.controllers.rules_controller import (
    activar_version_reglamento_view,
    revisar_regla_view,
)
from gestion_casos.controllers.seguimiento_controller import cerrar_seguimiento_view
from gestion_casos.models import (
    AccionSeguimiento,
    Caso,
    Curso,
    DocumentoInstitucional,
    Estudiante,
    Involucran,
    Lugar,
    Notificacion,
    ReglaInstitucional,
    Rol,
    SeguimientoCaso,
    Usuario,
    VersionReglamento,
)
from gestion_casos.reglamento import evaluar_reglas_para_caso
from gestion_casos.reglamento_2026 import (
    DISPOSICIONES_REGLAMENTO_2026,
    VERSION_FUENTE_REGLAMENTO_2026,
)


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
                with patch('gestion_casos.controllers.rules_controller.messages.success'):
                    response = revisar_regla_view(request, regla.pk)

                self.assertEqual(response.status_code, 302)
                regla.refresh_from_db()
                self.assertEqual(regla.cantidad_minima, cantidad)
                self.assertEqual(regla.umbral_anotaciones, cantidad)
                self.assertTrue(regla.puede_activarse())

    def test_reprocessing_preserves_existing_versions_and_approved_rules(self):
        texto_nuevo = 'Texto de reglamento recuperado mediante OCR.'
        with patch(
            'gestion_casos.controllers.documento_controller.extraer_paginas_pdf',
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
        with patch('gestion_casos.controllers.rules_controller.messages.success'):
            response = revisar_regla_view(request, self.rule.pk)
        self.assertEqual(response.status_code, 302)
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.estado, ReglaInstitucional.Estado.APROBADA)

        request = RequestFactory().post('/documentos/versiones/1/activar/')
        request.session = {'usuario_id': admin.pk, 'usuario_rol': 'Administrador'}
        with patch('gestion_casos.controllers.rules_controller.messages.success'):
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

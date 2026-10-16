"""La estructura de controladores: cada URL llega al controlador esperado y el sistema arranca sin errores.

Estas pruebas protegen la reorganización: si alguien mueve una vista sin actualizar las rutas, o rompe una
importación entre controladores, fallan aquí.
"""
import importlib

from django.test import Client, TestCase
from django.urls import resolve, reverse

# (nombre de la ruta, argumentos, módulo del controlador, función)
RUTAS = [
    ('login', {}, 'auth_controller', 'login_view'),
    ('logout', {}, 'auth_controller', 'logout_view'),
    ('dashboard', {}, 'dashboard_controller', 'dashboard_view'),
    ('historial_casos', {}, 'caso_controller', 'historial_casos_view'),
    ('registrar_caso', {}, 'caso_controller', 'registrar_caso_view'),
    ('solicitudes_casos_pendientes', {}, 'caso_controller', 'solicitudes_casos_pendientes_view'),
    ('detalle_caso', {'caso_id': 1}, 'caso_controller', 'detalle_caso_view'),
    ('descargar_caso_pdf', {'caso_id': 1}, 'report_controller', 'descargar_caso_pdf_view'),
    ('descargar_caso_xlsx', {'caso_id': 1}, 'report_controller', 'descargar_caso_xlsx_view'),
    ('estadisticas', {}, 'statistics_controller', 'estadisticas_view'),
    ('estadisticas_datos', {}, 'statistics_controller', 'estadisticas_datos_view'),
    ('estadisticas_pdf', {}, 'report_controller', 'estadisticas_pdf_view'),
    ('estadisticas_xlsx', {}, 'report_controller', 'estadisticas_xlsx_view'),
    ('notificaciones', {}, 'notification_controller', 'notificaciones_view'),
    ('marcar_notificacion_leida', {'notificacion_id': 1}, 'notification_controller', 'marcar_notificacion_leida_view'),
    ('cambiar_estado_notificacion', {'notificacion_id': 1}, 'notification_controller', 'cambiar_estado_notificacion_view'),
    ('seguimiento', {}, 'seguimiento_controller', 'seguimiento_view'),
    ('actualizar_accion_seguimiento', {'accion_id': 1}, 'seguimiento_controller', 'actualizar_accion_seguimiento_view'),
    ('cerrar_seguimiento', {'caso_id': 1, 'estudiante_id': 1}, 'seguimiento_controller', 'cerrar_seguimiento_view'),
    ('editar_caso', {'caso_id': 1}, 'caso_controller', 'editar_caso_view'),
    ('eliminar_estudiante_caso', {'caso_id': 1, 'estudiante_id': 1}, 'caso_controller', 'eliminar_estudiante_caso_view'),
    ('eliminar_caso', {'caso_id': 1}, 'caso_controller', 'eliminar_caso_view'),
    ('gestion_de_usuarios', {}, 'user_controller', 'gestion_de_usuarios_view'),
    ('editar_usuario', {'usuario_id': 1}, 'user_controller', 'editar_usuario_view'),
    ('acciones_masivas_usuarios', {}, 'user_controller', 'acciones_masivas_usuarios_view'),
    ('desbloquear_usuario', {'usuario_id': 1}, 'user_controller', 'desbloquear_usuario_view'),
    ('gestion_de_alumnos', {}, 'alumno_controller', 'gestion_de_estudiantes_view'),
    ('importar_estudiantes', {}, 'alumno_controller', 'importar_estudiantes_view'),
    ('eliminar_estudiante', {'estudiante_id': 1}, 'alumno_controller', 'eliminar_estudiante_view'),
    ('cambiar_estado_estudiante', {'estudiante_id': 1}, 'alumno_controller', 'cambiar_estado_estudiante_view'),
    ('editar_estudiante', {'estudiante_id': 1}, 'alumno_controller', 'editar_estudiante_view'),
    ('historial_de_usuarios', {}, 'user_controller', 'historial_usuarios_view'),
    ('gestion_datos_publicos', {}, 'profile_controller', 'gestion_datos_publicos_view'),
    ('gestion_configuracion', {}, 'configuracion_controller', 'gestion_configuracion_view'),
    ('gestion_documentos', {}, 'documento_controller', 'gestion_documentos_view'),
    ('reprocesar_documento', {'documento_id': 1}, 'documento_controller', 'reprocesar_documento_view'),
    ('crear_regla_manual', {'version_id': 1}, 'rules_controller', 'crear_regla_manual_view'),
    ('revisar_regla', {'regla_id': 1}, 'rules_controller', 'revisar_regla_view'),
    ('activar_version_reglamento', {'version_id': 1}, 'rules_controller', 'activar_version_reglamento_view'),
    ('eliminar_documento', {'documento_id': 1}, 'documento_controller', 'eliminar_documento_view'),
    ('mis_casos_curso', {}, 'caso_controller', 'mis_casos_curso_view'),
    ('descargar_casos_pdf', {}, 'report_controller', 'descargar_casos_pdf_view'),
    ('descargar_casos_xlsx', {}, 'report_controller', 'descargar_casos_xlsx_view'),
    ('busqueda_global', {}, 'busqueda_controller', 'busqueda_global_view'),
    ('detalle_estudiante', {'estudiante_id': 1}, 'alumno_controller', 'detalle_estudiante_view'),
]

# Rutas que responden con JSON y por eso devuelven 401 (y no una redirección) si no hay sesión.
RUTAS_JSON = {'busqueda_global', 'estadisticas_datos'}


class RutasLleganAlControladorEsperadoTests(TestCase):
    def test_cada_ruta_resuelve_al_controlador_esperado(self):
        for nombre, kwargs, modulo, funcion in RUTAS:
            with self.subTest(ruta=nombre):
                vista = resolve(reverse(nombre, kwargs=kwargs)).func
                self.assertEqual(vista.__module__, f'gestion_casos.controllers.{modulo}')
                self.assertEqual(vista.__name__, funcion)

    def test_todos_los_controladores_se_pueden_importar(self):
        for modulo in sorted({m for _, _, m, _ in RUTAS}):
            with self.subTest(modulo=modulo):
                importlib.import_module(f'gestion_casos.controllers.{modulo}')

    def test_views_py_sigue_exportando_las_mismas_funciones(self):
        """views.py quedó como fachada de compatibilidad: debe devolver exactamente las mismas funciones."""
        from gestion_casos import views
        for _, _, modulo, funcion in RUTAS:
            with self.subTest(vista=funcion):
                controlador = importlib.import_module(f'gestion_casos.controllers.{modulo}')
                self.assertIs(getattr(views, funcion), getattr(controlador, funcion))


class RutasSinSesionTests(TestCase):
    """Sin iniciar sesión, ninguna pantalla debe fallar: se redirige al acceso o se responde 401."""

    def test_ninguna_ruta_devuelve_error_sin_sesion(self):
        cliente = Client()
        for nombre, kwargs, _, _ in RUTAS:
            with self.subTest(ruta=nombre):
                respuesta = cliente.get(reverse(nombre, kwargs=kwargs))
                if nombre == 'login':
                    self.assertEqual(respuesta.status_code, 200)
                elif nombre in RUTAS_JSON:
                    self.assertEqual(respuesta.status_code, 401)
                else:
                    self.assertEqual(respuesta.status_code, 302)
                    self.assertIn(respuesta['Location'], ('/', '/dashboard/'))

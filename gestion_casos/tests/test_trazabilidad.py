"""Trazabilidad por consola: cada petición muestra su recorrido por las capas del sistema.

Estas pruebas capturan lo que se imprime en la consola y comprueban el orden de las capas
(HTTP -> vista -> controlador -> servicio -> base de datos), que es lo que se muestra en la demostración técnica.
"""
import io
from contextlib import redirect_stdout
from types import SimpleNamespace

from django.core.management import call_command
from django.db import connection
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, TransactionTestCase, override_settings

from gestion_casos import trazabilidad
from gestion_casos.controllers.caso_controller import registrar_caso_view
from gestion_casos.controllers.user_controller import gestion_de_usuarios_view
from gestion_casos.models import Caso, Curso, Estudiante, Involucran, Lugar, ProfesorJefe, Rol, Usuario


def capturar(funcion, *args, **kwargs):
    """Ejecuta la función y devuelve (resultado, líneas impresas por la trazabilidad)."""
    salida = io.StringIO()
    with redirect_stdout(salida):
        resultado = funcion(*args, **kwargs)
    return resultado, salida.getvalue().splitlines()


def en_orden(test, lineas, esperadas):
    """Comprueba que cada texto esperado aparece en las líneas, y en ese orden."""
    posicion = -1
    for texto in esperadas:
        encontradas = [i for i, linea in enumerate(lineas) if texto in linea and i > posicion]
        test.assertTrue(encontradas, f'No aparece (o aparece fuera de orden): {texto!r}\n' + '\n'.join(lineas))
        posicion = encontradas[0]


class NombreDeControladorTests(SimpleTestCase):
    def test_el_nombre_se_deriva_de_la_funcion(self):
        self.assertEqual(trazabilidad.nombre_controlador(registrar_caso_view),
                         ('CONTROLADOR', 'RegistrarCasoController'))
        self.assertEqual(trazabilidad.nombre_controlador(gestion_de_usuarios_view),
                         ('CONTROLADOR', 'GestionDeUsuariosController'))

    def test_las_vistas_de_la_api_se_distinguen(self):
        from gestion_casos.api import TokenObtainView
        self.assertEqual(trazabilidad.nombre_controlador(TokenObtainView.as_view()), ('API', 'TokenObtainView'))


class ConfiguracionDeMiddlewareTests(SimpleTestCase):
    SESION = 'django.contrib.sessions.middleware.SessionMiddleware'

    def test_la_configuracion_del_proyecto_es_correcta(self):
        self.assertEqual(trazabilidad.problemas_de_configuracion(), [])

    def test_avisa_si_faltan_los_middlewares(self):
        with override_settings(MIDDLEWARE=[self.SESION]):
            problemas = trazabilidad.problemas_de_configuracion()
        self.assertEqual(len(problemas), 2)
        self.assertIn('TrazabilidadMiddleware', problemas[0])
        self.assertIn('TrazabilidadControladorMiddleware', problemas[1])

    def test_avisa_si_el_middleware_de_controlador_no_es_el_ultimo(self):
        orden = [self.SESION, trazabilidad.MIDDLEWARE_PRINCIPAL, trazabilidad.MIDDLEWARE_CONTROLADOR,
                 'django.middleware.common.CommonMiddleware']
        with override_settings(MIDDLEWARE=orden):
            problemas = trazabilidad.problemas_de_configuracion()
        self.assertEqual(len(problemas), 1)
        self.assertIn('ÚLTIMO', problemas[0])

    def test_avisa_si_el_principal_va_antes_de_la_sesion(self):
        orden = [trazabilidad.MIDDLEWARE_PRINCIPAL, self.SESION, trazabilidad.MIDDLEWARE_CONTROLADOR]
        with override_settings(MIDDLEWARE=orden):
            problemas = trazabilidad.problemas_de_configuracion()
        self.assertEqual(len(problemas), 1)
        self.assertIn('DESPUÉS de SessionMiddleware', problemas[0])


class DecoradorTrazarTests(SimpleTestCase):
    @override_settings(TRAZA_NIVEL=1)
    def test_anuncia_el_servicio_y_no_altera_el_resultado(self):
        @trazabilidad.trazar('SERVICE', 'CasoService', 'validando datos')
        def sumar(a, b):
            """Documentación original."""
            return a + b

        resultado, lineas = capturar(sumar, 2, 3)
        self.assertEqual(resultado, 5)
        self.assertEqual(lineas, ['[SERVICE] CasoService: validando datos'])
        self.assertEqual(sumar.__name__, 'sumar')
        self.assertEqual(sumar.__doc__, 'Documentación original.')

    def test_los_mensajes_detallados_solo_salen_en_nivel_2(self):
        @trazabilidad.trazar('CONTROLADOR', 'AuthCasosController', 'verificando permiso', nivel_min=2)
        def comprobar():
            return True

        with override_settings(TRAZA_NIVEL=1):
            _, lineas = capturar(comprobar)
        self.assertEqual(lineas, [])
        with override_settings(TRAZA_NIVEL=2):
            _, lineas = capturar(comprobar)
        self.assertEqual(lineas, ['[CONTROLADOR] AuthCasosController: verificando permiso'])

    @override_settings(TRAZA_NIVEL=0)
    def test_apagada_no_imprime_nada(self):
        @trazabilidad.trazar('SERVICE', 'CasoService', 'x')
        def f():
            return 1

        resultado, lineas = capturar(f)
        self.assertEqual((resultado, lineas), (1, []))

    @override_settings(TRAZA_NIVEL=1)
    def test_consulta_con_filtros_solo_muestra_los_que_tienen_valor(self):
        _, lineas = capturar(trazabilidad.traza_consulta, 'usuarios', nombre='ana', rol='', estado='activo')
        self.assertEqual(lineas, ["[DB] Consultando usuarios según: nombre='ana', estado='activo'"])
        _, lineas = capturar(trazabilidad.traza_consulta, 'usuarios', nombre='', rol=None)
        self.assertEqual(lineas, [])


class PeticionesHttpTests(TestCase):
    @override_settings(TRAZA_NIVEL=0)
    def test_apagada_el_servidor_no_imprime_nada(self):
        _, lineas = capturar(self.client.get, '/')
        self.assertEqual(lineas, [])

    @override_settings(TRAZA_NIVEL=1)
    def test_una_pagina_muestra_http_controlador_vista_y_respuesta(self):
        respuesta, lineas = capturar(self.client.get, '/')
        self.assertEqual(respuesta.status_code, 200)
        en_orden(self, lineas, [
            '[HTTP] GET / usuario=anonimo',
            '[CONTROLADOR] LoginController: inicio',
            '[VISTA] V_Login (login.html): renderizando',
            '[CONTROLADOR] LoginController: completado',
            '[HTTP] GET / status=200',
        ])

    @override_settings(TRAZA_NIVEL=1)
    def test_una_redireccion_muestra_su_destino(self):
        respuesta, lineas = capturar(self.client.get, '/dashboard/')
        self.assertEqual(respuesta.status_code, 302)
        en_orden(self, lineas, [
            '[HTTP] GET /dashboard/ usuario=anonimo',
            '[CONTROLADOR] DashboardController: inicio',
            '[HTTP] GET /dashboard/ status=302 -> /',
        ])

    @override_settings(TRAZA_NIVEL=1)
    def test_si_un_middleware_rechaza_la_peticion_el_controlador_no_se_anuncia(self):
        """CSRF responde 403 antes de que la vista se ejecute: la consola no debe decir que el controlador inició."""
        cliente = Client(enforce_csrf_checks=True)
        respuesta, lineas = capturar(cliente.post, '/casos/nuevo/')
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(any('RegistrarCasoController: inicio' in l for l in lineas), '\n'.join(lineas))
        en_orden(self, lineas, [
            '[HTTP] POST /casos/nuevo/ usuario=anonimo',
            '[CONTROLADOR] RegistrarCasoController: no se ejecutó',
            '[HTTP] POST /casos/nuevo/ status=403',
        ])

    @override_settings(TRAZA_NIVEL=1)
    def test_la_ruta_con_parametros_aparece_en_ambas_lineas_http(self):
        _, lineas = capturar(self.client.get, '/administracion/usuarios/?nombre=ana&estado=activo')
        self.assertTrue(any(l.startswith('[HTTP] GET /administracion/usuarios/?nombre=ana&estado=activo usuario=')
                            for l in lineas))
        self.assertTrue(any('/administracion/usuarios/?nombre=ana&estado=activo status=' in l for l in lineas))

    @override_settings(TRAZA_NIVEL=1)
    def test_los_archivos_estaticos_no_ensucian_la_consola(self):
        _, lineas = capturar(self.client.get, '/static/no-existe.css')
        self.assertEqual(lineas, [])

    @override_settings(TRAZA_NIVEL=1)
    def test_una_excepcion_del_controlador_se_informa(self):
        peticion = RequestFactory().get('/casos/')
        peticion._traza = {'capa': 'CONTROLADOR', 'controlador': 'HistorialCasosController'}
        middleware = trazabilidad.TrazabilidadMiddleware(lambda r: None)
        _, lineas = capturar(middleware.process_exception, peticion, ValueError('dato inválido'))
        self.assertEqual(lineas, ['[ERROR] HistorialCasosController: excepción ValueError: dato inválido'])

    def test_los_mensajes_del_controlador_se_leen_sin_consumirlos(self):
        mensajes = [SimpleNamespace(level_tag='success', message='Caso registrado'),
                    SimpleNamespace(level_tag='error', message='Acceso denegado')]
        peticion = SimpleNamespace(_messages=SimpleNamespace(_queued_messages=mensajes))
        self.assertEqual(trazabilidad._avisos_del_controlador(peticion),
                         [('success', 'Caso registrado'), ('error', 'Acceso denegado')])
        self.assertEqual(len(mensajes), 2)
        self.assertEqual(trazabilidad._avisos_del_controlador(SimpleNamespace()), [])


@override_settings(TRAZA_NIVEL=1)
class AccesoABaseDeDatosTests(TransactionTestCase):
    """Las escrituras del ORM se anuncian: [DB] Creando registro de ... / ... guardado correctamente id=N."""

    # Tablas externas (managed = False) que el vaciado de la base necesita que existan, como en las demás pruebas
    modelos_externos = (Rol, Curso, Usuario, Estudiante, Lugar, Caso, Involucran, ProfesorJefe)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        activas = connection.disable_constraint_checking()
        with connection.schema_editor() as editor:
            for modelo in cls.modelos_externos:
                editor.create_model(modelo)
        if activas:
            connection.enable_constraint_checking()

    @classmethod
    def tearDownClass(cls):
        activas = connection.disable_constraint_checking()
        with connection.schema_editor() as editor:
            for modelo in reversed(cls.modelos_externos):
                editor.delete_model(modelo)
        if activas:
            connection.enable_constraint_checking()
        super().tearDownClass()

    def test_crear_actualizar_y_eliminar_un_registro(self):
        lugar, lineas = capturar(Lugar.objects.create, lugar_nombre='Patio central')
        self.assertEqual(lineas, ['[DB] Creando registro de lugar',
                                  f'[DB] Lugar guardado correctamente id={lugar.pk}'])

        lugar.lugar_nombre = 'Gimnasio'
        _, lineas = capturar(lugar.save)
        self.assertEqual(lineas, [f'[DB] Actualizando registro de lugar id={lugar.pk}',
                                  f'[DB] Lugar actualizado correctamente id={lugar.pk}'])

        identificador = lugar.pk
        _, lineas = capturar(lugar.delete)
        self.assertEqual(lineas, [f'[DB] Eliminando registro de lugar id={identificador}',
                                  f'[DB] Lugar eliminado correctamente id={identificador}'])

    def test_una_operacion_sql_directa_tambien_se_anuncia(self):
        lugar = Lugar.objects.create(lugar_nombre='Sala 10')

        def actualizar_directo():
            with connection.execute_wrapper(trazabilidad._envoltorio_sql):
                trazabilidad._reiniciar_contexto()
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE lugar SET lugar_nombre = %s WHERE lugar_id = %s', ['Sala 11', lugar.pk])

        _, lineas = capturar(actualizar_directo)
        self.assertEqual(lineas, ['[DB] UPDATE en lugar (SQL directo)'])


class ComandoVerificarControladoresTests(TestCase):
    def test_todas_las_rutas_resuelven_a_su_controlador(self):
        salida = io.StringIO()
        call_command('verificar_controladores', stdout=salida)
        texto = salida.getvalue()
        self.assertNotIn('[FALLO]', texto)
        self.assertIn('rutas correctas', texto)
        self.assertIn('RegistrarCasoController (caso_controller)', texto)

    def test_con_peticiones_ninguna_ruta_devuelve_error(self):
        salida = io.StringIO()
        call_command('verificar_controladores', '--peticiones', stdout=salida)
        texto = salida.getvalue()
        self.assertNotIn('[FALLO]', texto)
        self.assertRegex(texto, r'(\d+)/\1 rutas correctas')

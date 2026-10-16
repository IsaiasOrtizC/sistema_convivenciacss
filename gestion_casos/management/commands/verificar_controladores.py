"""Comprueba que cada ruta del sistema llega al controlador esperado y, opcionalmente, que responde sin errores.

    python manage.py verificar_controladores              # solo resuelve las rutas (no toca la base de datos)
    python manage.py verificar_controladores --peticiones # además envía un GET sin sesión a cada ruta

Con --peticiones se espera: 200 en el login, 302 hacia el acceso en las pantallas protegidas, 401 en los
endpoints JSON y 401/405 en la API. No modifica datos (son peticiones GET sin sesión iniciada).
"""
import re

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.test.utils import override_settings
from django.urls import URLPattern, URLResolver, get_resolver

from gestion_casos.trazabilidad import nombre_controlador

RUTAS_JSON = {'busqueda_global', 'estadisticas_datos'}


def _recorrer(patrones, prefijo=''):
    for patron in patrones:
        if isinstance(patron, URLResolver):
            yield from _recorrer(patron.url_patterns, prefijo + str(patron.pattern))
        elif isinstance(patron, URLPattern):
            yield prefijo + str(patron.pattern), patron


def _url_de_ejemplo(ruta):
    return '/' + re.sub(r'<(?:\w+:)?\w+>', '1', ruta)


class Command(BaseCommand):
    help = 'Verifica que cada URL del sistema llega a su controlador (y, con --peticiones, que responde sin errores).'

    def add_arguments(self, parser):
        parser.add_argument('--peticiones', action='store_true',
                            help='Envía un GET sin sesión a cada ruta y comprueba la respuesta.')

    def handle(self, *args, **opciones):
        rutas = [(ruta, p) for ruta, p in _recorrer(get_resolver().url_patterns)
                 if (getattr(p.callback, '__module__', '') or '').startswith('gestion_casos')]
        if not rutas:
            raise CommandError('No se encontraron rutas de gestion_casos.')

        cliente = None
        if opciones['peticiones']:
            cliente = Client()

        fallos = 0
        self.stdout.write(self.style.MIGRATE_HEADING(f"{'':<8}{'RUTA':<66} CONTROLADOR  ->  RESULTADO"))
        with override_settings(ALLOWED_HOSTS=['*']):
            for ruta, patron in sorted(rutas, key=lambda r: r[0]):
                capa, nombre = nombre_controlador(patron.callback)
                modulo = patron.callback.__module__.split('.')[-1]
                resultado, ok = 'resuelve', callable(patron.callback)
                if cliente is not None and ok:
                    url = _url_de_ejemplo(ruta)
                    try:
                        estado = cliente.get(url).status_code
                    except Exception as error:          # p. ej. base de datos no disponible
                        estado, ok = f'{type(error).__name__}', False
                    else:
                        if capa == 'API':
                            ok = estado in (401, 403, 405)
                        elif patron.name == 'login':
                            ok = estado == 200
                        elif patron.name in RUTAS_JSON:
                            ok = estado == 401
                        else:
                            ok = estado == 302
                    resultado = f'GET -> {estado}'
                marca = self.style.SUCCESS('[OK]   ') if ok else self.style.ERROR('[FALLO]')
                fallos += 0 if ok else 1
                etiqueta = f'[API] {nombre}' if capa == 'API' else nombre
                self.stdout.write(f'{marca} {url_visible(ruta):<66} {etiqueta} ({modulo})  ->  {resultado}')

        total = len(rutas)
        resumen = f'{total - fallos}/{total} rutas correctas'
        if fallos:
            self.stdout.write(self.style.ERROR(resumen))
            raise CommandError(f'{fallos} ruta(s) con problemas.')
        self.stdout.write(self.style.SUCCESS(resumen))


def url_visible(ruta):
    return '/' + ruta if not ruta.startswith('/') else ruta

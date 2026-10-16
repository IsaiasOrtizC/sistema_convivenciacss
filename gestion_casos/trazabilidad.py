"""Trazabilidad por consola: muestra cómo viaja cada petición por las capas del sistema.

Ejemplo de lo que imprime el servidor al registrar un caso:

    [HTTP] POST /casos/nuevo/ usuario=11
    [CONTROLADOR] RegistrarCasoController: inicio
    [SERVICE] CasoService: validando datos y registrando el caso
    [DB] Creando registro de caso
    [DB] Caso guardado correctamente id=25
    [CONTROLADOR] RegistrarCasoController: mensaje (success): Caso registrado correctamente
    [CONTROLADOR] RegistrarCasoController: completado
    [DB] 9 consultas en 14 ms | SELECT: curso, estudiante | INSERT: caso, involucran
    [HTTP] POST /casos/nuevo/ status=302 -> /casos/ tiempo=31ms

Se controla con la variable de entorno ``TRAZA_NIVEL`` (ver config/settings.py):

    0  apagado (valor por defecto cuando DEBUG es False)
    1  flujo principal: HTTP, vistas, controladores, servicios y escrituras en la base de datos
    2  detallado: además cada consulta SQL y las comprobaciones de permisos

Requiere DOS middlewares en settings.MIDDLEWARE:
    TrazabilidadMiddleware             justo después de SessionMiddleware (HTTP, resumen de la base de datos)
    TrazabilidadControladorMiddleware  el ÚLTIMO de la lista (anuncia el controlador solo si de verdad se ejecuta)

Las capas que se muestran corresponden a los diagramas de secuencia:
    [HTTP]         petición recibida y respuesta entregada
    [VISTA]        plantilla HTML que se renderiza (V_...)
    [CONTROLADOR]  controlador que atiende la petición (y sus componentes de apoyo)
    [API]          vista de la API REST (Django REST Framework)
    [SERVICE]      lógica de negocio (services/)
    [DB]           acceso a datos mediante el ORM de Django
    [ERROR]        excepciones no controladas
"""
import functools
import os
import re
import sys
import threading
import time

from django.conf import settings
from django.core.management.color import supports_color
from django.db import connection
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.urls import Resolver404, resolve

# ---------------------------------------------------------------------------- configuración

COLORES = {
    'HTTP': '36',          # cian
    'VISTA': '34',         # azul
    'CONTROLADOR': '32',   # verde
    'API': '32',
    'SERVICE': '33',       # amarillo
    'DB': '35',            # magenta
    'ERROR': '31',         # rojo
    'TRAZA': '90',         # gris
}

# nombre de la plantilla -> nombre de la vista en los diagramas
NOMBRES_VISTA = {
    'login.html': 'V_Login',
    'dashboard.html': 'V_Dashboard',
    'historial_casos.html': 'V_HistorialCasos',
    'registrar_caso.html': 'V_RegistrarCaso',
    'detalle_caso.html': 'V_DetalleCaso',
    'editar_caso.html': 'V_EditarCaso',
    'mis_casos_curso.html': 'V_MisCasosCurso',
    'solicitudes_casos_pendientes.html': 'V_SolicitudesPendientes',
    'seguimiento.html': 'V_Seguimiento',
    'estadisticas.html': 'V_Estadisticas',
    'notificaciones.html': 'V_Notificaciones',
    'detalle_estudiante.html': 'V_FichaAlumno',
    'gestion_documentos.html': 'V_Documentos',
    'gestion_datos_publicos.html': 'V_DatosPublicos',
    'gestion_configuracion.html': 'V_Configuracion',
    'gestion_de_usuarios.html': 'V_GestionUsuarios',
    'historial_de_usuarios.html': 'V_HistorialUsuarios',
    'gestion_de_estudiantes.html': 'V_GestionAlumnos',
}

# modelo -> (nombre en español, terminación del participio: 'o' masculino / 'a' femenino)
NOMBRES_MODELO = {
    'Rol': ('rol', 'o'), 'Usuario': ('usuario', 'o'), 'Curso': ('curso', 'o'),
    'Estudiante': ('estudiante', 'o'), 'Lugar': ('lugar', 'o'), 'Caso': ('caso', 'o'),
    'Involucran': ('involucrado en el caso', 'o'), 'Administrador': ('administrador', 'o'),
    'Inspector': ('inspector', 'o'), 'PConvivencia': ('encargado de convivencia', 'o'),
    'ProfesorJefe': ('profesor jefe', 'o'), 'Notificacion': ('notificación', 'a'),
    'HistorialUsuario': ('historial de usuario', 'o'),
    'DocumentoInstitucional': ('documento institucional', 'o'),
    'VersionReglamento': ('versión del reglamento', 'a'),
    'ReglaInstitucional': ('regla institucional', 'a'),
    'SeguimientoCaso': ('seguimiento de caso', 'o'),
    'AccionSeguimiento': ('acción de seguimiento', 'a'),
    'HistorialNotificacion': ('historial de notificación', 'o'),
    'HistorialAccionSeguimiento': ('historial de acción de seguimiento', 'o'),
    'HistorialSeguimientoCaso': ('historial de seguimiento', 'o'),
    'SesionActiva': ('sesión activa', 'a'),
    'HistorialImportacionEstudiantes': ('historial de importación de estudiantes', 'o'),
    'SolicitudCaso': ('solicitud de caso', 'a'),
}

VERBOS_ESCRITURA = ('INSERT', 'UPDATE', 'DELETE')
_contexto = threading.local()


def nivel():
    """Nivel de trazabilidad vigente (0 = apagado)."""
    try:
        return int(getattr(settings, 'TRAZA_NIVEL', 0))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------- configuración correcta

MIDDLEWARE_PRINCIPAL = 'gestion_casos.trazabilidad.TrazabilidadMiddleware'
MIDDLEWARE_CONTROLADOR = 'gestion_casos.trazabilidad.TrazabilidadControladorMiddleware'
MIDDLEWARE_SESION = 'django.contrib.sessions.middleware.SessionMiddleware'


def problemas_de_configuracion():
    """Describe qué falta o está mal ordenado en settings.MIDDLEWARE (lista vacía si todo está bien)."""
    middlewares = list(getattr(settings, 'MIDDLEWARE', []))
    problemas = []
    if MIDDLEWARE_PRINCIPAL not in middlewares:
        problemas.append(f"falta '{MIDDLEWARE_PRINCIPAL}' en MIDDLEWARE (justo después de SessionMiddleware)")
    elif MIDDLEWARE_SESION in middlewares and middlewares.index(MIDDLEWARE_PRINCIPAL) < middlewares.index(MIDDLEWARE_SESION):
        problemas.append('TrazabilidadMiddleware debe ir DESPUÉS de SessionMiddleware')
    if MIDDLEWARE_CONTROLADOR not in middlewares:
        problemas.append(f"falta '{MIDDLEWARE_CONTROLADOR}' como ÚLTIMO elemento de MIDDLEWARE")
    elif middlewares[-1] != MIDDLEWARE_CONTROLADOR:
        problemas.append('TrazabilidadControladorMiddleware debe ser el ÚLTIMO elemento de MIDDLEWARE')
    return problemas


# ---------------------------------------------------------------------------- salida

def traza(capa, mensaje, nivel_min=1):
    """Imprime una línea de traza si el nivel configurado es suficiente."""
    if nivel() < nivel_min:
        return
    etiqueta = f'[{capa}]'
    if supports_color():
        codigo = COLORES.get(capa, '0')
        etiqueta = f'\033[1;{codigo}m{etiqueta}\033[0m'
        if capa == 'ERROR':
            mensaje = f'\033[{codigo}m{mensaje}\033[0m'
    sys.stdout.write(f'{etiqueta} {mensaje}\n')
    sys.stdout.flush()


def traza_consulta(entidad, **filtros):
    """[DB] Consultando usuarios según: nombre='ana', estado='activo' (solo los filtros que tienen valor)."""
    activos = {k: v for k, v in filtros.items() if v not in (None, '')}
    if activos:
        detalle = ', '.join(f'{k}={v!r}' for k, v in activos.items())
        traza('DB', f'Consultando {entidad} según: {detalle}')


def paso_servicio(servicio, mensaje, nivel_min=1):
    """Atajo para anunciar un paso dentro de un servicio: [SERVICE] CasoService: validando datos."""
    traza('SERVICE', f'{servicio}: {mensaje}', nivel_min)


def trazar(capa, componente, mensaje=None, nivel_min=1):
    """Decorador: anuncia que un servicio o componente de apoyo fue invocado.

        @trazar('SERVICE', 'CasoService', 'validando datos y registrando el caso')
        def crear_caso_persistido(...): ...

    No altera el comportamiento de la función: solo imprime y devuelve su resultado (o relanza su excepción).
    """
    def decorador(funcion):
        texto = mensaje or funcion.__name__

        @functools.wraps(funcion)
        def envoltura(*args, **kwargs):
            traza(capa, f'{componente}: {texto}', nivel_min)
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


# ---------------------------------------------------------------------------- nombres

def nombre_controlador(vista):
    """registrar_caso_view -> ('CONTROLADOR', 'RegistrarCasoController'); vistas DRF -> ('API', 'NombreDeLaVista')."""
    clase = getattr(vista, 'cls', None)      # las vistas de Django REST Framework exponen .cls
    if clase is not None:
        return 'API', clase.__name__
    nombre = vista.__name__
    if nombre.endswith('_view'):
        nombre = nombre[:-5]
    return 'CONTROLADOR', ''.join(parte.capitalize() for parte in nombre.split('_')) + 'Controller'


# ---------------------------------------------------------------------------- SQL

_RE_TABLA = re.compile(r'(?:FROM|INTO|UPDATE|JOIN)\s+"?(\w+)"?', re.IGNORECASE)


def _reiniciar_contexto():
    _contexto.sql = {}              # verbo -> {tabla: cantidad}
    _contexto.total = 0
    _contexto.guardando = 0         # >0 mientras un modelo se guarda o elimina (sus señales ya informan)


def _envoltorio_sql(execute, sql, params, many, context):
    inicio = time.perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        _registrar_sql(sql, (time.perf_counter() - inicio) * 1000)


def _registrar_sql(sql, milisegundos):
    partes = sql.lstrip().split(None, 1)
    verbo = partes[0].upper() if partes else '?'
    if verbo in ('SAVEPOINT', 'RELEASE', 'BEGIN', 'COMMIT', 'ROLLBACK', 'PRAGMA'):
        return
    encontrada = _RE_TABLA.search(sql)
    tabla = encontrada.group(1) if encontrada else '?'
    por_tabla = getattr(_contexto, 'sql', None)
    if por_tabla is None:
        return
    por_tabla.setdefault(verbo, {})
    por_tabla[verbo][tabla] = por_tabla[verbo].get(tabla, 0) + 1
    _contexto.total += 1

    if nivel() >= 2:
        traza('DB', f'{verbo} {tabla} ({milisegundos:.1f} ms)', 2)
    elif verbo in VERBOS_ESCRITURA and not getattr(_contexto, 'guardando', 0):
        traza('DB', f'{verbo} en {tabla} (SQL directo)')


def _resumen_sql(milisegundos):
    por_tabla = getattr(_contexto, 'sql', None) or {}
    if not _contexto.total:
        return
    detalle = ' | '.join(
        f"{verbo}: {', '.join(sorted(tablas))}" for verbo, tablas in sorted(por_tabla.items()))
    palabra = 'consulta' if _contexto.total == 1 else 'consultas'
    traza('DB', f'{_contexto.total} {palabra} en {milisegundos:.0f} ms | {detalle}')


# ---------------------------------------------------------------------------- señales del ORM

def _nombre_modelo(instancia):
    nombre, _ = NOMBRES_MODELO.get(type(instancia).__name__, (str(instancia._meta.verbose_name), 'o'))
    return nombre


def _participio(instancia, base):
    """guardado/guardada, actualizado/actualizada, eliminado/eliminada según el género del modelo."""
    _, terminacion = NOMBRES_MODELO.get(type(instancia).__name__, ('', 'o'))
    return f'{base}{terminacion}'


def _antes_de_guardar(sender, instance, raw=False, **kwargs):
    if raw:
        return
    _contexto.guardando = getattr(_contexto, 'guardando', 0) + 1
    nombre = _nombre_modelo(instance)
    if instance._state.adding:
        traza('DB', f'Creando registro de {nombre}')
    else:
        traza('DB', f'Actualizando registro de {nombre} id={instance.pk}')


def _despues_de_guardar(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    _contexto.guardando = max(getattr(_contexto, 'guardando', 1) - 1, 0)
    nombre = _nombre_modelo(instance).capitalize()
    accion = _participio(instance, 'guardad' if created else 'actualizad')
    traza('DB', f'{nombre} {accion} correctamente id={instance.pk}')


def _antes_de_eliminar(sender, instance, **kwargs):
    _contexto.guardando = getattr(_contexto, 'guardando', 0) + 1
    traza('DB', f'Eliminando registro de {_nombre_modelo(instance)} id={instance.pk}')


def _despues_de_eliminar(sender, instance, **kwargs):
    _contexto.guardando = max(getattr(_contexto, 'guardando', 1) - 1, 0)
    traza('DB', f'{_nombre_modelo(instance).capitalize()} {_participio(instance, "eliminad")} '
                f'correctamente id={instance.pk}')


def conectar_senales():
    """Engancha la trazabilidad a todos los modelos de gestion_casos (se llama desde AppConfig.ready)."""
    from django.apps import apps
    for modelo in apps.get_app_config('gestion_casos').get_models():
        nombre = modelo.__name__
        pre_save.connect(_antes_de_guardar, sender=modelo, dispatch_uid=f'traza_pre_save_{nombre}')
        post_save.connect(_despues_de_guardar, sender=modelo, dispatch_uid=f'traza_post_save_{nombre}')
        pre_delete.connect(_antes_de_eliminar, sender=modelo, dispatch_uid=f'traza_pre_delete_{nombre}')
        post_delete.connect(_despues_de_eliminar, sender=modelo, dispatch_uid=f'traza_post_delete_{nombre}')


# ---------------------------------------------------------------------------- vistas (plantillas)

def parchear_render_de_plantillas():
    """Anuncia qué plantilla (vista V_...) se renderiza. Solo imprime cuando la trazabilidad está activa."""
    from django.template.backends.django import Template as PlantillaDjango
    if getattr(PlantillaDjango.render, '_traza_parcheado', False):
        return
    original = PlantillaDjango.render

    @functools.wraps(original)
    def render(self, context=None, request=None):
        if request is not None and nivel() >= 1:
            archivo = os.path.basename(getattr(self.template, 'name', '') or '')
            etiqueta = NOMBRES_VISTA.get(archivo)
            traza('VISTA', f'{etiqueta} ({archivo}): renderizando' if etiqueta else f'{archivo}: renderizando')
        return original(self, context, request)

    render._traza_parcheado = True
    PlantillaDjango.render = render


# ---------------------------------------------------------------------------- middleware HTTP

def _avisos_del_controlador(request):
    """Mensajes que el controlador dejó para el usuario (messages.success / error / ...), sin consumirlos."""
    almacen = getattr(request, '_messages', None)
    pendientes = getattr(almacen, '_queued_messages', None) or []
    return [(m.level_tag, str(m.message)) for m in pendientes]


class TrazabilidadMiddleware:
    """Registra cada petición HTTP, el controlador que la atiende y el resumen de acceso a la base de datos.

    Debe ir DESPUÉS de SessionMiddleware (para conocer al usuario) en settings.MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _es_recurso_estatico(self, request):
        prefijos = (getattr(settings, 'STATIC_URL', None) or '/static/', getattr(settings, 'MEDIA_URL', None) or '/media/')
        return request.path.startswith(prefijos) or request.path == '/favicon.ico'

    @staticmethod
    def _controlador_esperado(request):
        """Controlador al que apunta la URL, aunque un middleware pueda impedir que llegue a ejecutarse."""
        try:
            vista = resolve(request.path_info).func
        except Resolver404:
            return None
        modulo = getattr(vista, '__module__', '') or ''
        if modulo.startswith('gestion_casos'):
            return nombre_controlador(vista)
        return None

    def __call__(self, request):
        if nivel() == 0 or (self._es_recurso_estatico(request) and nivel() < 2):
            return self.get_response(request)

        inicio = time.perf_counter()
        usuario = request.session.get('usuario_id') if hasattr(request, 'session') else None
        request._traza = {'capa': None, 'controlador': None, 'esperado': self._controlador_esperado(request)}
        _reiniciar_contexto()

        ruta = request.get_full_path()
        if len(ruta) > 140:
            ruta = ruta[:137] + '...'
        traza('HTTP', f'{request.method} {ruta} usuario={usuario or "anonimo"}')

        with connection.execute_wrapper(_envoltorio_sql):
            respuesta = self.get_response(request)

        milisegundos = (time.perf_counter() - inicio) * 1000
        datos = request._traza
        if not datos['controlador'] and datos['esperado']:
            capa_esperada, nombre_esperado = datos['esperado']
            traza(capa_esperada, f'{nombre_esperado}: no se ejecutó (un middleware respondió antes: '
                                 f'sesión única, CSRF u otro filtro)')
        if datos['controlador']:
            capa, nombre = datos['capa'], datos['controlador']
            avisos = _avisos_del_controlador(request)
            for etiqueta, texto in avisos:
                traza(capa, f'{nombre}: mensaje ({etiqueta}): {texto[:110]}')
            if respuesta.status_code >= 500:
                traza('ERROR', f'{nombre}: falló (status {respuesta.status_code})')
            elif respuesta.status_code >= 400:
                traza(capa, f'{nombre}: respondió {respuesta.status_code}')
            elif any(etiqueta == 'error' for etiqueta, _ in avisos):
                traza(capa, f'{nombre}: rechazó la operación')
            else:
                traza(capa, f'{nombre}: completado')
        _resumen_sql(milisegundos)

        destino = ''
        if respuesta.status_code in (301, 302, 303, 307, 308) and respuesta.has_header('Location'):
            destino = f" -> {respuesta['Location']}"
        traza('HTTP', f'{request.method} {ruta} status={respuesta.status_code}{destino} tiempo={milisegundos:.0f}ms')
        return respuesta

    def process_exception(self, request, excepcion):
        if nivel() > 0 and hasattr(request, '_traza') and request._traza.get('controlador'):
            traza('ERROR', f"{request._traza['controlador']}: excepción {type(excepcion).__name__}: {excepcion}")
        return None


class TrazabilidadControladorMiddleware:
    """Anuncia el inicio del controlador justo antes de que la vista se ejecute.

    Debe ser el ÚLTIMO de settings.MIDDLEWARE: así, si un filtro anterior (CSRF, sesión única, cambio de
    contraseña obligatorio...) responde primero, el controlador no se anuncia porque nunca llegó a ejecutarse.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, vista, args, kwargs):
        if nivel() == 0 or not hasattr(request, '_traza'):
            return None
        modulo = getattr(vista, '__module__', '') or ''
        es_api = getattr(vista, 'cls', None) is not None
        if modulo.startswith('gestion_casos.controllers') or (es_api and modulo.startswith('gestion_casos')):
            capa, nombre = nombre_controlador(vista)
            request._traza['capa'], request._traza['controlador'] = capa, nombre
            traza(capa, f'{nombre}: inicio')
        return None

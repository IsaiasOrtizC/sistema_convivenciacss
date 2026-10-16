# Reorganización del sistema: controladores, servicios y permisos

Este documento describe cómo quedó organizado el código de `gestion_casos` y sirve de mapa para encontrar
dónde vive cada responsabilidad. Sigue la *Guía de reorganización del Sistema de Convivencia Escolar*.

## 1. Qué cambió (y qué no)

Antes, **toda** la lógica de las pantallas estaba en un único archivo, `views.py`, de 4.283 líneas con 72
funciones. Ahora se reparte por responsabilidad:

```
gestion_casos/
├── controllers/     Reciben la petición HTTP, validan la entrada y coordinan la respuesta
├── services/        Lógica de negocio reutilizable (casos, estadísticas, reportes, seguimiento)
├── permissions.py   Reglas de autorización reutilizables (qué rol accede a qué)
├── tests/           Pruebas organizadas por área (105 pruebas)
├── urls.py          Rutas: cada una apunta directamente a su controlador
├── trazabilidad.py  Trazas por consola: recorrido de cada petición por las capas (docs/DEMO_TECNICA.md)
├── management/commands/verificar_controladores.py   Comprueba que cada URL llega a su controlador
├── views.py         Fachada de compatibilidad: re-exporta las vistas desde controllers/
├── models.py        SIN CAMBIOS (modelos, relaciones y migraciones intactos)
├── reglamento*.py   SIN CAMBIOS (motor de lectura de PDF y evaluación de reglas)
├── api.py, authentication.py, tasks.py, middleware.py   SIN CAMBIOS
└── templates/       SIN CAMBIOS (los nombres de ruta `{% url %}` siguen existiendo)
```

**El comportamiento no cambió.** Las 72 funciones originales se movieron sin modificar su lógica: se comprobó
comparando el árbol sintáctico de cada una antes y después. La única edición intencional es que `login_view`
ahora envía el correo de recuperación a través de `email_controller.enviar_correo_html()` en vez de llamar a
Resend directamente.

> En Django, las *vistas* cumplen el papel de *controladores* (el patrón se llama MVT en lugar de MVC). Por eso
> el sistema ya tenía una capa de controladores; lo que faltaba era **separarla y nombrarla** según tu diagrama.

## 2. Flujo de una petición

1. **Plantilla HTML** — lo que ve el usuario.
2. **`urls.py`** — asocia la dirección con una función de un controlador.
3. **Controlador** (`controllers/`) — valida la entrada y coordina.
4. **Permisos y servicios** (`permissions.py`, `auth_casos_controller.py`, `services/`) — reglas de negocio y autorización.
5. **Modelos / PostgreSQL** (`models.py`, ORM de Django) — consultas y persistencia.
6. **Respuesta** — plantilla, redirección, descarga o JSON.

**Regla de dependencias:** `permissions` ← `services` ← `controllers`. Los controladores pueden usar servicios y
permisos; los servicios y permisos **no** deben importar vistas HTTP. (Excepción documentada: `caso_service`
usa `alert_controller` y `email_controller`, que son componentes de coordinación sin pantalla propia.)

## 3. Mapa de rutas

| URL | Nombre | Controlador y función | Plantilla |
|---|---|---|---|
| `/` | `login` | `auth_controller.login_view` | `login.html` |
| `/logout/` | `logout` | `auth_controller.logout_view` | — |
| `/dashboard/` | `dashboard` | `dashboard_controller.dashboard_view` | `dashboard.html` |
| `/casos/` | `historial_casos` | `caso_controller.historial_casos_view` | `historial_casos.html` |
| `/casos/nuevo/` | `registrar_caso` | `caso_controller.registrar_caso_view` | `registrar_caso.html` |
| `/casos/pendientes/` | `solicitudes_casos_pendientes` | `caso_controller.solicitudes_casos_pendientes_view` | `solicitudes_casos_pendientes.html` |
| `/casos/<int:caso_id>/` | `detalle_caso` | `caso_controller.detalle_caso_view` | `detalle_caso.html` |
| `/casos/<int:caso_id>/pdf/` | `descargar_caso_pdf` | `report_controller.descargar_caso_pdf_view` | — |
| `/casos/<int:caso_id>/xlsx/` | `descargar_caso_xlsx` | `report_controller.descargar_caso_xlsx_view` | — |
| `/estadisticas/` | `estadisticas` | `statistics_controller.estadisticas_view` | `estadisticas.html` |
| `/estadisticas/datos/` | `estadisticas_datos` | `statistics_controller.estadisticas_datos_view` | — |
| `/estadisticas/pdf/` | `estadisticas_pdf` | `report_controller.estadisticas_pdf_view` | — |
| `/estadisticas/xlsx/` | `estadisticas_xlsx` | `report_controller.estadisticas_xlsx_view` | — |
| `/notificaciones/` | `notificaciones` | `notification_controller.notificaciones_view` | `notificaciones.html` |
| `/notificaciones/<int:notificacion_id>/leer/` | `marcar_notificacion_leida` | `notification_controller.marcar_notificacion_leida_view` | — |
| `/notificaciones/<int:notificacion_id>/estado/` | `cambiar_estado_notificacion` | `notification_controller.cambiar_estado_notificacion_view` | — |
| `/seguimiento/` | `seguimiento` | `seguimiento_controller.seguimiento_view` | — |
| `/seguimiento/acciones/<int:accion_id>/estado/` | `actualizar_accion_seguimiento` | `seguimiento_controller.actualizar_accion_seguimiento_view` | — |
| `/seguimiento/casos/<int:caso_id>/estudiantes/<int:estudiante_id>/cerrar/` | `cerrar_seguimiento` | `seguimiento_controller.cerrar_seguimiento_view` | — |
| `/casos/editar/<int:caso_id>/` | `editar_caso` | `caso_controller.editar_caso_view` | `editar_caso.html` |
| `/casos/editar/<int:caso_id>/eliminar_estudiante/<int:estudiante_id>/` | `eliminar_estudiante_caso` | `caso_controller.eliminar_estudiante_caso_view` | — |
| `/casos/eliminar/<int:caso_id>/` | `eliminar_caso` | `caso_controller.eliminar_caso_view` | — |
| `/administracion/usuarios/` | `gestion_de_usuarios` | `user_controller.gestion_de_usuarios_view` | `gestion_de_usuarios.html` |
| `/administracion/usuarios/editar/<int:usuario_id>/` | `editar_usuario` | `user_controller.editar_usuario_view` | — |
| `/administracion/usuarios/acciones-masivas/` | `acciones_masivas_usuarios` | `user_controller.acciones_masivas_usuarios_view` | — |
| `/administracion/usuarios/desbloquear/<int:usuario_id>/` | `desbloquear_usuario` | `user_controller.desbloquear_usuario_view` | — |
| `/administracion/alumnos/` | `gestion_de_alumnos` | `alumno_controller.gestion_de_estudiantes_view` | `gestion_de_estudiantes.html` |
| `/administracion/alumnos/importar/` | `importar_estudiantes` | `alumno_controller.importar_estudiantes_view` | — |
| `/administracion/alumnos/eliminar/<int:estudiante_id>/` | `eliminar_estudiante` | `alumno_controller.eliminar_estudiante_view` | — |
| `/administracion/alumnos/estado/<int:estudiante_id>/` | `cambiar_estado_estudiante` | `alumno_controller.cambiar_estado_estudiante_view` | — |
| `/administracion/alumnos/editar/<int:estudiante_id>/` | `editar_estudiante` | `alumno_controller.editar_estudiante_view` | — |
| `/modulo-admin/historial-usuarios/` | `historial_de_usuarios` | `user_controller.historial_usuarios_view` | `historial_de_usuarios.html` |
| `/mis-datos/perfil/` | `gestion_datos_publicos` | `profile_controller.gestion_datos_publicos_view` | `gestion_datos_publicos.html` |
| `/mis-datos/configuracion/` | `gestion_configuracion` | `configuracion_controller.gestion_configuracion_view` | `gestion_configuracion.html` |
| `/documentos/` | `gestion_documentos` | `documento_controller.gestion_documentos_view` | `gestion_documentos.html` |
| `/documentos/<int:documento_id>/reprocesar/` | `reprocesar_documento` | `documento_controller.reprocesar_documento_view` | — |
| `/documentos/versiones/<int:version_id>/reglas/nueva/` | `crear_regla_manual` | `rules_controller.crear_regla_manual_view` | — |
| `/documentos/reglas/<int:regla_id>/revisar/` | `revisar_regla` | `rules_controller.revisar_regla_view` | — |
| `/documentos/versiones/<int:version_id>/activar/` | `activar_version_reglamento` | `rules_controller.activar_version_reglamento_view` | — |
| `/documentos/eliminar/<int:documento_id>/` | `eliminar_documento` | `documento_controller.eliminar_documento_view` | — |
| `/mis-casos-curso/` | `mis_casos_curso` | `caso_controller.mis_casos_curso_view` | `mis_casos_curso.html` |
| `/mis-casos-curso/pdf/` | `descargar_casos_pdf` | `report_controller.descargar_casos_pdf_view` | — |
| `/mis-casos-curso/xlsx/` | `descargar_casos_xlsx` | `report_controller.descargar_casos_xlsx_view` | — |
| `/busqueda/` | `busqueda_global` | `busqueda_controller.busqueda_global_view` | — |
| `/alumnos/<int:estudiante_id>/ficha/` | `detalle_estudiante` | `alumno_controller.detalle_estudiante_view` | `detalle_estudiante.html` |

Además, la API REST (`/api/...`) está en `api.py` y `api_urls.py` y usa autenticación JWT (`authentication.py`).

## 4. Tamaño de los módulos

| Módulo | Líneas |
|---|---|
| `gestion_casos/controllers/alert_controller.py` | 181 |
| `gestion_casos/controllers/alumno_controller.py` | 485 |
| `gestion_casos/controllers/auth_casos_controller.py` | 67 |
| `gestion_casos/controllers/auth_controller.py` | 160 |
| `gestion_casos/controllers/busqueda_controller.py` | 79 |
| `gestion_casos/controllers/caso_controller.py` | 913 |
| `gestion_casos/controllers/configuracion_controller.py` | 46 |
| `gestion_casos/controllers/dashboard_controller.py` | 139 |
| `gestion_casos/controllers/documento_controller.py` | 346 |
| `gestion_casos/controllers/email_controller.py` | 38 |
| `gestion_casos/controllers/notification_controller.py` | 190 |
| `gestion_casos/controllers/profile_controller.py` | 54 |
| `gestion_casos/controllers/report_controller.py` | 429 |
| `gestion_casos/controllers/rules_controller.py` | 240 |
| `gestion_casos/controllers/seguimiento_controller.py` | 119 |
| `gestion_casos/controllers/statistics_controller.py` | 41 |
| `gestion_casos/controllers/user_controller.py` | 439 |
| `gestion_casos/permissions.py` | 22 |
| `gestion_casos/services/caso_service.py` | 264 |
| `gestion_casos/services/estadistica_service.py` | 159 |
| `gestion_casos/services/reporte_service.py` | 92 |
| `gestion_casos/services/seguimiento_service.py` | 72 |

## 5. Estado de cada componente de tu diagrama

| Componente del diagrama | Estado | Dónde está |
|---|---|---|
| Auth casos | Implementado | `controllers/auth_casos_controller.py` |
| Auth Controller | Implementado | `controllers/auth_controller.py` (+ `middleware.py`: sesión única y cambio de contraseña) |
| Dashboard Controller | Implementado | `controllers/dashboard_controller.py` |
| Notification Controller | Implementado | `controllers/notification_controller.py` |
| Alumno Controller | Implementado | `controllers/alumno_controller.py` |
| Email Controller | Implementado | `controllers/email_controller.py` (+ tareas Celery en `tasks.py`) |
| Statistics Controller | Implementado | `controllers/statistics_controller.py` + `services/estadistica_service.py` |
| User Controller | Implementado | `controllers/user_controller.py` |
| Profile Controller | Implementado | `controllers/profile_controller.py` |
| Report Controller | Implementado | `controllers/report_controller.py` + `services/reporte_service.py` |
| Rules Controller | Implementado | `controllers/rules_controller.py` (el motor de reglas está en `reglamento.py`) |
| Alert Controller | Implementado | `controllers/alert_controller.py` |
| CasoService | Implementado | `services/caso_service.py` |
| Configuracion Controller | Implementado | `controllers/configuracion_controller.py` |
| Controlador de documentos / seguimiento / búsqueda | Implementado (no figuraban en el diagrama) | `documento_controller.py`, `seguimiento_controller.py`, `busqueda_controller.py` |
| Inicio Controller | **No creado** | La pantalla de inicio es el Dashboard; crear un archivo vacío no aportaría nada |
| Admin Controller | **No creado** | La administración está repartida en `user_controller`, `alumno_controller`, `documento_controller` y `permissions.py` |
| JWT Controller / Django REST Controller | Existe | `authentication.py`, `api.py`, `api_urls.py` |
| Celery Controller | Existe | `config/celery.py`, `tasks.py` |
| RedisController | Parcial | Solo como intermediario (broker) de Celery; no hay caché configurada |
| Resend API Client | Existe | `email_controller.enviar_correo_html()` y `tasks.py` |
| ApexCharts | Existe | Biblioteca JavaScript cargada por CDN en 3 plantillas (no es un controlador) |
| Django ORM / PostgreSQL | Existe | `models.py`, `DATABASES` en `config/settings.py` |
| React Router Controller, Axios | **No existen** | No hay frontend React: las pantallas son plantillas de Django |
| MVC Controller, ViewReplacement | **No se encontraron** | No hay código con ese nombre ni función equivalente |

Se recomienda actualizar el diagrama de componentes para reflejar esta tabla (quitar o marcar como "no implementado"
React Router, Axios, MVC Controller y ViewReplacement).

## 6. Cómo agregar una pantalla nueva

1. Si necesita lógica reutilizable, escríbela en `services/`.
2. Crea la función de vista en el controlador que corresponda (o un controlador nuevo en `controllers/`).
3. Registra la ruta en `urls.py` apuntando al controlador (`from .controllers import mi_controller`).
4. Agrega la fila a la lista `RUTAS` de `tests/test_estructura.py`.
5. Ejecuta `python manage.py check` y las pruebas.

## 7. Cómo ejecutar el sistema y las pruebas

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env        # y completar los valores reales
python manage.py check
python manage.py runserver
```

Para mostrar el recorrido de cada petición en la consola y comprobar los controladores, ver `docs/DEMO_TECNICA.md`:

```powershell
python manage.py verificar_controladores              # cada URL llega a su controlador
python manage.py verificar_controladores --peticiones # además, una petición GET a cada ruta
```

Pruebas (usan SQLite en memoria, no tocan la base de datos real):

```powershell
python manage.py test gestion_casos --settings=config.test_settings
```

## 8. Pendientes y recomendaciones

- **Seguridad:** `config/settings.py.backup` está versionado y contiene una clave y una contraseña escritas
  literalmente. Debe eliminarse del repositorio (`git rm --cached config/settings.py.backup`) y cambiarse esos valores.
- **Datos de alumnos en el repositorio:** `static/evidencias/` contiene imágenes de evidencia versionadas en git.
- `login_view` no redirige al panel si el usuario ya tiene sesión iniciada (comportamiento previo, no modificado).
- Hay 4 variables locales sin usar (avisos menores de `pyflakes`), heredadas del código original.

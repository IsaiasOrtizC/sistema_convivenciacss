# Demostración técnica: trazabilidad por consola

El servidor puede mostrar, en la consola donde corre `runserver`, **por qué capas pasa cada petición**:
la petición HTTP, la vista (plantilla), el controlador, el servicio, el acceso a la base de datos y la respuesta.
Sirve para comprobar que el sistema funciona como indican los diagramas de secuencia.

## 1. Cómo activarla

1. En tu archivo `.env` agrega:

   ```
   TRAZA_NIVEL=1
   ```

   | Nivel | Qué muestra |
   |---|---|
   | `0` | Nada (valor por defecto cuando `DEBUG=False`). |
   | `1` | Flujo principal: HTTP, vista, controlador, servicio y escrituras en la base de datos. |
   | `2` | Detallado: además **cada consulta SQL** y las comprobaciones de permisos. |

   Para probar un nivel solo en esa terminal (PowerShell): `$env:TRAZA_NIVEL=2; python manage.py runserver`

2. Asegúrate de que `config/settings.py` tenga estas piezas (ver `LEEME_TRAZABILIDAD.txt`):
   - `gestion_casos.trazabilidad.TrazabilidadMiddleware` en `MIDDLEWARE`, justo después de `SessionMiddleware`;
   - `gestion_casos.trazabilidad.TrazabilidadControladorMiddleware` como **último** elemento de `MIDDLEWARE`;
   - la línea `TRAZA_NIVEL = int(os.getenv('TRAZA_NIVEL', '1' if DEBUG else '0'))`.

3. Inicia el servidor: `python manage.py runserver`. Al arrancar verás:
   `[TRAZA] Trazabilidad activada (nivel 1). Cada petición mostrará su recorrido por las capas del sistema.`

## 2. Cómo leer la consola

| Etiqueta | Significado | Diagrama de secuencia |
|---|---|---|
| `[HTTP]` | Petición recibida (método, ruta, usuario) y respuesta entregada (status, destino, tiempo) | El actor y su navegador |
| `[VISTA]` | Plantilla que se renderiza, con el nombre de la vista del diagrama (`V_...`) | `V_GestionUsuarios`, `V_Login`, ... |
| `[CONTROLADOR]` | Controlador que atiende la petición, y componentes de apoyo (`AlertController`, `EmailController`, ...) | `C_Usuario`, `C_Caso`, ... |
| `[API]` | Vista de la API REST (Django REST Framework) | `C_Django Rest` |
| `[SERVICE]` | Lógica de negocio (`CasoService`, ...) | Servicios |
| `[DB]` | Acceso a datos con el ORM de Django: altas, cambios, bajas, filtros y un resumen de consultas | `C_Django ORM` y la entidad (`Usuario`, `Caso`, ...) |
| `[ERROR]` | Excepción no controlada en un controlador | |

Si un filtro anterior responde primero (por ejemplo CSRF o la sesión única), la consola lo dice:
`[CONTROLADOR] RegistrarCasoController: no se ejecutó (un middleware respondió antes: sesión única, CSRF u otro filtro)`.
Así nunca aparece un controlador "iniciado" que en realidad no corrió.

Además, cada controlador informa **su propio mensaje al usuario** (`mensaje (success)`, `mensaje (error)`) y termina con
`completado` o `rechazó la operación`, así se distingue de un vistazo una operación correcta de un acceso denegado.
La última línea `[DB] N consultas ... | SELECT: ... | INSERT: ...` resume qué tablas tocó la petición.

## 3. Ejemplos reales

> Salida capturada ejecutando el sistema con datos de prueba (no con tu base de datos real).

### 1. Abrir la pantalla de acceso (sin iniciar sesión)

```text
[HTTP] GET / usuario=anonimo
[CONTROLADOR] LoginController: inicio
[VISTA] V_Login (login.html): renderizando
[CONTROLADOR] LoginController: completado
[HTTP] GET / status=200 tiempo=12ms
```

### 2. Registrar un caso (POST, el flujo completo del ejemplo del profesor)

```text
[HTTP] POST /casos/nuevo/ usuario=1
[CONTROLADOR] RegistrarCasoController: inicio
[SERVICE] CasoService: validando datos y registrando el caso
[DB] Creando registro de caso
[DB] Caso guardado correctamente id=1
[DB] UPDATE en estudiante (SQL directo)
[DB] INSERT en involucran (SQL directo)
[CONTROLADOR] AlertController: verificando el umbral de casos del curso
[DB] Creando registro de seguimiento de caso
[DB] Seguimiento de caso guardado correctamente id=1
[DB] Creando registro de historial de seguimiento
[DB] Historial de seguimiento guardado correctamente id=1
[DB] Creando registro de notificación
[DB] Notificación guardada correctamente id=1
[DB] Creando registro de historial de notificación
[DB] Historial de notificación guardado correctamente id=1
[DB] Creando registro de historial de usuario
[DB] Historial de usuario guardado correctamente id=1
[CONTROLADOR] RegistrarCasoController: mensaje (success): Caso registrado exitosamente por Isaias.
[CONTROLADOR] RegistrarCasoController: completado
[DB] 18 consultas en 11 ms | INSERT: caso, historial_notificacion, historial_seguimiento_caso, historial_usuario, involucran, notificacion, seguimiento_caso | SELECT: caso, curso, estudiante, lugar, notificacion, regla_institucional, seguimiento_caso, sesion_activa, usuario | UPDATE: estudiante
[HTTP] POST /casos/nuevo/ status=302 -> /casos/ tiempo=11ms
```

### 3. Buscar usuarios con filtros (Caso de uso N°60)

```text
[HTTP] GET /administracion/usuarios/?nombre=ana&estado=activo usuario=1
[CONTROLADOR] GestionDeUsuariosController: inicio
[DB] Consultando usuarios según: nombre='ana', estado='activo'
[VISTA] V_GestionUsuarios (gestion_de_usuarios.html): renderizando
[CONTROLADOR] GestionDeUsuariosController: completado
[DB] 4 consultas en 11 ms | SELECT: curso, rol, sesion_activa, usuario
[HTTP] GET /administracion/usuarios/?nombre=ana&estado=activo status=200 tiempo=11ms
```

### 4. Abrir el listado de casos

```text
[HTTP] GET /casos/ usuario=1
[CONTROLADOR] HistorialCasosController: inicio
[VISTA] V_HistorialCasos (historial_casos.html): renderizando
[CONTROLADOR] HistorialCasosController: completado
[DB] 3 consultas en 5 ms | SELECT: caso, curso, sesion_activa
[HTTP] GET /casos/ status=200 tiempo=5ms
```

### 5. Un Profesor Jefe intenta entrar a una pantalla de administración

```text
[HTTP] GET /administracion/usuarios/ usuario=2
[CONTROLADOR] GestionDeUsuariosController: inicio
[CONTROLADOR] GestionDeUsuariosController: mensaje (error): Acceso denegado: No tienes permisos de Administrador.
[CONTROLADOR] GestionDeUsuariosController: rechazó la operación
[DB] 1 consulta en 1 ms | SELECT: sesion_activa
[HTTP] GET /administracion/usuarios/ status=302 -> /dashboard/ tiempo=1ms
```

### Nivel 2: cada consulta del ORM

```text
[HTTP] GET /administracion/usuarios/?nombre=ana usuario=1
[DB] SELECT sesion_activa (0.1 ms)
[CONTROLADOR] GestionDeUsuariosController: inicio
[DB] Consultando usuarios según: nombre='ana'
[VISTA] V_GestionUsuarios (gestion_de_usuarios.html): renderizando
[DB] SELECT usuario (0.2 ms)
[DB] SELECT rol (0.0 ms)
[DB] SELECT curso (0.0 ms)
[CONTROLADOR] GestionDeUsuariosController: completado
[DB] 4 consultas en 5 ms | SELECT: curso, rol, sesion_activa, usuario
[HTTP] GET /administracion/usuarios/?nombre=ana status=200 tiempo=5ms
```

## 4. Caso de uso N°60 (búsqueda de usuarios) frente al código real

El diagrama de la Figura 5.20 muestra: `V_GestionUsuarios → C_Usuario → C_Django Rest → C_Django ORM → Usuario`.
Esto es lo que el sistema hace realmente y cómo se ve en la consola:

| Paso del diagrama | Qué pasa en el código | Línea de la consola |
|---|---|---|
| Ingresa criterios en la barra de búsqueda | El navegador envía un GET con los filtros | `[HTTP] GET /administracion/usuarios/?nombre=ana&estado=activo usuario=1` |
| Solicitar búsqueda de usuarios | `gestion_de_usuarios_view` (`controllers/user_controller.py`) recibe la petición | `[CONTROLADOR] GestionDeUsuariosController: inicio` |
| Consultar usuarios según nombre, rol, estado o último acceso | El controlador arma la consulta con el ORM | `[DB] Consultando usuarios según: nombre='ana', estado='activo'` (y con nivel 2, cada `SELECT usuario`) |
| Retornar resultados / Cargar registros | El ORM devuelve los usuarios y el controlador los pasa a la plantilla | `[DB] 4 consultas ... SELECT: curso, rol, sesion_activa, usuario` |
| Mostrar resultado de búsqueda | Se renderiza `gestion_de_usuarios.html` | `[VISTA] V_GestionUsuarios (gestion_de_usuarios.html): renderizando` y `[HTTP] ... status=200` |

**Diferencia con el diagrama:** `C_Django Rest` **no participa** en esta búsqueda. La pantalla de gestión de usuarios
consulta el ORM directamente desde el controlador; Django REST Framework solo se usa en la API
(`/api/auth/token/`, `/api/auth/token/refresh/` y `/api/v1/me/`). La consola lo refleja con honestidad: no aparece
ninguna línea `[API]` en ese flujo.

Para que el diagrama y el sistema coincidan hay dos caminos:

1. **Recomendado: corregir el diagrama** quitando `C_Django Rest` de las secuencias de pantallas HTML
   (el flujo real es Vista → Controlador → ORM → Entidad).
2. Cambiar el sistema para que la pantalla consulte un endpoint REST. Es un cambio grande y no aporta nada funcional.

## 5. Comprobar que los controladores funcionan

```powershell
# Verifica que cada URL llega a su controlador (no toca la base de datos)
python manage.py verificar_controladores

# Además envía un GET sin sesión a cada ruta y comprueba la respuesta esperada
python manage.py verificar_controladores --peticiones

# Pruebas automáticas (105 pruebas, usan SQLite en memoria)
python manage.py test gestion_casos --settings=config.test_settings
```

Resultado esperado del primer comando: `48/48 rutas correctas` (45 de la aplicación y 3 de la API).

## 6. Guion sugerido para la demostración

1. Muestra la consola con `[TRAZA] Trazabilidad activada`.
2. Ejecuta `python manage.py verificar_controladores` para mostrar que cada ruta tiene su controlador.
3. En el navegador, abre el login y luego inicia sesión: aparece `LoginController` y `V_Login`.
4. Registra un caso: se ve la cadena HTTP → controlador → servicio → base de datos → redirección.
5. Busca usuarios con filtros y compara la consola con la tabla de la sección 4.
6. Entra con un Profesor Jefe a una pantalla de administración para mostrar `rechazó la operación`.
7. Cambia a `TRAZA_NIVEL=2` para mostrar cada consulta SQL del ORM.

## 7. Limitaciones

- Muestra lo que ocurre **en el servidor**; no ve lo que hace el navegador.
- El envío real de correos lo hace el *worker* de Celery, que imprime en **su propia consola**; en la del servidor solo
  verás `EmailController: encolando el envío de correo (Celery)`.
- Imprime rutas con sus parámetros de búsqueda y los identificadores de los registros, pero **nunca el cuerpo de las
  peticiones** (por eso las contraseñas no aparecen). Aun así, es una herramienta de desarrollo y demostración:
  déjala en `TRAZA_NIVEL=0` en producción.
- Los colores aparecen solo si la terminal los admite (Windows Terminal, VS Code); si no, el texto sale sin color.

# ConviData

Sistema web para la **gestión, registro y seguimiento de casos de convivencia escolar**, desarrollado para centralizar la información de estudiantes, usuarios, casos, notificaciones y estadísticas dentro de un establecimiento educacional.

El proyecto corresponde al desarrollo de la plataforma **ConviData**, realizada para la asignatura **Ingeniería de Software II – 2026**.

---

## Descripción

ConviData permite gestionar digitalmente diferentes procesos relacionados con la convivencia escolar, facilitando el registro de casos, seguimiento de incidentes y administración de información asociada a estudiantes y usuarios.

El sistema contempla distintos roles de usuario, permitiendo controlar el acceso a las funcionalidades según los permisos correspondientes.

### Roles del sistema

* Administrador
* Inspector
* Profesor
* Equipo de Convivencia

## Tecnologías utilizadas

### Backend

* Python 3.12
* Django 5.2
* Django REST Framework
* PostgreSQL
* JWT
* Cloudinary
* django-cloudinary-storage

### Frontend

* HTML5
* CSS3
* JavaScript
* Django Templates

### API autenticada con JWT

El sitio web conserva su autenticación de sesión. Para clientes de API:

* `POST /api/auth/token/` recibe JSON `{"correo": "...", "contrasena": "..."}` y devuelve `access` y `refresh`.
* `POST /api/auth/token/refresh/` recibe JSON `{"refresh": "..."}` y devuelve un nuevo `access`.
* `GET /api/v1/me/` devuelve la identidad y el rol del usuario autenticado.

Las solicitudes protegidas deben incluir `Authorization: Bearer <access>`.
Los tokens de acceso vencen a los 15 minutos y los refresh a las 24 horas. Las
cuentas inactivas, bloqueadas o pendientes de cambiar su contraseña temporal no
pueden obtener ni renovar tokens.

### Herramientas

* Git
* GitHub
* Visual Studio Code

---

## Estructura del proyecto

```text
sistema_convivenciacss/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── gestion_casos/
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── admin.py
│
├── media/
│
├── static/
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/IsaiasOrtizC/sistema_convivenciacss.git
```

Ingresar al directorio del proyecto:

```bash
cd Proyecto_Convidata-GRUPO-13
```

Si el código Django se encuentra dentro de otra carpeta:

```bash
cd sistema_convivenciacss
```

---

## 2. Crear entorno virtual

Se recomienda utilizar un entorno virtual para mantener aisladas las dependencias del proyecto.

### Linux / macOS

```bash
python3 -m venv venv
```

Activar:

```bash
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
```

Activar:

```powershell
venv\Scripts\activate
```

Al activarse correctamente debería aparecer `(venv)` al inicio de la terminal.

---

## 3. Instalar dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Si el proyecto no posee todavía un archivo `requirements.txt`, se pueden instalar las dependencias principales mediante:

```bash
pip install django
pip install djangorestframework
pip install psycopg2-binary
pip install PyJWT
pip install cloudinary
pip install django-cloudinary-storage
```

---

# Configuración del entorno

La configuración local se carga desde `.env`. Crea el archivo a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

En Linux o macOS:

```bash
cp .env.example .env
```

Completa en `.env` la clave de Django y las credenciales PostgreSQL de Supabase. Las variables opcionales para Resend, Cloudinary y Celery también están documentadas en la plantilla. No subas `.env` al repositorio: contiene credenciales y está excluido por `.gitignore`.

---

# Configuración de Cloudinary

El sistema utiliza **Cloudinary** para el almacenamiento de imágenes.

Instalar las dependencias:

```bash
pip install cloudinary
pip install django-cloudinary-storage
```

Luego configurar las credenciales correspondientes.

Ejemplo:

```python
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'TU_CLOUD_NAME',
    'API_KEY': 'TU_API_KEY',
    'API_SECRET': 'TU_API_SECRET',
}
```
---

# Migraciones

Una vez configurada la base de datos, ejecutar:

```bash
python manage.py makemigrations
```

Luego:

```bash
python manage.py migrate
```

Para comprobar el estado de las migraciones:

```bash
python manage.py showmigrations
```

# Ejecutar el proyecto

Con el entorno virtual activado:

```bash
python manage.py runserver
```

El servidor estará disponible normalmente en:

```text
http://127.0.0.1:8000/
```

Para detener el servidor:

```text
CTRL + C
```

---

# Comandos útiles

### Verificar Django

```bash
python manage.py check
```

### Crear migraciones

```bash
python manage.py makemigrations
```

### Aplicar migraciones

```bash
python manage.py migrate
```

### Ejecutar servidor

```bash
python manage.py runserver
```


### Abrir consola de Django

```bash
python manage.py shell
```

---

El archivo `.env` no debe ser subido a GitHub.

Agregar al `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
media/
```

---

# Flujo de trabajo con Git

Para obtener los últimos cambios del repositorio:

```bash
git pull
```

Para revisar el estado:

```bash
git status
```

Para crear una nueva rama:

```bash
git checkout -b nombre-de-la-rama
```

Para agregar cambios:

```bash
git add .
```

Para realizar un commit:

```bash
git commit -m "Descripción del cambio"
```

Para subir los cambios:

```bash
git push
```

---

# Equipo de Desarrollo

Proyecto desarrollado por:

* Max Fernandez
* Matías Urria
* Isaias Ortiz
* Osvaldo Caraccioli
* Maximiliano Soto
* Benjamin Orellana

---

# Contexto académico

**Asignatura:** Ingeniería de Software II
**Año:** 2026
**Proyecto:** ConviData

---

# Estado del proyecto

**En desarrollo**

---

# Reglamento institucional, notificaciones y seguimiento

Los administradores pueden cargar reglamentos PDF de hasta 20 MB. El backend
valida la extensión y la firma PDF, almacena el archivo en Cloudinary y extrae
texto seleccionable con `pypdf`. Las páginas escaneadas o con texto insuficiente
se procesan con PyMuPDF y Tesseract en español (`spa`); los PDF mixtos conservan
la extracción directa en las páginas que ya tienen texto. El extractor no
convierte párrafos arbitrarios en propuestas: las 316 propuestas históricas se
conservan intactas y no se reprocesan automáticamente. Las nuevas disposiciones
deben provenir de citas verificadas, conservan la referencia impresa y la página
real del PDF, y quedan pendientes de revisión humana.

El procesamiento actual es síncrono: no se usa Celery porque no se ha confirmado
un broker Redis operativo. Si el procesamiento falla, el documento conserva el
estado y un error explicativo; Administrador puede iniciar manualmente un
reprocesamiento desde la misma pantalla de documentos. Abrir o visualizar un PDF
no inicia OCR. Reprocesar actualiza la extracción guardada, pero no cambia reglas
ni versiones existentes; si un documento todavía no tiene versión, se crea una
versión borrador y sus propuestas quedan pendientes de revisión humana.

El modelo estructurado distingue anotaciones, faltas y reincidencias, y permite
marcar una cantidad como definida, no especificada, no aplicable o aún no
verificada. Las disposiciones verificadas del Reglamento 2026 se importan en
modalidad de solo presentación: exponen evidencia y medida para revisión, sin
crear sanciones, notificaciones ni acciones automáticamente. El sistema no tiene
un registro separado de anotaciones. Para los umbrales expresamente asociados a
anotaciones negativas de faltas leves, se cuentan casos distintos del estudiante
cuya gravedad sea Leve; casos graves o gravísimos no contribuyen a ese total y
actualizar el mismo caso no lo incrementa. Este mapeo solo puede usarse cuando
la regla aprobada declara unidad de anotaciones y un umbral de casos coincidente.

Para agregar las disposiciones estructuradas, el administrador primero debe
cargar y procesar exactamente el PDF oficial verificado en una versión borrador.
La operación valida su SHA-256 y vuelve a cotejar cada cita y número de página
con el archivo almacenado:

```powershell
.\.venv\Scripts\python.exe manage.py importar_disposiciones_reglamento_2026 --version-id <ID>
```

El comando es aditivo, no sobrescribe ni elimina reglas existentes, es
idempotente para el catálogo verificado y deja las nuevas disposiciones
pendientes de aprobación. No se
mezcla con reglas históricas: si la versión indicada ya contiene propuestas,
crea una nueva versión borrador para mantenerlas intactas y revisables. El comando
informa el identificador de esa versión destino. No se debe ejecutar contra
Supabase hasta que se aprueben el esquema y el procedimiento sobre la versión
correspondiente.

Despliegue reversible: crea y restaura un respaldo en staging que reproduzca
tanto el esquema como el historial `django_migrations` de producción. Ejecuta
allí `manage.py migrate --plan` y revisa cada operación antes de aplicar nada.
El plan contra una base nueva incluye migraciones iniciales y creación de tablas;
no demuestra qué migraciones están pendientes en Supabase ni autoriza aplicarlas
sobre tablas preexistentes. Reconcilia primero el historial de migraciones con
el esquema real; luego aplica en staging únicamente el plan aprobado y ejecuta
`manage.py check` y las pruebas.

En producción, respalda la base, verifica allí el plan real y la reconciliación
del esquema, obtiene aprobación explícita y aplica únicamente las migraciones
aprobadas antes de desplegar el código. Mantén el catálogo sin importar hasta
completar la revisión humana; después, importa solo con autorización expresa y
registra el ID de versión destino. Para volver atrás, revierte el código y deja
las columnas aditivas y las disposiciones intactas; no reviertas ni elimines
columnas o reglas con datos sin un respaldo y un procedimiento de restauración
aprobado. La revisión autorizada debe confirmar excepciones, redacción impresa,
permisos de Director y compatibilidad operativa antes de considerar el catálogo
para uso real.

### Instalar y configurar OCR

Las dependencias Python se instalan junto al resto del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` incluye `PyMuPDF`, `pytesseract` y `Pillow`; estos paquetes
no instalan el ejecutable Tesseract ni sus archivos de idioma.

En Windows, instala Tesseract OCR usando un instalador de Windows y selecciona
el idioma Spanish (`spa`). Comprueba en PowerShell:

```powershell
tesseract --version
tesseract --list-langs
```

La lista debe incluir `spa`. Si Tesseract no está en `PATH`, agrega al archivo
local `.env` las rutas de la instalación y de la carpeta que contiene
`spa.traineddata`:

```dotenv
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
```

En producción Linux, instala los paquetes del sistema en la imagen/entorno de
ejecución, además de instalar `requirements.txt`:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa
tesseract --version
tesseract --list-langs
```

Si el proveedor usa contenedores, incluye esos paquetes en la imagen. En
plataformas administradas, instala las dependencias del sistema mediante el
mecanismo admitido por ese proveedor y configura `TESSERACT_CMD` y
`TESSDATA_PREFIX` si las rutas no están en `PATH` o en la ruta estándar. El
repositorio no contiene configuración que permita confirmar cuál es el hosting
de producción; verifica esto con el proveedor antes de desplegar.

Los límites se configuran por variables de entorno: `REGLAMENTO_PDF_MAX_BYTES`
(20 MiB), `REGLAMENTO_PDF_MAX_PAGES` (500), `REGLAMENTO_PDF_MIN_TEXT_CHARS`
(30 por página para preferir OCR), `REGLAMENTO_PDF_MIN_USEFUL_CHARS` (30 por
documento), `REGLAMENTO_OCR_MAX_PAGES` (50), `REGLAMENTO_OCR_DPI` (200) y
`REGLAMENTO_OCR_TIMEOUT_SECONDS` (30 por página). Se pueden ajustar según los
recursos disponibles en el hosting.

Para probar con un reglamento real, instala Tesseract y `spa`, inicia Django,
carga desde Documentos un PDF escaneado legible y verifica que el estado de
procesamiento sea «Completado» y que el texto extraído aparezca en la revisión
del reglamento. Las propuestas detectadas deben continuar pendientes hasta su
aprobación manual. Para un documento que falló antes de instalar Tesseract, usa
«Reprocesar texto» en esa misma pantalla. El OCR puede requerir tiempo para
documentos largos; hay límites de tamaño, páginas, páginas OCR y tiempo por
página.

Las notificaciones y acciones se almacenan con claves de idempotencia, estados,
responsables, fechas límite e historial. Administrador y `PConvivencia` pueden
gestionarlas y cerrar seguimientos; Inspector solo consulta; Profesor Jefe no
puede acceder al módulo. El progreso se calcula dando el mismo peso a cada
acción requerida y no se muestra porcentaje cuando no existen acciones.

El Profesor Jefe puede enviar reportes de incidentes solo para los estudiantes
de su curso asignado. Estos se guardan como solicitudes pendientes separadas y
no crean casos oficiales ni afectan la bitácora, estadísticas o antecedentes
hasta que Administrador, Inspector o `PConvivencia` los apruebe desde «Revisar
casos pendientes». Los reportes rechazados conservan el estado y comentario de
revisión para que el profesor pueda consultarlos.

Las nuevas tablas y columnas están descritas en las migraciones
`gestion_casos/migrations/0008_documentoinstitucional_checksum_sha256_and_more.py`
y `gestion_casos/migrations/0009_reglainstitucional_umbral_anotaciones.py`,
`gestion_casos/migrations/0010_notificacion_evento_tipo_and_more.py`,
`gestion_casos/migrations/0011_reglainstitucional_disposicion_verificada.py` y
`gestion_casos/migrations/0014_solicitudcaso.py`.
**No ejecutes `migrate` contra Supabase sin que el
responsable de la base de datos revise primero las migraciones y autorice el
cambio.** No se aplicaron migraciones durante el desarrollo.

Para validar sin conectarse a Supabase:

```powershell
.\.venv\Scripts\python.exe manage.py check --settings=config.test_settings
.\.venv\Scripts\python.exe manage.py test gestion_casos.tests --settings=config.test_settings
```

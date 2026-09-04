# ConviData

Sistema web para la **gestión, registro y seguimiento de casos de convivencia escolar**, desarrollado para centralizar la información de estudiantes, usuarios, casos, notificaciones y estadísticas dentro de un establecimiento educacional.

El proyecto corresponde al desarrollo de la plataforma **ConviData**, realizada para la asignatura **Ingeniería de Software I – 2026**.

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
git clone https://github.com/Matias0752/Proyecto_Convidata-GRUPO-13.git
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

# Configuración de PostgreSQL

ConviData utiliza **PostgreSQL** como sistema de gestión de base de datos.

Se debe crear una base de datos antes de ejecutar el proyecto.

Ejemplo:

```sql
CREATE DATABASE convivencia_escolar;
```

Luego se deben configurar las credenciales de la base de datos en `settings.py` o, preferentemente, mediante variables de entorno.

Ejemplo:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'convivencia_escolar',
        'USER': 'postgres',
        'PASSWORD': 'TU_CONTRASEÑA',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

No se deben subir contraseñas reales al repositorio de GitHub.

Se recomienda utilizar un archivo `.env` y agregarlo al `.gitignore`.

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



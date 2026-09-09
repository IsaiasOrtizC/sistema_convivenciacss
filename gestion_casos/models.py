import re
import unicodedata
from django.db import models
from django.utils import timezone


def _quitar_tildes(texto):
    """Quita tildes/acentos de un texto (ej: 'Á' -> 'A'), para que el
    identificador del alumno solo use letras planas, como exige el formato."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def generar_identificador_alumno(nombre, apaterno, numero_lista, curso_grado, curso_letra):
    """
    Genera el identificador único de 7 caracteres para un alumno, según el formato:
    [Inicial Nombre][Inicial Apellido][N° Lista (2 dígitos)][Curso][Nivel][Paralelo]

    Ejemplo: Juan Pérez, lista N°5, 3° Medio, paralelo A -> "JP053MA"

    Reglas:
    - Básica: cursos válidos del 1 al 8 (nivel 'B')
    - Media: cursos válidos del 1 al 4 (nivel 'M')
    - El N° de lista es por curso + paralelo (no es global)

    Devuelve None si falta algún dato o si el resultado no cumple el formato
    (^[A-ZÑ]{2}\\d{2}([1-8]B|[1-4]M)[A-Z]$).
    """
    if not (nombre and apaterno and numero_lista and curso_grado and curso_letra):
        return None

    inicial_nombre = _quitar_tildes(nombre.strip()[0]).upper()
    inicial_apaterno = _quitar_tildes(apaterno.strip()[0]).upper()

    if not inicial_nombre.isalpha() or not inicial_apaterno.isalpha():
        return None

    try:
        lista_str = f"{int(numero_lista):02d}"
    except (ValueError, TypeError):
        return None

    match_curso = re.search(r'(\d+)', curso_grado)
    if not match_curso:
        return None
    curso_num = int(match_curso.group(1))

    curso_grado_normalizado = _quitar_tildes(curso_grado).lower()
    if 'basica' in curso_grado_normalizado:
        nivel = 'B'
        if not (1 <= curso_num <= 8):
            return None
    elif 'medio' in curso_grado_normalizado:
        nivel = 'M'
        if not (1 <= curso_num <= 4):
            return None
    else:
        return None

    paralelo = curso_letra.strip().upper()[:1]
    if not paralelo.isalpha():
        return None

    identificador = f"{inicial_nombre}{inicial_apaterno}{lista_str}{curso_num}{nivel}{paralelo}"

    # Validación final contra el regex oficial de la especificación
    if not re.match(r'^[A-ZÑ]{2}\d{2}([1-8]B|[1-4]M)[A-Z]$', identificador):
        return None

    return identificador

# 1. TABLA ROL
class Rol(models.Model):
    rol_id = models.AutoField(primary_key=True)
    rol_nombre = models.CharField(max_length=100)
    rol_descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'rol'       
        managed = False        

    def __str__(self):
        return self.rol_nombre

# 2. TABLA USUARIO
class Usuario(models.Model):
    usuario_id = models.AutoField(primary_key=True)
    usuario_nombre = models.CharField(max_length=100)
    usuario_apaterno = models.CharField(max_length=100)
    usuario_amaterno = models.CharField(max_length=100)
    usuario_correo = models.EmailField(unique=True)
    usuario_contrasena = models.CharField(max_length=255)
    usuario_ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    usuario_primer_ingreso = models.BooleanField(default=True)
    usuario_activo = models.BooleanField(default=True)
    
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='rol_id')

    class Meta:
        db_table = 'usuario'   
        managed = False  

    def __str__(self):
        return f"{self.usuario_nombre} {self.usuario_apaterno} ({self.rol.rol_nombre})"

# 3. TABLA CURSO
class Curso(models.Model):
    curso_id = models.AutoField(primary_key=True)
    curso_grado = models.CharField(max_length=50)
    curso_letra = models.CharField(max_length=1)

    class Meta:
        db_table = 'curso'     
        managed = False

    def __str__(self):
        return f"{self.curso_grado} {self.curso_letra}"

# 4. TABLA ESTUDIANTE
class Estudiante(models.Model):
    estudiante_id = models.AutoField(primary_key=True)
    estudiante_nombre = models.CharField(max_length=100)
    estudiante_apaterno = models.CharField(max_length=100)
    estudiante_amaterno = models.CharField(max_length=100)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, db_column='curso_id')
    estudiante_numero_lista = models.IntegerField(null=True, blank=True)
    estudiante_identificador = models.CharField(max_length=10, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'estudiante' 
        managed = False

    def __str__(self):
        return f"{self.estudiante_nombre} {self.estudiante_apaterno}"

    def save(self, *args, **kwargs):
        # Recalcula el identificador único cada vez que se guarda el alumno,
        # siempre que tenga los datos necesarios (nombre, apellido, N° lista y curso).
        if self.estudiante_numero_lista and self.curso_id:
            try:
                curso_obj = self.curso
            except Curso.DoesNotExist:
                curso_obj = None
            if curso_obj:
                nuevo_id = generar_identificador_alumno(
                    self.estudiante_nombre,
                    self.estudiante_apaterno,
                    self.estudiante_numero_lista,
                    curso_obj.curso_grado,
                    curso_obj.curso_letra,
                )
                if nuevo_id:
                    self.estudiante_identificador = nuevo_id
        super().save(*args, **kwargs)

# 5. TABLA LUGAR
class Lugar(models.Model):
    lugar_id = models.AutoField(primary_key=True)
    lugar_nombre = models.CharField(max_length=100)
    lugar_descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'lugar'     
        managed = False

    def __str__(self):
        return self.lugar_nombre

# 6. TABLA CASO
class Caso(models.Model):
    caso_id = models.AutoField(primary_key=True)
    caso_fecha = models.DateField()
    caso_descripcion = models.TextField()
    evidencia = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column='usuario_id')
    lugar = models.ForeignKey(Lugar, on_delete=models.PROTECT, db_column='lugar_id')
    estudiantes = models.ManyToManyField(Estudiante, through='Involucran')
    # Fecha/hora REAL en que se registró el caso en el sistema (distinta de caso_fecha,
    # que es la fecha del suceso elegida manualmente). Se usa para la regla de las 12 horas (RF-53).
    caso_creado_en = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        db_table = 'caso'      
        managed = False

    def __str__(self):
        return f"Caso #{self.caso_id} - {self.caso_fecha}"

# 7. TABLA INTERMEDIA: INVOLUCRAN
class Involucran(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, db_column='estudiante_id')
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, db_column='caso_id')
    tipo_falta = models.CharField(max_length=100)

    class Meta:
        db_table = 'involucran' 
        managed = False
        unique_together = (('estudiante', 'caso'),)

#ROLES

class Administrador(models.Model):
    administrador_id = models.AutoField(primary_key=True)
    admin_nombre = models.CharField(max_length=100)
    admin_apaterno = models.CharField(max_length=100)
    admin_amaterno = models.CharField(max_length=100)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'administrador' 
        managed = False

class Inspector(models.Model):
    inspector_id = models.AutoField(primary_key=True)
    inspector_nombre = models.CharField(max_length=100)
    inspector_apaterno = models.CharField(max_length=100)
    inspector_amaterno = models.CharField(max_length=100)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'inspector' 
        managed = False

class PConvivencia(models.Model):
    pconvivencia_id = models.AutoField(primary_key=True)
    convivencia_nombre = models.CharField(max_length=100)
    convivencia_apaterno = models.CharField(max_length=100)
    convivencia_amaterno = models.CharField(max_length=100)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'pconvivencia' 
        managed = False

class ProfesorJefe(models.Model):
    profesorjefe_id = models.AutoField(primary_key=True)
    profesor_nombre = models.CharField(max_length=100)
    profesor_apaterno = models.CharField(max_length=100)
    profesor_amaterno = models.CharField(max_length=100)
    curso = models.OneToOneField(Curso, on_delete=models.SET_NULL, null=True, db_column='curso_id')
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'profesorjefe' 
        managed = False

#tabla notificaciones

class Notificacion(models.Model):
    notificacion_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    
    notificacion_titulo = models.CharField(max_length=150)
    notificacion_mensaje = models.TextField()
    notificacion_fecha = models.DateTimeField(default=timezone.now)
    notificacion_leido = models.BooleanField(default=False)
    notificacion_icono = models.CharField(max_length=10, default='🔔')

    class Meta:
        db_table = 'notificacion'
        ordering = ['-notificacion_fecha']

    def __str__(self):
        return f"{self.notificacion_titulo} - {self.usuario.usuario_nombre}"
    
class HistorialUsuario(models.Model):
    historial_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='historial_acciones')
    
    historial_accion = models.CharField(max_length=50) # 'Creación' o 'Modificación'
    historial_detalle = models.TextField() # Detalles si creo o edito un caso
    historial_fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'historial_usuario'
        ordering = ['-historial_fecha']

    def __str__(self):
        return f"{self.usuario.usuario_nombre} - {self.historial_accion} - {self.historial_fecha}"


# TABLA DOCUMENTOS INSTITUCIONALES (Reglamento Interno / Protocolos de Convivencia)
class DocumentoInstitucional(models.Model):
    TIPO_CHOICES = [
        ('Reglamento', 'Reglamento Interno'),
        ('Protocolo', 'Protocolo de Convivencia'),
    ]

    documento_id = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=150)
    archivo = models.FileField(upload_to='documentos_institucionales/')
    fecha_subida = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, db_column='usuario_id')

    class Meta:
        db_table = 'documento_institucional'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_documento_display()})"


# CONTROL DE SESIÓN ÚNICA POR USUARIO
class SesionActiva(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE, db_column='usuario_id')
    session_key = models.CharField(max_length=40)
    fecha_inicio = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'sesion_activa'

    def __str__(self):
        return f"Sesión activa de {self.usuario.usuario_nombre}"
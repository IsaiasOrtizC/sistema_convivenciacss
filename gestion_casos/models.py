import re
import unicodedata
from django.db import models
from django.utils import timezone
from cloudinary_document_storage import CloudinaryDocumentStorage


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

    # RF: bloqueo de cuenta tras 5 intentos fallidos consecutivos de inicio de sesión
    usuario_intentos_fallidos = models.IntegerField(default=0)
    usuario_bloqueado = models.BooleanField(default=False)
    
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='rol_id')

    class Meta:
        db_table = 'usuario'   
        managed = False  

    @property
    def is_authenticated(self):
        return True

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
    estudiante_correo = models.EmailField(null=True, blank=True)
    estudiante_activo = models.BooleanField(default=True)
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
    class Estado(models.TextChoices):
        ESPERA = 'espera', 'En espera de resolución'
        REVISION = 'revision', 'En revisión'
        SOLUCIONADO = 'solucionado', 'Solucionado'

    class TipoEvento(models.TextChoices):
        CASO_CREADO = 'caso_creado', 'Caso registrado'
        CASO_ACTUALIZADO = 'caso_actualizado', 'Caso actualizado'

    notificacion_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    
    notificacion_titulo = models.CharField(max_length=150)
    notificacion_mensaje = models.TextField()
    notificacion_fecha = models.DateTimeField(default=timezone.now)
    notificacion_leido = models.BooleanField(default=False)
    notificacion_icono = models.CharField(max_length=10, default='🔔')
    regla = models.ForeignKey(
        'ReglaInstitucional', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notificaciones',
    )
    version_reglamento = models.ForeignKey(
        'VersionReglamento', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notificaciones',
    )
    caso = models.ForeignKey(
        'Caso', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notificaciones',
    )
    estudiante = models.ForeignKey(
        'Estudiante', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notificaciones',
    )
    evento_tipo = models.CharField(
        max_length=30, choices=TipoEvento.choices, blank=True, default='',
    )
    evento_clave = models.CharField(max_length=160, unique=True, null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ESPERA,
    )
    fecha_limite = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notificaciones_asignadas',
    )

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
    class EstadoProcesamiento(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        PROCESANDO = 'procesando', 'Procesando'
        COMPLETADO = 'completado', 'Completado'
        ERROR = 'error', 'Error'

    TIPO_CHOICES = [
        ('Reglamento', 'Reglamento Interno'),
        ('Protocolo', 'Protocolo de Convivencia'),
    ]

    documento_id = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=150)
    archivo = models.FileField(
        upload_to='documentos_institucionales/',
        storage=CloudinaryDocumentStorage(),
    )
    fecha_subida = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, db_column='usuario_id')
    estado_procesamiento = models.CharField(
        max_length=20,
        choices=EstadoProcesamiento.choices,
        default=EstadoProcesamiento.PENDIENTE,
    )
    texto_extraido = models.TextField(blank=True)
    error_procesamiento = models.TextField(blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    numero_paginas = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'documento_institucional'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_documento_display()})"


class VersionReglamento(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        VIGENTE = 'vigente', 'Vigente'
        REEMPLAZADA = 'reemplazada', 'Reemplazada'

    documento = models.ForeignKey(
        DocumentoInstitucional, on_delete=models.CASCADE, related_name='versiones_reglamento',
    )
    numero = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    creada_en = models.DateTimeField(default=timezone.now)
    creada_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='versiones_reglamento_creadas',
    )
    activada_en = models.DateTimeField(null=True, blank=True)
    activada_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='versiones_reglamento_activadas',
    )

    class Meta:
        db_table = 'version_reglamento'
        ordering = ['-creada_en']
        constraints = [
            models.UniqueConstraint(
                fields=['documento', 'numero'], name='uniq_version_por_documento',
            ),
        ]

    def __str__(self):
        return f"{self.documento.titulo} v{self.numero}"


class ReglaInstitucional(models.Model):
    class TipoMedida(models.TextChoices):
        CLASIFICACION = 'clasificacion', 'Clasificación de falta'
        PEDAGOGICA = 'pedagogica', 'Medida pedagógica/formativa'
        REPARATORIA = 'reparatoria', 'Medida reparatoria'
        PREVENTIVA = 'preventiva', 'Medida preventiva'
        SANCION_DISCIPLINARIA = 'sancion_disciplinaria', 'Sanción disciplinaria'
        RESOLUCION_ALTERNATIVA = 'resolucion_alternativa', 'Resolución alternativa de conflictos'
        NO_CLASIFICADA = 'no_clasificada', 'Tipo de medida pendiente de verificar'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de revisión'
        APROBADA = 'aprobada', 'Aprobada'
        RECHAZADA = 'rechazada', 'Rechazada'

    class Activador(models.TextChoices):
        MANUAL = 'manual', 'Sin evaluación automática'
        NUEVO_CASO = 'nuevo_caso', 'Al registrar un caso de esta categoría'
        UMBRAL_CASOS = 'umbral_casos', 'Al alcanzar un umbral de casos de esta categoría'

    class UnidadUmbral(models.TextChoices):
        ANOTACIONES = 'anotaciones', 'Anotaciones'
        FALTAS = 'faltas', 'Faltas'
        REINCIDENCIAS = 'reincidencias', 'Reincidencias'

    class EstadoCantidad(models.TextChoices):
        DEFINIDA = 'definida', 'Cantidad definida en el reglamento'
        NO_ESPECIFICADA = 'no_especificada', 'El reglamento no especifica cantidad'
        NO_APLICA = 'no_aplica', 'No aplica'
        NO_VERIFICADA = 'no_verificada', 'Cantidad aún no verificada'

    class UnidadDuracion(models.TextChoices):
        DIAS = 'dias', 'Días'
        DIAS_HABILES = 'dias_habiles', 'Días hábiles'
        NO_VERIFICADA = 'no_verificada', 'Unidad no verificada'

    class RolResponsable(models.TextChoices):
        ADMINISTRADOR = 'Administrador', 'Administrador'
        CONVIVENCIA = 'PConvivencia', 'Equipo de Convivencia'
        INSPECTOR = 'Inspector', 'Inspector'

    class ReferenciaPlazo(models.TextChoices):
        SIN_DEFINIR = 'sin_definir', 'Inicio no definido; no calcular fecha'
        EVENTO = 'evento', 'Desde el evento que activa la regla'

    version = models.ForeignKey(
        VersionReglamento, on_delete=models.CASCADE, related_name='reglas',
    )
    titulo = models.CharField(max_length=180)
    categoria_falta = models.CharField(max_length=100, blank=True)
    activador = models.CharField(
        max_length=20, choices=Activador.choices, default=Activador.MANUAL,
    )
    umbral_casos = models.PositiveIntegerField(null=True, blank=True)
    umbral_anotaciones = models.PositiveIntegerField(null=True, blank=True)
    conducta_condicion = models.TextField(blank=True)
    unidad_umbral = models.CharField(
        max_length=20, choices=UnidadUmbral.choices, blank=True,
    )
    cantidad_minima = models.PositiveIntegerField(null=True, blank=True)
    estado_cantidad = models.CharField(
        max_length=20,
        choices=EstadoCantidad.choices,
        default=EstadoCantidad.NO_VERIFICADA,
    )
    accion_requerida = models.TextField(blank=True)
    medida_asociada = models.TextField(blank=True)
    tipo_medida = models.CharField(
        max_length=30,
        choices=TipoMedida.choices,
        default=TipoMedida.NO_CLASIFICADA,
    )
    duracion_minima_dias = models.PositiveIntegerField(null=True, blank=True)
    duracion_maxima_dias = models.PositiveIntegerField(null=True, blank=True)
    unidad_duracion = models.CharField(
        max_length=20,
        choices=UnidadDuracion.choices,
        default=UnidadDuracion.NO_VERIFICADA,
    )
    condiciones = models.TextField(blank=True)
    excepciones = models.TextField(blank=True)
    requiere_citacion_apoderado = models.BooleanField(default=False)
    solo_presentacion = models.BooleanField(default=False)
    plazo_dias = models.PositiveIntegerField(null=True, blank=True)
    plazo_desde = models.CharField(
        max_length=20,
        choices=ReferenciaPlazo.choices,
        default=ReferenciaPlazo.SIN_DEFINIR,
    )
    responsable_rol = models.CharField(
        max_length=30, choices=RolResponsable.choices, blank=True,
    )
    evidencia_textual = models.TextField()
    referencia_origen = models.CharField(max_length=120, blank=True)
    titulo_fuente = models.CharField(max_length=100, blank=True)
    version_fuente = models.CharField(max_length=100, blank=True)
    seccion_fuente = models.CharField(max_length=180, blank=True)
    pagina_impresa = models.PositiveIntegerField(null=True, blank=True)
    pagina_pdf = models.PositiveIntegerField(null=True, blank=True)
    pagina_impresa_hasta = models.PositiveIntegerField(null=True, blank=True)
    pagina_pdf_hasta = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE,
    )
    revisada_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='reglas_revisadas',
    )
    revisada_en = models.DateTimeField(null=True, blank=True)
    hash_origen = models.CharField(max_length=64)

    class Meta:
        db_table = 'regla_institucional'
        ordering = ['version_id', 'referencia_origen', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['version', 'hash_origen'], name='uniq_regla_origen_por_version',
            ),
        ]

    def __str__(self):
        return self.titulo

    def puede_activarse(self):
        if not self.evidencia_textual.strip():
            return False
        if self.solo_presentacion:
            tiene_disposicion = any((
                self.categoria_falta.strip(),
                self.conducta_condicion.strip(),
                self.medida_asociada.strip(),
            ))
            tiene_origen_verificable = all((
                self.version_fuente.strip(),
                self.titulo_fuente.strip(),
                self.seccion_fuente.strip(),
                self.pagina_impresa,
                self.pagina_pdf,
            ))
            return bool(
                self.tipo_medida != self.TipoMedida.NO_CLASIFICADA
                and tiene_disposicion
                and tiene_origen_verificable
            )
        if not self.accion_requerida.strip() or not self.categoria_falta.strip():
            return False
        if re.search(r'\banotaci[oó]n(?:es)?\b', self.evidencia_textual, re.IGNORECASE):
            if (
                self.activador != self.Activador.UMBRAL_CASOS
                or self.unidad_umbral != self.UnidadUmbral.ANOTACIONES
                or self.cantidad_minima != self.umbral_casos
            ):
                return False
        if self.activador == self.Activador.UMBRAL_CASOS:
            return bool(self.umbral_casos and self.umbral_casos > 0)
        return self.activador in (
            self.Activador.MANUAL,
            self.Activador.NUEVO_CASO,
        )


class SeguimientoCaso(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = 'abierto', 'En seguimiento'
        SOLUCIONADO = 'solucionado', 'Solucionado'

    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='seguimientos')
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='seguimientos_casos',
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    creado_en = models.DateTimeField(default=timezone.now)
    solucionado_en = models.DateTimeField(null=True, blank=True)
    solucionado_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='seguimientos_cerrados',
    )
    motivo_cierre = models.TextField(blank=True)

    class Meta:
        db_table = 'seguimiento_caso'
        constraints = [
            models.UniqueConstraint(
                fields=['caso', 'estudiante'], name='uniq_seguimiento_caso_estudiante',
            ),
        ]

    @property
    def porcentaje_avance(self):
        total = self.acciones.count()
        if not total:
            return None
        completadas = self.acciones.filter(estado=AccionSeguimiento.Estado.COMPLETADA).count()
        return round(completadas * 100 / total)


class AccionSeguimiento(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADA = 'completada', 'Completada'

    seguimiento = models.ForeignKey(
        SeguimientoCaso, on_delete=models.CASCADE, related_name='acciones',
    )
    regla = models.ForeignKey(
        ReglaInstitucional, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='acciones_seguimiento',
    )
    notificacion = models.ForeignKey(
        Notificacion, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='acciones_seguimiento',
    )
    titulo = models.CharField(max_length=180)
    responsable = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='acciones_asignadas',
    )
    responsable_rol = models.CharField(max_length=30, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE,
    )
    creada_en = models.DateTimeField(default=timezone.now)
    completada_en = models.DateTimeField(null=True, blank=True)
    clave_idempotencia = models.CharField(max_length=180, unique=True)

    class Meta:
        db_table = 'accion_seguimiento'
        ordering = ['estado', 'fecha_limite', 'creada_en']


class HistorialNotificacion(models.Model):
    notificacion = models.ForeignKey(
        Notificacion, on_delete=models.CASCADE, related_name='historial_estados',
    )
    estado = models.CharField(max_length=20, choices=Notificacion.Estado.choices)
    cambiado_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
    )
    motivo = models.TextField(blank=True)
    cambiado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'historial_notificacion'
        ordering = ['cambiado_en', 'pk']


class HistorialAccionSeguimiento(models.Model):
    accion = models.ForeignKey(
        AccionSeguimiento, on_delete=models.CASCADE, related_name='historial',
    )
    estado = models.CharField(max_length=20, choices=AccionSeguimiento.Estado.choices)
    cambiado_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
    )
    motivo = models.TextField(blank=True)
    cambiado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'historial_accion_seguimiento'
        ordering = ['cambiado_en', 'pk']


class HistorialSeguimientoCaso(models.Model):
    seguimiento = models.ForeignKey(
        SeguimientoCaso, on_delete=models.CASCADE, related_name='historial',
    )
    estado = models.CharField(max_length=20, choices=SeguimientoCaso.Estado.choices)
    cambiado_por = models.ForeignKey(
        'Usuario', null=True, blank=True, on_delete=models.SET_NULL,
    )
    motivo = models.TextField()
    cambiado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'historial_seguimiento_caso'
        ordering = ['cambiado_en', 'pk']


# CONTROL DE SESIÓN ÚNICA POR USUARIO
class SesionActiva(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE, db_column='usuario_id')
    session_key = models.CharField(max_length=40)
    fecha_inicio = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'sesion_activa'

    def __str__(self):
        return f"Sesión activa de {self.usuario.usuario_nombre}"


class HistorialImportacionEstudiantes(models.Model):
    archivo = models.CharField(max_length=255)
    usuario_id_importo = models.PositiveIntegerField()
    usuario_correo_importo = models.EmailField()
    realizado_en = models.DateTimeField(default=timezone.now)
    alumnos_agregados = models.JSONField(default=list)
    duplicados_detectados = models.JSONField(default=list)
    filas_omitidas = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'historial_importacion_estudiantes'
        ordering = ['-realizado_en']


class SolicitudCaso(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'En espera de revisión'
        APROBADA = 'aprobada', 'Aprobada'
        RECHAZADA = 'rechazada', 'Rechazada'

    solicitante = models.ForeignKey(
        Usuario,
        null=True,
        on_delete=models.SET_NULL,
        related_name='solicitudes_casos',
    )
    lugar = models.ForeignKey(Lugar, on_delete=models.PROTECT)
    fecha_evento = models.DateField()
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField()
    tipo_falta = models.CharField(max_length=100)
    evidencia = models.CharField(max_length=500, blank=True)
    estudiantes = models.JSONField(default=list)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    revisada_por = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='solicitudes_casos_revisadas',
    )
    comentario_revision = models.TextField(blank=True)
    creada_en = models.DateTimeField(default=timezone.now)
    revisada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'solicitud_caso'
        ordering = ['-creada_en', '-pk']
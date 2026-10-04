import os
import io
import secrets
import string
import resend
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, transaction
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .models import Caso, Lugar, Estudiante, Involucran, Curso, Usuario, Rol, Notificacion, HistorialUsuario, DocumentoInstitucional, ProfesorJefe, Administrador, Inspector, PConvivencia, SesionActiva, _quitar_tildes
from django.contrib.messages import get_messages
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import ExtractMonth
import json
from datetime import timedelta
from django.db.models import Count, Value, Q
from django.db.models.functions import Concat
from django.db import transaction, connection

# Generación de reportes descargables (RF-40)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, LineChart, Reference


#PANTALLA LOGIN
resend.api_key = getattr(settings, 'RESEND_API_KEY', '')

def login_view(request):
    if request.method == 'POST':
        
        #RECUPERACION CONTRASEÑA CON RESSEND
        if 'correo_recuperacion' in request.POST:
            correo_destino = request.POST.get('correo_recuperacion').strip()
            #login
            try:
                usuario = Usuario.objects.get(usuario_correo=correo_destino)

                # Se genera una contraseña TEMPORAL nueva y aleatoria (nunca se vuelve a
                # mostrar/enviar la contraseña real, ya que ahora se guarda encriptada
                # y ni el propio sistema puede leerla). Se obliga a cambiarla al entrar.
                alfabeto = string.ascii_letters + string.digits
                contrasena_temporal = ''.join(secrets.choice(alfabeto) for _ in range(10))

                usuario.usuario_contrasena = make_password(contrasena_temporal)
                usuario.usuario_primer_ingreso = True
                usuario.usuario_bloqueado = False
                usuario.usuario_intentos_fallidos = 0
                usuario.save()

                html_recuperacion_contraseña = f"""
                <div style="font-family: 'Segoe UI', sans-serif; max-width: 550px; margin: 0 auto; border: 1px solid rgba(123,26,26,0.15); border-radius: 12px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #5A1010 0%, #7B1A1A 100%); padding: 24px; text-align: center; border-bottom: 3px solid #D4A017;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 1.4rem;">ConviData</h1>
                        <p style="color: #F0C030; margin: 4px 0 0 0; font-size: 0.8rem; text-transform: uppercase;">Colegio San Sebastián de Melipilla</p>
                    </div>
                    <div style="padding: 32px; background-color: #ffffff; color: #1C0A0A;">
                        <h2 style="font-size: 1.2rem; margin-top: 0; color: #7B1A1A;">Restablecimiento de Credenciales</h2>
                        <p style="font-size: 0.9rem;">Estimado(a) <strong>{usuario.usuario_nombre} {usuario.usuario_apaterno}</strong>,</p>
                        <p style="font-size: 0.9rem;">Hemos recibido una solicitud para recuperar tus credenciales de acceso. Se generó una <strong>contraseña temporal</strong> para que puedas volver a entrar.</p>
                        <div style="background-color: #F7F3ED; border-left: 4px solid #D4A017; padding: 14px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; font-size: 0.85rem;">
                                Tu contraseña temporal es: <strong style="font-size: 0.95rem; color: #7B1A1A; font-family: monospace;">{contrasena_temporal}</strong>
                            </p>
                        </div>
                        <p style="font-size: 0.82rem; color: #5C3A2A;">Por seguridad, el sistema te pedirá crear una contraseña nueva y personal apenas inicies sesión.</p>
                    </div>
                </div>
                """
                
                resend.Emails.send({
                    "from": "ConviData <onboarding@resend.dev>",
                    "to": [correo_destino],
                    "subject": "Recuperación de Contraseña - ConviData",
                    "html": html_recuperacion_contraseña
                })
                
                messages.success(request, f"Se ha enviado un correo con una contraseña temporal a {correo_destino}.")
                return redirect('login')
                
            except Usuario.DoesNotExist:
                messages.error(request, "El correo electrónico ingresado no corresponde a ningún funcionario activo.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error en el servidor de correos: {str(e)}")
                return redirect('login')

        # INICIO SESION
        else:
            correo_ingresado = request.POST.get('correo', '').strip()
            contrasena_ingresada = request.POST.get('contrasena', '')
            
            try:
                # Buscamos al funcionario por su correo real
                usuario = Usuario.objects.get(usuario_correo=correo_ingresado)

                # RF: cuenta bloqueada por intentos fallidos -> ni siquiera se valida la contraseña
                if usuario.usuario_bloqueado:
                    messages.error(request, "Cuenta bloqueada. Contacta al Administrador del sistema para restablecer el acceso.")
                    return redirect('login')

                # Validamos credenciales directo con tu string de contraseña de la BD
                if check_password(contrasena_ingresada, usuario.usuario_contrasena):

                    # RF: no dejar entrar a cuentas marcadas como inactivas
                    if not usuario.usuario_activo:
                        messages.error(request, "Tu cuenta se encuentra inactiva. Contacta al Administrador del sistema.")
                        return redirect('login')

                    usuario.usuario_intentos_fallidos = 0
                    usuario.usuario_ultimo_acceso=timezone.now()
                    usuario.save(update_fields=['usuario_intentos_fallidos', 'usuario_ultimo_acceso'])


                    # Inyectamos las variables obligatorias en la sesión web
                    request.session['usuario_id'] = usuario.usuario_id
                    request.session['usuario_nombre'] = f"{usuario.usuario_nombre} {usuario.usuario_apaterno}"
                    request.session['usuario_rol'] = usuario.rol.rol_nombre
                    request.session['usuario_correo'] = usuario.usuario_correo
                    
                    # CONTROL PARA PRIMER INGRESO
                    try:
                        request.session['primer_ingreso'] = usuario.usuario_primer_ingreso
                    except AttributeError:
                        request.session['primer_ingreso'] = False

                    # SESIÓN ÚNICA: esta sesión pasa a ser la única válida para esta cuenta.
                    # Si esta cuenta estaba abierta en otro dispositivo/navegador, ese quedará invalidado.
                    request.session.save()  # fuerza la creación del session_key si aún no existía
                    SesionActiva.objects.update_or_create(
                        usuario=usuario,
                        defaults={'session_key': request.session.session_key, 'fecha_inicio': timezone.now()}
                    )
                    
                    # El Profesor Jefe no tiene panel general: entra directo a su curso
                    if usuario.rol.rol_nombre == 'Profesor Jefe':
                        return redirect('mis_casos_curso')

                    return redirect('dashboard')
                else:
                    # RF: contraseña incorrecta -> cuenta el intento y bloquea al llegar a 5
                    usuario.usuario_intentos_fallidos += 1

                    if usuario.usuario_intentos_fallidos >= 5:
                        usuario.usuario_bloqueado = True
                        usuario.save(update_fields=['usuario_intentos_fallidos', 'usuario_bloqueado'])
                        messages.error(request, "Cuenta bloqueada. Se detectaron 5 intentos fallidos consecutivos. Contacta al Administrador del sistema.")
                    else:
                        usuario.save(update_fields=['usuario_intentos_fallidos'])
                        intentos_restantes = 5 - usuario.usuario_intentos_fallidos
                        messages.error(request, f"Contraseña incorrecta. Te quedan {intentos_restantes} intento(s) antes de que la cuenta se bloquee.")

                    return redirect('login')
                    
            except Usuario.DoesNotExist:
                messages.error(request, "El correo electrónico no se encuentra registrado en el sistema.")
                return redirect('login')

    return render(request, 'gestion_casos/login.html')


# CIERRE SESION
def logout_view(request):
    storage = get_messages(request)
    for message in storage:
        pass  

    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        SesionActiva.objects.filter(usuario_id=usuario_id).delete()

    request.session.flush()
    
    return redirect('login')


# ES LA PANTALLA DE INICIO
def _bloquear_si_profesor_jefe(request, mensaje=None):
    """Helper de seguridad: el Profesor Jefe solo debe acceder a 'Mi Curso',
    su Perfil, Configuración y Documentos. Se usa al inicio de las demás
    vistas para bloquearlo y redirigirlo a su propia sección."""
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        if mensaje:
            messages.error(request, mensaje)
        return redirect('mis_casos_curso')
    return None


def dashboard_view(request):
    # 1. Seguridad: Validar que el usuario haya iniciado sesión
    if 'usuario_id' not in request.session:
        return redirect('login')

    # El Profesor Jefe no ve el panel general: se le redirige directo a su curso
    redireccion = _bloquear_si_profesor_jefe(request)
    if redireccion:
        return redireccion

    # CONTADOR DE CASOS
    total_casos = Caso.objects.count()
    casos_leves = Involucran.objects.filter(tipo_falta='Leve').values('caso_id').distinct().count()
    casos_graves = Involucran.objects.filter(tipo_falta='Grave').values('caso_id').distinct().count()
    casos_gravisimas = Involucran.objects.filter(tipo_falta='Gravísima').values('caso_id').distinct().count()

    # CASOS POR ZONA
    hace_30_dias = timezone.localdate() - timedelta(days=30)
    casos_por_zona = Caso.objects.filter(caso_fecha__gte=hace_30_dias) \
                                 .values('lugar__lugar_nombre') \
                                 .annotate(total=Count('caso_id')) \
                                 .order_by('-total')

    zonas_labels = []
    zonas_data = []
    for registro in casos_por_zona:
        nombre_zona = registro['lugar__lugar_nombre'] if registro['lugar__lugar_nombre'] else "No asignado"
        zonas_labels.append(nombre_zona)
        zonas_data.append(registro['total'])

    # ULTIMOS REGISTROS
    casos_query = Caso.objects.select_related('lugar').all().order_by('-caso_id')[:5]
    
    #PARA VER EL TITULO DEL CASO
    lista_casos_dashboard = []
    for caso in casos_query:
        texto_completo = caso.caso_descripcion if caso.caso_descripcion else ""
        
        if "]" in texto_completo and "-" in texto_completo:
            partes = texto_completo.split("] -", 1)
            titulo_limpio = partes[0].replace("[", "").strip()
        else:
            titulo_limpio = f"Caso #{caso.caso_id}"
        lista_casos_dashboard.append({
            'id': caso.caso_id,
            'titulo': titulo_limpio,
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No asignado"
        })

    
    context = {
        'total_casos': total_casos,
        'casos_leves': casos_leves,
        'casos_graves': casos_graves,
        'casos_gravisimas': casos_gravisimas,
        'casos_recientes': lista_casos_dashboard,
        'zonas_labels_json': json.dumps(zonas_labels),
        'zonas_data_json': json.dumps(zonas_data),
    }
    
    return render(request, 'gestion_casos/dashboard.html', context)



# HISTORIAL DE CASOS
def historial_casos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    redireccion = _bloquear_si_profesor_jefe(request, "Acceso denegado: como Profesor Jefe, solo puedes ver los casos de tu curso.")
    if redireccion:
        return redireccion

    # RF-13: parámetros de búsqueda y filtros (vienen por GET, así se puede compartir/recargar la URL filtrada)
    busqueda = request.GET.get('q', '').strip()
    filtro_curso_id = request.GET.get('curso', '').strip()
    filtro_gravedad = request.GET.get('gravedad', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    casos_query = Caso.objects.all().select_related('lugar').order_by('-caso_fecha', '-caso_id')

    if busqueda:
        casos_query = casos_query.filter(caso_descripcion__icontains=busqueda)

    if filtro_curso_id:
        casos_query = casos_query.filter(estudiantes__curso_id=filtro_curso_id).distinct()

    if filtro_fecha_desde:
        casos_query = casos_query.filter(caso_fecha__gte=filtro_fecha_desde)

    if filtro_fecha_hasta:
        casos_query = casos_query.filter(caso_fecha__lte=filtro_fecha_hasta)

    if filtro_gravedad:
        # 'tipo_falta' vive en la tabla 'involucran', que no tiene columna 'id',
        # por eso se consulta con SQL directo (igual que en el resto del sistema).
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT caso_id FROM involucran WHERE tipo_falta = %s", [filtro_gravedad])
            ids_con_gravedad = [fila[0] for fila in cursor.fetchall()]
        casos_query = casos_query.filter(caso_id__in=ids_con_gravedad)

    lista_casos_formateada = []

    rol_usuario = request.session.get('usuario_rol', '')
    ahora = timezone.now()

    for caso in casos_query:
        titulo = "Sin título"
        descripcion_limpia = caso.caso_descripcion if caso.caso_descripcion else ""
        
        if descripcion_limpia.startswith('['):
            try:
                partes = descripcion_limpia.split('] - ', 1)
                if len(partes) == 2:
                    titulo = partes[0].replace('[', '')
                    descripcion_limpia = partes[1]
            except Exception:
                pass
        else:
            titulo = descripcion_limpia[:40] + "..." if len(descripcion_limpia) > 40 else descripcion_limpia

        # RF-52 / RF-53: ¿este usuario puede eliminar este caso?
        puede_eliminar = False
        if rol_usuario == 'Administrador':
            puede_eliminar = True
        elif rol_usuario == 'Inspector':
            if caso.caso_creado_en and (ahora - caso.caso_creado_en) <= timedelta(hours=12):
                puede_eliminar = True

        lista_casos_formateada.append({
            'caso_id': caso.caso_id,
            'titulo': titulo,
            'descripcion': descripcion_limpia,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'fecha': caso.caso_fecha,
            'usuario_id': caso.usuario_id,
            'puede_eliminar': puede_eliminar,
        })

    total_casos_filtrados = len(lista_casos_formateada)

    # Paginación: 10 casos por página, con indicador y flechas Anterior/Siguiente
    paginador = Paginator(lista_casos_formateada, 10)
    numero_pagina = request.GET.get('pagina')
    pagina_casos = paginador.get_page(numero_pagina)

    context = {
        'casos': pagina_casos,  # Page object: iterable + .has_next, .has_previous, .number, etc.
        'total_casos': total_casos_filtrados,  # RF-46 (cuenta TODOS los resultados, no solo los de esta página)
        'mostrar_contador': rol_usuario in ('Administrador', 'Inspector', 'PConvivencia'),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra'),
        'filtros': {
            'q': busqueda,
            'curso': filtro_curso_id,
            'gravedad': filtro_gravedad,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(busqueda or filtro_curso_id or filtro_gravedad or filtro_fecha_desde or filtro_fecha_hasta),
    }
    return render(request, 'gestion_casos/historial_casos.html', context)


def eliminar_caso_view(request, caso_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    caso = get_object_or_404(Caso, pk=caso_id)
    rol_usuario = request.session.get('usuario_rol', '')

    puede_eliminar = False
    if rol_usuario == 'Administrador':
        puede_eliminar = True
    elif rol_usuario == 'Inspector':
        if caso.caso_creado_en and (timezone.now() - caso.caso_creado_en) <= timedelta(hours=12):
            puede_eliminar = True
        else:
            messages.error(request, "Como Inspector, solo puedes eliminar un caso dentro de las primeras 12 horas desde su creación.")
            return redirect('historial_casos')

    if not puede_eliminar:
        messages.error(request, "Acceso denegado: no tienes permisos para eliminar este caso.")
        return redirect('historial_casos')

    try:
        usuario_id_sesion = request.session.get('usuario_id')
        usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion) if usuario_id_sesion else None

        with transaction.atomic():
            caso_id_eliminado = caso.caso_id
            caso.delete()  # El CASCADE elimina también sus filas en 'involucran'

            if usuario_instancia:
                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Eliminación",
                    historial_detalle=f"Eliminó el caso #{caso_id_eliminado} de la bitácora de convivencia."
                )

        messages.success(request, f"El caso #{caso_id_eliminado} fue eliminado exitosamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar el caso: {str(e)}")

    return redirect('historial_casos')

def _verificar_alerta_curso_mas_de_10_casos(curso):
    """
    RF-33 / RF-34

    Genera una alerta cuando un curso supera los 10 casos
    durante la semana actual (lunes a domingo).

    La alerta se genera una sola vez por curso y semana.
    """

    if not curso:
        return

    hoy = timezone.localdate()

    # Semana actual: lunes -> domingo
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    # Contar casos distintos asociados al curso.
    total_casos = (
        Caso.objects
        .filter(
            caso_fecha__gte=inicio_semana,
            caso_fecha__lte=fin_semana,
            estudiantes__curso=curso
        )
        .distinct()
        .count()
    )

    # La alerta aparece SOLO cuando supera 10.
    if total_casos <= 10:
        return

    nombre_curso = str(curso)

    titulo = "Alerta: alta cantidad de casos"

    mensaje = (
        f"El curso {nombre_curso} supera los 10 casos de convivencia "
        f"esta semana. Actualmente registra {total_casos} casos."
    )

    # ------------------------------------------------------------
    # RF-33
    # Administrador / Inspector / PConvivencia
    # ------------------------------------------------------------

    roles_alerta = Rol.objects.filter(
        rol_nombre__in=[
            'Administrador',
            'Inspector',
            'PConvivencia'
        ]
    )

    usuarios_generales = Usuario.objects.filter(
        rol__in=roles_alerta,
        usuario_activo=True,
        usuario_bloqueado=False
    )

    # ------------------------------------------------------------
    # RF-34
    # Profesor Jefe del curso
    # ------------------------------------------------------------

    profesor_jefe = (
        ProfesorJefe.objects
        .filter(
            curso=curso,
            usuario__usuario_activo=True,
            usuario__usuario_bloqueado=False
        )
        .select_related('usuario')
        .first()
    )

    usuarios_destino = {
        usuario.usuario_id: usuario
        for usuario in usuarios_generales
    }

    if profesor_jefe and profesor_jefe.usuario:
        usuarios_destino[profesor_jefe.usuario.usuario_id] = (
            profesor_jefe.usuario
        )

    # ------------------------------------------------------------
    # Evitar duplicados:
    # una alerta por curso y semana para cada usuario.
    # ------------------------------------------------------------

    for usuario in usuarios_destino.values():

        ya_existe = Notificacion.objects.filter(
            usuario=usuario,
            notificacion_titulo=titulo,
            notificacion_mensaje__contains=f"curso {nombre_curso}",
            notificacion_fecha__date__gte=inicio_semana,
            notificacion_fecha__date__lte=fin_semana
        ).exists()

        if ya_existe:
            continue

        Notificacion.objects.create(
            usuario=usuario,
            notificacion_titulo=titulo,
            notificacion_mensaje=mensaje,
            notificacion_icono="⚠️"
        )
# FORMULARIO DE REGISTRAR CASO
def registrar_caso_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    redireccion = _bloquear_si_profesor_jefe(request, "Acceso denegado: como Profesor Jefe no puedes registrar casos, solo consultarlos.")
    if redireccion:
        return redireccion

    # ZONA HORARIA LOCAL
    fecha_hoy = timezone.localdate().strftime('%Y-%m-%d')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        fecha = request.POST.get('fecha')
        lugar_id = request.POST.get('lugar')
        descripcion_cuerpo = request.POST.get('descripcion')
        tipo_falta = request.POST.get('tipo_falta')
        
        # CAPTURA DE ARREGLOS PARA MÚLTIPLES ESTUDIANTES Y NÚMERO DE LISTA
        nombres = request.POST.getlist('alumno_nombre[]')
        apaternos = request.POST.getlist('alumno_apaterno[]')
        amaternos = request.POST.getlist('alumno_amaterno[]')
        num_listas = request.POST.getlist('alumno_num_lista[]')
        cursos_ids = request.POST.getlist('curso[]')
        # Si el usuario eligió un alumno ya existente desde el buscador, viene su ID aquí.
        # Si está vacío, significa que se debe crear un alumno nuevo con los datos tipeados.
        estudiantes_ids = request.POST.getlist('estudiante_id[]')

        if fecha > fecha_hoy:
            messages.error(request, "Error: No se pueden registrar casos con fechas posteriores al día de hoy.")
            return redirect('registrar_caso')

        descripcion_final = f"[{titulo}] - {descripcion_cuerpo}"

        foto_adjunta = request.FILES.get('evidencia_foto')
        nombre_foto_guardado = None
        
        if foto_adjunta:
            try:
                ruta_evidencias = os.path.join(settings.BASE_DIR, 'static', 'evidencias')
                fs = FileSystemStorage(location=ruta_evidencias)
                nombre_foto_guardado = fs.save(foto_adjunta.name, foto_adjunta)
            except Exception:
                pass 

        try:
            with transaction.atomic():
                lugar_instancia = Lugar.objects.get(pk=lugar_id)
                usuario_id_sesion = request.session.get('usuario_id')
                usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion)

                # 1. Crear la cabecera del Caso
                nuevo_caso = Caso(
                    caso_fecha=fecha,
                    caso_descripcion=descripcion_final,
                    evidencia=nombre_foto_guardado,
                    lugar=lugar_instancia,
                    usuario=usuario_instancia
                )
                nuevo_caso.save() 

                nombres_involucrados = []
                cursos_alerta_ids = set()

                # 2. Recorrer todos los estudiantes ingresados en el formulario
                for nom, apat, amat, num_list, c_id, est_id_existente in zip(nombres, apaternos, amaternos, num_listas, cursos_ids, estudiantes_ids):
                    nom_clean = nom.strip()
                    apat_clean = apat.strip()
                    amat_clean = amat.strip()
                    num_lista_val = int(num_list) if num_list and num_list.isdigit() else None

                    curso_instancia = Curso.objects.get(pk=c_id)
                    cursos_alerta_ids.add(curso_instancia.curso_id)

                    # Si se eligió un alumno ya existente desde el buscador, se reutiliza
                    # directamente (evita crear un duplicado por variaciones de tipeo).
                    if est_id_existente:
                        try:
                            estudiante_instancia = Estudiante.objects.get(pk=est_id_existente)
                            creado = False
                        except Estudiante.DoesNotExist:
                            estudiante_instancia, creado = Estudiante.objects.get_or_create(
                                estudiante_nombre=nom_clean,
                                estudiante_apaterno=apat_clean,
                                estudiante_amaterno=amat_clean,
                                curso=curso_instancia
                            )
                    else:
                        # Buscar o crear estudiante (comportamiento original)
                        estudiante_instancia, creado = Estudiante.objects.get_or_create(
                            estudiante_nombre=nom_clean,
                            estudiante_apaterno=apat_clean,
                            estudiante_amaterno=amat_clean,
                            curso=curso_instancia
                        )

                    # Forzar el guardado/actualización del número de lista en PostgreSQL
                    if num_lista_val is not None:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE estudiante SET estudiante_numero_lista = %s WHERE estudiante_id = %s",
                                [num_lista_val, estudiante_instancia.estudiante_id]
                            )
                        estudiante_instancia.estudiante_numero_lista = num_lista_val

                    # Insertar en la tabla intermedia 'involucran'
                    query_insert_intermedia = """
                        INSERT INTO involucran (estudiante_id, caso_id, tipo_falta)
                        VALUES (%s, %s, %s)
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(query_insert_intermedia, [
                            estudiante_instancia.estudiante_id, 
                            nuevo_caso.caso_id, 
                            tipo_falta
                        ])

                    nombres_involucrados.append(f"{nom_clean} {apat_clean}")

                # RF-33 / RF-34
                # Verificar si alguno de los cursos involucrados
                # superó los 10 casos durante la semana actual.
                for curso_id_alerta in cursos_alerta_ids:
                    curso_alerta = Curso.objects.get(pk=curso_id_alerta)
                    _verificar_alerta_curso_mas_de_10_casos(curso_alerta)

                # 3. Notificación e Historial
                lista_nombres_str = ", ".join(nombres_involucrados)

                Notificacion.objects.create(
                    usuario=usuario_instancia,
                    notificacion_titulo="Nueva Bitácora Registrada",
                    notificacion_mensaje=f"Se ha creado el caso #{nuevo_caso.caso_id} [{titulo}] asociado a: {lista_nombres_str} en la zona: {lugar_instancia.lugar_nombre}.",
                    notificacion_icono="🚨"
                )
                
                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Creación",
                    historial_detalle=f"Registró exitosamente una nueva bitácora de caso: #{nuevo_caso.caso_id} [{titulo}] con {len(nombres_involucrados)} alumno(s) involucrado(s)."
                )

            messages.success(request, f"Caso registrado exitosamente por {usuario_instancia.usuario_nombre}.")
            return redirect('historial_casos')
            
        except Exception as e:
            messages.error(request, f"Hubo un problema al registrar en PostgreSQL: {str(e)}")
            return redirect('registrar_caso')

    lugares = Lugar.objects.all().order_by('lugar_nombre')
    cursos = Curso.objects.all().order_by('curso_grado', 'curso_letra')
    estudiantes_existentes = Estudiante.objects.select_related('curso').order_by(
        'estudiante_apaterno', 'estudiante_amaterno', 'estudiante_nombre'
    )
    
    context = {
        'lugares': lugares,
        'cursos': cursos,
        'fecha_hoy': fecha_hoy,
        'estudiantes_existentes': estudiantes_existentes,
    }
    return render(request, 'gestion_casos/registrar_caso.html', context)


# DETALLE DE CASO
def detalle_caso_view(request, caso_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    caso = get_object_or_404(Caso.objects.select_related('lugar', 'usuario'), pk=caso_id)

    # El Profesor Jefe solo puede ver el detalle si el caso pertenece a un alumno de SU curso
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        try:
            profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
        except ProfesorJefe.DoesNotExist:
            messages.error(request, "Acceso denegado.")
            return redirect('mis_casos_curso')

        pertenece_a_su_curso = Estudiante.objects.filter(
            involucran__caso_id=caso_id, curso=profesor.curso
        ).exists()

        if not pertenece_a_su_curso:
            messages.error(request, "Acceso denegado: ese caso no corresponde a los alumnos de tu curso.")
            return redirect('mis_casos_curso')

    titulo = "Sin título"
    descripcion_limpia = caso.caso_descripcion if caso.caso_descripcion else ""
    if descripcion_limpia.startswith('['):
        try:
            partes = descripcion_limpia.split('] - ', 1)
            if len(partes) == 2:
                titulo = partes[0].replace('[', '')
                descripcion_limpia = partes[1]
        except Exception:
            pass
    else:
        titulo = descripcion_limpia[:40] + "..." if len(descripcion_limpia) > 40 else descripcion_limpia

    # 🌟 DEFINIMOS LAS VARIABLES ANTES DEL BUCLE/SQL PARA EVITAR EL ERROR DE PYLANCE
    relaciones = []
    tipo_falta = "No especificado"

    query_sql = """
        SELECT e.estudiante_nombre, e.estudiante_apaterno, e.estudiante_amaterno, 
               e.estudiante_numero_lista, cu.curso_grado, cu.curso_letra, i.tipo_falta
        FROM involucran i
        INNER JOIN estudiante e ON i.estudiante_id = e.estudiante_id
        INNER JOIN curso cu ON e.curso_id = cu.curso_id
        WHERE i.caso_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_sql, [caso_id])
        rows = cursor.fetchall()
        
        for row in rows:
            tipo_falta = row[6]  # 🌟 Se actualiza con el valor real traído desde la BD
            relaciones.append({
                'estudiante': {
                    'estudiante_nombre': row[0],
                    'estudiante_apaterno': row[1],
                    'estudiante_amaterno': row[2],
                    'estudiante_numero_lista': row[3],
                    'curso': {
                        'curso_grado': row[4],
                        'curso_letra': row[5]
                    }
                }
            })

    es_mi_caso = False
    if caso.usuario and caso.usuario.usuario_id == request.session.get('usuario_id'):
        es_mi_caso = True

    context = {
        'caso': caso,
        'titulo': titulo,
        'descripcion': descripcion_limpia,
        'tipo_falta': tipo_falta,
        'relaciones': relaciones,
        'es_mi_caso': es_mi_caso,
        'nombre_foto': caso.evidencia, 
    }
    return render(request, 'gestion_casos/detalle_caso.html', context)

def gestion_datos_publicos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(Usuario.objects.select_related('rol'), pk=usuario_id_sesion)
    
    context = {
        'perfil': usuario_perfil
    }
    return render(request, 'gestion_casos/gestion_datos_publicos.html', context)

# GESTION USUARIOS
def gestion_de_usuarios_view(request):
    #VERIFICA SI ES ADMON
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    # NUEVO USUARIO
    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip()
        apaterno = request.POST.get('apaterno').strip()
        amaterno = request.POST.get('amaterno').strip()
        correo = request.POST.get('correo').strip()
        contrasena = request.POST.get('contrasena')
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')  # Solo se usa si el rol es "Profesor Jefe"

        try:
            #PARA VER SI EL CORREO EXISTE
            if Usuario.objects.filter(usuario_correo=correo).exists():
                messages.error(request, f"El correo {correo} ya se encuentra registrado.")
            else:
                rol_instancia = Rol.objects.get(pk=rol_id)

                # Si el rol es Profesor Jefe, el curso es obligatorio antes de crear nada
                curso_instancia = None
                if rol_instancia.rol_nombre == 'Profesor Jefe':
                    if not curso_id:
                        messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                        return redirect('gestion_de_usuarios')
                    curso_instancia = Curso.objects.get(pk=curso_id)

                with transaction.atomic():
                    nuevo_usuario = Usuario(
                        usuario_nombre=nombre,
                        usuario_apaterno=apaterno,
                        usuario_amaterno=amaterno,
                        usuario_correo=correo,
                        usuario_contrasena=make_password(contrasena),
                        rol=rol_instancia
                    )
                    nuevo_usuario.save()

                    # Crea también el registro específico según el rol asignado
                    if rol_instancia.rol_nombre == 'Administrador':
                        Administrador.objects.create(
                            usuario=nuevo_usuario, admin_nombre=nombre,
                            admin_apaterno=apaterno, admin_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'Inspector':
                        Inspector.objects.create(
                            usuario=nuevo_usuario, inspector_nombre=nombre,
                            inspector_apaterno=apaterno, inspector_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'PConvivencia':
                        PConvivencia.objects.create(
                            usuario=nuevo_usuario, convivencia_nombre=nombre,
                            convivencia_apaterno=apaterno, convivencia_amaterno=amaterno
                        )
                    elif rol_instancia.rol_nombre == 'Profesor Jefe':
                        ProfesorJefe.objects.create(
                            usuario=nuevo_usuario, curso=curso_instancia,
                            profesor_nombre=nombre, profesor_apaterno=apaterno,
                            profesor_amaterno=amaterno
                        )

                messages.success(request, f"Funcionario {nombre} {apaterno} creado exitosamente.")
                return redirect('gestion_de_usuarios')

        except Exception as e:
            messages.error(request, "Ocurrió un error al intentar registrar al usuario.")

    
    # RF: filtros combinables (nombre, rol, estado de cuenta, fecha de último acceso)
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_rol_id = request.GET.get('rol', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    usuarios_registrados = Usuario.objects.select_related('rol', 'profesorjefe').all().order_by('usuario_apaterno')

    if filtro_nombre:
        nombre_normalizado = _quitar_tildes(filtro_nombre)
        usuarios_registrados = usuarios_registrados.filter(
            Q(usuario_nombre__unaccent__icontains=nombre_normalizado) |
            Q(usuario_apaterno__unaccent__icontains=nombre_normalizado) |
            Q(usuario_amaterno__unaccent__icontains=nombre_normalizado) |
            Q(usuario_correo__icontains=filtro_nombre)
        )

    if filtro_rol_id:
        usuarios_registrados = usuarios_registrados.filter(rol_id=filtro_rol_id)

    if filtro_estado == 'activo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=True)
    elif filtro_estado == 'inactivo':
        usuarios_registrados = usuarios_registrados.filter(usuario_activo=False)

    if filtro_fecha_desde:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__gte=filtro_fecha_desde)

    if filtro_fecha_hasta:
        usuarios_registrados = usuarios_registrados.filter(usuario_ultimo_acceso__date__lte=filtro_fecha_hasta)

    roles_disponibles = Rol.objects.all().order_by('rol_nombre')
    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    context = {
        'usuarios': usuarios_registrados,
        'usuario_actual_id': request.session.get('usuario_id'),
        'roles': roles_disponibles,
        'cursos': cursos_disponibles,
        'filtros': {
            'nombre': filtro_nombre,
            'rol': filtro_rol_id,
            'estado': filtro_estado,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(filtro_nombre or filtro_rol_id or filtro_estado or filtro_fecha_desde or filtro_fecha_hasta),
    }
    return render(request, 'gestion_casos/gestion_de_usuarios.html', context)


# RF: SELECCIÓN MÚLTIPLE DE USUARIOS PARA DESACTIVAR O ELIMINAR (solo Administrador)
def acciones_masivas_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_usuarios')

    accion = request.POST.get('accion', '')
    if accion not in ('desactivar', 'eliminar'):
        messages.error(request, "Acción no válida.")
        return redirect('gestion_de_usuarios')

    ids = [int(x) for x in request.POST.getlist('usuarios_seleccionados') if x.isdigit()]
    if not ids:
        messages.warning(request, "Debes seleccionar al menos un usuario.")
        return redirect('gestion_de_usuarios')

    admin_id = request.session.get('usuario_id')

    # El Administrador no puede desactivarse ni eliminarse a sí mismo
    omitido_propio = admin_id in ids
    lista = list(Usuario.objects.filter(pk__in=ids).exclude(pk=admin_id))
    if not lista:
        messages.warning(request, "No se puede aplicar la acción sobre tu propia cuenta.")
        return redirect('gestion_de_usuarios')

    nombres = [f"{u.usuario_nombre} {u.usuario_apaterno} (#{u.usuario_id})" for u in lista]
    ids_objetivo = [u.usuario_id for u in lista]

    try:
        with transaction.atomic():
            if accion == 'desactivar':
                Usuario.objects.filter(pk__in=ids_objetivo).update(usuario_activo=False)
                accion_hist, verbo_msg = "Desactivación masiva", "desactivado(s)"
            else:
                # Django aplica los on_delete definidos en models.py (CASCADE / SET_NULL)
                Usuario.objects.filter(pk__in=ids_objetivo).delete()
                accion_hist, verbo_msg = "Eliminación masiva", "eliminado(s)"

            admin_instancia = Usuario.objects.filter(pk=admin_id).first()
            if admin_instancia:
                HistorialUsuario.objects.create(
                    usuario=admin_instancia,
                    historial_accion=accion_hist,
                    historial_detalle=f"{accion_hist} de {len(lista)} usuario(s): " + ", ".join(nombres) + "."
                )

        mensaje = f"{len(lista)} usuario(s) {verbo_msg} exitosamente."
        if omitido_propio:
            mensaje += " Tu propia cuenta fue omitida."
        messages.success(request, mensaje)
    except Exception as e:
        messages.error(request, f"Ocurrió un error al procesar la acción masiva: {str(e)}")

    return redirect('gestion_de_usuarios')


def editar_usuario_view(request, usuario_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    usuario_editar = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        contrasena = request.POST.get('contrasena', '').strip()  # Vacío = mantener la actual
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')  # Solo se usa si el rol es "Profesor Jefe"
        cuenta_activa = request.POST.get('activo') == 'on'  # checkbox: presente = activo

        try:
            # Verifica que el correo no pertenezca a OTRO usuario (excluyéndose a sí mismo)
            if Usuario.objects.filter(usuario_correo=correo).exclude(pk=usuario_id).exists():
                messages.error(request, f"El correo {correo} ya está en uso por otro funcionario.")
                return redirect('gestion_de_usuarios')

            rol_instancia = Rol.objects.get(pk=rol_id)

            curso_instancia = None
            if rol_instancia.rol_nombre == 'Profesor Jefe':
                if not curso_id:
                    messages.error(request, "Debes seleccionar un curso para el rol Profesor Jefe.")
                    return redirect('gestion_de_usuarios')
                curso_instancia = Curso.objects.get(pk=curso_id)

            with transaction.atomic():
                usuario_editar.usuario_nombre = nombre
                usuario_editar.usuario_apaterno = apaterno
                usuario_editar.usuario_amaterno = amaterno
                usuario_editar.usuario_correo = correo
                usuario_editar.rol = rol_instancia
                usuario_editar.usuario_activo = cuenta_activa
                # Si el Administrador edita y guarda al funcionario, se considera revisado:
                # se desbloquea la cuenta y se reinicia el contador de intentos fallidos.
                usuario_editar.usuario_bloqueado = False
                usuario_editar.usuario_intentos_fallidos = 0
                if contrasena:
                    usuario_editar.usuario_contrasena = make_password(contrasena)
                usuario_editar.save()

                # Se limpian los registros de subtipo anteriores (pudo haber cambiado de rol)
                # y se recrea el correspondiente al rol actual, para mantener todo sincronizado.
                Administrador.objects.filter(usuario=usuario_editar).delete()
                Inspector.objects.filter(usuario=usuario_editar).delete()
                PConvivencia.objects.filter(usuario=usuario_editar).delete()
                ProfesorJefe.objects.filter(usuario=usuario_editar).delete()

                if rol_instancia.rol_nombre == 'Administrador':
                    Administrador.objects.create(
                        usuario=usuario_editar, admin_nombre=nombre,
                        admin_apaterno=apaterno, admin_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'Inspector':
                    Inspector.objects.create(
                        usuario=usuario_editar, inspector_nombre=nombre,
                        inspector_apaterno=apaterno, inspector_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'PConvivencia':
                    PConvivencia.objects.create(
                        usuario=usuario_editar, convivencia_nombre=nombre,
                        convivencia_apaterno=apaterno, convivencia_amaterno=amaterno
                    )
                elif rol_instancia.rol_nombre == 'Profesor Jefe':
                    ProfesorJefe.objects.create(
                        usuario=usuario_editar, curso=curso_instancia,
                        profesor_nombre=nombre, profesor_apaterno=apaterno,
                        profesor_amaterno=amaterno
                    )

            messages.success(request, f"Funcionario {nombre} {apaterno} actualizado exitosamente.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al actualizar al usuario: {str(e)}")

    return redirect('gestion_de_usuarios')


def desbloquear_usuario_view(request, usuario_id):
    """RF: permite al Administrador desbloquear en un solo clic una cuenta
    que quedó bloqueada por 5 intentos fallidos de inicio de sesión."""
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    usuario_desbloquear = get_object_or_404(Usuario, pk=usuario_id)
    usuario_desbloquear.usuario_bloqueado = False
    usuario_desbloquear.usuario_intentos_fallidos = 0
    usuario_desbloquear.save(update_fields=['usuario_bloqueado', 'usuario_intentos_fallidos'])

    messages.success(request, f"La cuenta de {usuario_desbloquear.usuario_nombre} {usuario_desbloquear.usuario_apaterno} fue desbloqueada exitosamente.")
    return redirect('gestion_de_usuarios')

#panel de estadisticas
# ============================================================
#  RF-29 a RF-32 y RF-35: ESTADÍSTICAS DE CONVIVENCIA ESCOLAR
# ============================================================

def _tiene_acceso_estadisticas(request):
    return request.session.get('usuario_rol') in ('Administrador', 'Inspector', 'PConvivencia')

def _calcular_ids_casos(fecha_desde, fecha_hasta, curso_id, lugar_id, gravedad):
    """Devuelve la lista de caso_id que cumplen con los filtros dados."""
    qs = Caso.objects.filter(caso_fecha__gte=fecha_desde, caso_fecha__lte=fecha_hasta)
    
    if curso_id:
        qs = qs.filter(estudiantes__curso_id=curso_id)
    if lugar_id:
        qs = qs.filter(lugar_id=lugar_id)
        
    ids = list(qs.distinct().values_list('caso_id', flat=True))

    if gravedad and ids:
        placeholders = ','.join(['%s'] * len(ids))
        query = f"SELECT DISTINCT caso_id FROM involucran WHERE tipo_falta = %s AND caso_id IN ({placeholders})"
        params = [gravedad] + ids
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            ids = [row[0] for row in cursor.fetchall()]

    return ids

def _obtener_datos_estadisticas(request):
    """Calcula todos los datos (KPIs, series de gráficos y tabla) según los
    filtros de la request. Usada por la vista de la página, la API JSON y las
    exportaciones PDF/XLSX, para que todas muestren siempre lo mismo."""
    anio_actual = timezone.localdate().year

    filtro_gravedad = request.GET.get('gravedad', '').strip()
    filtro_curso_id = request.GET.get('curso', '').strip()
    filtro_lugar_id = request.GET.get('zona', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip() or f"{anio_actual}-01-01"
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip() or f"{anio_actual}-12-31"

    caso_ids = _calcular_ids_casos(filtro_fecha_desde, filtro_fecha_hasta, filtro_curso_id, filtro_lugar_id, filtro_gravedad)
    total_casos = len(caso_ids)

    # ---- Por gravedad (tipo de caso) ----
    dict_gravedad = {'Leve': 0, 'Grave': 0, 'Gravísima': 0}
    if caso_ids:
        placeholders = ','.join(['%s'] * len(caso_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT tipo_falta, COUNT(DISTINCT caso_id) FROM involucran WHERE caso_id IN ({placeholders}) GROUP BY tipo_falta",
                caso_ids
            )
            for tipo_falta, total in cursor.fetchall():
                if tipo_falta in dict_gravedad:
                    dict_gravedad[tipo_falta] = total
    gravedad_labels = list(dict_gravedad.keys())
    gravedad_data = list(dict_gravedad.values())
    tipo_caso_top = max(dict_gravedad, key=dict_gravedad.get) if max(dict_gravedad.values(), default=0) > 0 else "N/A"

    # ---- Por curso ----
    conteo_cursos = Estudiante.objects.filter(involucran__caso_id__in=caso_ids).exclude(curso__isnull=True)\
        .annotate(nombre_completo_curso=Concat('curso__curso_grado', Value(' '), 'curso__curso_letra'))\
        .values('nombre_completo_curso')\
        .annotate(total=Count('involucran__caso_id', distinct=True))\
        .order_by('-total')[:8]
    cursos_labels = [item['nombre_completo_curso'].strip() for item in conteo_cursos]
    cursos_data = [item['total'] for item in conteo_cursos]
    curso_top = cursos_labels[0] if cursos_labels else "N/A"

    # ---- Por zona del colegio (lugar) ----
    conteo_zonas = Caso.objects.filter(caso_id__in=caso_ids).values('lugar__lugar_nombre')\
        .annotate(total=Count('caso_id', distinct=True)).order_by('-total')[:8]
    zonas_labels = [item['lugar__lugar_nombre'] or "No especificado" for item in conteo_zonas]
    zonas_data = [item['total'] for item in conteo_zonas]
    zona_top = zonas_labels[0] if zonas_labels else "N/A"

    # ---- Evolución mensual (tendencia) ----
    conteo_mensual = Caso.objects.filter(caso_id__in=caso_ids)\
        .annotate(mes=ExtractMonth('caso_fecha')).values('mes')\
        .annotate(total=Count('caso_id', distinct=True)).order_by('mes')
    dict_meses = {i: 0 for i in range(1, 13)}
    for item in conteo_mensual:
        dict_meses[item['mes']] = item['total']
    meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    mensual_data = [dict_meses[i] for i in range(1, 13)]

    # ---- Variación % vs el mismo periodo del año anterior (con los mismos filtros de curso/zona/gravedad) ----
    anio_comparado = int(filtro_fecha_desde[:4])
    anio_anterior = anio_comparado - 1
    ids_anterior = _calcular_ids_casos(f"{anio_anterior}-01-01", f"{anio_anterior}-12-31", filtro_curso_id, filtro_lugar_id, filtro_gravedad)
    total_anterior = len(ids_anterior)
    if total_anterior > 0:
        variacion_pct = round(((total_casos - total_anterior) / total_anterior) * 100, 1)
    elif total_casos > 0:
        variacion_pct = 100.0
    else:
        variacion_pct = 0.0

    # ---- Tabla de datos (detalle de los casos filtrados, usada en pantalla y en las exportaciones) ----
    tabla_datos = []
    casos_detalle = Caso.objects.filter(caso_id__in=caso_ids).select_related('lugar').order_by('-caso_fecha')
    for caso in casos_detalle:
        texto = caso.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()

        with connection.cursor() as cursor:
            cursor.execute("SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s", [caso.caso_id])
            filas = cursor.fetchall()

        cursos_del_caso = set()
        gravedad_caso = ""
        for est_id, tf in filas:
            gravedad_caso = tf
            try:
                est = Estudiante.objects.select_related('curso').get(pk=est_id)
                if est.curso:
                    cursos_del_caso.add(f"{est.curso.curso_grado} {est.curso.curso_letra}")
            except Estudiante.DoesNotExist:
                pass

        tabla_datos.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'fecha': caso.caso_fecha,
            'cursos': ", ".join(sorted(cursos_del_caso)) if cursos_del_caso else "Sin curso",
            'zona': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'gravedad': gravedad_caso,
        })

    return {
        'total_casos': total_casos,
        'curso_top': curso_top,
        'tipo_caso_top': tipo_caso_top,
        'zona_top': zona_top,
        'variacion_pct': variacion_pct,
        'gravedad_labels': gravedad_labels,
        'gravedad_data': gravedad_data,
        'cursos_labels': cursos_labels,
        'cursos_data': cursos_data,
        'zonas_labels': zonas_labels,
        'zonas_data': zonas_data,
        'meses_labels': meses_labels,
        'mensual_data': mensual_data,
        'tabla_datos': tabla_datos,
        'filtros': {
            'gravedad': filtro_gravedad,
            'curso': filtro_curso_id,
            'zona': filtro_lugar_id,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        }
    }


def estadisticas_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _tiene_acceso_estadisticas(request):
        messages.error(request, "Acceso denegado: Esta sección es exclusiva para Administrador, Inspector o Convivencia Escolar.")
        return redirect('dashboard')

    datos = _obtener_datos_estadisticas(request)

    context = {
        'datos_json': json.dumps(datos, default=str),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra'),
        'zonas': Lugar.objects.all().order_by('lugar_nombre'),
        'filtros': datos['filtros'],
    }
    return render(request, 'gestion_casos/estadisticas.html', context)


def estadisticas_datos_view(request):
    """API JSON usada por el frontend para refrescar los gráficos automáticamente
    cuando se cambian los filtros, sin recargar la página (RF-30)."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if not _tiene_acceso_estadisticas(request):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    datos = _obtener_datos_estadisticas(request)
    return JsonResponse(datos, safe=False)


def _crear_grafico_barras_pdf(labels, data, ancho=460, alto=190):
    drawing = Drawing(ancho, alto)
    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 40
    chart.width = ancho - 70
    chart.height = alto - 60
    chart.data = [data if data else [0]]
    chart.categoryAxis.categoryNames = labels if labels else ['Sin datos']
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.dy = -12
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor('#7B1A1A')
    drawing.add(chart)
    return drawing


def _crear_grafico_torta_pdf(labels, data, ancho=460, alto=210):
    drawing = Drawing(ancho, alto)
    pie = Pie()
    pie.x = 150
    pie.y = 25
    pie.width = 150
    pie.height = 150
    tiene_datos = sum(data) > 0 if data else False
    pie.data = data if tiene_datos else [1]
    pie.labels = labels if tiene_datos else ['Sin datos']
    paleta = [colors.HexColor('#7B1A1A'), colors.HexColor('#D4A017'), colors.HexColor('#1E8449'),
              colors.HexColor('#2874A6'), colors.HexColor('#B7860B'), colors.HexColor('#8E44AD'),
              colors.HexColor('#C0392B'), colors.HexColor('#16A085')]
    for i in range(len(pie.data)):
        pie.slices[i].fillColor = paleta[i % len(paleta)]
    drawing.add(pie)
    return drawing


def estadisticas_pdf_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _tiene_acceso_estadisticas(request):
        messages.error(request, "Acceso denegado.")
        return redirect('dashboard')

    datos = _obtener_datos_estadisticas(request)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=30, bottomMargin=30, leftMargin=35, rightMargin=35)
    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Estadísticas de Convivencia Escolar", estilos['Title']))
    elementos.append(Paragraph(f"Periodo: {datos['filtros']['fecha_desde']} a {datos['filtros']['fecha_hasta']}", estilos['Normal']))
    elementos.append(Paragraph(f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))
    elementos.append(Spacer(1, 14))

    resumen_data = [
        ["Total Casos", "Curso c/ más incidentes", "Tipo más frecuente", "Zona c/ más incidentes", "Variación vs año anterior"],
        [str(datos['total_casos']), datos['curso_top'], datos['tipo_caso_top'], datos['zona_top'], f"{datos['variacion_pct']}%"]
    ]
    tabla_resumen = Table(resumen_data, colWidths=[85, 105, 100, 105, 95])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1A1A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 18))

    elementos.append(Paragraph("Casos por Gravedad", estilos['Heading3']))
    elementos.append(_crear_grafico_barras_pdf(datos['gravedad_labels'], datos['gravedad_data']))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Casos por Zona del Colegio", estilos['Heading3']))
    elementos.append(_crear_grafico_torta_pdf(datos['zonas_labels'], datos['zonas_data']))
    elementos.append(Spacer(1, 18))

    elementos.append(Paragraph("Detalle de Casos", estilos['Heading3']))
    tabla_data = [["ID", "Título", "Fecha", "Curso(s)", "Zona", "Gravedad"]]
    for c in datos['tabla_datos']:
        tabla_data.append([
            f"#{c['caso_id']}", c['titulo'],
            c['fecha'].strftime('%d/%m/%Y') if c['fecha'] else '',
            c['cursos'], c['zona'], c['gravedad']
        ])
    if len(tabla_data) == 1:
        elementos.append(Paragraph("No hay casos que coincidan con los filtros aplicados.", estilos['Normal']))
    else:
        tabla = Table(tabla_data, repeatRows=1, colWidths=[30, 135, 55, 100, 90, 60])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F3ED')]),
        ]))
        elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    nombre_archivo = f"estadisticas_convivencia_{timezone.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


def estadisticas_xlsx_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _tiene_acceso_estadisticas(request):
        messages.error(request, "Acceso denegado.")
        return redirect('dashboard')

    datos = _obtener_datos_estadisticas(request)
    wb = Workbook()

    # Hoja 1: Resumen
    ws_resumen = wb.active
    ws_resumen.title = "Resumen"
    ws_resumen['A1'] = "Estadísticas de Convivencia Escolar"
    ws_resumen['A1'].font = Font(bold=True, size=14, color="7B1A1A")
    ws_resumen['A2'] = f"Periodo: {datos['filtros']['fecha_desde']} a {datos['filtros']['fecha_hasta']}"
    ws_resumen.append([])
    ws_resumen.append(["Total de Casos", "Curso con más incidentes", "Tipo Más Frecuente", "Zona con más incidentes", "Variación % vs año anterior"])
    for col in range(1, 6):
        celda = ws_resumen.cell(row=4, column=col)
        celda.fill = PatternFill(start_color="7B1A1A", end_color="7B1A1A", fill_type="solid")
        celda.font = Font(color="FFFFFF", bold=True)
    ws_resumen.append([datos['total_casos'], datos['curso_top'], datos['tipo_caso_top'], datos['zona_top'], f"{datos['variacion_pct']}%"])
    for i, ancho in enumerate([14, 26, 20, 26, 24], 1):
        ws_resumen.column_dimensions[get_column_letter(i)].width = ancho

    # Hoja 2: Gravedad (gráfico de barras)
    ws_grav = wb.create_sheet("Por Gravedad")
    ws_grav.append(["Gravedad", "Total de Casos"])
    for label, valor in zip(datos['gravedad_labels'], datos['gravedad_data']):
        ws_grav.append([label, valor])
    chart_barras = BarChart()
    chart_barras.title = "Casos por Gravedad"
    chart_barras.y_axis.title = 'Casos'
    filas = max(len(datos['gravedad_labels']), 1) + 1
    chart_barras.add_data(Reference(ws_grav, min_col=2, min_row=1, max_row=filas), titles_from_data=True)
    chart_barras.set_categories(Reference(ws_grav, min_col=1, min_row=2, max_row=filas))
    ws_grav.add_chart(chart_barras, "D2")

    # Hoja 3: Cursos (gráfico de barras)
    ws_cursos = wb.create_sheet("Por Curso")
    ws_cursos.append(["Curso", "Total de Casos"])
    for label, valor in zip(datos['cursos_labels'], datos['cursos_data']):
        ws_cursos.append([label, valor])
    chart_cursos = BarChart()
    chart_cursos.title = "Casos por Curso"
    filas = max(len(datos['cursos_labels']), 1) + 1
    chart_cursos.add_data(Reference(ws_cursos, min_col=2, min_row=1, max_row=filas), titles_from_data=True)
    chart_cursos.set_categories(Reference(ws_cursos, min_col=1, min_row=2, max_row=filas))
    ws_cursos.add_chart(chart_cursos, "D2")

    # Hoja 4: Zonas (gráfico de torta)
    ws_zonas = wb.create_sheet("Por Zona")
    ws_zonas.append(["Zona", "Total de Casos"])
    for label, valor in zip(datos['zonas_labels'], datos['zonas_data']):
        ws_zonas.append([label, valor])
    chart_torta = PieChart()
    chart_torta.title = "Casos por Zona del Colegio"
    filas = max(len(datos['zonas_labels']), 1) + 1
    chart_torta.add_data(Reference(ws_zonas, min_col=2, min_row=1, max_row=filas), titles_from_data=True)
    chart_torta.set_categories(Reference(ws_zonas, min_col=1, min_row=2, max_row=filas))
    ws_zonas.add_chart(chart_torta, "D2")

    # Hoja 5: Evolución mensual (gráfico de línea)
    ws_mensual = wb.create_sheet("Evolución Mensual")
    ws_mensual.append(["Mes", "Total de Casos"])
    for label, valor in zip(datos['meses_labels'], datos['mensual_data']):
        ws_mensual.append([label, valor])
    chart_linea = LineChart()
    chart_linea.title = "Evolución Mensual de Casos"
    filas = len(datos['meses_labels']) + 1
    chart_linea.add_data(Reference(ws_mensual, min_col=2, min_row=1, max_row=filas), titles_from_data=True)
    chart_linea.set_categories(Reference(ws_mensual, min_col=1, min_row=2, max_row=filas))
    ws_mensual.add_chart(chart_linea, "D2")

    # Hoja 6: Detalle de casos
    ws_detalle = wb.create_sheet("Detalle de Casos")
    ws_detalle.append(["ID", "Título", "Fecha", "Curso(s)", "Zona", "Gravedad"])
    for col in range(1, 7):
        celda = ws_detalle.cell(row=1, column=col)
        celda.fill = PatternFill(start_color="7B1A1A", end_color="7B1A1A", fill_type="solid")
        celda.font = Font(color="FFFFFF", bold=True)
    for c in datos['tabla_datos']:
        ws_detalle.append([
            f"#{c['caso_id']}", c['titulo'],
            c['fecha'].strftime('%d/%m/%Y') if c['fecha'] else '',
            c['cursos'], c['zona'], c['gravedad']
        ])
    for i, ancho in enumerate([8, 32, 12, 20, 20, 12], 1):
        ws_detalle.column_dimensions[get_column_letter(i)].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre_archivo = f"estadisticas_convivencia_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response

#vistas de notificaciones
def notificaciones_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    id_usuario = request.session['usuario_id']

    alertas_reales = (
        Notificacion.objects
        .filter(usuario_id=id_usuario)
        .order_by('-notificacion_fecha')
    )

    context = {
        'notificaciones': alertas_reales
    }

    return render(
        request,
        'gestion_casos/notificaciones.html',
        context
    )


def marcar_notificacion_leida_view(request, notificacion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.method != 'POST':
        return redirect('notificaciones')

    notificacion = get_object_or_404(
        Notificacion,
        pk=notificacion_id,
        usuario_id=request.session['usuario_id']
    )

    notificacion.notificacion_leido = True
    notificacion.save(
        update_fields=['notificacion_leido']
    )

    return redirect('notificaciones')
# editar un caso
def editar_caso_view(request, caso_id):
    # 1. Seguridad: Validar sesión activa
    if 'usuario_id' not in request.session:
        return redirect('login')

    redireccion = _bloquear_si_profesor_jefe(request, "Acceso denegado: como Profesor Jefe no puedes editar casos.")
    if redireccion:
        return redireccion

    usuario_id_sesion = request.session.get('usuario_id')
    usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion)

    # 2. Rescatar el caso o lanzar error 404 si no existe
    caso = get_object_or_404(Caso, pk=caso_id)
    creador_caso = caso.usuario
    usuario_id_sesion = request.session['usuario_id']
    rol_usuario = request.session.get('usuario_rol', '').lower() # Asegúrate de que guardas el rol en la sesión al loguear

    # 3. 🚨 REGLA DE NEGOCIO RF-40: Validar permisos de edición
    # Si no es Administrador y el caso pertenece a otro usuario, se le deniega el acceso
    if rol_usuario != 'administrador' and caso.usuario_id != usuario_id_sesion:
        messages.error(request, "Acceso denegado: Solo puedes editar los casos registrados por ti mismo.")
        return redirect('historial_casos')

    # 4. Obtener TODOS los estudiantes involucrados en el caso (antes traía solo 1 con LIMIT 1)
    query_estudiantes = """
        SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s
    """
    lista_ids_involucrados = []
    tipo_falta_actual = ""
    with connection.cursor() as cursor:
        cursor.execute(query_estudiantes, [caso.caso_id])
        filas = cursor.fetchall()
        for fila in filas:
            lista_ids_involucrados.append(fila[0])
            tipo_falta_actual = fila[1]  # la severidad es a nivel de caso, igual para todos

    estudiantes_qs = Estudiante.objects.filter(estudiante_id__in=lista_ids_involucrados).select_related('curso')
    estudiantes_dict = {e.estudiante_id: e for e in estudiantes_qs}
    estudiantes_involucrados = [estudiantes_dict[eid] for eid in lista_ids_involucrados if eid in estudiantes_dict]

    # 5. Procesar el envío del formulario (POST)
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion_cuerpo = request.POST.get('descripcion')
        lugar_id = request.POST.get('lugar')
        tipo_falta = request.POST.get('tipo_falta')

        # Ahora vienen como listas, un valor por cada alumno del formulario
        estudiante_ids = request.POST.getlist('estudiante_id[]')
        nombres = request.POST.getlist('alumno_nombre[]')
        apaternos = request.POST.getlist('alumno_apaterno[]')
        amaternos = request.POST.getlist('alumno_amaterno[]')
        cursos_ids = request.POST.getlist('curso[]')

        try:
            with transaction.atomic():
                # Actualizar datos del Caso
                caso.caso_descripcion = f"[{titulo}] - {descripcion_cuerpo}"
                caso.lugar = Lugar.objects.get(pk=lugar_id)
                caso.save()

                # Actualizar datos de cada alumno involucrado
                for est_id, nom, apat, amat, c_id in zip(estudiante_ids, nombres, apaternos, amaternos, cursos_ids):
                    estudiante_obj = Estudiante.objects.get(pk=est_id)
                    estudiante_obj.estudiante_nombre = nom.strip()
                    estudiante_obj.estudiante_apaterno = apat.strip()
                    estudiante_obj.estudiante_amaterno = amat.strip()
                    estudiante_obj.curso = Curso.objects.get(pk=c_id)
                    estudiante_obj.save()

                    # Actualizar el tipo de falta en la tabla intermedia nativa
                    query_update_intermedia = """
                        UPDATE involucran SET tipo_falta = %s WHERE caso_id = %s AND estudiante_id = %s
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(query_update_intermedia, [tipo_falta, caso.caso_id, est_id])

                # Notificar al creador si otro usuario modificó el caso
                if creador_caso and creador_caso.usuario_id != usuario_instancia.usuario_id:
                    Notificacion.objects.create(
                        usuario=creador_caso,
                        notificacion_titulo="Caso modificado",
                        notificacion_mensaje=(
                            f"El caso #{caso.caso_id} fue modificado por "
                            f"{usuario_instancia.usuario_nombre} "
                            f"{usuario_instancia.usuario_apaterno}."
                        ),
                        notificacion_icono="✏️"
                    )

                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Modificación",
                    historial_detalle=f"Modificó los registros de la bitácora del caso #{caso.caso_id} [{titulo}]."
                )

            messages.success(request, f"El caso #{caso.caso_id} ha sido modificado exitosamente.")
            return redirect('historial_casos')

        except Exception as e:
            messages.error(request, f"Error al procesar la edición: {str(e)}")

    # 6. Preparar los datos pre-cargados para el formulario (GET)
    # Separamos el título de la descripción para rellenar los inputs limpios
    texto_completo = caso.caso_descripcion if caso.caso_descripcion else ""
    titulo_preparado = ""
    descripcion_preparada = texto_completo
    if "]" in texto_completo and "-" in texto_completo:
        partes = texto_completo.split("] -", 1)
        titulo_preparado = partes[0].replace("[", "").strip()
        descripcion_preparada = partes[1].strip()

    context = {
        'caso': caso,
        'titulo_actual': titulo_preparado,
        'descripcion_actual': descripcion_preparada,
        'tipo_falta_actual': tipo_falta_actual,
        'estudiantes': estudiantes_involucrados,   # <-- ahora es una lista, no un solo objeto
        'lugares': Lugar.objects.all().order_by('lugar_nombre'),
        'cursos': Curso.objects.all().order_by('curso_grado', 'curso_letra')
    }
    return render(request, 'gestion_casos/editar_caso.html', context)


# ELIMINAR UN ALUMNO DE UN CASO (botón "✕" en la pantalla de edición)
def eliminar_estudiante_caso_view(request, caso_id, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')

    caso = get_object_or_404(Caso, pk=caso_id)
    rol_usuario = request.session.get('usuario_rol', '').lower()
    usuario_id_sesion = request.session['usuario_id']

    if rol_usuario != 'administrador' and caso.usuario_id != usuario_id_sesion:
        messages.error(request, "Acceso denegado: Solo puedes editar los casos registrados por ti mismo.")
        return redirect('historial_casos')

    # No permitir dejar un caso sin ningún alumno involucrado
    total_involucrados = Involucran.objects.filter(caso_id=caso_id).count()
    if total_involucrados <= 1:
        messages.error(request, "No puedes eliminar al único alumno involucrado en este caso.")
        return redirect('editar_caso', caso_id=caso_id)

    Involucran.objects.filter(caso_id=caso_id, estudiante_id=estudiante_id).delete()
    messages.success(request, "Alumno eliminado del caso correctamente.")
    return redirect('editar_caso', caso_id=caso_id)

# HISTORIAL DE ACCIONES USUARIOS
def historial_usuarios_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    rol_actual = request.session.get('usuario_rol', '').lower()
    if rol_actual != 'administrador':
        messages.error(request, "Acceso denegado: Solo el Administrador puede visualizar la bitácora de usuarios.")
        return redirect('dashboard')
    from django.utils.dateparse import parse_date

    # Filtros combinables: usuario responsable, tipo de acción y rango de fechas
    filtro_usuario = request.GET.get('usuario', '').strip()
    filtro_accion = request.GET.get('accion', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    base_qs = HistorialUsuario.objects.select_related('usuario')
    total_registros = base_qs.count()
    registros_auditoria = base_qs.order_by('-historial_fecha')

    # Usuario responsable: cada palabra escrita debe coincidir con nombre, apellidos o correo
    if filtro_usuario:
        for termino in filtro_usuario.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(usuario__usuario_nombre__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_apaterno__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_amaterno__unaccent__icontains=termino_norm) |
                Q(usuario__usuario_correo__icontains=termino)
            )

    # Tipo de acción
    if filtro_accion:
        registros_auditoria = registros_auditoria.filter(historial_accion=filtro_accion)

    # Rango de fechas (se ignoran valores con formato inválido)
    def _fecha_valida(texto):
        if not texto:
            return None
        try:
            return parse_date(texto)
        except ValueError:
            return None

    fecha_desde = _fecha_valida(filtro_fecha_desde)
    fecha_hasta = _fecha_valida(filtro_fecha_hasta)

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
        messages.warning(request, "La fecha 'desde' era posterior a 'hasta'; se invirtieron para aplicar el filtro.")

    if fecha_desde:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__gte=fecha_desde)
    if fecha_hasta:
        registros_auditoria = registros_auditoria.filter(historial_fecha__date__lte=fecha_hasta)

    filtro_fecha_desde = fecha_desde.isoformat() if fecha_desde else ''
    filtro_fecha_hasta = fecha_hasta.isoformat() if fecha_hasta else ''

    # Opciones de los filtros (solo lo que realmente existe en la bitácora)
    acciones_disponibles = (
        HistorialUsuario.objects.order_by('historial_accion')
        .values_list('historial_accion', flat=True).distinct()
    )
    usuarios_historial = (
        Usuario.objects.filter(historial_acciones__isnull=False)
        .distinct().order_by('usuario_apaterno', 'usuario_nombre')
    )

    context = {
        'historial': registros_auditoria,
        'total_registros': total_registros,
        'acciones_disponibles': acciones_disponibles,
        'usuarios_historial': usuarios_historial,
        'filtros': {
            'usuario': filtro_usuario,
            'accion': filtro_accion,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(filtro_usuario or filtro_accion or filtro_fecha_desde or filtro_fecha_hasta),
    }
    return render(request, 'gestion_casos/historial_de_usuarios.html', context)

def _numero_lista_ya_usado(curso, numero_lista, excluir_estudiante_id=None):
    """Verifica si otro alumno del MISMO curso ya tiene ese número de lista.
    'excluir_estudiante_id' se usa al editar, para no chocar contra sí mismo."""
    if not numero_lista or not curso:
        return False
    qs = Estudiante.objects.filter(curso=curso, estudiante_numero_lista=numero_lista)
    if excluir_estudiante_id:
        qs = qs.exclude(pk=excluir_estudiante_id)
    return qs.exists()


def gestion_de_estudiantes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip()
        apaterno = request.POST.get('apaterno').strip()
        amaterno = request.POST.get('amaterno').strip()
        curso_id = request.POST.get('curso')
        numero_lista = request.POST.get('numero_lista', '').strip()

        try:
            curso_instancia = Curso.objects.get(pk=curso_id)
            numero_lista_val = int(numero_lista) if numero_lista.isdigit() else None

            if numero_lista_val and _numero_lista_ya_usado(curso_instancia, numero_lista_val):
                messages.error(
                    request,
                    f"Ya existe un alumno con el N° de lista {numero_lista_val} en {curso_instancia}. "
                    f"El número de lista debe ser único dentro del mismo curso."
                )
                return redirect('gestion_de_alumnos')

            nuevo_estudiante = Estudiante(
                estudiante_nombre=nombre,
                estudiante_apaterno=apaterno,
                estudiante_amaterno=amaterno,
                curso=curso_instancia,
                estudiante_numero_lista=numero_lista_val,
            )
            nuevo_estudiante.save()

            if nuevo_estudiante.estudiante_identificador:
                messages.success(
                    request,
                    f"Alumno(a) {nombre} {apaterno} registrado(a) exitosamente. "
                    f"Identificador asignado: {nuevo_estudiante.estudiante_identificador}"
                )
            else:
                messages.warning(
                    request,
                    f"Alumno(a) {nombre} {apaterno} registrado(a), pero no se pudo generar su "
                    f"identificador único (revisa que el N° de lista y el curso sean válidos)."
                )
            return redirect('gestion_de_alumnos')
                
        except Exception as e:
            messages.error(request, "Ocurrió un error al intentar registrar al alumno.")

    from urllib.parse import urlencode

    # Filtros combinables: búsqueda por texto, curso y N° de lista
    filtro_busqueda = request.GET.get('busqueda', '').strip()
    filtro_curso = request.GET.get('curso', '').strip()
    filtro_lista = request.GET.get('numero_lista', '').strip()

    estudiantes_registrados = Estudiante.objects.select_related('curso').all().order_by(
        'curso__curso_grado',
        'curso__curso_letra',
        'estudiante_apaterno',
        'estudiante_nombre'
    )

    # Búsqueda: cada palabra escrita debe coincidir con nombre, apellidos o identificador
    if filtro_busqueda:
        for termino in filtro_busqueda.split():
            termino_norm = _quitar_tildes(termino)
            estudiantes_registrados = estudiantes_registrados.filter(
                Q(estudiante_nombre__unaccent__icontains=termino_norm) |
                Q(estudiante_apaterno__unaccent__icontains=termino_norm) |
                Q(estudiante_amaterno__unaccent__icontains=termino_norm) |
                Q(estudiante_identificador__icontains=termino)
            )

    # Curso (se ignoran valores que no sean un id numérico)
    if filtro_curso.isdigit():
        estudiantes_registrados = estudiantes_registrados.filter(curso_id=int(filtro_curso))
    else:
        filtro_curso = ''

    # N° de lista
    if filtro_lista.isdigit():
        estudiantes_registrados = estudiantes_registrados.filter(estudiante_numero_lista=int(filtro_lista))
    else:
        filtro_lista = ''

    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    # Para que los enlaces de paginación conserven los filtros activos
    parametros = {k: val for k, val in (
        ('busqueda', filtro_busqueda), ('curso', filtro_curso), ('numero_lista', filtro_lista)
    ) if val}
    querystring_filtros = ('&' + urlencode(parametros)) if parametros else ''

    # Paginación: 10 alumnos por página, con flechas Anterior/Siguiente
    paginador = Paginator(estudiantes_registrados, 10)
    numero_pagina = request.GET.get('pagina')
    pagina_estudiantes = paginador.get_page(numero_pagina)

    context = {
        'estudiantes': pagina_estudiantes,  # Page object: iterable + tiene .has_next, .has_previous, etc.
        'cursos': cursos_disponibles,
        'filtros': {
            'busqueda': filtro_busqueda,
            'curso': filtro_curso,
            'numero_lista': filtro_lista,
        },
        'hay_filtros_activos': bool(parametros),
        'querystring_filtros': querystring_filtros,
    }
    return render(request, 'gestion_casos/gestion_de_estudiantes.html', context)

def eliminar_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    nombre_completo = f"{estudiante.estudiante_nombre} {estudiante.estudiante_apaterno}"

    try:
        with transaction.atomic():
            # Antes de eliminar al alumno, identificamos en qué casos participaba
            casos_afectados_ids = list(
                Involucran.objects.filter(estudiante=estudiante).values_list('caso_id', flat=True).distinct()
            )

            estudiante.delete()  # El CASCADE también elimina sus filas en 'involucran'

            # Si algún caso quedó sin ningún alumno involucrado, se elimina también
            casos_eliminados = 0
            for caso_id in casos_afectados_ids:
                if not Involucran.objects.filter(caso_id=caso_id).exists():
                    Caso.objects.filter(pk=caso_id).delete()
                    casos_eliminados += 1

        if casos_eliminados > 0:
            messages.success(
                request,
                f"Alumno(a) {nombre_completo} eliminado(a). Además, se eliminaron {casos_eliminados} "
                f"caso(s) de convivencia que quedaron sin ningún alumno asociado."
            )
        else:
            messages.success(request, f"Alumno(a) {nombre_completo} eliminado(a) exitosamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al intentar eliminar al alumno: {str(e)}")

    return redirect('gestion_de_alumnos')


# ============================================================
#  RF-70: IMPORTACIÓN MASIVA DE ALUMNOS DESDE EXCEL (.XLSX)
# ============================================================

def importar_estudiantes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    if request.method != 'POST' or not request.FILES.get('archivo_excel'):
        messages.error(request, "Debes seleccionar un archivo Excel (.xlsx) para importar.")
        return redirect('gestion_de_alumnos')

    archivo = request.FILES['archivo_excel']

    if not archivo.name.lower().endswith('.xlsx'):
        messages.error(request, "El archivo debe estar en formato .xlsx.")
        return redirect('gestion_de_alumnos')

    try:
        libro = load_workbook(archivo, data_only=True)
        hoja = libro.active
    except Exception as e:
        messages.error(request, f"No se pudo leer el archivo. Verifica que sea un Excel válido. Detalle: {str(e)}")
        return redirect('gestion_de_alumnos')

    creados = 0
    omitidos = 0
    errores = []

    # Fila 1 = encabezados. Los datos parten en la fila 2.
    # Columnas esperadas: A) Nombres  B) Apellido Paterno  C) Apellido Materno  D) Curso (Grado)  E) Curso (Letra)  F) N° Lista (opcional)
    for num_fila, fila in enumerate(hoja.iter_rows(min_row=2, max_col=6, values_only=True), start=2):
        if not fila or all(c is None or str(c).strip() == '' for c in fila):
            continue  # fila completamente vacía, se ignora sin marcarla como error

        try:
            nombre = str(fila[0]).strip() if fila[0] is not None else ''
            apaterno = str(fila[1]).strip() if fila[1] is not None else ''
            amaterno = str(fila[2]).strip() if fila[2] is not None else ''
            valor_curso_grado = fila[3]
            curso_letra = str(fila[4]).strip() if fila[4] is not None else ''
            valor_numero_lista = fila[5] if len(fila) > 5 else None

            if not (nombre and apaterno and amaterno and valor_curso_grado is not None and curso_letra):
                errores.append(f"Fila {num_fila}: faltan datos obligatorios.")
                omitidos += 1
                continue

            # El curso se puede escribir solo como número (1, 2, 3, 4) -> se arma "1° Medio", etc.
            # Excel suele guardar los números como celdas numéricas (int/float), no como texto.
            if isinstance(valor_curso_grado, (int, float)):
                curso_grado = f"{int(valor_curso_grado)}° Medio"
            else:
                texto_grado = str(valor_curso_grado).strip()
                curso_grado = f"{texto_grado}° Medio" if texto_grado.isdigit() else texto_grado

            curso_instancia = Curso.objects.filter(
                curso_grado__iexact=curso_grado, curso_letra__iexact=curso_letra
            ).first()

            if not curso_instancia:
                errores.append(f"Fila {num_fila}: el curso '{curso_grado} {curso_letra}' no existe en el sistema.")
                omitidos += 1
                continue

            numero_lista = None
            if isinstance(valor_numero_lista, (int, float)):
                numero_lista = int(valor_numero_lista)
            elif isinstance(valor_numero_lista, str) and valor_numero_lista.strip().isdigit():
                numero_lista = int(valor_numero_lista.strip())

            if numero_lista and _numero_lista_ya_usado(curso_instancia, numero_lista):
                errores.append(
                    f"Fila {num_fila}: el N° de lista {numero_lista} ya está en uso por otro "
                    f"alumno en {curso_instancia}. Se creó/actualizó sin número de lista asignado."
                )
                numero_lista = None  # se registra igual al alumno, pero sin el N° de lista repetido

            estudiante, creado = Estudiante.objects.get_or_create(
                estudiante_nombre=nombre,
                estudiante_apaterno=apaterno,
                estudiante_amaterno=amaterno,
                curso=curso_instancia,
                defaults={'estudiante_numero_lista': numero_lista}
            )
            if creado:
                creados += 1
            else:
                omitidos += 1
                errores.append(f"Fila {num_fila}: {nombre} {apaterno} {amaterno} ya existía en ese curso, se omitió.")

        except Exception as e:
            errores.append(f"Fila {num_fila}: error inesperado ({str(e)}).")
            omitidos += 1

    if creados > 0:
        messages.success(request, f"Importación completada: {creados} alumno(s) nuevo(s) registrado(s), {omitidos} fila(s) omitida(s).")
    else:
        messages.warning(request, f"No se registró ningún alumno nuevo. {omitidos} fila(s) omitida(s) o con datos repetidos.")

    if errores:
        detalle = " | ".join(errores[:8])
        if len(errores) > 8:
            detalle += f" ... y {len(errores) - 8} fila(s) más con problemas."
        messages.error(request, f"Detalle de filas no importadas: {detalle}")

    return redirect('gestion_de_alumnos')


def editar_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        curso_id = request.POST.get('curso')
        numero_lista = request.POST.get('numero_lista', '').strip()

        try:
            curso_instancia = Curso.objects.get(pk=curso_id)
            numero_lista_val = int(numero_lista) if numero_lista.isdigit() else None

            if numero_lista_val and _numero_lista_ya_usado(curso_instancia, numero_lista_val, excluir_estudiante_id=estudiante.estudiante_id):
                messages.error(
                    request,
                    f"Ya existe OTRO alumno con el N° de lista {numero_lista_val} en {curso_instancia}. "
                    f"El número de lista debe ser único dentro del mismo curso."
                )
                return redirect('gestion_de_alumnos')

            estudiante.estudiante_nombre = nombre
            estudiante.estudiante_apaterno = apaterno
            estudiante.estudiante_amaterno = amaterno
            estudiante.curso = curso_instancia
            estudiante.estudiante_numero_lista = numero_lista_val
            estudiante.save()  # recalcula el identificador automáticamente
            messages.success(request, f"Alumno(a) {nombre} {apaterno} actualizado(a) exitosamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al actualizar al alumno: {str(e)}")

    return redirect('gestion_de_alumnos')

def gestion_configuracion_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(Usuario.objects.select_related('rol'), pk=usuario_id_sesion)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        nueva_contrasena = request.POST.get('contrasena', '')

        try:
            if nombre and apaterno and amaterno:
                usuario_perfil.usuario_nombre = nombre
                usuario_perfil.usuario_apaterno = apaterno
                usuario_perfil.usuario_amaterno = amaterno
                request.session['usuario_nombre'] = f"{nombre} {apaterno}"
            
            if nueva_contrasena:
                usuario_perfil.usuario_contrasena = make_password(nueva_contrasena)
                # RF: ya cambió su contraseña temporal -> deja de estar obligado a hacerlo
                usuario_perfil.usuario_primer_ingreso = False
                request.session['primer_ingreso'] = False

            usuario_perfil.save()
            messages.success(request, "Tus credenciales y datos privados se actualizaron correctamente.")
            return redirect('gestion_configuracion')
        except Exception as e:
            messages.error(request, "Ocurrió un error al intentar actualizar la configuración.")

    context = {
        'perfil': usuario_perfil,
        'debe_cambiar_contrasena': request.session.get('primer_ingreso', False),
    }
    return render(request, 'gestion_casos/gestion_configuracion.html', context)


# ============================================================
#  DOCUMENTOS INSTITUCIONALES (Reglamento Interno / Protocolos)
# ============================================================

def gestion_documentos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    rol_usuario = request.session.get('usuario_rol', '')
    es_administrador = rol_usuario == 'Administrador'

    if request.method == 'POST':
        if not es_administrador:
            messages.error(request, "Acceso denegado: Solo un Administrador puede subir documentos.")
            return redirect('gestion_documentos')

        tipo_documento = request.POST.get('tipo_documento')
        titulo = request.POST.get('titulo', '').strip()
        archivo = request.FILES.get('archivo')

        if tipo_documento not in ('Reglamento', 'Protocolo'):
            messages.error(request, "Debes seleccionar una categoría válida para el documento.")
            return redirect('gestion_documentos')

        if not archivo:
            messages.error(request, "Debes seleccionar un archivo para subir.")
            return redirect('gestion_documentos')

        # Validación: solo archivos PDF (por extensión y por tipo MIME)
        if not archivo.name.lower().endswith('.pdf') or archivo.content_type != 'application/pdf':
            messages.error(request, "Solo se permiten archivos en formato PDF.")
            return redirect('gestion_documentos')

        # Límite de tamaño: 20 MB
        if archivo.size > 20 * 1024 * 1024:
            messages.error(request, "El archivo supera el tamaño máximo permitido (20 MB).")
            return redirect('gestion_documentos')

        try:
            usuario_instancia = Usuario.objects.get(pk=request.session['usuario_id'])
            DocumentoInstitucional.objects.create(
                tipo_documento=tipo_documento,
                titulo=titulo if titulo else archivo.name,
                archivo=archivo,
                usuario=usuario_instancia
            )
            messages.success(request, "Documento subido y publicado exitosamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al subir el documento: {str(e)}")

        return redirect('gestion_documentos')

    context = {
        'reglamentos': DocumentoInstitucional.objects.filter(tipo_documento='Reglamento'),
        'protocolos': DocumentoInstitucional.objects.filter(tipo_documento='Protocolo'),
        'es_administrador': es_administrador,
    }
    return render(request, 'gestion_casos/gestion_documentos.html', context)


def eliminar_documento_view(request, documento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('gestion_documentos')

    documento = get_object_or_404(DocumentoInstitucional, pk=documento_id)
    try:
        documento.archivo.delete(save=False)  # elimina el archivo físico del servidor
        documento.delete()
        messages.success(request, "Documento eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar el documento: {str(e)}")

    return redirect('gestion_documentos')


# ============================================================
#  RF-40: DESCARGA DE CASOS DEL CURSO (PROFESOR JEFE)
# ============================================================

def _obtener_casos_del_curso(curso):
    """Devuelve una lista de diccionarios con los datos de los casos de un curso,
    listos para mostrarse en pantalla o exportarse a PDF/XLSX."""
    casos_qs = Caso.objects.filter(estudiantes__curso=curso).distinct().select_related('lugar').order_by('-caso_fecha')

    resultado = []
    for caso in casos_qs:
        texto_completo = caso.caso_descripcion or ""
        titulo = ""
        descripcion = texto_completo
        if "]" in texto_completo and "-" in texto_completo:
            partes = texto_completo.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()
            descripcion = partes[1].strip()

        # OJO: la tabla 'involucran' no tiene columna 'id', por eso se consulta
        # con SQL directo en vez del ORM (igual que en el resto del sistema).
        nombres_alumnos = []
        tipo_falta = ""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT estudiante_id, tipo_falta FROM involucran WHERE caso_id = %s",
                [caso.caso_id]
            )
            filas_involucrados = cursor.fetchall()

        for estudiante_id, tf in filas_involucrados:
            try:
                est = Estudiante.objects.get(pk=estudiante_id)
                nombres_alumnos.append(
                    f"{est.estudiante_nombre} {est.estudiante_apaterno} {est.estudiante_amaterno}"
                )
            except Estudiante.DoesNotExist:
                pass
            tipo_falta = tf

        resultado.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'descripcion': descripcion,
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else '',
            'tipo_falta': tipo_falta,
            'alumnos': ", ".join(nombres_alumnos),
        })
    return resultado


def _validar_profesor_jefe(request):
    """Valida sesión + rol + curso asignado. Devuelve el objeto Curso o None si algo falla."""
    if 'usuario_id' not in request.session:
        return None
    if request.session.get('usuario_rol', '') != 'Profesor Jefe':
        return None
    try:
        profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
    except ProfesorJefe.DoesNotExist:
        return None
    if not profesor.curso:
        return None
    return profesor.curso


def mis_casos_curso_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_rol', '') != 'Profesor Jefe':
        messages.error(request, "Acceso denegado: Esta sección es exclusiva para el Profesor Jefe de un curso.")
        return redirect('dashboard')

    try:
        profesor = ProfesorJefe.objects.select_related('curso').get(usuario_id=request.session['usuario_id'])
    except ProfesorJefe.DoesNotExist:
        messages.error(request, "No se encontró un perfil de Profesor Jefe asociado a tu cuenta.")
        return redirect('dashboard')

    if not profesor.curso:
        messages.error(request, "No tienes un curso asignado actualmente. Contacta al Administrador.")
        return redirect('dashboard')

    casos_del_curso = _obtener_casos_del_curso(profesor.curso)

    context = {
        'curso': profesor.curso,
        'casos': casos_del_curso,
        'total_casos': len(casos_del_curso),  # RF-47
    }
    return render(request, 'gestion_casos/mis_casos_curso.html', context)


def descargar_casos_pdf_view(request):
    curso = _validar_profesor_jefe(request)
    if not curso:
        messages.error(request, "Acceso denegado o no tienes un curso asignado como Profesor Jefe.")
        return redirect('dashboard')

    casos = _obtener_casos_del_curso(curso)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=30, bottomMargin=30, leftMargin=25, rightMargin=25)
    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f"Bitácora de Casos de Convivencia — {curso.curso_grado} {curso.curso_letra}", estilos['Title']))
    elementos.append(Paragraph(f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))
    elementos.append(Spacer(1, 14))

    data = [["ID", "Título", "Fecha", "Lugar", "Severidad", "Alumno(s) Involucrado(s)", "Descripción"]]
    for c in casos:
        data.append([
            f"#{c['caso_id']}",
            c['titulo'],
            c['fecha'].strftime('%d/%m/%Y') if c['fecha'] else '',
            c['lugar'],
            c['tipo_falta'],
            c['alumnos'],
            c['descripcion'][:250],
        ])

    if len(data) == 1:
        elementos.append(Paragraph("No hay casos registrados para este curso.", estilos['Normal']))
    else:
        tabla = Table(data, repeatRows=1, colWidths=[35, 95, 55, 75, 60, 150, 250])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F3ED')]),
        ]))
        elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)

    nombre_archivo = f"casos_{curso.curso_grado}_{curso.curso_letra}_{timezone.now().strftime('%Y%m%d')}.pdf".replace(' ', '_')
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


def descargar_casos_xlsx_view(request):
    curso = _validar_profesor_jefe(request)
    if not curso:
        messages.error(request, "Acceso denegado o no tienes un curso asignado como Profesor Jefe.")
        return redirect('dashboard')

    casos = _obtener_casos_del_curso(curso)

    wb = Workbook()
    ws = wb.active
    ws.title = "Casos del Curso"

    ws.merge_cells('A1:G1')
    ws['A1'] = f"Bitácora de Casos de Convivencia — {curso.curso_grado} {curso.curso_letra}"
    ws['A1'].font = Font(bold=True, size=13, color="7B1A1A")

    ws.merge_cells('A2:G2')
    ws['A2'] = f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}"
    ws['A2'].font = Font(italic=True, size=9, color="777777")

    encabezados = ["ID", "Título", "Fecha", "Lugar", "Severidad", "Alumno(s) Involucrado(s)", "Descripción"]
    ws.append([])
    ws.append(encabezados)
    fila_encabezado = 4

    header_fill = PatternFill(start_color="7B1A1A", end_color="7B1A1A", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for col_num in range(1, len(encabezados) + 1):
        celda = ws.cell(row=fila_encabezado, column=col_num)
        celda.fill = header_fill
        celda.font = header_font

    for c in casos:
        ws.append([
            f"#{c['caso_id']}",
            c['titulo'],
            c['fecha'].strftime('%d/%m/%Y') if c['fecha'] else '',
            c['lugar'],
            c['tipo_falta'],
            c['alumnos'],
            c['descripcion'],
        ])

    anchos = [8, 26, 12, 18, 12, 38, 55]
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    nombre_archivo = f"casos_{curso.curso_grado}_{curso.curso_letra}_{timezone.now().strftime('%Y%m%d')}.xlsx".replace(' ', '_')
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


# ============================================================
#  BÚSQUEDA GLOBAL (lupa en la barra superior)
# ============================================================

def busqueda_global_view(request):
    """API JSON para el buscador global de la barra superior (alumnos, casos y funcionarios).
    Ignora tildes y mayúsculas/minúsculas en ambos lados (lo que se busca y lo guardado)."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    # El Profesor Jefe no tiene acceso al buscador global (solo ve su propio curso)
    if request.session.get('usuario_rol') == 'Profesor Jefe':
        return JsonResponse({'error': 'Acceso denegado'}, status=403)

    query = request.GET.get('q', '').strip()
    resultado = {'estudiantes': [], 'casos': [], 'usuarios': []}

    if len(query) < 2:
        return JsonResponse(resultado)

    # Se le quitan las tildes al término buscado, para que coincida sin importar
    # si el usuario escribe "jose" o "josé" (el campo también se compara sin tildes,
    # vía la extensión 'unaccent' de PostgreSQL con el lookup __unaccent).
    query_normalizada = _quitar_tildes(query)

    # ---- Alumnos ----
    estudiantes = Estudiante.objects.select_related('curso').filter(
        Q(estudiante_nombre__unaccent__icontains=query_normalizada) |
        Q(estudiante_apaterno__unaccent__icontains=query_normalizada) |
        Q(estudiante_amaterno__unaccent__icontains=query_normalizada) |
        Q(estudiante_identificador__icontains=query.upper())
    )[:8]
    for e in estudiantes:
        resultado['estudiantes'].append({
            'id': e.estudiante_id,
            'nombre_completo': f"{e.estudiante_nombre} {e.estudiante_apaterno} {e.estudiante_amaterno}",
            'curso': f"{e.curso.curso_grado} {e.curso.curso_letra}" if e.curso else "Sin curso asignado",
        })

    # ---- Casos ----
    casos = Caso.objects.filter(
        caso_descripcion__unaccent__icontains=query_normalizada
    ).select_related('lugar').order_by('-caso_fecha')[:8]
    for c in casos:
        texto = c.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()
        resultado['casos'].append({
            'id': c.caso_id,
            'titulo': titulo if titulo else f"Caso #{c.caso_id}",
            'fecha': c.caso_fecha.strftime('%d/%m/%Y') if c.caso_fecha else '',
            'lugar': c.lugar.lugar_nombre if c.lugar else 'No especificado',
        })

    # ---- Funcionarios (Profesor Jefe, Inspector, Administrador, Convivencia) ----
    usuarios = Usuario.objects.select_related('rol').filter(
        Q(usuario_nombre__unaccent__icontains=query_normalizada) |
        Q(usuario_apaterno__unaccent__icontains=query_normalizada) |
        Q(usuario_amaterno__unaccent__icontains=query_normalizada) |
        Q(usuario_correo__icontains=query)
    )[:6]
    for u in usuarios:
        resultado['usuarios'].append({
            'id': u.usuario_id,
            'nombre_completo': f"{u.usuario_nombre} {u.usuario_apaterno} {u.usuario_amaterno}",
            'correo': u.usuario_correo,
            'rol': u.rol.rol_nombre if u.rol else '',
        })

    return JsonResponse(resultado)


def detalle_estudiante_view(request, estudiante_id):
    """Ficha de un alumno: sus datos + todos los casos en los que ha estado involucrado."""
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_rol') == 'Profesor Jefe':
        messages.error(request, "Acceso denegado.")
        return redirect('mis_casos_curso')

    estudiante = get_object_or_404(Estudiante.objects.select_related('curso'), pk=estudiante_id)

    # La tabla 'involucran' no tiene columna 'id', se consulta con SQL directo
    with connection.cursor() as cursor:
        cursor.execute("SELECT caso_id, tipo_falta FROM involucran WHERE estudiante_id = %s", [estudiante_id])
        filas = cursor.fetchall()

    caso_ids = [f[0] for f in filas]
    gravedad_por_caso = {f[0]: f[1] for f in filas}

    casos_qs = Caso.objects.filter(caso_id__in=caso_ids).select_related('lugar').order_by('-caso_fecha')

    casos_detalle = []
    conteo_gravedad = {'Leve': 0, 'Grave': 0, 'Gravísima': 0}

    for caso in casos_qs:
        texto = caso.caso_descripcion or ""
        titulo = texto
        if "]" in texto and "-" in texto:
            partes = texto.split("] -", 1)
            titulo = partes[0].replace("[", "").strip()

        gravedad_caso = gravedad_por_caso.get(caso.caso_id, '')
        if gravedad_caso in conteo_gravedad:
            conteo_gravedad[gravedad_caso] += 1

        casos_detalle.append({
            'caso_id': caso.caso_id,
            'titulo': titulo if titulo else f"Caso #{caso.caso_id}",
            'fecha': caso.caso_fecha,
            'lugar': caso.lugar.lugar_nombre if caso.lugar else "No especificado",
            'gravedad': gravedad_caso,
        })

    total_casos = len(casos_detalle)

    # ---- Estado del alumno (semáforo automático según cantidad y gravedad de casos) ----
    # Puntaje ponderado: Leve = 1, Grave = 3, Gravísima = 5.
    # Se basa SOLO en el puntaje acumulado (una sola falta gravísima aislada no dispara
    # la alerta máxima por sí sola, se necesita una acumulación real).
    puntaje = (conteo_gravedad['Leve'] * 1) + (conteo_gravedad['Grave'] * 3) + (conteo_gravedad['Gravísima'] * 5)

    if puntaje >= 10:
        estado_clave = 'alerta'
        estado_texto = 'Alerta: requiere intervención'
        estado_detalle = 'Este alumno acumula una cantidad importante de faltas graves o gravísimas. Se recomienda intervención prioritaria de Convivencia Escolar.'
    elif puntaje >= 5:
        estado_clave = 'atencion'
        estado_texto = 'Requiere atención'
        estado_detalle = 'El alumno tiene antecedentes que ameritan seguimiento cercano, aunque no son motivo de alarma todavía.'
    elif puntaje >= 1:
        estado_clave = 'seguimiento'
        estado_texto = 'Bajo seguimiento'
        estado_detalle = 'El alumno tiene antecedentes leves registrados. No requiere acción urgente, pero conviene monitorear.'
    else:
        estado_clave = 'sin_incidencias'
        estado_texto = 'Sin incidencias'
        estado_detalle = 'Este alumno no tiene casos de convivencia registrados en el sistema.'

    context = {
        'estudiante': estudiante,
        'casos': casos_detalle,
        'total_casos': total_casos,
        'conteo_gravedad': conteo_gravedad,
        'puntaje_riesgo': puntaje,
        'estado_clave': estado_clave,
        'estado_texto': estado_texto,
        'estado_detalle': estado_detalle,
    }
    return render(request, 'gestion_casos/detalle_estudiante.html', context)

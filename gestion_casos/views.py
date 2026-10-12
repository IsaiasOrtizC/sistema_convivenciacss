import os
import io
import hashlib
import logging
import secrets
import string
import resend
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, transaction
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator
from .models import (
    AccionSeguimiento, Administrador, Caso, Curso, DocumentoInstitucional,
    Estudiante, Inspector,
    HistorialAccionSeguimiento, HistorialImportacionEstudiantes,
    HistorialNotificacion, HistorialSeguimientoCaso,
    HistorialUsuario, Involucran, Lugar, Notificacion, PConvivencia,
    ProfesorJefe, ReglaInstitucional, Rol, SeguimientoCaso, SesionActiva,
    SolicitudCaso, Usuario, VersionReglamento, _quitar_tildes,
)
from .reglamento import (
    ErrorProcesamientoPDF,
    extraer_paginas_pdf,
    evaluar_reglas_para_caso,
    guardar_candidatas,
)
from django.contrib.messages import get_messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.templatetags.static import static
from django.db.models import Count
from django.db.models.functions import ExtractMonth
import json
from datetime import timedelta
from xml.sax.saxutils import escape
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

logger = logging.getLogger(__name__)


def _programar_tarea_correo(request, tarea, argumentos, mensaje_error):
    def encolar():
        try:
            tarea.delay(*argumentos)
        except Exception:
            logger.exception("No se pudo encolar el envío de correo.")
            messages.warning(request, mensaje_error)

    transaction.on_commit(encolar)


def _generar_contrasena_temporal():
    alfabeto = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabeto) for _ in range(14))


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
                messages.error(request, "Usuario no existente: el correo ingresado no está registrado.")
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
                messages.error(request, "Usuario no existente: el correo ingresado no está registrado en el sistema.")
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


def _puede_editar_caso(rol, caso, momento=None):
    if rol == 'Administrador':
        return True
    if rol not in ('Inspector', 'PConvivencia') or not caso.caso_creado_en:
        return False
    diferencia = (momento or timezone.now()) - caso.caso_creado_en
    return timedelta(0) <= diferencia <= timedelta(hours=48)


ROLES_SEGUIMIENTO = ('Administrador', 'PConvivencia', 'Inspector')
ROLES_GESTION_SEGUIMIENTO = ('Administrador', 'PConvivencia')
ROLES_APROBACION_CASOS = ('Administrador', 'PConvivencia', 'Inspector')


def _rol_seguimiento_permitido(request, roles=ROLES_SEGUIMIENTO):
    if 'usuario_id' not in request.session:
        return False
    return request.session.get('usuario_rol') in roles


def _identificador_estudiante(estudiante):
    return estudiante.estudiante_identificador or f'Estudiante #{estudiante.estudiante_id}'


def _regla_notificacion_operativa(regla):
    return bool(
        regla
        and regla.estado == ReglaInstitucional.Estado.APROBADA
        and regla.version.estado == VersionReglamento.Estado.VIGENTE
        and not regla.solo_presentacion
        and regla.activador != ReglaInstitucional.Activador.MANUAL
        and regla.accion_requerida.strip()
    )


def _mensaje_notificacion_seguro(notificacion):
    if (
        notificacion.notificacion_titulo in (
            'Nueva Bitácora Registrada',
            'Nuevo caso registrado',
        )
        or getattr(notificacion, 'evento_tipo', '')
        == Notificacion.TipoEvento.CASO_CREADO
    ):
        return (
            'Se registró un caso nuevo. Revisa sus antecedentes y el detalle '
            'antes de definir acciones.'
        )
    return notificacion.notificacion_mensaje


def _url_caso_notificacion(notificacion):
    if notificacion.caso_id:
        return reverse('detalle_caso', args=[notificacion.caso_id])
    if notificacion.notificacion_titulo == 'Nueva Bitácora Registrada':
        fecha = timezone.localtime(notificacion.notificacion_fecha).date().isoformat()
        return (
            f"{reverse('historial_casos')}?"
            f"fecha_desde={fecha}&fecha_hasta={fecha}"
        )
    return ''


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

    hoy = timezone.localdate()
    fecha_inicio = hoy - timedelta(days=29)
    fecha_inicio_anterior = fecha_inicio - timedelta(days=30)
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    casos_periodo = Caso.objects.filter(caso_fecha__range=(fecha_inicio, hoy))
    total_casos_periodo = casos_periodo.count()
    total_casos_periodo_anterior = Caso.objects.filter(
        caso_fecha__range=(fecha_inicio_anterior, fecha_fin_anterior)
    ).count()

    # CASOS POR ZONA
    casos_por_zona = list(
        casos_periodo.values('lugar__lugar_nombre')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'lugar__lugar_nombre')
    )

    zonas_labels = []
    zonas_data = []
    for registro in casos_por_zona:
        nombre_zona = registro['lugar__lugar_nombre'] if registro['lugar__lugar_nombre'] else "No asignado"
        zonas_labels.append(nombre_zona)
        zonas_data.append(registro['total'])

    resumen_tipo = (
        Involucran.objects.filter(caso__caso_fecha__range=(fecha_inicio, hoy))
        .values('tipo_falta')
        .annotate(total=Count('caso_id', distinct=True))
        .order_by('-total', 'tipo_falta')
        .first()
    )
    resumen_curso = (
        casos_periodo.values(
            'estudiantes__curso__curso_grado',
            'estudiantes__curso__curso_letra',
        )
        .annotate(total=Count('caso_id', distinct=True))
        .order_by(
            '-total',
            'estudiantes__curso__curso_grado',
            'estudiantes__curso__curso_letra',
        )
        .first()
    )
    if total_casos_periodo_anterior:
        variacion_periodo = round(
            (total_casos_periodo - total_casos_periodo_anterior)
            / total_casos_periodo_anterior * 100,
            1,
        )
    else:
        variacion_periodo = 100.0 if total_casos_periodo else 0.0

    curso_mas_incidentes = (
        f"{resumen_curso['estudiantes__curso__curso_grado']} "
        f"{resumen_curso['estudiantes__curso__curso_letra']}"
        if resumen_curso else "Sin datos"
    )
    tipo_falta_frecuente = (
        resumen_tipo['tipo_falta'] if resumen_tipo else "Sin datos"
    )
    zona_mas_conflictos = (
        (casos_por_zona[0]['lugar__lugar_nombre'] or "No asignado")
        if casos_por_zona else "Sin datos"
    )

    # El listado completo se pagina y prioriza los incidentes más recientes.
    casos_query = Caso.objects.select_related('lugar').order_by(
        '-caso_fecha', '-caso_id',
    )
    pagina_casos = Paginator(casos_query, 10).get_page(
        request.GET.get('pagina'),
    )

    # PARA VER EL TITULO DEL CASO
    lista_casos_dashboard = []
    for caso in pagina_casos:
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
        'pagina_casos': pagina_casos,
        'casos_periodo': total_casos_periodo,
        'curso_mas_incidentes': curso_mas_incidentes,
        'tipo_falta_frecuente': tipo_falta_frecuente,
        'zona_mas_conflictos': zona_mas_conflictos,
        'variacion_periodo': variacion_periodo,
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
            'puede_editar': _puede_editar_caso(rol_usuario, caso, ahora),
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
            creador = caso.usuario
            if (
                creador
                and creador.usuario_id != usuario_instancia.usuario_id
            ):
                clave = (
                    f'caso_eliminado:{caso_id_eliminado}:'
                    f'creador:{creador.usuario_id}'
                )
                notificacion, creada = Notificacion.objects.get_or_create(
                    evento_clave=clave,
                    defaults={
                        'usuario': creador,
                        'notificacion_titulo': 'Caso eliminado',
                        'notificacion_mensaje': (
                            f'El caso #{caso_id_eliminado} que registraste fue '
                            'eliminado por otro usuario.'
                        ),
                        'notificacion_icono': '🗑️',
                    },
                )
                if creada:
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion,
                        estado=notificacion.estado,
                        cambiado_por=usuario_instancia,
                        motivo='Notificación creada al eliminar un caso de otro usuario.',
                    )
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


def _notificar_caso_gravisimo(request, caso, tipo_falta, lugar):
    destinatarios = list(
        Usuario.objects.filter(
            rol__rol_nombre='Administrador',
            usuario_activo=True,
            usuario_bloqueado=False,
        ).exclude(usuario_correo='').order_by('usuario_id')
    )
    if not destinatarios:
        logger.warning(
            "El caso gravísimo #%s no tiene administradores activos con correo.",
            caso.caso_id,
        )
        return

    for destinatario in destinatarios:
        clave = f'caso_gravisimo:{caso.caso_id}:admin:{destinatario.usuario_id}'
        notificacion, creada = Notificacion.objects.get_or_create(
            evento_clave=clave,
            defaults={
                'usuario': destinatario,
                'notificacion_titulo': f'Caso gravísimo #{caso.caso_id}',
                'notificacion_mensaje': (
                    f'Se registró el caso #{caso.caso_id} como {tipo_falta} '
                    f'en {lugar.lugar_nombre}. Revisa sus antecedentes.'
                ),
                'notificacion_icono': '🚨',
                'caso': caso,
                'evento_tipo': Notificacion.TipoEvento.CASO_CREADO,
            },
        )
        if creada:
            HistorialNotificacion.objects.create(
                notificacion=notificacion,
                estado=notificacion.estado,
                cambiado_por_id=request.session['usuario_id'],
                motivo='Alerta creada por el registro de un caso gravísimo.',
            )

    from .tasks import enviar_alerta_caso_gravisimo

    _programar_tarea_correo(
        request,
        enviar_alerta_caso_gravisimo,
        (
            [usuario.usuario_correo for usuario in destinatarios],
            caso.caso_id,
            caso.caso_fecha.strftime('%d/%m/%Y'),
            lugar.lugar_nombre,
            tipo_falta,
        ),
        "El caso se registró, pero no se pudo encolar el correo de alerta a los administradores.",
    )


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
def _crear_caso_persistido(
    request,
    usuario_instancia,
    fecha,
    titulo,
    descripcion_cuerpo,
    evidencia,
    lugar_instancia,
    tipo_falta,
    estudiantes_data,
):
    nuevo_caso = Caso.objects.create(
        caso_fecha=fecha,
        caso_descripcion=f"[{titulo}] - {descripcion_cuerpo}",
        evidencia=evidencia,
        lugar=lugar_instancia,
        usuario=usuario_instancia,
    )
    identificadores_involucrados = []
    estudiantes_involucrados = []
    cursos_alerta_ids = set()

    for datos in estudiantes_data:
        nom_clean = datos['nombre'].strip()
        apat_clean = datos['apellido_paterno'].strip()
        amat_clean = datos['apellido_materno'].strip()
        curso_instancia = Curso.objects.get(pk=datos['curso_id'])
        cursos_alerta_ids.add(curso_instancia.curso_id)
        estudiante_id = datos.get('estudiante_id')

        if estudiante_id:
            try:
                estudiante_instancia = Estudiante.objects.get(
                    pk=estudiante_id,
                    estudiante_activo=True,
                )
            except Estudiante.DoesNotExist:
                if Estudiante.objects.filter(pk=estudiante_id).exists():
                    raise ValidationError(
                        "No se pueden asociar alumnos inactivos a casos nuevos."
                    )
                estudiante_instancia, _ = Estudiante.objects.get_or_create(
                    estudiante_nombre=nom_clean,
                    estudiante_apaterno=apat_clean,
                    estudiante_amaterno=amat_clean,
                    curso=curso_instancia,
                )
        else:
            estudiante_instancia, _ = Estudiante.objects.get_or_create(
                estudiante_nombre=nom_clean,
                estudiante_apaterno=apat_clean,
                estudiante_amaterno=amat_clean,
                curso=curso_instancia,
            )

        if estudiante_instancia.curso_id != curso_instancia.curso_id:
            raise ValidationError(
                "El curso del estudiante seleccionado no coincide con el formulario."
            )
        if not estudiante_instancia.estudiante_activo:
            raise ValidationError(
                "No se pueden asociar alumnos inactivos a casos nuevos."
            )

        numero_lista = datos.get('numero_lista')
        if numero_lista is not None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE estudiante SET estudiante_numero_lista = %s "
                    "WHERE estudiante_id = %s",
                    [numero_lista, estudiante_instancia.estudiante_id],
                )
            estudiante_instancia.estudiante_numero_lista = numero_lista

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO involucran (estudiante_id, caso_id, tipo_falta)
                VALUES (%s, %s, %s)
                """,
                [
                    estudiante_instancia.estudiante_id,
                    nuevo_caso.caso_id,
                    tipo_falta,
                ],
            )

        identificadores_involucrados.append(
            _identificador_estudiante(estudiante_instancia)
        )
        estudiantes_involucrados.append(estudiante_instancia)

    for curso_id_alerta in cursos_alerta_ids:
        _verificar_alerta_curso_mas_de_10_casos(
            Curso.objects.get(pk=curso_id_alerta)
        )

    evaluar_reglas_para_caso(
        nuevo_caso,
        estudiantes_involucrados,
        usuario_instancia,
    )

    lista_identificadores = ", ".join(identificadores_involucrados)
    notificacion_nueva, notificacion_creada = Notificacion.objects.get_or_create(
        evento_clave=(
            f'caso_creado:{nuevo_caso.caso_id}:'
            f'usuario:{usuario_instancia.usuario_id}'
        ),
        defaults={
            'usuario': usuario_instancia,
            'notificacion_titulo': 'Nuevo caso registrado',
            'notificacion_mensaje': (
                f"Se registró el caso #{nuevo_caso.caso_id} para "
                f"{lista_identificadores} en la zona "
                f"{lugar_instancia.lugar_nombre}."
            ),
            'notificacion_icono': '🚨',
            'caso': nuevo_caso,
            'evento_tipo': Notificacion.TipoEvento.CASO_CREADO,
        },
    )
    if notificacion_creada:
        HistorialNotificacion.objects.create(
            notificacion=notificacion_nueva,
            estado=notificacion_nueva.estado,
            cambiado_por=usuario_instancia,
            motivo='Notificación creada al registrar un caso.',
        )

    if _quitar_tildes(tipo_falta.casefold()) == 'gravisima':
        _notificar_caso_gravisimo(
            request,
            nuevo_caso,
            tipo_falta,
            lugar_instancia,
        )

    HistorialUsuario.objects.create(
        usuario=usuario_instancia,
        historial_accion="Creación",
        historial_detalle=(
            f"Registró exitosamente el caso #{nuevo_caso.caso_id} "
            f"con {len(estudiantes_involucrados)} estudiante(s): "
            + ", ".join(
                f"{estudiante.estudiante_nombre} "
                f"{estudiante.estudiante_apaterno} "
                f"{estudiante.estudiante_amaterno}"
                for estudiante in estudiantes_involucrados
            )
            + "."
        ),
    )
    return nuevo_caso


def registrar_caso_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    es_profesor_jefe = request.session.get('usuario_rol') == 'Profesor Jefe'
    curso_profesor = _validar_profesor_jefe(request) if es_profesor_jefe else None
    if es_profesor_jefe and not curso_profesor:
        messages.error(
            request,
            "No se encontró un curso asignado para tu cuenta de Profesor Jefe.",
        )
        return redirect('mis_casos_curso')
    if not es_profesor_jefe:
        redireccion = _bloquear_si_profesor_jefe(
            request,
            "Acceso denegado: como Profesor Jefe solo puedes reportar casos de tu curso.",
        )
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

        fecha_validada = parse_date(fecha) if fecha else None
        if not fecha_validada or fecha_validada > timezone.localdate():
            messages.error(
                request,
                "La fecha del caso debe ser válida y no puede ser posterior al día de hoy.",
            )
            return redirect('registrar_caso')
        if (
            not titulo
            or len(titulo.strip()) > 180
            or not descripcion_cuerpo
            or tipo_falta not in ('Leve', 'Grave', 'Gravísima')
        ):
            messages.error(
                request,
                "Completa el título, la descripción y una clasificación de gravedad válida.",
            )
            return redirect('registrar_caso')

        listas_estudiantes = (
            nombres, apaternos, amaternos, num_listas, cursos_ids, estudiantes_ids,
        )
        if not nombres or any(len(lista) != len(nombres) for lista in listas_estudiantes):
            messages.error(request, "Completa los datos de todos los estudiantes involucrados.")
            return redirect('registrar_caso')

        foto_adjunta = request.FILES.get('evidencia_foto')
        nombre_foto_guardado = None
        if foto_adjunta:
            extension = os.path.splitext(foto_adjunta.name)[1].lower()
            extensiones_permitidas = {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
                '.png', '.jpg', '.jpeg',
            }
            if extension not in extensiones_permitidas:
                messages.error(
                    request,
                    "Adjunta un documento PDF, Word, Excel, texto o una imagen válida.",
                )
                return redirect('registrar_caso')
            if foto_adjunta.size > 20 * 1024 * 1024:
                messages.error(request, "El archivo adjunto supera el límite de 20 MB.")
                return redirect('registrar_caso')

        if foto_adjunta:
            try:
                nombre_seguro = os.path.basename(foto_adjunta.name)
                nombre_foto_guardado = default_storage.save(
                    f'evidencias/{nombre_seguro}',
                    foto_adjunta,
                )
            except Exception:
                logger.exception("No se pudo guardar la evidencia adjunta del caso.")
                messages.error(
                    request,
                    "No se pudo guardar el archivo adjunto. Intenta nuevamente.",
                )
                return redirect('registrar_caso')

        estudiantes_data = []
        try:
            for nom, apat, amat, num_lista, curso_id, estudiante_id in zip(
                nombres, apaternos, amaternos, num_listas, cursos_ids, estudiantes_ids,
            ):
                if not nom.strip() or not apat.strip() or not curso_id:
                    raise ValidationError(
                        "Completa nombre, apellido y curso de cada estudiante."
                    )
                curso_id = int(curso_id)
                if es_profesor_jefe and curso_id != curso_profesor.pk:
                    raise ValidationError(
                        "Solo puedes reportar estudiantes de tu curso asignado."
                    )
                if num_lista and not num_lista.isdigit():
                    raise ValidationError(
                        "El número de lista debe ser un número entero."
                    )
                estudiante_id_valido = int(estudiante_id) if estudiante_id else None
                nombre_final = nom.strip()
                apellido_paterno_final = apat.strip()
                apellido_materno_final = amat.strip()
                numero_lista_final = int(num_lista) if num_lista else None
                if es_profesor_jefe and estudiante_id_valido:
                    estudiante_existente = Estudiante.objects.filter(
                        pk=estudiante_id_valido,
                        curso_id=curso_profesor.pk,
                        estudiante_activo=True,
                    ).first()
                    if not estudiante_existente:
                        raise ValidationError(
                            "El estudiante seleccionado no pertenece a tu curso o está inactivo."
                        )
                    nombre_final = estudiante_existente.estudiante_nombre
                    apellido_paterno_final = estudiante_existente.estudiante_apaterno
                    apellido_materno_final = estudiante_existente.estudiante_amaterno
                    numero_lista_final = estudiante_existente.estudiante_numero_lista
                estudiantes_data.append({
                    'nombre': nombre_final,
                    'apellido_paterno': apellido_paterno_final,
                    'apellido_materno': apellido_materno_final,
                    'numero_lista': numero_lista_final,
                    'curso_id': curso_id,
                    'estudiante_id': estudiante_id_valido,
                })
        except (ValueError, ValidationError) as error:
            if nombre_foto_guardado:
                default_storage.delete(nombre_foto_guardado)
            messages.error(request, str(error))
            return redirect('registrar_caso')

        if es_profesor_jefe:
            try:
                with transaction.atomic():
                    solicitud = SolicitudCaso.objects.create(
                        solicitante=Usuario.objects.get(
                            pk=request.session['usuario_id']
                        ),
                        lugar=Lugar.objects.get(pk=lugar_id),
                        fecha_evento=fecha,
                        titulo=(titulo or '').strip(),
                        descripcion=(descripcion_cuerpo or '').strip(),
                        tipo_falta=tipo_falta or '',
                        evidencia=nombre_foto_guardado or '',
                        estudiantes=estudiantes_data,
                    )
                messages.success(
                    request,
                    f"El caso quedó en espera de revisión (solicitud #{solicitud.pk}).",
                )
                return redirect('mis_casos_curso')
            except Exception:
                if nombre_foto_guardado:
                    default_storage.delete(nombre_foto_guardado)
                logger.exception("No se pudo guardar la solicitud de caso del profesor.")
                messages.error(
                    request,
                    "No se pudo enviar el caso para revisión. Intenta nuevamente.",
                )
                return redirect('registrar_caso')

        try:
            with transaction.atomic():
                lugar_instancia = Lugar.objects.get(pk=lugar_id)
                usuario_id_sesion = request.session.get('usuario_id')
                usuario_instancia = Usuario.objects.get(pk=usuario_id_sesion)
                nuevo_caso = _crear_caso_persistido(
                    request,
                    usuario_instancia,
                    fecha,
                    titulo,
                    descripcion_cuerpo,
                    nombre_foto_guardado,
                    lugar_instancia,
                    tipo_falta,
                    estudiantes_data,
                )

            messages.success(request, f"Caso registrado exitosamente por {usuario_instancia.usuario_nombre}.")
            return redirect('historial_casos')
            
        except Exception as e:
            messages.error(request, f"Hubo un problema al registrar en PostgreSQL: {str(e)}")
            return redirect('registrar_caso')

    lugares = Lugar.objects.all().order_by('lugar_nombre')
    cursos = Curso.objects.filter(pk=curso_profesor.pk) if curso_profesor else Curso.objects.all()
    cursos = cursos.order_by('curso_grado', 'curso_letra')
    estudiantes_existentes = Estudiante.objects.filter(
        estudiante_activo=True
    ).select_related('curso').order_by(
        'estudiante_apaterno', 'estudiante_amaterno', 'estudiante_nombre'
    )
    if curso_profesor:
        estudiantes_existentes = estudiantes_existentes.filter(curso=curso_profesor)
    
    context = {
        'lugares': lugares,
        'cursos': cursos,
        'fecha_hoy': fecha_hoy,
        'estudiantes_existentes': estudiantes_existentes,
        'requiere_aprobacion': es_profesor_jefe,
    }
    return render(request, 'gestion_casos/registrar_caso.html', context)


def solicitudes_casos_pendientes_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') not in ROLES_APROBACION_CASOS:
        return HttpResponseForbidden(
            "No tienes permisos para revisar solicitudes de casos."
        )

    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        decision = request.POST.get('decision')
        comentario = request.POST.get('comentario', '').strip()
        if decision not in ('aprobar', 'rechazar'):
            messages.error(request, "La decisión de revisión no es válida.")
            return redirect('solicitudes_casos_pendientes')

        mensaje_resultado = ''
        try:
            with transaction.atomic():
                solicitud = get_object_or_404(
                    SolicitudCaso.objects.select_for_update(),
                    pk=solicitud_id,
                )
                if solicitud.estado != SolicitudCaso.Estado.PENDIENTE:
                    messages.warning(
                        request,
                        "Esta solicitud ya fue revisada por otro usuario.",
                    )
                    return redirect('solicitudes_casos_pendientes')

                revisor = Usuario.objects.get(pk=request.session['usuario_id'])
                if decision == 'aprobar':
                    estudiantes_data = solicitud.estudiantes
                    if not estudiantes_data:
                        raise ValidationError(
                            "La solicitud no contiene estudiantes involucrados."
                        )
                    if solicitud.solicitante and solicitud.solicitante.rol.rol_nombre == 'Profesor Jefe':
                        perfil_profesor = ProfesorJefe.objects.select_related(
                            'curso'
                        ).filter(usuario_id=solicitud.solicitante_id).first()
                        curso_profesor = (
                            perfil_profesor.curso if perfil_profesor else None
                        )
                        if not curso_profesor or any(
                            int(estudiante['curso_id']) != curso_profesor.pk
                            for estudiante in estudiantes_data
                        ):
                            raise ValidationError(
                                "El curso asignado al profesor cambió; no se puede aprobar "
                                "esta solicitud hasta corregir su información."
                            )

                    caso = _crear_caso_persistido(
                        request,
                        solicitud.solicitante or revisor,
                        solicitud.fecha_evento,
                        solicitud.titulo,
                        solicitud.descripcion,
                        solicitud.evidencia,
                        solicitud.lugar,
                        solicitud.tipo_falta,
                        estudiantes_data,
                    )
                    solicitud.estado = SolicitudCaso.Estado.APROBADA
                    solicitud.comentario_revision = comentario
                    mensaje_resultado = (
                        f"Solicitud aprobada. El caso #{caso.caso_id} ya está registrado."
                    )
                else:
                    solicitud.estado = SolicitudCaso.Estado.RECHAZADA
                    solicitud.comentario_revision = comentario or "Solicitud rechazada."
                    mensaje_resultado = "La solicitud fue rechazada."

                solicitud.revisada_por = revisor
                solicitud.revisada_en = timezone.now()
                solicitud.save(update_fields=[
                    'estado',
                    'comentario_revision',
                    'revisada_por',
                    'revisada_en',
                ])
                HistorialUsuario.objects.create(
                    usuario=revisor,
                    historial_accion=(
                        "Aprobación de caso"
                        if decision == 'aprobar'
                        else "Rechazo de caso"
                    ),
                    historial_detalle=(
                        f"Revisó la solicitud #{solicitud.pk} del Profesor Jefe "
                        f"{solicitud.solicitante.usuario_nombre if solicitud.solicitante else 'sin usuario'}: "
                        f"{solicitud.get_estado_display()}."
                    ),
                )
            messages.success(request, mensaje_resultado)
        except (SolicitudCaso.DoesNotExist, Usuario.DoesNotExist):
            messages.error(request, "No se encontró la solicitud o el usuario revisor.")
        except ValidationError as error:
            messages.error(request, str(error))
        except Exception:
            logger.exception("No se pudo completar la revisión de la solicitud de caso.")
            messages.error(
                request,
                "No se pudo completar la revisión; la solicitud permanece sin cambios.",
            )
        return redirect('solicitudes_casos_pendientes')

    solicitudes = list(SolicitudCaso.objects.select_related(
        'solicitante__rol', 'lugar', 'revisada_por',
    ).filter(estado=SolicitudCaso.Estado.PENDIENTE))
    cursos = Curso.objects.in_bulk({
        estudiante['curso_id']
        for solicitud in solicitudes
        for estudiante in solicitud.estudiantes
    })
    elementos_solicitud = []
    for solicitud in solicitudes:
        estudiantes = []
        for estudiante in solicitud.estudiantes:
            curso = cursos.get(estudiante['curso_id'])
            estudiantes.append({
                **estudiante,
                'curso': (
                    f"{curso.curso_grado} {curso.curso_letra}"
                    if curso else "Curso no disponible"
                ),
            })
        elementos_solicitud.append({
            'solicitud': solicitud,
            'estudiantes': estudiantes,
            'evidencia_url': (
                default_storage.url(solicitud.evidencia)
                if solicitud.evidencia
                and default_storage.exists(solicitud.evidencia)
                else ''
            ),
        })
    return render(
        request,
        'gestion_casos/solicitudes_casos_pendientes.html',
        {'solicitudes': elementos_solicitud},
    )


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

    evidencia_url = ''
    evidencia_es_imagen = False
    if caso.evidencia:
        nombre_evidencia = caso.evidencia
        extension_evidencia = os.path.splitext(nombre_evidencia)[1].lower()
        evidencia_es_imagen = extension_evidencia in {'.png', '.jpg', '.jpeg'}
        if default_storage.exists(nombre_evidencia):
            evidencia_url = default_storage.url(nombre_evidencia)
        else:
            evidencia_url = static(
                nombre_evidencia
                if nombre_evidencia.startswith('evidencias/')
                else f'evidencias/{nombre_evidencia}'
            )

    context = {
        'caso': caso,
        'titulo': titulo,
        'descripcion': descripcion_limpia,
        'tipo_falta': tipo_falta,
        'relaciones': relaciones,
        'es_mi_caso': es_mi_caso,
        'puede_editar': _puede_editar_caso(
            request.session.get('usuario_rol', ''),
            caso,
        ),
        'nombre_foto': caso.evidencia, 
        'evidencia_url': evidencia_url,
        'evidencia_es_imagen': evidencia_es_imagen,
    }
    return render(request, 'gestion_casos/detalle_caso.html', context)

def _datos_reporte_caso(caso):
    texto = caso.caso_descripcion or ''
    titulo = f'Caso #{caso.caso_id}'
    descripcion = texto
    if texto.startswith('[') and '] - ' in texto:
        titulo, descripcion = texto[1:].split('] - ', 1)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.estudiante_identificador, e.estudiante_nombre,
                   e.estudiante_apaterno, e.estudiante_amaterno,
                   cu.curso_grado, cu.curso_letra, i.tipo_falta
            FROM involucran i
            JOIN estudiante e ON e.estudiante_id = i.estudiante_id
            JOIN curso cu ON cu.curso_id = e.curso_id
            WHERE i.caso_id = %s
            ORDER BY e.estudiante_apaterno, e.estudiante_nombre
            """,
            [caso.caso_id],
        )
        involucrados = cursor.fetchall()

    return {
        'id': caso.caso_id,
        'titulo': titulo.strip(),
        'descripcion': descripcion.strip(),
        'fecha': caso.caso_fecha,
        'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
        'involucrados': [
            {
                'identificador': identificador or '',
                'nombre': f'{nombre} {apaterno} {amaterno}'.strip(),
                'curso': f'{grado} {letra}',
                'tipo_falta': tipo_falta,
            }
            for identificador, nombre, apaterno, amaterno, grado, letra, tipo_falta
            in involucrados
        ],
    }


def _validar_acceso_exportacion_caso(request, caso_id):
    if 'usuario_id' not in request.session:
        return None
    rol = request.session.get('usuario_rol')
    if rol not in ('Administrador', 'Inspector', 'PConvivencia', 'Profesor Jefe'):
        messages.error(request, "Acceso denegado: no tienes permisos para descargar este caso.")
        return None
    caso = get_object_or_404(
        Caso.objects.select_related('lugar'),
        pk=caso_id,
    )
    if rol == 'Profesor Jefe':
        curso = _validar_profesor_jefe(request)
        if not curso or not Estudiante.objects.filter(
            involucran__caso_id=caso_id,
            curso=curso,
        ).exists():
            messages.error(request, "Acceso denegado: ese caso no corresponde a tu curso.")
            return None
    return caso


def _valor_xlsx_seguro(valor):
    if isinstance(valor, str) and valor.startswith(('=', '+', '-', '@')):
        return f"'{valor}"
    return valor


def descargar_caso_pdf_view(request, caso_id):
    caso = _validar_acceso_exportacion_caso(request, caso_id)
    if caso is None:
        if 'usuario_id' not in request.session:
            return redirect('login')
        return redirect('historial_casos')

    datos = _datos_reporte_caso(caso)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=32,
        bottomMargin=32,
        leftMargin=36,
        rightMargin=36,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph('Reporte de caso de convivencia', estilos['Title']),
        Spacer(1, 10),
        Paragraph(
            f"<b>Caso:</b> #{datos['id']} · {escape(datos['titulo'])}",
            estilos['Normal'],
        ),
        Paragraph(
            f"<b>Fecha:</b> {datos['fecha'].strftime('%d/%m/%Y') if datos['fecha'] else 'Sin fecha'}"
            f" · <b>Zona:</b> {escape(datos['lugar'])}",
            estilos['Normal'],
        ),
        Paragraph(
            f"<b>Descripción:</b> {escape(datos['descripcion'])}",
            estilos['Normal'],
        ),
        Spacer(1, 14),
        Paragraph('Estudiantes involucrados', estilos['Heading2']),
    ]
    filas = [['Identificador', 'Estudiante', 'Curso', 'Tipo de falta']]
    filas.extend([
        [
            item['identificador'],
            item['nombre'],
            item['curso'],
            item['tipo_falta'],
        ]
        for item in datos['involucrados']
    ])
    if len(filas) == 1:
        filas.append(['', 'Sin estudiantes asociados', '', ''])
    tabla = Table(filas, repeatRows=1, colWidths=[95, 220, 120, 130])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7B1A1A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D8D0C9')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F3ED')]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(tabla)
    doc.build(elementos)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="caso_{datos["id"]}.pdf"'
    return response


def descargar_caso_xlsx_view(request, caso_id):
    caso = _validar_acceso_exportacion_caso(request, caso_id)
    if caso is None:
        if 'usuario_id' not in request.session:
            return redirect('login')
        return redirect('historial_casos')

    datos = _datos_reporte_caso(caso)
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Caso'
    hoja.append(['Campo', 'Detalle'])
    hoja.append(['ID', datos['id']])
    hoja.append(['Título', _valor_xlsx_seguro(datos['titulo'])])
    hoja.append(['Descripción', _valor_xlsx_seguro(datos['descripcion'])])
    hoja.append(['Fecha', datos['fecha']])
    hoja.append(['Zona', _valor_xlsx_seguro(datos['lugar'])])
    for celda in hoja[1]:
        celda.fill = PatternFill(start_color='7B1A1A', end_color='7B1A1A', fill_type='solid')
        celda.font = Font(color='FFFFFF', bold=True)
    hoja.column_dimensions['A'].width = 20
    hoja.column_dimensions['B'].width = 72
    hoja.freeze_panes = 'A2'

    involucrados = libro.create_sheet('Estudiantes')
    involucrados.append(['Identificador', 'Estudiante', 'Curso', 'Tipo de falta'])
    for item in datos['involucrados']:
        involucrados.append([
            _valor_xlsx_seguro(item['identificador']),
            _valor_xlsx_seguro(item['nombre']),
            _valor_xlsx_seguro(item['curso']),
            _valor_xlsx_seguro(item['tipo_falta']),
        ])
    for celda in involucrados[1]:
        celda.fill = PatternFill(start_color='7B1A1A', end_color='7B1A1A', fill_type='solid')
        celda.font = Font(color='FFFFFF', bold=True)
    for columna, ancho in enumerate([18, 36, 22, 24], 1):
        involucrados.column_dimensions[get_column_letter(columna)].width = ancho
    involucrados.freeze_panes = 'A2'

    buffer = io.BytesIO()
    libro.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="caso_{datos["id"]}.xlsx"'
    return response


def gestion_datos_publicos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(Usuario.objects.select_related('rol'), pk=usuario_id_sesion)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        try:
            if not all((nombre, apaterno, amaterno, correo)):
                raise ValidationError("Completa todos los datos personales.")
            validate_email(correo)
            if Usuario.objects.filter(usuario_correo__iexact=correo).exclude(
                pk=usuario_perfil.pk
            ).exists():
                raise ValidationError("Ese correo ya está asociado a otra cuenta.")

            usuario_perfil.usuario_nombre = nombre
            usuario_perfil.usuario_apaterno = apaterno
            usuario_perfil.usuario_amaterno = amaterno
            usuario_perfil.usuario_correo = correo
            usuario_perfil.save()
            request.session['usuario_nombre'] = f'{nombre} {apaterno}'
            request.session['usuario_correo'] = correo
            messages.success(request, "Tus datos personales se actualizaron correctamente.")
            return redirect('gestion_datos_publicos')
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Exception:
            logger.exception("Error actualizando el perfil del usuario %s", usuario_id_sesion)
            messages.error(request, "No fue posible actualizar tus datos personales.")

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
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        rol_id = request.POST.get('rol')
        curso_id = request.POST.get('curso')  # Solo se usa si el rol es "Profesor Jefe"

        try:
            validate_email(correo)
            if not (nombre and apaterno and amaterno):
                messages.error(request, "Completa los nombres y apellidos del funcionario.")
                return redirect('gestion_de_usuarios')

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

                contrasena_temporal = _generar_contrasena_temporal()
                with transaction.atomic():
                    nuevo_usuario = Usuario(
                        usuario_nombre=nombre,
                        usuario_apaterno=apaterno,
                        usuario_amaterno=amaterno,
                        usuario_correo=correo,
                        usuario_contrasena=make_password(contrasena_temporal),
                        usuario_primer_ingreso=True,
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

                    from .tasks import enviar_credenciales_usuario

                    _programar_tarea_correo(
                        request,
                        enviar_credenciales_usuario,
                        (correo, nombre, apaterno, contrasena_temporal),
                        "La cuenta se creó, pero no se pudo encolar el correo con la contraseña temporal. Contacta al administrador del sistema.",
                    )

                messages.success(request, f"Funcionario {nombre} {apaterno} creado. Se enviará una contraseña temporal a su correo institucional.")
                return redirect('gestion_de_usuarios')

        except ValidationError:
            messages.error(request, "Ingresa un correo institucional válido.")
        except Exception as e:
            logger.exception("No se pudo crear el usuario institucional.")
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
    if not _rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para consultar el módulo de seguimiento.")

    id_usuario = request.session['usuario_id']

    alertas_reales = list(
        Notificacion.objects
        .filter(Q(usuario_id=id_usuario) | Q(regla__isnull=False))
        .select_related(
            'caso', 'estudiante', 'regla', 'regla__version',
            'version_reglamento', 'responsable',
        )
        .prefetch_related('historial_estados__cambiado_por')
        .distinct()
        .order_by('-notificacion_fecha')
    )
    caso_ids = {alerta.caso_id for alerta in alertas_reales if alerta.caso_id}
    categorias_por_caso = {}
    for caso_id, categoria in Involucran.objects.filter(
        caso_id__in=caso_ids,
    ).values_list('caso_id', 'tipo_falta'):
        categorias_por_caso.setdefault(caso_id, set()).add(categoria)

    categoria_css_por_gravedad = {
        'Leve': 'leve',
        'Grave': 'grave',
        'Gravísima': 'gravisima',
    }
    for alerta in alertas_reales:
        alerta.url_caso = _url_caso_notificacion(alerta)
        alerta.notificacion_mensaje = _mensaje_notificacion_seguro(alerta)
        categorias = sorted(categorias_por_caso.get(alerta.caso_id, set()))
        alerta.categoria_falta = ', '.join(categorias) or 'No especificada'
        alerta.categoria_css = (
            categoria_css_por_gravedad.get(categorias[0], 'sin-clasificar')
            if len(categorias) == 1
            else 'sin-clasificar'
        )
        regla = alerta.regla
        alerta.regla_operativa = _regla_notificacion_operativa(regla)
        if regla and not alerta.regla_operativa:
            alerta.notificacion_titulo = 'Referencia reglamentaria para revisión'
            alerta.notificacion_mensaje = (
                'La disposición asociada no está actualmente aprobada y vigente '
                'para orientar acciones. Revisa el detalle del caso y consulta '
                'al personal autorizado.'
            )

    filtro_estado = request.GET.get('estado_seguimiento', '')
    if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
        filtro_estado = ''
    context = {
        'notificaciones': alertas_reales,
        'filas_seguimiento': _obtener_filas_seguimiento(filtro_estado),
        'filtro_estado': filtro_estado,
        'puede_gestionar': request.session.get('usuario_rol') in ROLES_GESTION_SEGUIMIENTO,
        'hoy': timezone.localdate(),
        'estados_notificacion': Notificacion.Estado.choices,
    }

    return render(
        request,
        'gestion_casos/notificaciones.html',
        context
    )


def _obtener_filas_seguimiento(filtro_estado=''):
    if filtro_estado not in ('', *SeguimientoCaso.Estado.values):
        filtro_estado = ''
    casos = list(
        Caso.objects.select_related('lugar')
        .prefetch_related('estudiantes')
        .order_by('-caso_fecha', '-caso_id')[:100]
    )
    caso_ids = [caso.caso_id for caso in casos]
    estudiante_ids = {
        estudiante.estudiante_id
        for caso in casos
        for estudiante in caso.estudiantes.all()
    }
    seguimientos = SeguimientoCaso.objects.filter(
        caso_id__in=caso_ids,
        estudiante_id__in=estudiante_ids,
    ).prefetch_related('acciones', 'historial')
    seguimiento_por_clave = {
        (item.caso_id, item.estudiante_id): item for item in seguimientos
    }
    categorias = {}
    for relacion in Involucran.objects.filter(caso_id__in=caso_ids).values(
        'caso_id', 'estudiante_id', 'tipo_falta'
    ):
        categorias.setdefault((relacion['caso_id'], relacion['estudiante_id']), set()).add(
            relacion['tipo_falta']
        )

    filas = []
    for caso in casos:
        estudiantes = list(caso.estudiantes.all())
        if not estudiantes:
            estudiantes = [None]
        for estudiante in estudiantes:
            seguimiento = (
                seguimiento_por_clave.get((caso.caso_id, estudiante.estudiante_id))
                if estudiante else None
            )
            estado = seguimiento.estado if seguimiento else SeguimientoCaso.Estado.ABIERTO
            if filtro_estado and estado != filtro_estado:
                continue
            acciones = list(seguimiento.acciones.all()) if seguimiento else []
            filas.append({
                'caso': caso,
                'estudiante_id': (
                    _identificador_estudiante(estudiante) if estudiante else 'Sin estudiante asociado'
                ),
                'estudiante_pk': estudiante.estudiante_id if estudiante else None,
                'categoria': ', '.join(sorted(categorias.get(
                    (caso.caso_id, estudiante.estudiante_id), set()
                ))) if estudiante else '',
                'seguimiento': seguimiento,
                'estado': estado,
                'estado_label': (
                    seguimiento.get_estado_display() if seguimiento else 'En seguimiento'
                ),
                'acciones': acciones,
                'avance': (
                    round(
                        sum(a.estado == AccionSeguimiento.Estado.COMPLETADA for a in acciones)
                        * 100 / len(acciones)
                    ) if acciones else None
                ),
            })
    return filas


def _redirect_to_seguimiento():
    return redirect(f"{reverse('notificaciones')}#seguimiento")


def marcar_notificacion_leida_view(request, notificacion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para modificar esta notificación.")

    if request.method != 'POST':
        return redirect('notificaciones')

    notificacion = get_object_or_404(
        Notificacion.objects.filter(
            Q(usuario_id=request.session['usuario_id']) | Q(regla__isnull=False)
        ),
        pk=notificacion_id,
    )

    if not notificacion.notificacion_leido:
        notificacion.notificacion_leido = True
        notificacion.save(update_fields=['notificacion_leido'])

    return redirect('notificaciones')


def cambiar_estado_notificacion_view(request, notificacion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden gestionar notificaciones.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    notificacion = get_object_or_404(
        Notificacion.objects.filter(
            Q(usuario_id=request.session['usuario_id']) | Q(regla__isnull=False)
        ),
        pk=notificacion_id,
    )
    estado = request.POST.get('estado', '')
    motivo = request.POST.get('motivo', '').strip()
    if estado not in Notificacion.Estado.values:
        messages.error(request, "Selecciona un estado válido.")
        return redirect('notificaciones')
    if not motivo:
        messages.error(request, "Debes indicar el motivo del cambio de estado.")
        return redirect('notificaciones')
    if notificacion.estado == estado:
        return redirect('notificaciones')

    with transaction.atomic():
        notificacion.estado = estado
        notificacion.save(update_fields=['estado'])
        HistorialNotificacion.objects.create(
            notificacion=notificacion,
            estado=estado,
            cambiado_por_id=request.session['usuario_id'],
            motivo=motivo,
        )
    return redirect('notificaciones')


def seguimiento_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _rol_seguimiento_permitido(request):
        return HttpResponseForbidden("No tienes permiso para consultar el módulo de seguimiento.")

    return _redirect_to_seguimiento()


def actualizar_accion_seguimiento_view(request, accion_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden gestionar acciones.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    accion = get_object_or_404(AccionSeguimiento, pk=accion_id)
    estado = request.POST.get('estado', '')
    motivo = request.POST.get('motivo', '').strip()
    if estado not in AccionSeguimiento.Estado.values or not motivo:
        messages.error(request, "El estado y el motivo del cambio son obligatorios.")
        return _redirect_to_seguimiento()
    if accion.estado == estado:
        return _redirect_to_seguimiento()

    with transaction.atomic():
        accion.estado = estado
        accion.completada_en = (
            timezone.now() if estado == AccionSeguimiento.Estado.COMPLETADA else None
        )
        accion.save(update_fields=['estado', 'completada_en'])
        HistorialAccionSeguimiento.objects.create(
            accion=accion,
            estado=estado,
            cambiado_por_id=request.session['usuario_id'],
            motivo=motivo,
        )
    return _redirect_to_seguimiento()


def cerrar_seguimiento_view(request, caso_id, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if not _rol_seguimiento_permitido(request, ROLES_GESTION_SEGUIMIENTO):
        return HttpResponseForbidden("Solo el Administrador o Convivencia pueden cerrar un seguimiento.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    caso = get_object_or_404(Caso, pk=caso_id)
    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if not caso.estudiantes.filter(pk=estudiante.pk).exists():
        return HttpResponseForbidden("El estudiante no está asociado a este caso.")
    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, "Debes indicar el motivo del cierre.")
        return _redirect_to_seguimiento()

    with transaction.atomic():
        seguimiento, _ = SeguimientoCaso.objects.get_or_create(
            caso=caso, estudiante=estudiante,
        )
        seguimiento = SeguimientoCaso.objects.select_for_update().get(pk=seguimiento.pk)
        if seguimiento.acciones.exclude(estado=AccionSeguimiento.Estado.COMPLETADA).exists():
            messages.error(request, "Completa todas las acciones requeridas antes de cerrar el seguimiento.")
            return _redirect_to_seguimiento()
        if seguimiento.estado != SeguimientoCaso.Estado.SOLUCIONADO:
            seguimiento.estado = SeguimientoCaso.Estado.SOLUCIONADO
            seguimiento.solucionado_en = timezone.now()
            seguimiento.solucionado_por_id = request.session['usuario_id']
            seguimiento.motivo_cierre = motivo
            seguimiento.save(update_fields=[
                'estado', 'solucionado_en', 'solucionado_por', 'motivo_cierre',
            ])
            HistorialSeguimientoCaso.objects.create(
                seguimiento=seguimiento,
                estado=seguimiento.estado,
                cambiado_por_id=request.session['usuario_id'],
                motivo=motivo,
            )
            notificaciones = Notificacion.objects.filter(
                caso=caso, estudiante=estudiante,
            ).exclude(estado=Notificacion.Estado.SOLUCIONADO)
            for notificacion in notificaciones:
                notificacion.estado = Notificacion.Estado.SOLUCIONADO
                notificacion.save(update_fields=['estado'])
                HistorialNotificacion.objects.create(
                    notificacion=notificacion,
                    estado=notificacion.estado,
                    cambiado_por_id=request.session['usuario_id'],
                    motivo=f'Cierre autorizado del seguimiento: {motivo}',
                )
    return _redirect_to_seguimiento()
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
    rol_usuario = request.session.get('usuario_rol', '')

    if not _puede_editar_caso(rol_usuario, caso):
        if rol_usuario == 'Administrador':
            messages.error(request, "No fue posible validar el plazo de edición del caso.")
        elif rol_usuario in ('Inspector', 'PConvivencia'):
            messages.error(
                request,
                "Solo puedes editar casos dentro de las 48 horas desde su creación.",
            )
        else:
            messages.error(request, "Acceso denegado: no tienes permisos para editar este caso.")
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

                evaluar_reglas_para_caso(
                    caso,
                    estudiantes_involucrados,
                    usuario_instancia,
                    evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    fecha_evento=timezone.now(),
                )

                # Notificar al creador si otro usuario modificó el caso
                if creador_caso and creador_caso.usuario_id != usuario_instancia.usuario_id:
                    notificacion_modificacion = Notificacion.objects.create(
                        usuario=creador_caso,
                        notificacion_titulo="Caso actualizado",
                        notificacion_mensaje=(
                            f"El caso #{caso.caso_id} fue modificado por "
                            f"{usuario_instancia.usuario_nombre} "
                            f"{usuario_instancia.usuario_apaterno}."
                        ),
                        notificacion_icono="✏️",
                        caso=caso,
                        evento_tipo=Notificacion.TipoEvento.CASO_ACTUALIZADO,
                    )
                    HistorialNotificacion.objects.create(
                        notificacion=notificacion_modificacion,
                        estado=notificacion_modificacion.estado,
                        cambiado_por=usuario_instancia,
                        motivo='Notificación creada al modificar un caso.',
                    )

                HistorialUsuario.objects.create(
                    usuario=usuario_instancia,
                    historial_accion="Modificación",
                    historial_detalle=(
                        f"Modificó los registros del caso #{caso.caso_id}. "
                        "Estudiantes: "
                        + ", ".join(
                            f"{estudiante.estudiante_nombre} "
                            f"{estudiante.estudiante_apaterno} "
                            f"{estudiante.estudiante_amaterno}"
                            for estudiante in estudiantes_involucrados
                        )
                        + "."
                    )
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
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    caso = get_object_or_404(Caso, pk=caso_id)
    rol_usuario = request.session.get('usuario_rol', '')
    if not _puede_editar_caso(rol_usuario, caso):
        if rol_usuario in ('Inspector', 'PConvivencia'):
            messages.error(
                request,
                "Solo puedes editar casos dentro de las 48 horas desde su creación.",
            )
        else:
            messages.error(
                request,
                "Acceso denegado: no tienes permisos para editar este caso.",
            )
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

    from django.utils.dateparse import parse_date

    # Filtros combinables: usuario responsable, tipo de acción y rango de fechas
    filtro_usuario = request.GET.get('usuario', '').strip()
    filtro_busqueda = request.GET.get('busqueda', '').strip()
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

    if filtro_busqueda:
        for termino in filtro_busqueda.split():
            termino_norm = _quitar_tildes(termino)
            registros_auditoria = registros_auditoria.filter(
                Q(historial_detalle__unaccent__icontains=termino_norm)
                | Q(usuario__usuario_nombre__icontains=termino)
                | Q(usuario__usuario_apaterno__icontains=termino)
                | Q(usuario__usuario_amaterno__icontains=termino)
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
            'busqueda': filtro_busqueda,
            'accion': filtro_accion,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
        },
        'hay_filtros_activos': bool(
            filtro_usuario or filtro_busqueda or filtro_accion
            or filtro_fecha_desde or filtro_fecha_hasta
        ),
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
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        curso_id = request.POST.get('curso')
        numero_lista = request.POST.get('numero_lista', '').strip()

        try:
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError("Completa los nombres y apellidos del alumno.")
            if correo:
                validate_email(correo)
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
                estudiante_correo=correo or None,
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
                
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Exception:
            logger.exception("Error registrando alumno %s %s", nombre, apaterno)
            messages.error(request, "No fue posible registrar al alumno. Revisa el curso y vuelve a intentarlo.")

    from urllib.parse import urlencode

    # Filtros combinables: búsqueda por texto, curso y N° de lista
    filtro_busqueda = request.GET.get('busqueda', '').strip()
    filtro_curso = request.GET.get('curso', '').strip()
    filtro_lista = request.GET.get('numero_lista', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()

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

    if filtro_estado in ('activo', 'inactivo'):
        estudiantes_registrados = estudiantes_registrados.filter(
            estudiante_activo=(filtro_estado == 'activo')
        )
    else:
        filtro_estado = ''

    cursos_disponibles = Curso.objects.all().order_by('curso_grado', 'curso_letra')

    # Para que los enlaces de paginación conserven los filtros activos
    parametros = {k: val for k, val in (
        ('busqueda', filtro_busqueda), ('curso', filtro_curso),
        ('numero_lista', filtro_lista), ('estado', filtro_estado)
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
            'estado': filtro_estado,
        },
        'hay_filtros_activos': bool(parametros),
        'querystring_filtros': querystring_filtros,
        'historial_importaciones': HistorialImportacionEstudiantes.objects.all()[:10],
    }
    return render(request, 'gestion_casos/gestion_de_estudiantes.html', context)

def eliminar_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_alumnos')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    estudiante.estudiante_activo = False
    estudiante.save(update_fields=['estudiante_activo'])
    messages.success(
        request,
        f"El alumno {estudiante.estudiante_nombre} {estudiante.estudiante_apaterno} fue desactivado. "
        "Sus datos y antecedentes se conservaron.",
    )

    return redirect('gestion_de_alumnos')


def cambiar_estado_estudiante_view(request, estudiante_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('gestion_de_alumnos')

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    estudiante.estudiante_activo = not estudiante.estudiante_activo
    estudiante.save(update_fields=['estudiante_activo'])
    estado = 'activado' if estudiante.estudiante_activo else 'desactivado'
    messages.success(
        request,
        f"El alumno {estudiante.estudiante_nombre} {estudiante.estudiante_apaterno} fue {estado}.",
    )
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
    alumnos_agregados = []
    duplicados_detectados = []

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
                alumnos_agregados.append(
                    f"{nombre} {apaterno} {amaterno} ({curso_instancia})"
                )
            else:
                omitidos += 1
                duplicado = f"{nombre} {apaterno} {amaterno} ({curso_instancia})"
                duplicados_detectados.append(duplicado)
                errores.append(f"Fila {num_fila}: {duplicado} ya existía, se omitió.")

        except Exception as e:
            logger.exception("Error importando alumno desde fila %s del archivo %s", num_fila, archivo.name)
            errores.append(f"Fila {num_fila}: error inesperado ({str(e)}).")
            omitidos += 1

    try:
        usuario_importador = Usuario.objects.only('usuario_correo').get(
            pk=request.session['usuario_id']
        )
        HistorialImportacionEstudiantes.objects.create(
            archivo=archivo.name[:255],
            usuario_id_importo=usuario_importador.pk,
            usuario_correo_importo=usuario_importador.usuario_correo,
            alumnos_agregados=alumnos_agregados,
            duplicados_detectados=duplicados_detectados,
            filas_omitidas=omitidos,
        )
    except Exception:
        logger.exception("No fue posible registrar la auditoría de importación de alumnos")
        messages.error(
            request,
            "La importación se procesó, pero no se pudo guardar su registro de auditoría. Contacta al administrador.",
        )

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
        correo = request.POST.get('correo', '').strip()
        curso_id = request.POST.get('curso')
        numero_lista = request.POST.get('numero_lista', '').strip()

        try:
            if not all((nombre, apaterno, amaterno)):
                raise ValidationError("Completa los nombres y apellidos del alumno.")
            if correo:
                validate_email(correo)
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
            estudiante.estudiante_correo = correo or None
            estudiante.curso = curso_instancia
            estudiante.estudiante_numero_lista = numero_lista_val
            estudiante.save()  # recalcula el identificador automáticamente
            messages.success(request, f"Alumno(a) {nombre} {apaterno} actualizado(a) exitosamente.")
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Exception:
            logger.exception("Error actualizando estudiante %s", estudiante_id)
            messages.error(request, "No fue posible actualizar al alumno. Revisa los datos ingresados.")

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

        if not archivo.name.lower().endswith('.pdf'):
            messages.error(request, "Solo se permiten archivos PDF.")
            return redirect('gestion_documentos')

        limite_bytes = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
        if not archivo.size:
            messages.error(request, "El archivo PDF está vacío.")
            return redirect('gestion_documentos')
        if archivo.size > limite_bytes:
            messages.error(
                request,
                f"El archivo supera el tamaño máximo permitido "
                f"({limite_bytes // (1024 * 1024)} MB).",
            )
            return redirect('gestion_documentos')

        tipo_mime = getattr(archivo, 'content_type', '')
        if tipo_mime not in ('', 'application/pdf', 'application/octet-stream'):
            messages.error(request, "El tipo de contenido del archivo no corresponde a un PDF.")
            return redirect('gestion_documentos')

        contenido = archivo.read()
        archivo.seek(0)
        if not contenido.startswith(b'%PDF-'):
            messages.error(request, "El contenido del archivo no es un PDF válido.")
            return redirect('gestion_documentos')

        try:
            usuario_instancia = Usuario.objects.get(pk=request.session['usuario_id'])
            documento = DocumentoInstitucional.objects.create(
                tipo_documento=tipo_documento,
                titulo=titulo if titulo else archivo.name,
                archivo=archivo,
                usuario=usuario_instancia,
                estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.PROCESANDO,
                checksum_sha256=hashlib.sha256(contenido).hexdigest(),
            )
        except Exception as error:
            logger.error(
                "Error al almacenar un documento institucional (%s).",
                type(error).__name__,
            )
            messages.error(request, "No se pudo almacenar el documento. Revisa la configuración de Cloudinary.")
            return redirect('gestion_documentos')

        try:
            candidatas_count = _procesar_documento_institucional(
                documento,
                contenido,
                usuario_instancia,
            )
            if tipo_documento == 'Reglamento':
                messages.success(
                    request,
                    f"Reglamento almacenado y procesado. "
                    f"Se detectaron {candidatas_count} propuestas, todas pendientes de revisión.",
                )
            else:
                messages.success(request, "Documento institucional almacenado y procesado.")
        except ErrorProcesamientoPDF as error:
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = str(error)
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            messages.error(request, str(error))
        except Exception as error:
            logger.error(
                "Error al extraer texto del documento institucional %s (%s).",
                documento.documento_id,
                type(error).__name__,
            )
            documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
            documento.error_procesamiento = (
                'Ocurrió un error interno durante la extracción. '
                'Revisa el archivo y vuelve a intentarlo.'
            )
            documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
            messages.error(request, documento.error_procesamiento)

        return redirect('gestion_documentos')

    context = {
        'reglamentos': DocumentoInstitucional.objects.filter(
            tipo_documento='Reglamento',
        ).annotate(
            version_count=Count('versiones_reglamento', distinct=True),
            rule_count=Count('versiones_reglamento__reglas', distinct=True),
        ),
        'protocolos': DocumentoInstitucional.objects.filter(
            tipo_documento='Protocolo',
        ).annotate(
            version_count=Count('versiones_reglamento', distinct=True),
            rule_count=Count('versiones_reglamento__reglas', distinct=True),
        ),
        'es_administrador': es_administrador,
        'versiones_reglamento': VersionReglamento.objects.select_related(
            'documento', 'creada_por', 'activada_por',
        ).prefetch_related('reglas').order_by('-creada_en'),
        'puede_revisar_reglas': es_administrador,
        'estados_regla': ReglaInstitucional.Estado.choices,
        'activadores_regla': ReglaInstitucional.Activador.choices,
        'tipos_medida': ReglaInstitucional.TipoMedida.choices,
        'roles_responsables': ReglaInstitucional.RolResponsable.choices,
        'referencias_plazo': ReglaInstitucional.ReferenciaPlazo.choices,
        'limite_pdf_mb': getattr(
            settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024
        ) // (1024 * 1024),
    }
    return render(request, 'gestion_casos/gestion_documentos.html', context)

def _procesar_documento_institucional(documento, contenido, usuario):
    paginas = extraer_paginas_pdf(contenido)
    documento.texto_extraido = '\n\n'.join(paginas)
    documento.numero_paginas = len(paginas)
    documento.error_procesamiento = ''
    documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
    documento.save(update_fields=[
        'texto_extraido', 'numero_paginas', 'error_procesamiento',
        'estado_procesamiento',
    ])

    if documento.tipo_documento != 'Reglamento':
        return 0
    if VersionReglamento.objects.filter(documento=documento).exists():
        return 0

    ultimo_numero = (
        VersionReglamento.objects.filter(documento__tipo_documento='Reglamento')
        .order_by('-numero')
        .values_list('numero', flat=True)
        .first()
        or 0
    )
    with transaction.atomic():
        version = VersionReglamento.objects.create(
            documento=documento,
            numero=ultimo_numero + 1,
            creada_por=usuario,
        )
        candidatas = guardar_candidatas(version, paginas)
    return len(candidatas)


def reprocesar_documento_view(request, documento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede reprocesar documentos.")
    if request.method != 'POST':
        return HttpResponseForbidden("El reprocesamiento requiere una solicitud POST.")

    documento = get_object_or_404(DocumentoInstitucional, pk=documento_id)
    if documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.ERROR:
        messages.error(request, "Solo se pueden reprocesar documentos que estén en estado de error.")
        return redirect('gestion_documentos')

    documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.PROCESANDO
    documento.error_procesamiento = ''
    documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
    limite_bytes = getattr(settings, 'REGLAMENTO_PDF_MAX_BYTES', 20 * 1024 * 1024)
    try:
        with documento.archivo.open('rb') as archivo:
            contenido = archivo.read(limite_bytes + 1)
        if len(contenido) > limite_bytes:
            raise ErrorProcesamientoPDF(
                f'El PDF supera el límite de {limite_bytes // (1024 * 1024)} MB.'
            )
        if not contenido.startswith(b'%PDF-'):
            raise ErrorProcesamientoPDF("El archivo almacenado no contiene un PDF válido.")

        propuestas = _procesar_documento_institucional(
            documento,
            contenido,
            Usuario.objects.get(pk=request.session['usuario_id']),
        )
        mensaje = "Documento reprocesado correctamente."
        if documento.tipo_documento == 'Reglamento':
            if propuestas:
                mensaje += (
                    f" Se crearon {propuestas} propuestas nuevas, pendientes de revisión."
                )
            else:
                mensaje += " Se conservaron las versiones y reglas existentes."
        messages.success(request, mensaje)
    except ErrorProcesamientoPDF as error:
        documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
        documento.error_procesamiento = str(error)
        documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
        messages.error(request, str(error))
    except Exception as error:
        logger.error(
            "Error al reprocesar documento institucional %s (%s).",
            documento.documento_id,
            type(error).__name__,
        )
        documento.estado_procesamiento = DocumentoInstitucional.EstadoProcesamiento.ERROR
        documento.error_procesamiento = (
            'Ocurrió un error interno durante el reprocesamiento. '
            'Comprueba el almacenamiento y la configuración del servidor.'
        )
        documento.save(update_fields=['estado_procesamiento', 'error_procesamiento'])
        messages.error(request, documento.error_procesamiento)
    return redirect('gestion_documentos')


def crear_regla_manual_view(request, version_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede crear o revisar reglas.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    version = get_object_or_404(
        VersionReglamento.objects.select_related('documento'),
        pk=version_id,
        documento__estado_procesamiento=DocumentoInstitucional.EstadoProcesamiento.COMPLETADO,
    )
    if version.estado == VersionReglamento.Estado.VIGENTE:
        messages.error(request, "Una versión vigente es inmutable. Sube una nueva versión para revisarla.")
        return redirect('gestion_documentos')
    evidencia = request.POST.get('evidencia_textual', '').strip()
    if not evidencia or evidencia not in version.documento.texto_extraido:
        messages.error(request, "La cita debe coincidir con texto extraído del documento.")
        return redirect('gestion_documentos')

    pagina = request.POST.get('pagina', '').strip()
    referencia = f'Página {pagina}' if pagina.isdigit() else ''
    regla = ReglaInstitucional.objects.create(
        version=version,
        titulo=request.POST.get('titulo', '').strip()[:180] or evidencia[:180],
        evidencia_textual=evidencia,
        referencia_origen=referencia,
        hash_origen=hashlib.sha256(
            f'manual\0{version.pk}\0{referencia}\0{evidencia}'.encode('utf-8')
        ).hexdigest(),
    )
    HistorialUsuario.objects.create(
        usuario_id=request.session['usuario_id'],
        historial_accion='Creación',
        historial_detalle=f'Creó una propuesta de regla para la versión {version.pk}.',
    )
    messages.success(request, "Propuesta creada; completa sus campos y revísala antes de aprobarla.")
    return redirect('gestion_documentos')


def revisar_regla_view(request, regla_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede revisar reglas.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    regla = get_object_or_404(ReglaInstitucional, pk=regla_id)
    if regla.version.estado == VersionReglamento.Estado.VIGENTE:
        messages.error(request, "Una versión vigente es inmutable. Sube una nueva versión para cambiar sus reglas.")
        return redirect('gestion_documentos')
    estado = request.POST.get('estado', '')
    activador = request.POST.get('activador', '')
    tipo_medida = request.POST.get('tipo_medida', regla.tipo_medida)
    titulo = request.POST.get('titulo', '').strip()
    categoria = request.POST.get('categoria_falta', '').strip()
    accion = request.POST.get('accion_requerida', '').strip()
    responsable = request.POST.get('responsable_rol', '').strip()
    umbral_raw = request.POST.get('umbral_casos', '').strip()
    umbral_anotaciones_raw = request.POST.get('umbral_anotaciones', '').strip()
    plazo_raw = request.POST.get('plazo_dias', '').strip()
    plazo_desde = request.POST.get(
        'plazo_desde', ReglaInstitucional.ReferenciaPlazo.SIN_DEFINIR,
    )
    if estado not in ReglaInstitucional.Estado.values:
        messages.error(request, "Selecciona un estado de revisión válido.")
        return redirect('gestion_documentos')
    if activador not in ReglaInstitucional.Activador.values:
        messages.error(request, "Selecciona un tipo de condición válido.")
        return redirect('gestion_documentos')
    if tipo_medida not in ReglaInstitucional.TipoMedida.values:
        messages.error(request, "Selecciona un tipo de disposición válido.")
        return redirect('gestion_documentos')
    if responsable and responsable not in ReglaInstitucional.RolResponsable.values:
        messages.error(request, "Selecciona un responsable válido.")
        return redirect('gestion_documentos')
    if plazo_desde not in ReglaInstitucional.ReferenciaPlazo.values:
        messages.error(request, "Selecciona un inicio de plazo válido.")
        return redirect('gestion_documentos')

    try:
        umbral = int(umbral_raw) if umbral_raw else None
        umbral_anotaciones = (
            int(umbral_anotaciones_raw) if umbral_anotaciones_raw else None
        )
        if (
            umbral_anotaciones is None
            and regla.unidad_umbral == ReglaInstitucional.UnidadUmbral.ANOTACIONES
        ):
            umbral_anotaciones = regla.cantidad_minima
        plazo = int(plazo_raw) if plazo_raw else None
    except ValueError:
        messages.error(request, "El umbral y el plazo deben ser números enteros.")
        return redirect('gestion_documentos')
    if (
        (umbral is not None and not 1 <= umbral <= 10000)
        or (
            umbral_anotaciones is not None
            and not 1 <= umbral_anotaciones <= 10000
        )
        or (plazo is not None and not 0 <= plazo <= 3650)
    ):
        messages.error(request, "El umbral o el plazo están fuera del rango permitido.")
        return redirect('gestion_documentos')
    if activador == ReglaInstitucional.Activador.UMBRAL_CASOS and umbral is None:
        messages.error(request, "La condición por umbral requiere un número de casos.")
        return redirect('gestion_documentos')
    if plazo_desde == ReglaInstitucional.ReferenciaPlazo.EVENTO and plazo is None:
        messages.error(request, "Define los días del plazo antes de calcular su vencimiento.")
        return redirect('gestion_documentos')
    if estado == ReglaInstitucional.Estado.APROBADA and (
        not regla.evidencia_textual.strip()
        or not (
            categoria
            or regla.conducta_condicion.strip()
            or regla.medida_asociada.strip()
        )
        or (
            not regla.solo_presentacion
            and (not categoria or not accion)
        )
    ):
        messages.error(
            request,
            "Para aprobar, completa la disposición, su evidencia y los campos "
            "requeridos por su modalidad.",
        )
        return redirect('gestion_documentos')
    if (
        estado == ReglaInstitucional.Estado.APROBADA
        and regla.solo_presentacion
        and (
            tipo_medida == ReglaInstitucional.TipoMedida.NO_CLASIFICADA
            or not regla.version_fuente.strip()
            or not regla.titulo_fuente.strip()
            or not regla.seccion_fuente.strip()
            or not regla.pagina_impresa
            or not regla.pagina_pdf
        )
    ):
        messages.error(
            request,
            "Para aprobar una disposición de solo presentación, completa su tipo "
            "y referencia verificable de versión, sección y páginas.",
        )
        return redirect('gestion_documentos')

    with transaction.atomic():
        if titulo:
            regla.titulo = titulo[:180]
        regla.tipo_medida = tipo_medida
        regla.categoria_falta = categoria[:100]
        regla.activador = activador
        regla.umbral_casos = (
            umbral if activador == ReglaInstitucional.Activador.UMBRAL_CASOS else None
        )
        regla.umbral_anotaciones = umbral_anotaciones
        regla.accion_requerida = accion
        regla.requiere_citacion_apoderado = request.POST.get('requiere_citacion') == 'on'
        regla.plazo_dias = plazo
        regla.plazo_desde = plazo_desde
        regla.responsable_rol = responsable
        regla.estado = estado
        regla.revisada_por_id = request.session['usuario_id']
        regla.revisada_en = timezone.now()
        regla.save(update_fields=[
            'titulo', 'tipo_medida', 'categoria_falta', 'activador', 'umbral_casos', 'accion_requerida',
            'umbral_anotaciones', 'requiere_citacion_apoderado', 'plazo_dias',
            'plazo_desde', 'responsable_rol',
            'estado', 'revisada_por', 'revisada_en',
        ])
        HistorialUsuario.objects.create(
            usuario_id=request.session['usuario_id'],
            historial_accion='Modificación',
            historial_detalle=(
                f'Revisó la regla {regla.pk}: '
                f'{regla.get_estado_display()} ({regla.referencia_origen or "sin referencia"}).'
            ),
        )
    messages.success(request, "La revisión de la regla quedó registrada.")
    return redirect('gestion_documentos')


def activar_version_reglamento_view(request, version_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        return HttpResponseForbidden("Solo un Administrador puede activar una versión.")
    if request.method != 'POST':
        return HttpResponseForbidden("La acción requiere una solicitud POST.")

    with transaction.atomic():
        version = get_object_or_404(
            VersionReglamento.objects.select_for_update().select_related('documento'),
            pk=version_id,
        )
        reglas_aprobadas = list(
            version.reglas.filter(estado=ReglaInstitucional.Estado.APROBADA)
        )
        if (
            version.documento.estado_procesamiento != DocumentoInstitucional.EstadoProcesamiento.COMPLETADO
            or not reglas_aprobadas
            or any(not regla.puede_activarse() for regla in reglas_aprobadas)
        ):
            messages.error(
                request,
                "No se puede activar: el documento debe estar procesado y debe existir "
                "al menos una disposición aprobada con evidencia y datos suficientes.",
            )
            return redirect('gestion_documentos')

        VersionReglamento.objects.filter(estado=VersionReglamento.Estado.VIGENTE).exclude(
            pk=version.pk
        ).update(estado=VersionReglamento.Estado.REEMPLAZADA)
        version.estado = VersionReglamento.Estado.VIGENTE
        version.activada_en = timezone.now()
        version.activada_por_id = request.session['usuario_id']
        version.save(update_fields=['estado', 'activada_en', 'activada_por'])
        HistorialUsuario.objects.create(
            usuario_id=request.session['usuario_id'],
            historial_accion='Modificación',
            historial_detalle=f'Activó la versión {version.pk} del reglamento institucional.',
        )
    messages.success(request, "La versión aprobada ahora está vigente.")
    return redirect('gestion_documentos')


def eliminar_documento_view(request, documento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 'Administrador':
        messages.error(request, "Acceso denegado: No tienes permisos de Administrador.")
        return redirect('gestion_documentos')
    if request.method != 'POST':
        return HttpResponseForbidden("La eliminación requiere una solicitud POST.")

    try:
        with transaction.atomic():
            documento = (
                DocumentoInstitucional.objects.select_for_update()
                .filter(pk=documento_id)
                .first()
            )
            if documento is None:
                messages.info(
                    request,
                    "El documento ya no existe; puede que se haya eliminado "
                    "desde otra sesión. Actualiza la página para ver el listado vigente.",
                )
                return redirect('gestion_documentos')

            documento_id_auditoria = documento.pk
            titulo = documento.titulo
            nombre_archivo = documento.archivo.name
            almacenamiento = documento.archivo.storage
            cantidad_versiones = documento.versiones_reglamento.count()
            cantidad_reglas = ReglaInstitucional.objects.filter(
                version__documento=documento,
            ).count()

            Notificacion.objects.filter(
                Q(regla__version__documento=documento)
                | Q(version_reglamento__documento=documento)
            ).update(
                notificacion_titulo='Disposición reglamentaria retirada',
                notificacion_mensaje=(
                    'La disposición vinculada a esta notificación fue retirada '
                    'al reemplazar el documento. No utilices la orientación anterior; '
                    'solicita revisión del personal autorizado.'
                ),
                regla=None,
                version_reglamento=None,
            )
            HistorialUsuario.objects.create(
                usuario_id=request.session['usuario_id'],
                historial_accion='Eliminación',
                historial_detalle=(
                    f'Eliminó el documento institucional "{titulo}" '
                    f'(ID {documento.pk}), junto con {cantidad_versiones} versión(es) '
                    f'y {cantidad_reglas} propuesta(s) asociada(s).'
                ),
            )
            documento.delete()
    except Exception:
        logger.exception(
            "Error al eliminar el documento institucional %s.", documento_id,
        )
        messages.error(
            request,
            "No se pudo eliminar el documento y sus propuestas. No se confirmó "
            "la eliminación del archivo.",
        )
        return redirect('gestion_documentos')

    try:
        if nombre_archivo:
            almacenamiento.delete(nombre_archivo)
    except Exception:
        logger.exception(
            "El registro del documento %s se eliminó, pero falló la limpieza del archivo.",
            documento_id_auditoria,
        )
        messages.warning(
            request,
            "El documento y sus versiones/propuestas se eliminaron, pero el archivo "
            "almacenado no pudo limpiarse. Contacta al Administrador del sistema.",
        )
    else:
        messages.success(
            request,
            f"Se eliminó «{titulo}» junto con {cantidad_versiones} versión(es) "
            f"y {cantidad_reglas} propuesta(s). Ya puedes subir el reglamento de reemplazo.",
        )

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


def _filtrar_casos_del_curso(request, curso):
    desde_raw = request.GET.get('fecha_desde', '').strip()
    hasta_raw = request.GET.get('fecha_hasta', '').strip()
    gravedad = request.GET.get('gravedad', '').strip()
    desde = parse_date(desde_raw) if desde_raw else None
    hasta = parse_date(hasta_raw) if hasta_raw else None
    if desde_raw and not desde:
        messages.warning(request, "La fecha inicial no es válida y se ignoró.")
    if hasta_raw and not hasta:
        messages.warning(request, "La fecha final no es válida y se ignoró.")
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde
        messages.warning(request, "Las fechas estaban invertidas; se intercambiaron para aplicar el filtro.")

    casos = _obtener_casos_del_curso(curso)
    if desde:
        casos = [caso for caso in casos if caso['fecha'] and caso['fecha'] >= desde]
    if hasta:
        casos = [caso for caso in casos if caso['fecha'] and caso['fecha'] <= hasta]
    if gravedad in ('Leve', 'Grave', 'Gravísima'):
        casos = [caso for caso in casos if caso['tipo_falta'] == gravedad]
    else:
        gravedad = ''
    return casos, {
        'fecha_desde': desde.isoformat() if desde else '',
        'fecha_hasta': hasta.isoformat() if hasta else '',
        'gravedad': gravedad,
    }


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

    casos_del_curso, filtros = _filtrar_casos_del_curso(request, profesor.curso)
    from urllib.parse import urlencode
    filtros_query = urlencode({key: value for key, value in filtros.items() if value})

    context = {
        'curso': profesor.curso,
        'casos': casos_del_curso,
        'total_casos': len(casos_del_curso),
        'solicitudes_caso': SolicitudCaso.objects.filter(
            solicitante_id=request.session['usuario_id'],
        ).select_related('lugar', 'revisada_por')[:10],
        'filtros': filtros,
        'filtros_query': filtros_query,
    }
    return render(request, 'gestion_casos/mis_casos_curso.html', context)


def descargar_casos_pdf_view(request):
    curso = _validar_profesor_jefe(request)
    if not curso:
        messages.error(request, "Acceso denegado o no tienes un curso asignado como Profesor Jefe.")
        return redirect('dashboard')

    casos, _ = _filtrar_casos_del_curso(request, curso)

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

    casos, _ = _filtrar_casos_del_curso(request, curso)

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

    prioridad_gravedad = {'Gravísima': 0, 'Grave': 1, 'Leve': 2}
    casos_detalle.sort(
        key=lambda caso: prioridad_gravedad.get(caso['gravedad'], 3)
    )

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

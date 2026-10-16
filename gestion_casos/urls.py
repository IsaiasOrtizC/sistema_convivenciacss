from django.urls import path
from .controllers import (
    alumno_controller,
    auth_controller,
    busqueda_controller,
    caso_controller,
    configuracion_controller,
    dashboard_controller,
    documento_controller,
    notification_controller,
    profile_controller,
    report_controller,
    rules_controller,
    seguimiento_controller,
    statistics_controller,
    user_controller,
)

urlpatterns = [
    path('', auth_controller.login_view, name='login'),
    path('logout/', auth_controller.logout_view, name='logout'),
    path('dashboard/', dashboard_controller.dashboard_view, name='dashboard'),
    path('casos/', caso_controller.historial_casos_view, name='historial_casos'),
    path('casos/nuevo/', caso_controller.registrar_caso_view, name='registrar_caso'),
    path(
        'casos/pendientes/',
        caso_controller.solicitudes_casos_pendientes_view,
        name='solicitudes_casos_pendientes',
    ),
    path('casos/<int:caso_id>/', caso_controller.detalle_caso_view, name='detalle_caso'),
    path('casos/<int:caso_id>/pdf/', report_controller.descargar_caso_pdf_view, name='descargar_caso_pdf'),
    path('casos/<int:caso_id>/xlsx/', report_controller.descargar_caso_xlsx_view, name='descargar_caso_xlsx'),
    path('estadisticas/', statistics_controller.estadisticas_view, name='estadisticas'),
    path('estadisticas/datos/', statistics_controller.estadisticas_datos_view, name='estadisticas_datos'),
    path('estadisticas/pdf/', report_controller.estadisticas_pdf_view, name='estadisticas_pdf'),
    path('estadisticas/xlsx/', report_controller.estadisticas_xlsx_view, name='estadisticas_xlsx'),
    path('notificaciones/', notification_controller.notificaciones_view, name='notificaciones'),
    path(
    'notificaciones/<int:notificacion_id>/leer/',
    notification_controller.marcar_notificacion_leida_view,
    name='marcar_notificacion_leida'),
    path(
        'notificaciones/<int:notificacion_id>/estado/',
        notification_controller.cambiar_estado_notificacion_view,
        name='cambiar_estado_notificacion',
    ),
    path('seguimiento/', seguimiento_controller.seguimiento_view, name='seguimiento'),
    path(
        'seguimiento/acciones/<int:accion_id>/estado/',
        seguimiento_controller.actualizar_accion_seguimiento_view,
        name='actualizar_accion_seguimiento',
    ),
    path(
        'seguimiento/casos/<int:caso_id>/estudiantes/<int:estudiante_id>/cerrar/',
        seguimiento_controller.cerrar_seguimiento_view,
        name='cerrar_seguimiento',
    ),
    path('casos/editar/<int:caso_id>/', caso_controller.editar_caso_view, name='editar_caso'),
    path('casos/editar/<int:caso_id>/eliminar_estudiante/<int:estudiante_id>/', caso_controller.eliminar_estudiante_caso_view, name='eliminar_estudiante_caso'),
    path('casos/eliminar/<int:caso_id>/', caso_controller.eliminar_caso_view, name='eliminar_caso'),

    # Módulos de Administración
    path('administracion/usuarios/', user_controller.gestion_de_usuarios_view, name='gestion_de_usuarios'),
    path('administracion/usuarios/editar/<int:usuario_id>/', user_controller.editar_usuario_view, name='editar_usuario'),
    path('administracion/usuarios/acciones-masivas/', user_controller.acciones_masivas_usuarios_view, name='acciones_masivas_usuarios'),
    path('administracion/usuarios/desbloquear/<int:usuario_id>/', user_controller.desbloquear_usuario_view, name='desbloquear_usuario'),
    path('administracion/alumnos/', alumno_controller.gestion_de_estudiantes_view, name='gestion_de_alumnos'),
    path('administracion/alumnos/importar/', alumno_controller.importar_estudiantes_view, name='importar_estudiantes'),
    path('administracion/alumnos/eliminar/<int:estudiante_id>/', alumno_controller.eliminar_estudiante_view, name='eliminar_estudiante'),
    path('administracion/alumnos/estado/<int:estudiante_id>/', alumno_controller.cambiar_estado_estudiante_view, name='cambiar_estado_estudiante'),
    path('administracion/alumnos/editar/<int:estudiante_id>/', alumno_controller.editar_estudiante_view, name='editar_estudiante'),
    path('modulo-admin/historial-usuarios/', user_controller.historial_usuarios_view, name='historial_de_usuarios'),
    
    # PARA VER DATOS PUBLICOS
    path('mis-datos/perfil/', profile_controller.gestion_datos_publicos_view, name='gestion_datos_publicos'),
    
    # PARA VER CONFIG
    path('mis-datos/configuracion/', configuracion_controller.gestion_configuracion_view, name='gestion_configuracion'),

    # Documentos institucionales (Reglamento Interno / Protocolos de Convivencia)
    path('documentos/', documento_controller.gestion_documentos_view, name='gestion_documentos'),
    path(
        'documentos/<int:documento_id>/reprocesar/',
        documento_controller.reprocesar_documento_view,
        name='reprocesar_documento',
    ),
    path(
        'documentos/versiones/<int:version_id>/reglas/nueva/',
        rules_controller.crear_regla_manual_view,
        name='crear_regla_manual',
    ),
    path(
        'documentos/reglas/<int:regla_id>/revisar/',
        rules_controller.revisar_regla_view,
        name='revisar_regla',
    ),
    path(
        'documentos/versiones/<int:version_id>/activar/',
        rules_controller.activar_version_reglamento_view,
        name='activar_version_reglamento',
    ),
    path('documentos/eliminar/<int:documento_id>/', documento_controller.eliminar_documento_view, name='eliminar_documento'),

    # RF-40: Descarga de casos del curso (Profesor Jefe)
    path('mis-casos-curso/', caso_controller.mis_casos_curso_view, name='mis_casos_curso'),
    path('mis-casos-curso/pdf/', report_controller.descargar_casos_pdf_view, name='descargar_casos_pdf'),
    path('mis-casos-curso/xlsx/', report_controller.descargar_casos_xlsx_view, name='descargar_casos_xlsx'),

    # Buscador global (lupa en la barra superior)
    path('busqueda/', busqueda_controller.busqueda_global_view, name='busqueda_global'),
    path('alumnos/<int:estudiante_id>/ficha/', alumno_controller.detalle_estudiante_view, name='detalle_estudiante'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('casos/', views.historial_casos_view, name='historial_casos'),
    path('casos/nuevo/', views.registrar_caso_view, name='registrar_caso'),
    path('casos/<int:caso_id>/', views.detalle_caso_view, name='detalle_caso'),
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
    path('estadisticas/datos/', views.estadisticas_datos_view, name='estadisticas_datos'),
    path('estadisticas/pdf/', views.estadisticas_pdf_view, name='estadisticas_pdf'),
    path('estadisticas/xlsx/', views.estadisticas_xlsx_view, name='estadisticas_xlsx'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('casos/editar/<int:caso_id>/', views.editar_caso_view, name='editar_caso'),
    path('casos/editar/<int:caso_id>/eliminar_estudiante/<int:estudiante_id>/', views.eliminar_estudiante_caso_view, name='eliminar_estudiante_caso'),
    path('casos/eliminar/<int:caso_id>/', views.eliminar_caso_view, name='eliminar_caso'),

    # Módulos de Administración
    path('administracion/usuarios/', views.gestion_de_usuarios_view, name='gestion_de_usuarios'),
    path('administracion/usuarios/editar/<int:usuario_id>/', views.editar_usuario_view, name='editar_usuario'),
    path('administracion/alumnos/', views.gestion_de_estudiantes_view, name='gestion_de_alumnos'),
    path('administracion/alumnos/importar/', views.importar_estudiantes_view, name='importar_estudiantes'),
    path('administracion/alumnos/eliminar/<int:estudiante_id>/', views.eliminar_estudiante_view, name='eliminar_estudiante'),
    path('administracion/alumnos/editar/<int:estudiante_id>/', views.editar_estudiante_view, name='editar_estudiante'),
    path('modulo-admin/historial-usuarios/', views.historial_usuarios_view, name='historial_de_usuarios'),
    
    # PARA VER DATOS PUBLICOS
    path('mis-datos/perfil/', views.gestion_datos_publicos_view, name='gestion_datos_publicos'),
    
    # PARA VER CONFIG
    path('mis-datos/configuracion/', views.gestion_configuracion_view, name='gestion_configuracion'),

    # Documentos institucionales (Reglamento Interno / Protocolos de Convivencia)
    path('documentos/', views.gestion_documentos_view, name='gestion_documentos'),
    path('documentos/eliminar/<int:documento_id>/', views.eliminar_documento_view, name='eliminar_documento'),

    # RF-40: Descarga de casos del curso (Profesor Jefe)
    path('mis-casos-curso/', views.mis_casos_curso_view, name='mis_casos_curso'),
    path('mis-casos-curso/pdf/', views.descargar_casos_pdf_view, name='descargar_casos_pdf'),
    path('mis-casos-curso/xlsx/', views.descargar_casos_xlsx_view, name='descargar_casos_xlsx'),
]

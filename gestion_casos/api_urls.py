from django.urls import path

from .administration_api import (
    EstudiantesAdminAPIView,
    HistorialUsuariosAPIView,
    UsuariosAdminAPIView,
    UsuariosAdminBulkAPIView,
)
from .documents_api import (
    ActivarVersionReglamentoAPIView,
    DocumentosAPIView,
    ReglaInstitucionalAPIView,
    VersionReglamentoAPIView,
)
from .migration_api import (
    BusquedaGlobalAPIView,
    CasoExportAPIView,
    EstadisticasExportAPIView,
    MiCursoAPIView,
    MiCursoExportAPIView,
)
from .api import (
    CasoDetalleAPIView,
    DashboardAPIView,
    EstadisticasAPIView,
    CasoFormularioAPIView,
    HistorialCasosAPIView,
    NotificacionesAPIView,
    PerfilAPIView,
    RegistrarCasoAPIView,
    SolicitudesCasosAPIView,
    SeguimientoAPIView,
    TokenObtainView,
    TokenRefreshView,
)


urlpatterns = [
    path('auth/token/', TokenObtainView.as_view(), name='api_token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('v1/me/', PerfilAPIView.as_view(), name='api_me'),
    path('v1/busqueda/', BusquedaGlobalAPIView.as_view(), name='api_busqueda_global'),
    path('v1/mi-curso/', MiCursoAPIView.as_view(), name='api_mi_curso'),
    path(
        'v1/mi-curso/exportar/<str:formato>/',
        MiCursoExportAPIView.as_view(),
        name='api_exportar_mi_curso',
    ),
    path(
        'v1/casos/<int:caso_id>/exportar/<str:formato>/',
        CasoExportAPIView.as_view(),
        name='api_exportar_caso',
    ),
    path(
        'v1/estadisticas/exportar/<str:formato>/',
        EstadisticasExportAPIView.as_view(),
        name='api_exportar_estadisticas',
    ),
    path('v1/documentos/', DocumentosAPIView.as_view(), name='api_documentos'),
    path(
        'v1/documentos/<int:documento_id>/',
        DocumentosAPIView.as_view(),
        name='api_documento',
    ),
    path(
        'v1/documentos/versiones/<int:version_id>/reglas/',
        VersionReglamentoAPIView.as_view(),
        name='api_crear_regla_documento',
    ),
    path(
        'v1/documentos/reglas/<int:regla_id>/',
        ReglaInstitucionalAPIView.as_view(),
        name='api_revisar_regla_documento',
    ),
    path(
        'v1/documentos/versiones/<int:version_id>/activar/',
        ActivarVersionReglamentoAPIView.as_view(),
        name='api_activar_version_documento',
    ),
    path('v1/admin/usuarios/', UsuariosAdminAPIView.as_view(), name='api_admin_usuarios'),
    path(
        'v1/admin/usuarios/acciones-masivas/',
        UsuariosAdminBulkAPIView.as_view(),
        name='api_admin_usuarios_acciones_masivas',
    ),
    path(
        'v1/admin/usuarios/<int:usuario_id>/',
        UsuariosAdminAPIView.as_view(),
        name='api_admin_usuario',
    ),
    path(
        'v1/admin/estudiantes/',
        EstudiantesAdminAPIView.as_view(),
        name='api_admin_estudiantes',
    ),
    path(
        'v1/admin/estudiantes/importar/',
        EstudiantesAdminAPIView.as_view(),
        name='api_admin_importar_estudiantes',
    ),
    path(
        'v1/admin/estudiantes/<int:estudiante_id>/',
        EstudiantesAdminAPIView.as_view(),
        name='api_admin_estudiante',
    ),
    path(
        'v1/admin/historial-usuarios/',
        HistorialUsuariosAPIView.as_view(),
        name='api_admin_historial_usuarios',
    ),
    path('v1/dashboard/', DashboardAPIView.as_view(), name='api_dashboard'),
    path('v1/estadisticas/', EstadisticasAPIView.as_view(), name='api_estadisticas'),
    path('v1/casos/', HistorialCasosAPIView.as_view(), name='api_casos'),
    path(
        'v1/casos/<int:caso_id>/',
        CasoDetalleAPIView.as_view(),
        name='api_caso_detalle',
    ),
    path(
        'v1/casos/formulario/',
        CasoFormularioAPIView.as_view(),
        name='api_casos_formulario',
    ),
    path('v1/casos/nuevo/', RegistrarCasoAPIView.as_view(), name='api_registrar_caso'),
    path(
        'v1/casos/pendientes/',
        SolicitudesCasosAPIView.as_view(),
        name='api_solicitudes_casos_pendientes',
    ),
    path(
        'v1/casos/pendientes/<int:solicitud_id>/',
        SolicitudesCasosAPIView.as_view(),
        name='api_revisar_solicitud_caso',
    ),
    path(
        'v1/notificaciones/',
        NotificacionesAPIView.as_view(),
        name='api_notificaciones',
    ),
    path(
        'v1/notificaciones/<int:notificacion_id>/',
        NotificacionesAPIView.as_view(),
        name='api_notificacion_accion',
    ),
    path(
        'v1/seguimiento/',
        SeguimientoAPIView.as_view(),
        name='api_seguimiento',
    ),
    path(
        'v1/seguimiento/acciones/<int:accion_id>/',
        SeguimientoAPIView.as_view(),
        name='api_seguimiento_accion',
    ),
    path(
        'v1/seguimiento/casos/<int:caso_id>/estudiantes/<int:estudiante_id>/cerrar/',
        SeguimientoAPIView.as_view(),
        name='api_cerrar_seguimiento',
    ),
]

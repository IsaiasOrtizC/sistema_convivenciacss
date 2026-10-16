"""Compatibilidad hacia atrás.

Las vistas ahora viven en `gestion_casos/controllers/`. Este módulo solo las re-exporta para que
el código antiguo que haga `from gestion_casos import views` siga funcionando.
El código nuevo debe importar directamente desde el controlador correspondiente.
"""

from .controllers.alumno_controller import cambiar_estado_estudiante_view, detalle_estudiante_view, editar_estudiante_view, eliminar_estudiante_view, gestion_de_estudiantes_view, importar_estudiantes_view  # noqa: F401
from .controllers.auth_controller import login_view, logout_view  # noqa: F401
from .controllers.busqueda_controller import busqueda_global_view  # noqa: F401
from .controllers.caso_controller import detalle_caso_view, editar_caso_view, eliminar_caso_view, eliminar_estudiante_caso_view, historial_casos_view, mis_casos_curso_view, registrar_caso_view, solicitudes_casos_pendientes_view  # noqa: F401
from .controllers.configuracion_controller import gestion_configuracion_view  # noqa: F401
from .controllers.dashboard_controller import dashboard_view  # noqa: F401
from .controllers.documento_controller import eliminar_documento_view, gestion_documentos_view, reprocesar_documento_view  # noqa: F401
from .controllers.notification_controller import cambiar_estado_notificacion_view, marcar_notificacion_leida_view, notificaciones_view  # noqa: F401
from .controllers.profile_controller import gestion_datos_publicos_view  # noqa: F401
from .controllers.report_controller import descargar_caso_pdf_view, descargar_caso_xlsx_view, descargar_casos_pdf_view, descargar_casos_xlsx_view, estadisticas_pdf_view, estadisticas_xlsx_view  # noqa: F401
from .controllers.rules_controller import activar_version_reglamento_view, crear_regla_manual_view, revisar_regla_view  # noqa: F401
from .controllers.seguimiento_controller import actualizar_accion_seguimiento_view, cerrar_seguimiento_view, seguimiento_view  # noqa: F401
from .controllers.statistics_controller import estadisticas_datos_view, estadisticas_view  # noqa: F401
from .controllers.user_controller import acciones_masivas_usuarios_view, desbloquear_usuario_view, editar_usuario_view, gestion_de_usuarios_view, historial_usuarios_view  # noqa: F401

__all__ = [
    'acciones_masivas_usuarios_view',
    'activar_version_reglamento_view',
    'actualizar_accion_seguimiento_view',
    'busqueda_global_view',
    'cambiar_estado_estudiante_view',
    'cambiar_estado_notificacion_view',
    'cerrar_seguimiento_view',
    'crear_regla_manual_view',
    'dashboard_view',
    'desbloquear_usuario_view',
    'descargar_caso_pdf_view',
    'descargar_caso_xlsx_view',
    'descargar_casos_pdf_view',
    'descargar_casos_xlsx_view',
    'detalle_caso_view',
    'detalle_estudiante_view',
    'editar_caso_view',
    'editar_estudiante_view',
    'editar_usuario_view',
    'eliminar_caso_view',
    'eliminar_documento_view',
    'eliminar_estudiante_caso_view',
    'eliminar_estudiante_view',
    'estadisticas_datos_view',
    'estadisticas_pdf_view',
    'estadisticas_view',
    'estadisticas_xlsx_view',
    'gestion_configuracion_view',
    'gestion_datos_publicos_view',
    'gestion_de_estudiantes_view',
    'gestion_de_usuarios_view',
    'gestion_documentos_view',
    'historial_casos_view',
    'historial_usuarios_view',
    'importar_estudiantes_view',
    'login_view',
    'logout_view',
    'marcar_notificacion_leida_view',
    'mis_casos_curso_view',
    'notificaciones_view',
    'registrar_caso_view',
    'reprocesar_documento_view',
    'revisar_regla_view',
    'seguimiento_view',
    'solicitudes_casos_pendientes_view',
]

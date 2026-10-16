import os
import sys

from django.apps import AppConfig


class GestionCasosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_casos'

    def ready(self):
        from . import trazabilidad

        trazabilidad.conectar_senales()
        trazabilidad.parchear_render_de_plantillas()

        # Aviso de arranque: solo en el proceso que realmente atiende peticiones (no en el recargador)
        es_servidor = 'runserver' in sys.argv
        proceso_activo = os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv
        if es_servidor and proceso_activo and trazabilidad.nivel() > 0:
            problemas = trazabilidad.problemas_de_configuracion()
            if problemas:
                for problema in problemas:
                    trazabilidad.traza('ERROR', f'Trazabilidad mal configurada: {problema}')
                trazabilidad.traza('TRAZA', 'Revisa config/settings.py (ver docs/DEMO_TECNICA.md, sección 1).')
            else:
                trazabilidad.traza(
                    'TRAZA',
                    f'Trazabilidad activada (nivel {trazabilidad.nivel()}). '
                    'Cada petición mostrará su recorrido por las capas del sistema.',
                )

"""Reglas reutilizables de autorización: roles que pueden acceder a cada área del sistema."""



ROLES_SEGUIMIENTO = ('Administrador', 'PConvivencia', 'Inspector')
ROLES_GESTION_SEGUIMIENTO = ('Administrador', 'PConvivencia')
ROLES_APROBACION_CASOS = ('Administrador', 'PConvivencia', 'Inspector')


def rol_seguimiento_permitido(request, roles=ROLES_SEGUIMIENTO):
    if 'usuario_id' not in request.session:
        return False
    return request.session.get('usuario_rol') in roles


#panel de estadisticas
# ============================================================
#  RF-29 a RF-32 y RF-35: ESTADÍSTICAS DE CONVIVENCIA ESCOLAR
# ============================================================

def tiene_acceso_estadisticas(request):
    return request.session.get('usuario_rol') in ('Administrador', 'Inspector', 'PConvivencia')

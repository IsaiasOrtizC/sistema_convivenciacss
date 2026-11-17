from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from gestion_casos.models import SesionActiva


def _es_peticion_api(request):
    """Detecta si la solicitud proviene de la API REST o espera respuesta JSON."""
    accept = request.headers.get('Accept', '')
    return (
        request.path.startswith('/api/')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in accept
    )


class ForzarSesionUnicaMiddleware:
    """
    En cada petición, revisa que la sesión actual siga siendo la única válida
    para la cuenta y que el usuario permanezca activo y sin bloqueo.
    """

    RUTAS_EXCLUIDAS = ('/logout/',)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_id = request.session.get('usuario_id')

        if usuario_id and request.path not in self.RUTAS_EXCLUIDAS:
            registro = (
                SesionActiva.objects
                .filter(usuario_id=usuario_id)
                .values_list(
                    'session_key',
                    'usuario__usuario_activo',
                    'usuario__usuario_bloqueado',
                )
                .first()
            )

            if registro is not None:
                session_key_activa, activo, bloqueado = registro
                session_key_actual = request.session.session_key

                if not activo or bloqueado:
                    request.session.flush()
                    mensaje = "Tu cuenta ha sido desactivada o bloqueada. Contacta al Administrador."
                    if _es_peticion_api(request):
                        return JsonResponse({'detail': mensaje}, status=403)
                    messages.error(request, mensaje)
                    return redirect('login')

                if session_key_actual and session_key_activa != session_key_actual:
                    request.session.flush()
                    mensaje = (
                        "Tu sesión se cerró porque esta cuenta inició sesión "
                        "en otro dispositivo o navegador."
                    )
                    if _es_peticion_api(request):
                        return JsonResponse({'detail': mensaje}, status=401)
                    messages.error(request, mensaje)
                    return redirect('login')

        return self.get_response(request)


class ExigirCambioContrasenaMiddleware:
    """
    Obliga a los usuarios con contraseña temporal (primer ingreso) a cambiarla
    antes de acceder al resto del sistema.
    """

    RUTAS_PERMITIDAS = (
        '/mis-datos/configuracion/',
        '/logout/',
        '/api/v1/auth/logout/',
        '/api/v1/perfil/contrasena/',
    )
    PREFIJOS_EXCLUIDOS = ('/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get('usuario_id') and request.session.get('primer_ingreso'):
            path = request.path
            excluido = (
                path in self.RUTAS_PERMITIDAS
                or path.startswith(self.PREFIJOS_EXCLUIDOS)
            )
            if not excluido:
                mensaje = (
                    "Debes cambiar tu contraseña temporal antes de continuar "
                    "usando el sistema."
                )
                if _es_peticion_api(request):
                    return JsonResponse(
                        {'detail': mensaje, 'requiere_cambio_contrasena': True},
                        status=403,
                    )
                messages.error(request, mensaje)
                return redirect('gestion_configuracion')

        return self.get_response(request)
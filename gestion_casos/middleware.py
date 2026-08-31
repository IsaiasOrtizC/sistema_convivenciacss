from django.shortcuts import redirect
from django.contrib import messages


class ForzarSesionUnicaMiddleware:
    """
    En cada petición, revisa si la sesión actual del usuario sigue siendo
    la única válida para su cuenta. Si en otro dispositivo/navegador se
    inició sesión con la misma cuenta después, esta sesión queda obsoleta
    y se cierra automáticamente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_id = request.session.get('usuario_id')

        if usuario_id:
            # Import local para evitar problemas de carga de apps al iniciar Django
            from gestion_casos.models import SesionActiva

            try:
                sesion_activa = SesionActiva.objects.get(usuario_id=usuario_id)
                if sesion_activa.session_key != request.session.session_key:
                    # Esta sesión ya no es la vigente: alguien más inició sesión con esta cuenta.
                    request.session.flush()
                    messages.error(
                        request,
                        "Tu sesión se cerró porque esta cuenta inició sesión en otro dispositivo o navegador."
                    )
                    return redirect('login')
            except SesionActiva.DoesNotExist:
                # No hay registro de sesión activa (por ejemplo, cuentas creadas antes de
                # activar esta función). No se bloquea, simplemente no aplica el control.
                pass

        response = self.get_response(request)
        return response

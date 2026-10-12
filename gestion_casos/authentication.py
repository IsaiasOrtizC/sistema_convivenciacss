from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from .models import Usuario


class UsuarioJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed('El token no identifica a un usuario.')

        try:
            usuario = Usuario.objects.select_related('rol').get(pk=user_id)
        except (Usuario.DoesNotExist, TypeError, ValueError):
            raise AuthenticationFailed('El usuario del token ya no existe.')

        if not usuario.usuario_activo or usuario.usuario_bloqueado:
            raise AuthenticationFailed('La cuenta está inactiva o bloqueada.')

        return usuario

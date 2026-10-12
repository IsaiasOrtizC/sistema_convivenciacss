from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario


class TokenObtainView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía correo y contraseña en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correo = request.data.get('correo', '')
        contrasena = request.data.get('contrasena', '')
        if not isinstance(correo, str) or not isinstance(contrasena, str):
            return Response(
                {'detail': 'Envía correo y contraseña en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = (
            Usuario.objects.select_related('rol')
            .filter(usuario_correo=correo.strip())
            .first()
        )
        if usuario is None:
            return self._invalid_credentials()
        if usuario.usuario_bloqueado:
            return Response(
                {'detail': 'La cuenta está bloqueada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not check_password(contrasena, usuario.usuario_contrasena):
            usuario.usuario_intentos_fallidos += 1
            update_fields = ['usuario_intentos_fallidos']
            if usuario.usuario_intentos_fallidos >= 5:
                usuario.usuario_bloqueado = True
                update_fields.append('usuario_bloqueado')
            usuario.save(update_fields=update_fields)
            return self._invalid_credentials()
        if not usuario.usuario_activo:
            return Response(
                {'detail': 'La cuenta está inactiva.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if usuario.usuario_primer_ingreso:
            return Response(
                {
                    'detail': (
                        'Cambia tu contraseña temporal desde el sitio web '
                        'antes de solicitar un token.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario.usuario_intentos_fallidos = 0
        usuario.usuario_ultimo_acceso = timezone.now()
        usuario.save(
            update_fields=['usuario_intentos_fallidos', 'usuario_ultimo_acceso']
        )

        refresh = RefreshToken()
        refresh[api_settings.USER_ID_CLAIM] = usuario.pk
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'token_type': 'Bearer',
        })

    @staticmethod
    def _invalid_credentials():
        return Response(
            {'detail': 'Correo o contraseña incorrectos.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class TokenRefreshView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía el token refresh en formato JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_token = request.data.get('refresh', '')
        if not isinstance(raw_token, str) or not raw_token:
            return Response(
                {'detail': 'El campo refresh es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(raw_token)
            user_id = refresh.get(api_settings.USER_ID_CLAIM)
            if user_id is None:
                raise TokenError('El token no identifica a un usuario.')
            usuario = Usuario.objects.get(pk=user_id)
        except (TokenError, Usuario.DoesNotExist, TypeError, ValueError):
            return Response(
                {'detail': 'El token refresh no es válido.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if (
            not usuario.usuario_activo
            or usuario.usuario_bloqueado
            or usuario.usuario_primer_ingreso
        ):
            return Response(
                {'detail': 'La cuenta no puede renovar tokens.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({'access': str(refresh.access_token), 'token_type': 'Bearer'})


class PerfilAPIView(APIView):
    def get(self, request):
        usuario = request.user
        return Response({
            'id': usuario.pk,
            'nombre': usuario.usuario_nombre,
            'apellido_paterno': usuario.usuario_apaterno,
            'apellido_materno': usuario.usuario_amaterno,
            'correo': usuario.usuario_correo,
            'rol': usuario.rol.rol_nombre,
        })

from django.urls import path

from .api import PerfilAPIView, TokenObtainView, TokenRefreshView


urlpatterns = [
    path('auth/token/', TokenObtainView.as_view(), name='api_token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('v1/me/', PerfilAPIView.as_view(), name='api_me'),
]

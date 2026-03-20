from django.urls import path

from apps.clientes.views import LoginView, MeView, RegisterView, TokenRefreshViewCustom

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshViewCustom.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
]

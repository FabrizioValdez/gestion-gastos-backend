import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestRegisterView:
    def test_registro_exitoso(self, api_client):
        url = reverse("registro")
        data = {
            "nombre": "Juan Perez",
            "correo": "juan@test.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "cliente" in response.data
        assert "tokens" in response.data
        assert response.data["tokens"]["access"] is not None

    def test_registro_correo_existente(self, api_client, cliente):
        url = reverse("registro")
        data = {
            "nombre": "Otro Usuario",
            "correo": cliente.correo,
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "correo" in response.data

    def test_registro_contrasenas_no_coinciden(self, api_client):
        url = reverse("registro")
        data = {
            "nombre": "Juan Perez",
            "correo": "juan@test.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registro_campos_faltantes(self, api_client):
        url = reverse("registro")
        data = {"nombre": "Juan Perez"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginView:
    def test_login_exitoso(self, api_client, cliente):
        url = reverse("login")
        data = {
            "correo": cliente.correo,
            "password": "TestPass123!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "cliente" in response.data
        assert "tokens" in response.data

    def test_login_credenciales_invalidas(self, api_client, cliente):
        url = reverse("login")
        data = {
            "correo": cliente.correo,
            "password": "WrongPassword!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_usuario_inactivo(self, api_client, cliente):
        cliente.is_active = False
        cliente.save()
        url = reverse("login")
        data = {
            "correo": cliente.correo,
            "password": "TestPass123!",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_campos_faltantes(self, api_client):
        url = reverse("login")
        data = {}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeView:
    def test_obtener_perfil_autenticado(self, auth_client, cliente):
        url = reverse("me")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["correo"] == cliente.correo
        assert response.data["nombre"] == cliente.nombre

    def test_obtener_perfil_sin_autenticacion(self, api_client):
        url = reverse("me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_actualizar_perfil(self, auth_client, cliente):
        url = reverse("me")
        data = {"nombre": "Nombre Actualizado"}
        response = auth_client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        cliente.refresh_from_db()
        assert cliente.nombre == "Nombre Actualizado"


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_token_valido(self, api_client, cliente):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(cliente)
        url = reverse("token_refresh")
        data = {"refresh": str(refresh)}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_token_invalido(self, api_client):
        url = reverse("token_refresh")
        data = {"refresh": "token_invalido"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

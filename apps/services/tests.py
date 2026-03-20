from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check(self, api_client):
        url = reverse("health_check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"


@pytest.mark.django_db
class TestTipoServicioViewSet:
    def test_listar_tipos_servicio(self, auth_client, tipo_servicio_luz):
        url = reverse("tipos-servicio-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_listar_sin_autenticacion(self, api_client):
        url = reverse("tipos-servicio-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCatalogoServicioViewSet:
    def test_listar_catalogo(self, auth_client, catalogo_servicio):
        url = reverse("catalogo-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filtrar_por_tipo(self, auth_client, catalogo_servicio, tipo_servicio_luz):
        url = reverse("catalogo-list")
        response = auth_client.get(url, {"tipo_servicio": tipo_servicio_luz.id})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestServicioUsuarioViewSet:
    def test_crear_servicio_con_catalogo(
        self, auth_client, tipo_servicio_luz, catalogo_servicio
    ):
        url = reverse("servicios-list")
        data = {
            "tipo_servicio": tipo_servicio_luz.id,
            "catalogo_servicio": catalogo_servicio.id,
            "monto_mensual": "350.50",
            "dia_vencimiento": 20,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data["monto_mensual"]) == Decimal("350.50")

    def test_crear_servicio_sin_catalogo(self, auth_client, tipo_servicio_agua):
        url = reverse("servicios-list")
        data = {
            "tipo_servicio": tipo_servicio_agua.id,
            "nombre_servicio": "Agua Potable Municipal",
            "monto_mensual": "200.00",
            "dia_vencimiento": 10,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_error_ambos_campos_catalogo(
        self, auth_client, tipo_servicio_luz, catalogo_servicio
    ):
        url = reverse("servicios-list")
        data = {
            "tipo_servicio": tipo_servicio_luz.id,
            "catalogo_servicio": catalogo_servicio.id,
            "nombre_servicio": "Nombre personalizado",
            "monto_mensual": "100.00",
            "dia_vencimiento": 1,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_error_sin_catalogo_ni_nombre(self, auth_client, tipo_servicio_luz):
        url = reverse("servicios-list")
        data = {
            "tipo_servicio": tipo_servicio_luz.id,
            "monto_mensual": "100.00",
            "dia_vencimiento": 1,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_listar_servicios_propios(self, auth_client, servicio_usuario, cliente):
        url = reverse("servicios-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_eliminar_servicio_soft_delete(self, auth_client, servicio_usuario):
        url = reverse("servicios-detail", kwargs={"pk": servicio_usuario.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        servicio_usuario.refresh_from_db()
        assert servicio_usuario.activo is False

    def test_resumen_gastos(self, auth_client, servicio_usuario):
        url = reverse("servicios-resumen")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_mensual" in response.data
        assert "servicios_activos" in response.data

    def test_gastos_por_tipo(self, auth_client, servicio_usuario):
        url = reverse("servicios-por-tipo")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_dia_vencimiento_invalido(
        self, auth_client, tipo_servicio_luz, catalogo_servicio
    ):
        url = reverse("servicios-list")
        data = {
            "tipo_servicio": tipo_servicio_luz.id,
            "catalogo_servicio": catalogo_servicio.id,
            "monto_mensual": "100.00",
            "dia_vencimiento": 32,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestHistorialPagoViewSet:
    def test_crear_pago_pendiente(self, auth_client, servicio_usuario):
        url = reverse("pagos-list")
        data = {
            "servicio_usuario": servicio_usuario.id,
            "monto_pagado": "500.00",
            "fecha_vencimiento_cubierta": "2026-04-15",
            "estado": "pendiente",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["estado"] == "pendiente"

    def test_crear_pago_pagado_autofecha(self, auth_client, servicio_usuario):
        url = reverse("pagos-list")
        data = {
            "servicio_usuario": servicio_usuario.id,
            "monto_pagado": "500.00",
            "fecha_vencimiento_cubierta": "2026-03-15",
            "estado": "pagado",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["estado"] == "pagado"
        assert response.data["fecha_pago"] is not None

    def test_listar_pagos_usuario(self, auth_client, historial_pago):
        url = reverse("pagos-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_filtrar_pagos_por_estado(self, auth_client, historial_pago):
        url = reverse("pagos-list")
        response = auth_client.get(url, {"estado": "pagado"})
        assert response.status_code == status.HTTP_200_OK

    def test_pagos_por_servicio(self, auth_client, historial_pago, servicio_usuario):
        url = reverse("pagos-por-servicio", kwargs={"servicio_id": servicio_usuario.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPagarDeuda:
    def test_pagar_deuda_exito(self, auth_client, servicio_usuario):
        url = reverse("servicios-pagar-deuda", kwargs={"pk": servicio_usuario.id})
        data = {"fecha_pago": "2026-03-10", "monto_pagado": "500.00"}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "mensaje" in response.data

    def test_pagar_deuda_sin_fecha(self, auth_client, servicio_usuario):
        url = reverse("servicios-pagar-deuda", kwargs={"pk": servicio_usuario.id})
        data = {}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pagar_deuda_fecha_invalida(self, auth_client, servicio_usuario):
        url = reverse("servicios-pagar-deuda", kwargs={"pk": servicio_usuario.id})
        data = {"fecha_pago": "fecha-invalida"}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestNotificacionViewSet:
    def test_listar_notificaciones(self, auth_client, notificacion):
        url = reverse("notificaciones-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_notificaciones_pendientes(self, auth_client, notificacion):
        url = reverse("notificaciones-pendientes")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_marcar_como_leida(self, auth_client, notificacion):
        url = reverse("notificaciones-marcar-leida", kwargs={"pk": notificacion.id})
        response = auth_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        notificacion.refresh_from_db()
        assert notificacion.leida is True


@pytest.mark.django_db
class TestAyudaViewSet:
    def test_listar_ayuda(self, auth_client, ayuda_faq):
        url = reverse("ayuda-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filtrar_por_categoria(self, auth_client, ayuda_faq):
        url = reverse("ayuda-list")
        response = auth_client.get(url, {"categoria": "pagos"})
        assert response.status_code == status.HTTP_200_OK

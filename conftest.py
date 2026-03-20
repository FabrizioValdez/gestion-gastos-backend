import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker(["es_MX"])

from apps.clientes.models import Cliente
from apps.services.models import (
    Tipo_servicio,
    Catalogo_servicio,
    Servicio_usuario,
    Historial_pago,
    Notificacion,
    Ayuda,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def cliente(db):
    return Cliente.objects.create_user(
        correo=fake.unique.email(),
        nombre=fake.name(),
        password="TestPass123!"
    )


@pytest.fixture
def cliente_factory(db):
    class _Factory(DjangoModelFactory):
        class Meta:
            model = Cliente

        correo = fake.email
        nombre = fake.name()
        is_active = True

        @classmethod
        def _create(cls, model_class, *args, **kwargs):
            password = kwargs.pop("password", "TestPass123!")
            instance = super()._create(model_class, *args, **kwargs)
            instance.set_password(password)
            instance.save()
            return instance

    return _Factory


@pytest.fixture
def auth_client(cliente):
    client = APIClient()
    refresh = RefreshToken.for_user(cliente)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def tipo_servicio_luz(db):
    return Tipo_servicio.objects.create(nombre="Luz")


@pytest.fixture
def tipo_servicio_agua(db):
    return Tipo_servicio.objects.create(nombre="Agua")


@pytest.fixture
def catalogo_servicio(db, tipo_servicio_luz):
    return Catalogo_servicio.objects.create(
        tipo_servicio=tipo_servicio_luz,
        nombre="CFE Básico"
    )


@pytest.fixture
def servicio_usuario(db, cliente, tipo_servicio_luz, catalogo_servicio):
    return Servicio_usuario.objects.create(
        cliente=cliente,
        tipo_servicio=tipo_servicio_luz,
        catalogo_servicio=catalogo_servicio,
        monto_mensual=500.00,
        dia_vencimiento=15
    )


@pytest.fixture
def historial_pago(db, servicio_usuario):
    return Historial_pago.objects.create(
        servicio_usuario=servicio_usuario,
        monto_pagado=500.00,
        fecha_vencimiento_cubierta="2026-03-15",
        estado="pagado"
    )


@pytest.fixture
def notificacion(db, cliente, servicio_usuario):
    return Notificacion.objects.create(
        cliente=cliente,
        servicio_usuario=servicio_usuario,
        tipo="vencimiento_proximo",
        mensaje="Tu servicio vence pronto"
    )


@pytest.fixture
def ayuda_faq(db):
    return Ayuda.objects.create(
        pregunta="¿Cómo pago mi servicio?",
        respuesta="Puedes pagar desde la app.",
        categoria="pagos",
        orden=1
    )

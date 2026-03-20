from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.services.views import (
    AyudaViewSet,
    Catalogo_servicioViewSet,
    HealthCheckView,
    Historial_pagoViewSet,
    NotificacionViewSet,
    Servicio_usuarioViewSet,
    Tipo_servicioViewSet,
)

router = DefaultRouter()
router.register(r"tipos-servicio", Tipo_servicioViewSet, basename="tipos-servicio")
router.register(r"catalogo", Catalogo_servicioViewSet, basename="catalogo")
router.register(r"servicios", Servicio_usuarioViewSet, basename="servicios")
router.register(r"pagos", Historial_pagoViewSet, basename="pagos")
router.register(r"notificaciones", NotificacionViewSet, basename="notificaciones")
router.register(r"ayuda", AyudaViewSet, basename="ayuda")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path("", include(router.urls)),
]

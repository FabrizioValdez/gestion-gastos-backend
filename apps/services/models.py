from django.core.exceptions import ValidationError
from django.db import models

from apps.clientes.models import Cliente


def validate_servicio_choice(instance):
    """
    Valida que solo uno de catalogo_servicio o nombre_servicio esté presente.
    CHECK CONSTRAINT a nivel de aplicación.
    """
    if instance.catalogo_servicio_id and instance.nombre_servicio:
        raise ValidationError(
            "Solo puede especificarse catalogo_servicio o nombre_servicio, no ambos."
        )
    if not instance.catalogo_servicio_id and not instance.nombre_servicio:
        raise ValidationError(
            "Debe especificarse al menos uno: catalogo_servicio o nombre_servicio."
        )


class Tipo_servicio(models.Model):
    """Tipos de servicios disponibles (Luz, Agua, Internet, etc.)"""

    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "tipo_servicio"
        verbose_name = "Tipo de Servicio"
        verbose_name_plural = "Tipos de Servicios"

    def __str__(self):
        return self.nombre


class Catalogo_servicio(models.Model):
    """Catálogo de servicios predefinidos por tipo."""

    tipo_servicio = models.ForeignKey(
        Tipo_servicio, on_delete=models.CASCADE, related_name="catalogos"
    )
    nombre = models.CharField(max_length=150)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "catalogo_servicio"
        verbose_name = "Catálogo de Servicio"
        verbose_name_plural = "Catálogos de Servicios"
        unique_together = ["tipo_servicio", "nombre"]

    def __str__(self):
        return f"{self.tipo_servicio.nombre} - {self.nombre}"


class Servicio_usuario(models.Model):
    """Servicio asociado a un usuario específico."""

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="servicios"
    )
    tipo_servicio = models.ForeignKey(
        Tipo_servicio, on_delete=models.CASCADE, related_name="servicios_usuario"
    )
    catalogo_servicio = models.ForeignKey(
        Catalogo_servicio,
        on_delete=models.CASCADE,
        related_name="servicios_usuario",
        blank=True,
        null=True,
    )
    nombre_servicio = models.CharField(max_length=150, blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    dia_vencimiento = models.PositiveSmallIntegerField(
        default=1, help_text="Día del mes de vencimiento (1-31)"
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "servicio_usuario"
        verbose_name = "Servicio de Usuario"
        verbose_name_plural = "Servicios de Usuario"

    def clean(self):
        validate_servicio_choice(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.nombre_servicio or self.catalogo_servicio.nombre
        return f"{self.cliente.correo} - {nombre}"


class Historial_pago(models.Model):
    """Historial de pagos de un servicio."""

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
    ]

    servicio_usuario = models.ForeignKey(
        Servicio_usuario, on_delete=models.CASCADE, related_name="historial_pagos"
    )
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    fecha_vencimiento_cubierta = models.DateField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_pago"
        verbose_name = "Historial de Pago"
        verbose_name_plural = "Historial de Pagos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.servicio_usuario} - {self.estado}"


class Notificacion(models.Model):
    """Notificaciones para el usuario."""

    TIPO_CHOICES = [
        ("vencimiento_proximo", "Vencimiento Próximo"),
        ("pago_pendiente", "Pago Pendiente"),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="notificaciones"
    )
    servicio_usuario = models.ForeignKey(
        Servicio_usuario,
        on_delete=models.CASCADE,
        related_name="notificaciones",
        blank=True,
        null=True,
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificacion"
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.cliente.correo} - {self.tipo}"


class Ayuda(models.Model):
    """Preguntas frecuentes y ayuda para pagos."""

    pregunta = models.CharField(max_length=255)
    respuesta = models.TextField()
    categoria = models.CharField(
        max_length=50,
        choices=[
            ("pagos", "Pagos"),
            ("servicios", "Servicios"),
            ("cuenta", "Cuenta"),
            ("general", "General"),
        ],
    )
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "ayuda"
        verbose_name = "Ayuda"
        verbose_name_plural = "Ayuda"
        ordering = ["orden", "pregunta"]

    def __str__(self):
        return self.pregunta

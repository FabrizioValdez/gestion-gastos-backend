import calendar

from celery import shared_task
from django.utils import timezone

from .models import Notificacion, Servicio_usuario


@shared_task
def generar_notificaciones_vencimiento():
    """Genera notificaciones 3 días antes del día de vencimiento de cada servicio."""
    fecha_hoy = timezone.now().date()
    anio_actual = fecha_hoy.year
    mes_actual = fecha_hoy.month
    dia_actual = fecha_hoy.day
    ultimo_dia_mes = calendar.monthrange(anio_actual, mes_actual)[1]

    servicios = Servicio_usuario.objects.filter(activo=True)

    notificaciones_creadas = 0

    for servicio in servicios:
        dia_venc = servicio.dia_vencimiento
        dia_ajustado = min(dia_venc, ultimo_dia_mes)

        dias_restantes = dia_ajustado - dia_actual

        if dias_restantes == 3:
            ya_existe = Notificacion.objects.filter(
                servicio_usuario=servicio,
                tipo="vencimiento_proximo",
                created_at__date=fecha_hoy,
            ).exists()

            if not ya_existe:
                nombre_servicio = (
                    servicio.nombre_servicio or servicio.catalogo_servicio.nombre
                )

                Notificacion.objects.create(
                    cliente=servicio.cliente,
                    servicio_usuario=servicio,
                    tipo="vencimiento_proximo",
                    mensaje=f'El servicio "{nombre_servicio}" vence en 3 días (día {dia_venc} de este mes)',
                )
                notificaciones_creadas += 1

    return f"Se crearon {notificaciones_creadas} notificaciones"


@shared_task
def generar_notificaciones_pago_pendiente():
    """Genera notificaciones para pagos pendientes."""
    from .models import Historial_pago

    pagos_pendientes = Historial_pago.objects.filter(estado="pendiente")

    notificaciones_creadas = 0

    for pago in pagos_pendientes:
        ya_existe = Notificacion.objects.filter(
            servicio_usuario=pago.servicio_usuario,
            tipo="pago_pendiente",
            created_at__date=timezone.now().date(),
        ).exists()

        if not ya_existe:
            nombre_servicio = (
                pago.servicio_usuario.nombre_servicio
                or pago.servicio_usuario.catalogo_servicio.nombre
            )

            Notificacion.objects.create(
                cliente=pago.servicio_usuario.cliente,
                servicio_usuario=pago.servicio_usuario,
                tipo="pago_pendiente",
                mensaje=f'Tienes un pago pendiente de ${pago.monto_pagado} para "{nombre_servicio}"',
            )
            notificaciones_creadas += 1

    return f"Se crearon {notificaciones_creadas} notificaciones de pago pendiente"

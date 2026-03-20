from django.core.management.base import BaseCommand

from apps.services.models import Tipo_servicio


class Command(BaseCommand):
    help = 'Seed de los 8 tipos de servicio iniciales'

    TIPOS_SERVICIO = [
        'Luz',
        'Agua',
        'Internet',
        'Gas',
        'Línea móvil',
        'Suscripción',
        'Alquiler',
        'Otro',
    ]

    def handle(self, *args, **options):
        creados = 0
        existentes = 0

        for nombre in self.TIPOS_SERVICIO:
            tipo, created = Tipo_servicio.objects.get_or_create(
                nombre=nombre,
                defaults={'nombre': nombre}
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Creado: {tipo.nombre}')
                )
            else:
                existentes += 1
                self.stdout.write(
                    self.style.WARNING(f'Ya existe: {tipo.nombre}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeed completado. Creados: {creados}, Existentes: {existentes}'
            )
        )

from django.core.management.base import BaseCommand
from django.utils import timezone
from workshops.models import Workshop, DianResolution


class Command(BaseCommand):
    help = 'Crear resolución DIAN de prueba para un taller'

    def add_arguments(self, parser):
        parser.add_argument('workshop_id', type=str, help='ID del taller')
        parser.add_argument('--resolution', type=str, default='18760000001', help='Número de resolución')
        parser.add_argument('--prefix', type=str, default='EPOS', help='Prefijo de numeración')
        parser.add_argument('--from-number', type=int, default=1, help='Número inicial')
        parser.add_argument('--to-number', type=int, default=1000, help='Número final')

    def handle(self, *args, **options):
        try:
            workshop = Workshop.objects.get(id=options['workshop_id'])
        except Workshop.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Taller con ID {options["workshop_id"]} no encontrado'))
            return

        # Crear resolución DIAN
        resolution, created = DianResolution.objects.get_or_create(
            workshop=workshop,
            resolution_number=options['resolution'],
            defaults={
                'resolution_date': timezone.now().date(),
                'expires_date': timezone.now().date() + timezone.timedelta(days=365*2),
                'prefix': options['prefix'],
                'from_number': options['from_number'],
                'to_number': options['to_number'],
                'document_type': 'invoice',
                'notes': 'Resolución de prueba creada automáticamente'
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Resolución DIAN creada exitosamente:\n'
                    f'  Número: {resolution.resolution_number}\n'
                    f'  Prefijo: {resolution.prefix}\n'
                    f'  Rango: {resolution.from_number} - {resolution.to_number}\n'
                    f'  Vence: {resolution.expires_date}'
                )
            )
        else:
            self.stdout.write(self.style.WARNING('La resolución DIAN ya existe'))
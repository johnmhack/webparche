from django.core.management.base import BaseCommand
from workshops.models import Workshop, DianConfiguration


class Command(BaseCommand):
    help = 'Crear configuración DIAN para un taller'

    def add_arguments(self, parser):
        parser.add_argument('workshop_id', type=str, help='ID del taller')
        parser.add_argument('--environment', type=str, choices=['test', 'production'], default='test', help='Ambiente DIAN')
        parser.add_argument('--software-id', type=str, help='ID del software')
        parser.add_argument('--software-pin', type=str, help='PIN del software')

    def handle(self, *args, **options):
        try:
            workshop = Workshop.objects.get(id=options['workshop_id'])
        except Workshop.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Taller con ID {options["workshop_id"]} no encontrado'))
            return

        # Crear configuración DIAN
        config, created = DianConfiguration.objects.get_or_create(
            workshop=workshop,
            defaults={
                'environment': options['environment'],
                'test_username': 'test@example.com',
                'test_password': 'CHANGE_THIS_PASSWORD_IN_PRODUCTION',
                'signature_provider': 'camerfirma',
                'enable_schematron_validation': True,
                'enable_xml_validation': True,
                'enable_dian_validation': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Configuración DIAN creada exitosamente:\n'
                    f'  Ambiente: {config.environment}\n'
                    f'  Software ID: {config.software_id}\n'
                    f'  Proveedor de firma: {config.signature_provider}\n'
                    f'  Validaciones activas: Schematron={config.enable_schematron_validation}, '
                    f'XML={config.enable_xml_validation}, DIAN={config.enable_dian_validation}'
                )
            )
        else:
            self.stdout.write(self.style.WARNING('La configuración DIAN ya existe'))
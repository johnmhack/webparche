from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from workshops.models import Workshop

class Command(BaseCommand):
    help = 'Crear usuario de prueba para testing'

    def handle(self, *args, **options):
        if User.objects.filter(email='test@example.com').exists():
            self.stdout.write('Usuario de prueba ya existe')
            return

        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='test123',
            first_name='Usuario',
            last_name='Prueba'
        )

        workshop = Workshop.objects.create(
            name='Taller Demo',
            owner=user,
            email='test@example.com',
            phone='+573001234567'
        )

        self.stdout.write(
            self.style.SUCCESS('Usuario de prueba creado exitosamente!')
        )
        self.stdout.write(f'Email: test@example.com')
        self.stdout.write(f'Password: test123')
        self.stdout.write(f'Taller: Taller Demo')
import os
import django

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_api.settings')
django.setup()

from core.models import Negocio

# Crea el negocio 'Servimotos' si no existe
negocio, creado = Negocio.objects.get_or_create(
    nombre='Servimotos',
    defaults={
        'tipo': 'taller',
        'direccion': 'Calle 123 #45-67',
        'telefono': '3001234567',
        'correo': 'servimotos@email.com',
        'nit': '123456789-0',
    }
)

if creado:
    print('Negocio "Servimotos" creado exitosamente.')
else:
    print('El negocio "Servimotos" ya existe.') 
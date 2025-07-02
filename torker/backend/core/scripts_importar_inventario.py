import os
import django
import csv

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_api.settings')
django.setup()

from core.models import Negocio, Inventario

# Nombre del archivo CSV
CSV_FILENAME = 'inventario_servimotos.csv'

# Busca el negocio 'Servimotos'
try:
    negocio = Negocio.objects.get(nombre='Servimotos')
except Negocio.DoesNotExist:
    print('El negocio "Servimotos" no existe. Crea el negocio antes de importar el inventario.')
    exit(1)

# Abre y lee el archivo CSV
with open(CSV_FILENAME, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    count = 0
    for row in reader:
        Inventario.objects.create(
            negocio=negocio,
            nombre=row.get('Nombre del repuesto', '').strip(),
            descripcion=row.get('descripción', '').strip(),
            marca=row.get('marca', '').strip(),
            tamano=row.get('tamaño', '').strip(),
            categoria=row.get('categoria', '').strip(),
            cantidad=int(row.get('cantidad', 0) or 0),
            precio=float(row.get('precio estimado', 0) or 0),
            codigo=row.get('codigo', '').strip(),
            ubicacion=row.get('ubicación', '').strip(),
        )
        count += 1
    print(f'Se importaron {count} productos al inventario de Servimotos.') 
#!/usr/bin/env python
"""
Script para configurar el taller con datos reales de MERCY MELENDEZ AHUANARI
Ejecutar después de hacer las migraciones iniciales
"""

import os
import sys
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from workshops.models import Workshop, DianResolution, DianConfiguration

def configure_workshop():
    """Configura el taller con datos reales de producción"""

    print("Configurando taller SERVIMOTOS CENTRO...")

    # Buscar el taller existente (asumiendo que ya existe uno)
    try:
        workshop = Workshop.objects.first()
        if not workshop:
            print("❌ No se encontró ningún taller. Crea uno primero.")
            return False

        print(f"Configurando taller: {workshop.name}")

        # Actualizar información fiscal real
        workshop.nit = "211144934"
        workshop.legal_name = "MERCY MELENDEZ AHUANARI"
        workshop.name = "SERVIMOTOS CENTRO"
        workshop.address = "CR 5 #7-17"
        workshop.city = "VILLETA"
        workshop.department = "CUNDINAMARCA"
        workshop.phone = "3192589035"
        workshop.email = "123mercym@gmail.com"
        workshop.save()

        print("Informacion del taller actualizada")

        # Configurar resolución DIAN
        dian_resolution, created = DianResolution.objects.get_or_create(
            workshop=workshop,
            resolution_number="18764100117389",
            defaults={
                'resolution_date': date(2025, 10, 15),
                'expires_date': date(2026, 10, 15),
                'prefix': 'SMFE',
                'from_number': 1,
                'to_number': 2000,
                'document_type': 'invoice',
                'is_active': True,
                'notes': 'Resolucion DIAN para facturacion electronica'
            }
        )

        if created:
            print("Resolucion DIAN creada")
        else:
            print("Resolucion DIAN ya existia")

        # Configurar DIAN (ambiente de pruebas por ahora)
        dian_config, created = DianConfiguration.objects.get_or_create(
            workshop=workshop,
            defaults={
                'environment': 'test',  # Cambiar a 'production' cuando tengas credenciales
                'test_webservice_url': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
                'production_webservice_url': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc',
                'software_id': '710d99d0-6d49-4e18-bb70-196d1b17785f',
                'software_pin': '12345',
                'software_security_code': 'cfb3e564f5660585cd0ba4f23090242a73d3f4f298110d2eaa3976ce03cba4c6f980f6fa9a41b68a072d8e7decbd53a8',
                'default_currency': 'COP',
                'default_country': 'CO',
                'default_language': 'es',
                'enable_schematron_validation': True,
                'enable_xml_validation': True,
                'enable_dian_validation': True,
            }
        )

        if created:
            print("Configuracion DIAN creada")
        else:
            print("Configuracion DIAN ya existia")

        # Mostrar resumen de configuración
        print("\n" + "="*50)
        print("CONFIGURACION COMPLETADA")
        print("="*50)
        print(f"Taller: {workshop.name}")
        print(f"Propietario: {workshop.legal_name}")
        print(f"NIT: {workshop.nit}")
        print(f"Direccion: {workshop.address}, {workshop.city}, {workshop.department}")
        print(f"Telefono: {workshop.phone}")
        print(f"Email: {workshop.email}")
        print()
        print("Resolucion DIAN:")
        print(f"   Numero: {dian_resolution.resolution_number}")
        print(f"   Prefijo: {dian_resolution.prefix}")
        print(f"   Rango: {dian_resolution.from_number}-{dian_resolution.to_number}")
        print(f"   Vigencia: {dian_resolution.resolution_date} - {dian_resolution.expires_date}")
        print()
        print("Ambiente DIAN: PRUEBAS (cambiar a PRODUCCION cuando tengas credenciales)")
        print("="*50)

        return True

    except Exception as e:
        print(f"Error configurando taller: {str(e)}")
        return False

if __name__ == '__main__':
    success = configure_workshop()
    if success:
        print("\nConfiguracion exitosa. El sistema esta listo para generar facturas con datos reales.")
        print("Recuerda cambiar el ambiente DIAN a 'production' cuando tengas las credenciales reales.")
    else:
        print("\nError en la configuracion.")
        sys.exit(1)
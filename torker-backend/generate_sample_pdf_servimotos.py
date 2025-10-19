#!/usr/bin/env python
"""
Script para generar PDF de muestra con datos de Servimotos
Taller de Mercy Meléndez
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from workshops.models import (
    User, Workshop, Customer, Vehicle, Mechanic,
    DianResolution, ElectronicInvoice, ElectronicInvoiceDetail
)
from workshops.pdf_generator import generate_electronic_invoice_pdf
from workshops.qr_generator import generate_and_save_qr_code


def create_sample_data():
    """Crear datos de muestra de Servimotos"""
    
    # Limpiar datos anteriores de Servimotos
    try:
        old_workshop = Workshop.objects.filter(name='Servimotos').first()
        if old_workshop:
            old_workshop.delete()
            print("   OK Datos anteriores eliminados")
    except:
        pass
    
    # Crear usuario Mercy Meléndez
    user, _ = User.objects.get_or_create(
        email='mercy@servimotos.com',
        defaults={
            'username': 'mercy@servimotos.com',
            'first_name': 'Mercy',
            'last_name': 'Meléndez',
            'phone': '3001234567'
        }
    )
    user.set_password('servimotos123')
    user.save()
    
    # Crear taller Servimotos
    workshop, _ = Workshop.objects.get_or_create(
        owner=user,
        defaults={
            'name': 'Servimotos',
            'nit': '900123456',
            'legal_name': 'Servimotos S.A.S.',
            'address': 'Calle 45 #23-67',
            'city': 'Bogotá',
            'department': 'Cundinamarca',
            'phone': '6012345678',
            'email': 'contacto@servimotos.com',
            'tax_regime': 'comun',
            'organization_type': '1',
            'tax_responsibilities': ['O-08', 'O-09', 'O-16', 'O-22'],
            'default_tax_rate': Decimal('19.00')
        }
    )
    
    # Crear mecánico
    mechanic, _ = Mechanic.objects.get_or_create(
        workshop=workshop,
        document_number='123456789',
        defaults={
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'document_type': 'cc',
            'specialization': 'motorcycle',
            'experience_level': 'senior',
            'hourly_rate': Decimal('25000.00')
        }
    )
    
    # Crear cliente
    customer, _ = Customer.objects.get_or_create(
        workshop=workshop,
        document_number='987654321',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'document_type': 'cc',
            'phone': '3109876543',
            'email': 'juan.perez@email.com',
            'address': 'Carrera 15 #30-45',
            'city': 'Bogotá',
            'department': 'Cundinamarca'
        }
    )
    
    # Crear vehículo
    vehicle, _ = Vehicle.objects.get_or_create(
        workshop=workshop,
        customer=customer,
        license_plate='ABC123',
        defaults={
            'vehicle_type': 'motorcycle',
            'brand': 'Yamaha',
            'model': 'FZ16',
            'year': 2020,
            'color': 'Negro',
            'mileage': 15000
        }
    )
    
    # Crear resolución DIAN
    resolution, _ = DianResolution.objects.get_or_create(
        workshop=workshop,
        resolution_number='18764000000001',
        defaults={
            'resolution_date': timezone.now().date(),
            'expires_date': timezone.now().date().replace(year=timezone.now().year + 1),
            'prefix': 'SMFE',
            'from_number': 1,
            'to_number': 5000,
            'current_number': 0,
            'document_type': 'invoice',
            'technical_key': 'clave-tecnica-dian-12345'
        }
    )
    
    # Crear factura electrónica
    invoice = ElectronicInvoice.objects.create(
        workshop=workshop,
        customer=customer,
        dian_resolution=resolution,
        workshop_nit=workshop.nit,
        workshop_name=workshop.legal_name,
        workshop_address=workshop.address,
        workshop_city=workshop.city,
        workshop_department=workshop.department,
        workshop_phone=workshop.phone,
        workshop_email=workshop.email,
        customer_name=customer.full_name,
        customer_document_type=customer.document_type,
        customer_document=customer.document_number,
        customer_address=customer.address,
        customer_city=customer.city,
        customer_department=customer.department,
        customer_phone=customer.phone,
        customer_email=customer.email,
        subtotal=Decimal('150000.00'),
        discount=Decimal('0.00'),
        tax_rate=Decimal('19.00'),
        tax_amount=Decimal('28500.00'),
        total=Decimal('178500.00'),
        payment_method='cash'
    )
    
    # Crear detalles de factura
    ElectronicInvoiceDetail.objects.create(
        electronic_invoice=invoice,
        description='Cambio de aceite sintético',
        part_number='ACE001',
        unspsc_code='81111500',
        quantity=Decimal('1.00'),
        unit_code='E48',
        unit_price=Decimal('80000.00'),
        discount=Decimal('0.00'),
        tax_rate=Decimal('19.00')
    )
    
    ElectronicInvoiceDetail.objects.create(
        electronic_invoice=invoice,
        description='Filtro de aceite original',
        part_number='FIL002',
        unspsc_code='25170000',
        quantity=Decimal('1.00'),
        unit_code='NIU',
        unit_price=Decimal('35000.00'),
        discount=Decimal('0.00'),
        tax_rate=Decimal('19.00')
    )
    
    ElectronicInvoiceDetail.objects.create(
        electronic_invoice=invoice,
        description='Revisión general de frenos',
        part_number='SRV003',
        unspsc_code='81111500',
        quantity=Decimal('1.00'),
        unit_code='E48',
        unit_price=Decimal('35000.00'),
        discount=Decimal('0.00'),
        tax_rate=Decimal('19.00')
    )
    
    return invoice


def main():
    """Generar PDF de muestra"""
    print("="*80)
    print("GENERADOR DE PDF DE MUESTRA - SERVIMOTOS")
    print("="*80)
    
    try:
        # Crear datos de muestra
        print("\n1. Creando datos de muestra...")
        invoice = create_sample_data()
        print(f"   OK Factura creada: {invoice.invoice_number}")
        print(f"   OK CUDE: {invoice.cude[:20]}...")
        
        # Generar QR code
        print("\n2. Generando código QR...")
        try:
            qr_url = generate_and_save_qr_code(invoice)
            print(f"   OK QR generado: {qr_url}")
        except Exception as e:
            print(f"   ⚠ Error generando QR (continuando sin QR): {str(e)}")
        
        # Generar PDF
        print("\n3. Generando PDF...")
        pdf_data = generate_electronic_invoice_pdf(invoice.id)
        
        # Guardar PDF
        output_file = 'factura_muestra_servimotos.pdf'
        with open(output_file, 'wb') as f:
            f.write(pdf_data)
        
        print(f"   OK PDF generado exitosamente")
        print(f"   OK Archivo: {output_file}")
        print(f"   OK Tamaño: {len(pdf_data)} bytes")
        
        print("\n" + "="*80)
        print("RESUMEN DE LA FACTURA")
        print("="*80)
        print(f"Taller: {invoice.workshop_name}")
        print(f"NIT: {invoice.workshop_nit}")
        print(f"Cliente: {invoice.customer_name}")
        print(f"Documento: {invoice.customer_document}")
        print(f"Número Factura: {invoice.invoice_number}")
        print(f"Subtotal: ${invoice.subtotal:,.0f}")
        print(f"IVA (19%): ${invoice.tax_amount:,.0f}")
        print(f"Total: ${invoice.total:,.0f}")
        print(f"Items: {invoice.details.count()}")
        print("="*80)
        
        print(f"\n✅ PDF generado exitosamente: {output_file}")
        print("Abre el archivo para ver la estructura del PDF\n")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
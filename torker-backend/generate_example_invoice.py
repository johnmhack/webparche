#!/usr/bin/env python
"""
Script para generar una factura electrónica de ejemplo con datos genéricos
para mostrar a SERVIMOTOS y al contador
"""

import os
import sys
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from workshops.models import (
    Workshop, Customer, Vehicle, Service, SparePart,
    WorkOrder, WorkOrderItem, ElectronicInvoice, ElectronicInvoiceDetail,
    DianResolution
)

def create_example_data():
    """Crear datos de ejemplo para la factura"""

    print("Creando datos de ejemplo...")

    # Obtener el taller configurado
    workshop = Workshop.objects.first()
    if not workshop:
        print("Error: No hay taller configurado. Ejecuta configure_workshop.py primero.")
        return None

    # Crear cliente de ejemplo
    customer, created = Customer.objects.get_or_create(
        workshop=workshop,
        document_type='cc',
        document_number='12345678',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Pérez González',
            'phone': '3001234567',
            'email': 'juan.perez@email.com',
            'address': 'Calle 123 # 45-67',
            'city': 'Bogotá',
            'department': 'Cundinamarca'
        }
    )

    # Crear vehículo de ejemplo
    vehicle, created = Vehicle.objects.get_or_create(
        customer=customer,
        workshop=workshop,
        license_plate='ABC123',
        defaults={
            'vehicle_type': 'motorcycle',
            'brand': 'Honda',
            'model': 'CBR 600',
            'year': 2020,
            'color': 'Rojo',
            'mileage': 15000
        }
    )

    # Crear servicios de ejemplo
    services_data = [
        {
            'name': 'Cambio de aceite y filtro',
            'description': 'Cambio completo de aceite de motor y filtro',
            'estimated_hours': 1.5,
            'base_price': 45000,
            'hourly_rate': 0,
            'category': 'maintenance',
            'service_code': 'SVC-OIL-CHANGE'
        },
        {
            'name': 'Revisión de frenos',
            'description': 'Inspección completa del sistema de frenos',
            'estimated_hours': 2.0,
            'base_price': 35000,
            'hourly_rate': 0,
            'category': 'diagnostic',
            'service_code': 'SVC-BRAKE-CHECK'
        },
        {
            'name': 'Alineación y balanceo',
            'description': 'Alineación de ruedas delanteras y balanceo',
            'estimated_hours': 1.0,
            'base_price': 25000,
            'hourly_rate': 0,
            'category': 'maintenance',
            'service_code': 'SVC-ALIGN-BALANCE'
        }
    ]

    services = []
    for service_data in services_data:
        service, created = Service.objects.get_or_create(
            workshop=workshop,
            service_code=service_data['service_code'],
            defaults=service_data
        )
        services.append(service)

    # Crear repuestos de ejemplo
    parts_data = [
        {
            'name': 'Aceite de motor 20W50',
            'part_number': 'OIL-20W50-1L',
            'internal_code': 'PART-OIL-001',
            'category': 'lubricantes',
            'stock_quantity': 50,
            'unit_cost': 25000,
            'sale_price': 35000,
            'brand': 'Castrol'
        },
        {
            'name': 'Filtro de aceite Honda CBR',
            'part_number': 'FLT-OIL-HCBR',
            'internal_code': 'PART-FLT-001',
            'category': 'filtros',
            'stock_quantity': 25,
            'unit_cost': 15000,
            'sale_price': 22000,
            'brand': 'Honda'
        }
    ]

    parts = []
    for part_data in parts_data:
        part, created = SparePart.objects.get_or_create(
            workshop=workshop,
            internal_code=part_data['internal_code'],
            defaults=part_data
        )
        parts.append(part)

    return {
        'workshop': workshop,
        'customer': customer,
        'vehicle': vehicle,
        'services': services,
        'parts': parts
    }

def create_example_work_order(data):
    """Crear orden de trabajo de ejemplo"""

    print("Creando orden de trabajo de ejemplo...")

    # Crear orden de trabajo con número único
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # Generar número de orden único
    while True:
        order_number = f"OT-{unique_id}-{uuid.uuid4().hex[:4].upper()}"
        if not WorkOrder.objects.filter(order_number=order_number).exists():
            break

    work_order = WorkOrder.objects.create(
        workshop=data['workshop'],
        customer=data['customer'],
        vehicle=data['vehicle'],
        order_number=order_number,
        title=f'Mantenimiento preventivo motocicleta Honda CBR 600 - {unique_id}',
        description='Servicio de mantenimiento preventivo completo',
        priority='normal',
        status='completed'  # Para poder facturar
    )

    # Agregar servicios a la OT
    WorkOrderItem.objects.create(
        work_order=work_order,
        item_type='service',
        service=data['services'][0],  # Cambio de aceite
        description='Cambio de aceite y filtro de motor',
        service_quantity=1.5,  # 1.5 horas
        service_unit_price=30000,  # $30.000 por hora
        estimated_time_hours=1.5
    )

    WorkOrderItem.objects.create(
        work_order=work_order,
        item_type='service',
        service=data['services'][1],  # Revisión frenos
        description='Revisión completa del sistema de frenos',
        service_quantity=2.0,  # 2 horas
        service_unit_price=25000,  # $25.000 por hora
        estimated_time_hours=2.0
    )

    # Agregar repuestos a la OT
    WorkOrderItem.objects.create(
        work_order=work_order,
        item_type='part',
        part=data['parts'][0],  # Aceite
        description='Aceite de motor Castrol 20W50 - 1 litro',
        part_quantity=1,
        part_unit_price=35000,
        estimated_time_hours=0.5
    )

    WorkOrderItem.objects.create(
        work_order=work_order,
        item_type='part',
        part=data['parts'][1],  # Filtro
        description='Filtro de aceite original Honda CBR',
        part_quantity=1,
        part_unit_price=22000,
        estimated_time_hours=0.5
    )

    # Actualizar costos de la OT
    work_order.update_costs()

    return work_order

def create_example_invoice(work_order):
    """Crear factura electrónica de ejemplo"""

    print("Creando factura electrónica de ejemplo...")

    # Crear factura directamente usando el modelo (más simple para el script)
    try:
        # Verificar que el taller tenga resolución DIAN activa (preferir SMFE)
        try:
            # Primero intentar con SMFE
            dian_resolution = DianResolution.objects.filter(
                workshop=work_order.workshop,
                document_type='invoice',
                prefix='SMFE',
                is_active=True
            ).first()

            # Si no hay SMFE, usar cualquier resolución activa
            if not dian_resolution:
                dian_resolution = DianResolution.objects.filter(
                    workshop=work_order.workshop,
                    document_type='invoice',
                    is_active=True
                ).first()

            if not dian_resolution:
                raise DianResolution.DoesNotExist()
        except DianResolution.DoesNotExist:
            print("Error: No hay resolución DIAN activa para facturas electrónicas")
            print("Ejecuta el comando create_dian_resolution primero")
            return None

        # Crear factura electrónica directamente
        electronic_invoice = ElectronicInvoice.objects.create(
            workshop=work_order.workshop,
            customer=work_order.customer,
            work_order=work_order,
            dian_resolution=dian_resolution,
            payment_method='cash',
            # Información fiscal del taller
            workshop_nit=work_order.workshop.nit or '',
            workshop_name=work_order.workshop.legal_name or work_order.workshop.name,
            workshop_address=work_order.workshop.address,
            workshop_city=work_order.workshop.city or '',
            workshop_department=work_order.workshop.department or '',
            workshop_phone=work_order.workshop.phone or '',
            workshop_email=work_order.workshop.email or '',
            # Información del cliente
            customer_name=work_order.customer.full_name,
            customer_document_type=work_order.customer.document_type,
            customer_document=work_order.customer.document_number,
            customer_address=work_order.customer.full_address,
            customer_city=work_order.customer.city or '',
            customer_department=work_order.customer.department or '',
            customer_phone=work_order.customer.phone or '',
            customer_email=work_order.customer.email or '',
            # Configuración fiscal
            tax_rate=work_order.workshop.default_tax_rate,
        )

        # Crear detalles de factura electrónica desde los ítems de la orden de trabajo
        subtotal = 0
        for item in work_order.details.all():
            # Usar la descripción del ítem o generar una apropiada
            description = item.description
            if not description:
                if item.service:
                    description = f"Servicio: {item.service.name}"
                elif item.part:
                    description = f"Repuesto: {item.part.name}"
                else:
                    description = "Ítem de orden de trabajo"

            # Determinar código UNSPSC (simplificado)
            unspsc_code = ""
            if item.service:
                unspsc_code = "81111500"  # Servicios de reparación de vehículos de motor
            elif item.part:
                unspsc_code = "25170000"  # Partes de vehículos de motor

            electronic_invoice_detail = ElectronicInvoiceDetail.objects.create(
                electronic_invoice=electronic_invoice,
                part=None,  # No usar part por ahora para evitar problemas de tabla
                description=description,
                part_number=item.part.internal_code if item.part else "",
                unspsc_code=unspsc_code,
                brand_name=item.part.brand if item.part else "",
                model_name="",
                quantity=item.part_quantity if item.part_quantity > 0 else item.service_quantity,
                unit_code="NIU" if item.part else "E48",  # NIU para unidades, E48 para horas
                unit_price=item.part_unit_price if item.part_unit_price > 0 else item.service_unit_price,
                discount=0,  # Por ahora sin descuento
            )
            subtotal += electronic_invoice_detail.subtotal

        # Calcular totales
        tax_amount = subtotal * (electronic_invoice.tax_rate / 100) if electronic_invoice.tax_rate > 0 else 0
        total = subtotal + tax_amount

        # Actualizar factura electrónica
        electronic_invoice.subtotal = subtotal
        electronic_invoice.tax_amount = tax_amount
        electronic_invoice.total = total
        electronic_invoice.save()

        # Actualizar estadísticas del cliente
        work_order.customer.total_spent += total
        work_order.customer.total_visits += 1
        work_order.customer.last_visit = electronic_invoice.issue_date
        work_order.customer.save()

        # Cambiar estado de la OT a facturada
        work_order.change_status('invoiced', work_order.workshop.owner, f'Factura electrónica DIAN {electronic_invoice.invoice_number} creada')

        print(f"Factura creada exitosamente: {electronic_invoice.invoice_number}")
        return electronic_invoice

    except Exception as e:
        print(f"Error creando factura: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_pdf(invoice):
    """Generar PDF de la factura"""

    print("Generando PDF de ejemplo...")

    try:
        from workshops.pdf_generator import generate_electronic_invoice_pdf

        pdf_data = generate_electronic_invoice_pdf(invoice.id)

        # Guardar PDF en archivo
        filename = f"factura_ejemplo_{invoice.invoice_number}.pdf"
        filepath = os.path.join(os.getcwd(), filename)

        with open(filepath, 'wb') as f:
            f.write(pdf_data)

        print(f"PDF generado exitosamente: {filepath}")
        return filepath

    except ImportError:
        print("Error: Generador de PDF no disponible")
        return None
    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        return None

def main():
    """Función principal"""

    print("="*60)
    print("GENERADOR DE FACTURA ELECTRÓNICA DE EJEMPLO")
    print("="*60)
    print("Este script creará una factura de ejemplo con datos genéricos")
    print("para mostrar a SERVIMOTOS y al contador.")
    print()

    try:
        # Crear datos de ejemplo
        data = create_example_data()
        if not data:
            return

        # Crear orden de trabajo
        work_order = create_example_work_order(data)

        # Crear factura electrónica
        invoice = create_example_invoice(work_order)
        if not invoice:
            return

        # Generar XML primero para crear el QR
        try:
            from workshops.dian_xml_generator import DianXmlGenerator
            xml_generator = DianXmlGenerator(invoice)
            xml_content = xml_generator.get_xml_string()

            # El QR se genera automáticamente en el constructor
            print("XML y QR generados exitosamente")
        except Exception as e:
            print(f"Error generando XML/QR: {str(e)}")

        # Generar PDF
        try:
            from workshops.pdf_generator import generate_electronic_invoice_pdf
            pdf_data = generate_electronic_invoice_pdf(invoice.id)

            # Guardar PDF en archivo
            filename = f"factura_ejemplo_{invoice.invoice_number}.pdf"
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, 'wb') as f:
                f.write(pdf_data)

            pdf_path = filepath
            print(f"PDF generado exitosamente: {filepath}")
        except Exception as e:
            pdf_path = None
            print(f"Error generando PDF: {str(e)}")

        print("\n" + "="*60)
        print("FACTURA DE EJEMPLO CREADA EXITOSAMENTE")
        print("="*60)
        print(f"Número de factura: {invoice.invoice_number}")
        print(f"Cliente: {invoice.customer_name}")
        print(f"Total: ${invoice.total:,.0f}")
        print(f"PDF generado: {pdf_path}")
        print()
        print("Puedes mostrar este PDF a SERVIMOTOS y al contador")
        print("para validar que el formato y diseño están correctos.")
        print("="*60)

    except Exception as e:
        print(f"Error general: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
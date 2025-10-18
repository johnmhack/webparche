"""
Tests unitarios para modelos de workshops
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from workshops.models import (
    User, Workshop, Customer, Vehicle, Mechanic,
    Service, SparePart, WorkOrder, WorkOrderItem,
    DianResolution, ElectronicInvoice, ElectronicInvoiceDetail
)


class UserModelTest(TestCase):
    """Tests para el modelo User"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez'
        )

    def test_user_creation(self):
        """Verificar que el usuario se crea correctamente"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str(self):
        """Verificar representación en string"""
        expected = "Juan Pérez - test@example.com"
        self.assertEqual(str(self.user), expected)


class WorkshopModelTest(TestCase):
    """Tests para el modelo Workshop"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123',
            first_name='Carlos',
            last_name='García'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test',
            nit='900123456-7',
            address='Calle 123',
            city='Bogotá',
            department='Cundinamarca'
        )

    def test_workshop_creation(self):
        """Verificar que el taller se crea correctamente"""
        self.assertEqual(self.workshop.name, 'Taller Test')
        self.assertEqual(self.workshop.owner, self.user)

    def test_subscription_expires_default(self):
        """Verificar que subscription_expires se genera dinámicamente"""
        today = timezone.now().date()
        expected_expiry = today + timedelta(days=30)
        self.assertEqual(self.workshop.subscription_expires, expected_expiry)

    def test_is_subscription_active(self):
        """Verificar propiedad is_subscription_active"""
        self.assertTrue(self.workshop.is_subscription_active)
        
        # Expirar suscripción
        self.workshop.subscription_expires = timezone.now().date() - timedelta(days=1)
        self.workshop.save()
        self.assertFalse(self.workshop.is_subscription_active)


class CustomerModelTest(TestCase):
    """Tests para el modelo Customer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test'
        )
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='María',
            last_name='López',
            document_type='cc',
            document_number='1234567890',
            email='maria@example.com',
            phone='+573001234567',
            address='Carrera 45 #12-34',
            city='Medellín',
            department='Antioquia'
        )

    def test_customer_creation(self):
        """Verificar creación de cliente"""
        self.assertEqual(self.customer.first_name, 'María')
        self.assertEqual(self.customer.workshop, self.workshop)

    def test_full_name_property(self):
        """Verificar propiedad full_name"""
        self.assertEqual(self.customer.full_name, 'María López')

    def test_full_address_property(self):
        """Verificar propiedad full_address"""
        expected = 'Carrera 45 #12-34, Medellín, Antioquia'
        self.assertEqual(self.customer.full_address, expected)

    def test_unique_together_constraint(self):
        """Verificar que no se pueden crear clientes duplicados"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                workshop=self.workshop,
                first_name='Pedro',
                last_name='Gómez',
                document_type='cc',
                document_number='1234567890'  # Mismo documento
            )


class DianResolutionModelTest(TestCase):
    """Tests para el modelo DianResolution"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test'
        )
        self.resolution = DianResolution.objects.create(
            workshop=self.workshop,
            resolution_number='18760000001',
            resolution_date=timezone.now().date(),
            expires_date=timezone.now().date() + timedelta(days=365),
            prefix='SMFE',
            from_number=1,
            to_number=1000,
            current_number=0,
            document_type='invoice',
            is_active=True
        )

    def test_resolution_creation(self):
        """Verificar creación de resolución"""
        self.assertEqual(self.resolution.prefix, 'SMFE')
        self.assertEqual(self.resolution.from_number, 1)
        self.assertEqual(self.resolution.to_number, 1000)

    def test_is_valid_property(self):
        """Verificar propiedad is_valid"""
        self.assertTrue(self.resolution.is_valid)
        
        # Expirar resolución
        self.resolution.expires_date = timezone.now().date() - timedelta(days=1)
        self.resolution.save()
        self.assertFalse(self.resolution.is_valid)

    def test_get_next_number(self):
        """Verificar generación de siguiente número"""
        number1 = self.resolution.get_next_number()
        self.assertEqual(number1, 'SMFE0001')
        self.assertEqual(self.resolution.current_number, 1)
        
        number2 = self.resolution.get_next_number()
        self.assertEqual(number2, 'SMFE0002')
        self.assertEqual(self.resolution.current_number, 2)

    def test_get_next_number_exhausted(self):
        """Verificar error cuando se agotan los números"""
        self.resolution.current_number = 1000
        self.resolution.save()
        
        with self.assertRaises(ValueError) as context:
            self.resolution.get_next_number()
        
        self.assertIn('No hay números disponibles', str(context.exception))

    def test_usage_percentage(self):
        """Verificar cálculo de porcentaje de uso"""
        self.assertEqual(self.resolution.usage_percentage, 0)
        
        self.resolution.current_number = 500
        self.resolution.save()
        self.assertEqual(self.resolution.usage_percentage, 50.0)


class WorkOrderModelTest(TestCase):
    """Tests para el modelo WorkOrder"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test'
        )
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='Pedro',
            last_name='Ramírez',
            document_type='cc',
            document_number='9876543210'
        )
        self.vehicle = Vehicle.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle_type='motorcycle',
            brand='Yamaha',
            model='FZ16',
            year=2020,
            license_plate='ABC123'
        )
        self.work_order = WorkOrder.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            vehicle=self.vehicle,
            title='Mantenimiento preventivo',
            description='Cambio de aceite y filtros',
            status='draft'
        )

    def test_work_order_creation(self):
        """Verificar creación de orden de trabajo"""
        self.assertEqual(self.work_order.workshop, self.workshop)
        self.assertEqual(self.work_order.customer, self.customer)
        self.assertIsNotNone(self.work_order.order_number)

    def test_order_number_generation(self):
        """Verificar generación automática de número de orden"""
        self.assertTrue(self.work_order.order_number.startswith('OT'))
        self.assertIn(timezone.now().strftime('%Y%m%d'), self.work_order.order_number)

    def test_can_be_invoiced(self):
        """Verificar propiedad can_be_invoiced"""
        self.assertFalse(self.work_order.can_be_invoiced)
        
        self.work_order.status = 'completed'
        self.work_order.save()
        self.assertTrue(self.work_order.can_be_invoiced)

    def test_update_costs(self):
        """Verificar actualización de costos desde items"""
        # Crear items
        WorkOrderItem.objects.create(
            work_order=self.work_order,
            item_type='service',
            description='Cambio de aceite',
            service_quantity=1,
            service_unit_price=Decimal('50000')
        )
        WorkOrderItem.objects.create(
            work_order=self.work_order,
            item_type='part',
            description='Filtro de aceite',
            part_quantity=1,
            part_unit_price=Decimal('15000')
        )
        
        self.work_order.update_costs()
        self.assertEqual(self.work_order.labor_cost, Decimal('50000'))
        self.assertEqual(self.work_order.parts_cost, Decimal('15000'))
        self.assertEqual(self.work_order.final_cost, Decimal('65000'))


class ElectronicInvoiceModelTest(TestCase):
    """Tests para el modelo ElectronicInvoice"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller Test',
            nit='900123456-7'
        )
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='Ana',
            last_name='Martínez',
            document_type='cc',
            document_number='1122334455'
        )
        self.resolution = DianResolution.objects.create(
            workshop=self.workshop,
            resolution_number='18760000001',
            resolution_date=timezone.now().date(),
            expires_date=timezone.now().date() + timedelta(days=365),
            prefix='SMFE',
            from_number=1,
            to_number=1000,
            current_number=0,
            document_type='invoice'
        )

    def test_electronic_invoice_creation(self):
        """Verificar creación de factura electrónica"""
        invoice = ElectronicInvoice.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            dian_resolution=self.resolution,
            workshop_nit='900123456-7',
            workshop_name='Taller Test',
            workshop_address='Calle 123',
            workshop_city='Bogotá',
            workshop_department='Cundinamarca',
            customer_name='Ana Martínez',
            customer_document_type='cc',
            customer_document='1122334455',
            subtotal=Decimal('100000'),
            tax_rate=Decimal('19.00')
        )
        
        self.assertIsNotNone(invoice.invoice_number)
        self.assertTrue(invoice.invoice_number.startswith('SMFE'))
        self.assertIsNotNone(invoice.cude)

    def test_cude_generation(self):
        """Verificar generación de CUDE"""
        invoice = ElectronicInvoice.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            dian_resolution=self.resolution,
            workshop_nit='900123456-7',
            workshop_name='Taller Test',
            workshop_address='Calle 123',
            workshop_city='Bogotá',
            workshop_department='Cundinamarca',
            customer_name='Ana Martínez',
            customer_document_type='cc',
            customer_document='1122334455',
            subtotal=Decimal('100000')
        )
        
        self.assertEqual(len(invoice.cude), 96)  # SHA384 = 96 caracteres hex

    def test_invoice_number_validation(self):
        """Verificar validación de número de factura"""
        invoice = ElectronicInvoice.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            dian_resolution=self.resolution,
            workshop_nit='900123456-7',
            workshop_name='Taller Test',
            workshop_address='Calle 123',
            workshop_city='Bogotá',
            workshop_department='Cundinamarca',
            customer_name='Ana Martínez',
            customer_document_type='cc',
            customer_document='1122334455',
            subtotal=Decimal('100000')
        )
        
        self.assertTrue(invoice.validate_invoice_number())
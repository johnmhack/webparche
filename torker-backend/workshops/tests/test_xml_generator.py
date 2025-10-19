"""
Tests para generador de XML UBL 2.1 DIAN
"""
from decimal import Decimal
from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from workshops.models import (
    User, Workshop, Customer, DianResolution, ElectronicInvoice, ElectronicInvoiceDetail
)
from workshops.dian_xml_generator import (
    generate_electronic_invoice_xml,
    validate_xml_structure,
    create_element,
    format_decimal,
    format_date,
    format_time,
)


class XMLGeneratorTestCase(TestCase):
    """Tests para generación de XML"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Crear taller
        self.workshop = Workshop.objects.create(
            owner=self.user,
            name='Taller de Prueba',
            nit='900123456',
            legal_name='Taller de Prueba S.A.S.',
            address='Calle 123 #45-67',
            city='Bogotá',
            department='Cundinamarca',
            phone='3001234567',
            email='taller@example.com',
            tax_regime='comun',
            default_tax_rate=Decimal('19.00')
        )
        
        # Crear cliente
        self.customer = Customer.objects.create(
            workshop=self.workshop,
            first_name='Juan',
            last_name='Pérez',
            document_type='cc',
            document_number='123456789',
            phone='3009876543',
            email='juan@example.com',
            address='Carrera 10 #20-30',
            city='Bogotá',
            department='Cundinamarca'
        )
        
        # Crear resolución DIAN
        self.resolution = DianResolution.objects.create(
            workshop=self.workshop,
            resolution_number='18764000000001',
            resolution_date=timezone.now().date(),
            expires_date=timezone.now().date(),
            prefix='SMFE',
            from_number=1,
            to_number=5000,
            current_number=0,
            document_type='invoice'
        )
    
    def test_format_decimal(self):
        """Test formateo de decimales"""
        self.assertEqual(format_decimal(Decimal('1000.00'), 2), '1000.00')
        self.assertEqual(format_decimal(Decimal('1000.5'), 2), '1000.50')
        self.assertEqual(format_decimal(Decimal('1000'), 2), '1000.00')
    
    def test_format_date(self):
        """Test formateo de fechas"""
        test_date = datetime(2024, 1, 15).date()
        self.assertEqual(format_date(test_date), '2024-01-15')
    
    def test_format_time(self):
        """Test formateo de horas"""
        test_time = datetime(2024, 1, 15, 10, 30, 0)
        formatted = format_time(test_time)
        self.assertIn('10:30:00', formatted)
        self.assertIn('-05:00', formatted)
    
    def test_create_element_basic(self):
        """Test creación de elemento XML básico"""
        elem = create_element('cbc:ID', '12345')
        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, '12345')
    
    def test_validate_xml_structure_valid(self):
        """Test validación de XML válido"""
        valid_xml = '<?xml version="1.0"?><root><child>test</child></root>'
        is_valid, message = validate_xml_structure(valid_xml)
        self.assertTrue(is_valid)
    
    def test_validate_xml_structure_invalid(self):
        """Test validación de XML inválido"""
        invalid_xml = '<root><child>test</root>'  # Tag no cerrado
        is_valid, message = validate_xml_structure(invalid_xml)
        self.assertFalse(is_valid)
        self.assertIn('inválido', message)
    
    def test_generate_xml_basic_structure(self):
        """Test generación básica de XML de factura"""
        # Crear factura electrónica
        invoice = ElectronicInvoice.objects.create(
            workshop=self.workshop,
            customer=self.customer,
            dian_resolution=self.resolution,
            workshop_nit=self.workshop.nit,
            workshop_name=self.workshop.legal_name,
            workshop_address=self.workshop.address,
            workshop_city=self.workshop.city,
            workshop_department=self.workshop.department,
            workshop_phone=self.workshop.phone,
            workshop_email=self.workshop.email,
            customer_name=self.customer.full_name,
            customer_document_type=self.customer.document_type,
            customer_document=self.customer.document_number,
            customer_address=self.customer.address,
            customer_city=self.customer.city,
            customer_department=self.customer.department,
            customer_phone=self.customer.phone,
            customer_email=self.customer.email,
            subtotal=Decimal('1000000.00'),
            discount=Decimal('0.00'),
            tax_rate=Decimal('19.00'),
            tax_amount=Decimal('190000.00'),
            total=Decimal('1190000.00'),
            payment_method='cash'
        )
        
        # Agregar detalle
        ElectronicInvoiceDetail.objects.create(
            electronic_invoice=invoice,
            description='Cambio de aceite',
            part_number='ACE001',
            unspsc_code='81111500',
            quantity=Decimal('1.00'),
            unit_code='E48',
            unit_price=Decimal('50000.00'),
            discount=Decimal('0.00'),
            tax_rate=Decimal('19.00')
        )
        
        # Generar XML
        xml_content = generate_electronic_invoice_xml(invoice)
        
        # Verificar que se generó XML
        self.assertIsNotNone(xml_content)
        self.assertIn('<?xml', xml_content)
        self.assertIn('Invoice', xml_content)
        self.assertIn('UBL 2.1', xml_content)
        self.assertIn(invoice.invoice_number, xml_content)
        self.assertIn(invoice.cude, xml_content)
        self.assertIn(self.workshop.nit, xml_content)
        self.assertIn(self.customer.document_number, xml_content)
        
        # Validar estructura
        is_valid, message = validate_xml_structure(xml_content)
        self.assertTrue(is_valid, f"XML inválido: {message}")
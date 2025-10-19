"""
Tests para utilidades DIAN - Facturación Electrónica
Valida algoritmos críticos según Resolución 000042 de 2020
"""
from decimal import Decimal
from datetime import datetime, date
from django.test import TestCase
from workshops.dian_utils import (
    generate_cufe,
    generate_cude,
    calculate_nit_verification_digit,
    validate_nit,
    format_nit,
    TaxCalculator,
    validate_invoice_number_format,
    generate_invoice_number,
    generate_qr_data,
    format_currency,
)


class CUFEGenerationTestCase(TestCase):
    """Tests para generación de CUFE/CUDE"""
    
    def test_generate_cufe_basic(self):
        """Test generación básica de CUFE"""
        cufe = generate_cufe(
            invoice_number="SMFE0001",
            issue_date=datetime(2024, 1, 15, 10, 30, 0),
            issue_time="10:30:00-05:00",
            invoice_total=Decimal("1000000.00"),
            tax_code_1="01",
            tax_value_1=Decimal("190000.00"),
            tax_code_2="04",
            tax_value_2=Decimal("0.00"),
            tax_code_3="03",
            tax_value_3=Decimal("0.00"),
            total_with_tax=Decimal("1190000.00"),
            supplier_nit="900123456",
            customer_document="123456789",
            software_pin="12345",
            environment_type="2"
        )
        
        # CUFE debe ser SHA-384 (96 caracteres hexadecimales)
        self.assertEqual(len(cufe), 96)
        self.assertTrue(all(c in '0123456789abcdef' for c in cufe))
    
    def test_cufe_deterministic(self):
        """Test que CUFE es determinístico (mismos datos = mismo CUFE)"""
        params = {
            "invoice_number": "SMFE0001",
            "issue_date": datetime(2024, 1, 15, 10, 30, 0),
            "issue_time": "10:30:00-05:00",
            "invoice_total": Decimal("1000000.00"),
            "tax_code_1": "01",
            "tax_value_1": Decimal("190000.00"),
            "tax_code_2": "04",
            "tax_value_2": Decimal("0.00"),
            "tax_code_3": "03",
            "tax_value_3": Decimal("0.00"),
            "total_with_tax": Decimal("1190000.00"),
            "supplier_nit": "900123456",
            "customer_document": "123456789",
            "software_pin": "12345",
            "environment_type": "2"
        }
        
        cufe1 = generate_cufe(**params)
        cufe2 = generate_cufe(**params)
        
        self.assertEqual(cufe1, cufe2)
    
    def test_cufe_different_for_different_data(self):
        """Test que CUFE cambia con datos diferentes"""
        base_params = {
            "invoice_number": "SMFE0001",
            "issue_date": datetime(2024, 1, 15, 10, 30, 0),
            "issue_time": "10:30:00-05:00",
            "invoice_total": Decimal("1000000.00"),
            "tax_code_1": "01",
            "tax_value_1": Decimal("190000.00"),
            "tax_code_2": "04",
            "tax_value_2": Decimal("0.00"),
            "tax_code_3": "03",
            "tax_value_3": Decimal("0.00"),
            "total_with_tax": Decimal("1190000.00"),
            "supplier_nit": "900123456",
            "customer_document": "123456789",
            "software_pin": "12345",
            "environment_type": "2"
        }
        
        cufe1 = generate_cufe(**base_params)
        
        # Cambiar número de factura
        modified_params = base_params.copy()
        modified_params["invoice_number"] = "SMFE0002"
        cufe2 = generate_cufe(**modified_params)
        
        self.assertNotEqual(cufe1, cufe2)
    
    def test_generate_cude_same_as_cufe(self):
        """Test que CUDE usa el mismo algoritmo que CUFE"""
        params = {
            "document_number": "SMFE0001",
            "issue_date": datetime(2024, 1, 15, 10, 30, 0),
            "issue_time": "10:30:00-05:00",
            "document_total": Decimal("1000000.00"),
            "tax_code_1": "01",
            "tax_value_1": Decimal("190000.00"),
            "tax_code_2": "04",
            "tax_value_2": Decimal("0.00"),
            "tax_code_3": "03",
            "tax_value_3": Decimal("0.00"),
            "total_with_tax": Decimal("1190000.00"),
            "supplier_nit": "900123456",
            "customer_document": "123456789",
            "software_pin": "12345",
            "environment_type": "2"
        }
        
        cude = generate_cude(**params)
        
        # CUDE debe tener el mismo formato que CUFE
        self.assertEqual(len(cude), 96)
        self.assertTrue(all(c in '0123456789abcdef' for c in cude))


class NITValidationTestCase(TestCase):
    """Tests para validación de NIT"""
    
    def test_calculate_nit_dv_known_values(self):
        """Test cálculo de DV con valores conocidos"""
        # Casos de prueba con DVs calculados correctamente
        test_cases = [
            ("900123456", "8"),  # DV correcto calculado
            ("800197268", "4"),  # DV correcto calculado
            ("890903938", "8"),  # DV correcto calculado
        ]
        
        for nit, expected_dv in test_cases:
            calculated_dv = calculate_nit_verification_digit(nit)
            self.assertEqual(
                calculated_dv,
                expected_dv,
                f"DV incorrecto para NIT {nit}. Esperado: {expected_dv}, Obtenido: {calculated_dv}"
            )
    
    def test_validate_nit_valid(self):
        """Test validación de NIT válido"""
        is_valid, message = validate_nit("900123456", "8")
        self.assertTrue(is_valid)
        self.assertEqual(message, "NIT válido")
    
    def test_validate_nit_invalid_dv(self):
        """Test validación de NIT con DV incorrecto"""
        is_valid, message = validate_nit("900123456", "9")
        self.assertFalse(is_valid)
        self.assertIn("Dígito de verificación incorrecto", message)
    
    def test_validate_nit_with_hyphen(self):
        """Test validación de NIT con guión"""
        is_valid, message = validate_nit("900123456-8")
        self.assertTrue(is_valid)
    
    def test_validate_nit_invalid_format(self):
        """Test validación de NIT con formato inválido"""
        is_valid, message = validate_nit("ABC")
        self.assertFalse(is_valid)
        # El mensaje puede ser "solo números" o "entre 6 y 10 dígitos"
        self.assertTrue("solo números" in message or "entre 6 y 10 dígitos" in message)
    
    def test_format_nit_with_dv(self):
        """Test formateo de NIT con DV"""
        formatted = format_nit("900123456", include_dv=True)
        self.assertEqual(formatted, "900123456-8")
    
    def test_format_nit_without_dv(self):
        """Test formateo de NIT sin DV"""
        formatted = format_nit("900123456", include_dv=False)
        self.assertEqual(formatted, "900123456")


class TaxCalculatorTestCase(TestCase):
    """Tests para cálculo de impuestos"""
    
    def test_calculate_iva_19_percent(self):
        """Test cálculo de IVA al 19%"""
        base = Decimal("1000000.00")
        iva = TaxCalculator.calculate_iva(base, "19")
        self.assertEqual(iva, Decimal("190000.00"))
    
    def test_calculate_iva_5_percent(self):
        """Test cálculo de IVA al 5%"""
        base = Decimal("1000000.00")
        iva = TaxCalculator.calculate_iva(base, "5")
        self.assertEqual(iva, Decimal("50000.00"))
    
    def test_calculate_iva_0_percent(self):
        """Test cálculo de IVA al 0% (excluido)"""
        base = Decimal("1000000.00")
        iva = TaxCalculator.calculate_iva(base, "0")
        self.assertEqual(iva, Decimal("0.00"))
    
    def test_calculate_iva_invalid_rate(self):
        """Test cálculo de IVA con tarifa inválida"""
        with self.assertRaises(ValueError):
            TaxCalculator.calculate_iva(Decimal("1000000.00"), "25")
    
    def test_calculate_inc_8_percent(self):
        """Test cálculo de INC al 8%"""
        base = Decimal("1000000.00")
        inc = TaxCalculator.calculate_inc(base, "8")
        self.assertEqual(inc, Decimal("80000.00"))
    
    def test_calculate_retention(self):
        """Test cálculo de retención"""
        base = Decimal("1000000.00")
        retention = TaxCalculator.calculate_retention(base, Decimal("0.025"))
        self.assertEqual(retention, Decimal("25000.00"))
    
    def test_calculate_invoice_totals_complete(self):
        """Test cálculo completo de totales de factura"""
        totals = TaxCalculator.calculate_invoice_totals(
            subtotal=Decimal("1000000.00"),
            iva_rate="19",
            inc_rate="0",
            discount=Decimal("50000.00"),
            retention_rate=Decimal("0.025")
        )
        
        self.assertEqual(totals['subtotal'], Decimal("1000000.00"))
        self.assertEqual(totals['discount'], Decimal("50000.00"))
        self.assertEqual(totals['base_after_discount'], Decimal("950000.00"))
        self.assertEqual(totals['iva'], Decimal("180500.00"))  # 950000 * 0.19
        self.assertEqual(totals['inc'], Decimal("0.00"))
        self.assertEqual(totals['total_with_tax'], Decimal("1130500.00"))
        self.assertEqual(totals['retention'], Decimal("23750.00"))  # 950000 * 0.025
        self.assertEqual(totals['total_to_pay'], Decimal("1106750.00"))


class InvoiceNumberValidationTestCase(TestCase):
    """Tests para validación de numeración de facturas"""
    
    def test_validate_invoice_number_valid(self):
        """Test validación de número de factura válido"""
        is_valid, message = validate_invoice_number_format(
            "SMFE0001",
            "SMFE",
            1,
            5000
        )
        self.assertTrue(is_valid)
    
    def test_validate_invoice_number_wrong_prefix(self):
        """Test validación con prefijo incorrecto"""
        is_valid, message = validate_invoice_number_format(
            "WRONG0001",
            "SMFE",
            1,
            5000
        )
        self.assertFalse(is_valid)
        self.assertIn("prefijo", message)
    
    def test_validate_invoice_number_below_range(self):
        """Test validación con número fuera de rango (inferior)"""
        is_valid, message = validate_invoice_number_format(
            "SMFE0000",
            "SMFE",
            1,
            5000
        )
        self.assertFalse(is_valid)
        self.assertIn("por debajo del rango", message)
    
    def test_validate_invoice_number_above_range(self):
        """Test validación con número fuera de rango (superior)"""
        is_valid, message = validate_invoice_number_format(
            "SMFE9999",
            "SMFE",
            1,
            5000
        )
        self.assertFalse(is_valid)
        self.assertIn("excede el rango", message)
    
    def test_generate_invoice_number_with_padding(self):
        """Test generación de número de factura con padding"""
        number = generate_invoice_number("SMFE", 1, 4)
        self.assertEqual(number, "SMFE0001")
        
        number = generate_invoice_number("F", 123, 6)
        self.assertEqual(number, "F000123")


class QRCodeGenerationTestCase(TestCase):
    """Tests para generación de datos de código QR"""
    
    def test_generate_qr_data_format(self):
        """Test formato de datos para QR"""
        qr_data = generate_qr_data(
            invoice_number="SMFE0001",
            issue_date=date(2024, 1, 15),
            supplier_nit="900123456",
            customer_document_type="13",
            customer_document="123456789",
            invoice_total=Decimal("1000000.00"),
            iva_total=Decimal("190000.00"),
            other_tax_total=Decimal("0.00"),
            total_with_tax=Decimal("1190000.00"),
            cufe="abc123def456"
        )
        
        # Verificar que contiene todos los campos requeridos
        self.assertIn("NumFac=SMFE0001", qr_data)
        self.assertIn("FecFac=2024-01-15", qr_data)
        self.assertIn("NitFac=900123456", qr_data)
        self.assertIn("DocAdq=13", qr_data)
        self.assertIn("NitAdq=123456789", qr_data)
        self.assertIn("ValFac=1000000.00", qr_data)
        self.assertIn("ValIva=190000.00", qr_data)
        self.assertIn("ValOtroIm=0.00", qr_data)
        self.assertIn("ValTotal=1190000.00", qr_data)
        self.assertIn("CUFE=abc123def456", qr_data)
        self.assertIn("URL=", qr_data)


class UtilityFunctionsTestCase(TestCase):
    """Tests para funciones utilitarias"""
    
    def test_format_currency(self):
        """Test formateo de moneda"""
        formatted = format_currency(Decimal("1190000.00"))
        self.assertEqual(formatted, "$1.190.000,00")
        
        formatted = format_currency(Decimal("50.50"))
        self.assertEqual(formatted, "$50,50")
#!/usr/bin/env python
"""Script temporal para escribir dian_utils.py"""

DIAN_UTILS_CONTENT = '''"""
Utilidades para cumplimiento DIAN - Facturación Electrónica Colombia
Implementa algoritmos y validaciones según Resolución 000042 de 2020
"""
import hashlib
import re
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional


# ============================================================================
# ALGORITMO CUDE/CUFE SEGÚN ESPECIFICACIÓN DIAN
# ============================================================================

def generate_cufe(
    invoice_number: str,
    issue_date: datetime,
    issue_time: str,
    invoice_total: Decimal,
    tax_code_1: str,
    tax_value_1: Decimal,
    tax_code_2: str,
    tax_value_2: Decimal,
    tax_code_3: str,
    tax_value_3: Decimal,
    total_with_tax: Decimal,
    supplier_nit: str,
    customer_document: str,
    software_pin: str,
    environment_type: str
) -> str:
    """
    Genera CUFE (Código Único de Factura Electrónica) según algoritmo DIAN.
    
    Algoritmo oficial DIAN:
    CUFE = SHA-384(
        NumFac + FecFac + HorFac + ValFac + 
        CodImp1 + ValImp1 + CodImp2 + ValImp2 + CodImp3 + ValImp3 + 
        ValTot + NitOFE + NumAdq + Software-PIN + TipoAmbiente
    )
    """
    fecha_factura = issue_date.strftime('%Y-%m-%d')
    val_fac = f"{invoice_total:.2f}"
    val_imp1 = f"{tax_value_1:.2f}"
    val_imp2 = f"{tax_value_2:.2f}"
    val_imp3 = f"{tax_value_3:.2f}"
    val_tot = f"{total_with_tax:.2f}"
    
    cufe_string = (
        f"{invoice_number}"
        f"{fecha_factura}"
        f"{issue_time}"
        f"{val_fac}"
        f"{tax_code_1}"
        f"{val_imp1}"
        f"{tax_code_2}"
        f"{val_imp2}"
        f"{tax_code_3}"
        f"{val_imp3}"
        f"{val_tot}"
        f"{supplier_nit}"
        f"{customer_document}"
        f"{software_pin}"
        f"{environment_type}"
    )
    
    cufe_hash = hashlib.sha384(cufe_string.encode('utf-8')).hexdigest()
    return cufe_hash


def generate_cude(
    document_number: str,
    issue_date: datetime,
    issue_time: str,
    document_total: Decimal,
    tax_code_1: str,
    tax_value_1: Decimal,
    tax_code_2: str,
    tax_value_2: Decimal,
    tax_code_3: str,
    tax_value_3: Decimal,
    total_with_tax: Decimal,
    supplier_nit: str,
    customer_document: str,
    software_pin: str,
    environment_type: str,
    document_type: str = "01"
) -> str:
    """Genera CUDE para documentos equivalentes."""
    return generate_cufe(
        document_number, issue_date, issue_time, document_total,
        tax_code_1, tax_value_1, tax_code_2, tax_value_2,
        tax_code_3, tax_value_3, total_with_tax, supplier_nit,
        customer_document, software_pin, environment_type
    )


def calculate_nit_verification_digit(nit: str) -> str:
    """Calcula el dígito de verificación de un NIT colombiano según algoritmo DIAN."""
    weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    nit_clean = re.sub(r'\\D', '', nit)
    nit_reversed = nit_clean[::-1]
    total = sum(int(digit) * weight for digit, weight in zip(nit_reversed, weights))
    remainder = total % 11
    dv = 11 - remainder
    
    if dv == 11:
        dv = 0
    elif dv == 10:
        dv = 1
    
    return str(dv)


def validate_nit(nit: str, dv: Optional[str] = None) -> Tuple[bool, str]:
    """Valida un NIT colombiano con su dígito de verificación."""
    if '-' in nit:
        parts = nit.split('-')
        nit_number = parts[0]
        provided_dv = parts[1] if len(parts) > 1 else dv
    else:
        nit_number = nit
        provided_dv = dv
    
    nit_clean = re.sub(r'\\D', '', nit_number)
    
    if not nit_clean or not nit_clean.isdigit():
        return False, "NIT debe contener solo números"
    
    if len(nit_clean) < 6 or len(nit_clean) > 10:
        return False, "NIT debe tener entre 6 y 10 dígitos"
    
    calculated_dv = calculate_nit_verification_digit(nit_clean)
    
    if provided_dv is None:
        return True, f"NIT válido. Dígito de verificación: {calculated_dv}"
    
    if str(provided_dv) != calculated_dv:
        return False, f"Dígito de verificación incorrecto. Esperado: {calculated_dv}, Recibido: {provided_dv}"
    
    return True, "NIT válido"


def format_nit(nit: str, include_dv: bool = True) -> str:
    """Formatea un NIT colombiano en formato estándar."""
    nit_clean = re.sub(r'\\D', '', nit)
    
    if not nit_clean:
        return ""
    
    dv = calculate_nit_verification_digit(nit_clean)
    
    if include_dv:
        return f"{nit_clean}-{dv}"
    else:
        return nit_clean


class TaxCalculator:
    """Calculadora de impuestos según normativa DIAN colombiana"""
    
    IVA_RATES = {
        '0': Decimal('0.00'),
        '5': Decimal('0.05'),
        '19': Decimal('0.19'),
    }
    
    INC_RATES = {
        '0': Decimal('0.00'),
        '4': Decimal('0.04'),
        '8': Decimal('0.08'),
        '16': Decimal('0.16'),
    }
    
    TAX_CODES = {
        'IVA': '01',
        'INC': '04',
        'ICA': '03',
        'RTE_FTE': '06',
        'RTE_IVA': '05',
    }
    
    @staticmethod
    def calculate_iva(base: Decimal, rate: str = '19') -> Decimal:
        """Calcula IVA sobre una base gravable."""
        if rate not in TaxCalculator.IVA_RATES:
            raise ValueError(f"Tarifa IVA inválida: {rate}")
        return base * TaxCalculator.IVA_RATES[rate]
    
    @staticmethod
    def calculate_inc(base: Decimal, rate: str = '8') -> Decimal:
        """Calcula INC (Impuesto Nacional al Consumo)."""
        if rate not in TaxCalculator.INC_RATES:
            raise ValueError(f"Tarifa INC inválida: {rate}")
        return base * TaxCalculator.INC_RATES[rate]
    
    @staticmethod
    def calculate_retention(base: Decimal, rate: Decimal) -> Decimal:
        """Calcula retención en la fuente o retención de IVA."""
        return base * rate
    
    @staticmethod
    def calculate_invoice_totals(
        subtotal: Decimal,
        iva_rate: str = '19',
        inc_rate: str = '0',
        discount: Decimal = Decimal('0'),
        retention_rate: Decimal = Decimal('0')
    ) -> Dict[str, Decimal]:
        """Calcula todos los totales de una factura."""
        base_after_discount = subtotal - discount
        iva = TaxCalculator.calculate_iva(base_after_discount, iva_rate)
        inc = TaxCalculator.calculate_inc(base_after_discount, inc_rate)
        total_with_tax = base_after_discount + iva + inc
        retention = TaxCalculator.calculate_retention(base_after_discount, retention_rate)
        total_to_pay = total_with_tax - retention
        
        return {
            'subtotal': subtotal,
            'discount': discount,
            'base_after_discount': base_after_discount,
            'iva': iva,
            'inc': inc,
            'total_tax': iva + inc,
            'total_with_tax': total_with_tax,
            'retention': retention,
            'total_to_pay': total_to_pay,
        }


def validate_invoice_number_format(
    invoice_number: str,
    prefix: str,
    min_number: int,
    max_number: int
) -> Tuple[bool, str]:
    """Valida que un número de factura cumpla con el formato y rango de la resolución DIAN."""
    if not invoice_number.startswith(prefix):
        return False, f"El número debe comenzar con el prefijo '{prefix}'"
    
    number_part = invoice_number[len(prefix):]
    
    if not number_part.isdigit():
        return False, "La parte numérica debe contener solo dígitos"
    
    try:
        number = int(number_part)
    except ValueError:
        return False, "Número de factura inválido"
    
    if number < min_number:
        return False, f"Número {number} está por debajo del rango autorizado (mínimo: {min_number})"
    
    if number > max_number:
        return False, f"Número {number} excede el rango autorizado (máximo: {max_number})"
    
    return True, "Número de factura válido"


def generate_invoice_number(prefix: str, consecutive: int, padding: int = 4) -> str:
    """Genera un número de factura con formato estándar."""
    return f"{prefix}{str(consecutive).zfill(padding)}"


def generate_qr_data(
    invoice_number: str,
    issue_date: date,
    supplier_nit: str,
    customer_document_type: str,
    customer_document: str,
    invoice_total: Decimal,
    iva_total: Decimal,
    other_tax_total: Decimal,
    total_with_tax: Decimal,
    cufe: str,
    validation_url: str = "https://catalogo-vpfe.dian.gov.co/document/searchqr"
) -> str:
    """Genera la cadena de datos para el código QR según formato DIAN."""
    qr_string = (
        f"NumFac={invoice_number}\\n"
        f"FecFac={issue_date.strftime('%Y-%m-%d')}\\n"
        f"NitFac={supplier_nit}\\n"
        f"DocAdq={customer_document_type}\\n"
        f"NitAdq={customer_document}\\n"
        f"ValFac={invoice_total:.2f}\\n"
        f"ValIva={iva_total:.2f}\\n"
        f"ValOtroIm={other_tax_total:.2f}\\n"
        f"ValTotal={total_with_tax:.2f}\\n"
        f"CUFE={cufe}\\n"
        f"URL={validation_url}?documentkey={cufe}"
    )
    return qr_string


def format_currency(amount: Decimal, currency: str = 'COP') -> str:
    """Formatea un valor monetario según estándares colombianos."""
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"${formatted}"


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    """Valida que un rango de fechas sea válido."""
    if start_date > end_date:
        return False, "La fecha inicial no puede ser posterior a la fecha final"
    
    if end_date > date.today():
        return False, "La fecha final no puede ser futura"
    
    return True, "Rango de fechas válido"
'''

if __name__ == '__main__':
    with open('workshops/dian_utils.py', 'w', encoding='utf-8') as f:
        f.write(DIAN_UTILS_CONTENT)
    print("✅ Archivo dian_utils.py escrito exitosamente")
    
    # Verificar tamaño
    import os
    size = os.path.getsize('workshops/dian_utils.py')
    print(f"📊 Tamaño del archivo: {size} bytes")
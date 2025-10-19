"""
Catálogo de Códigos de Impuestos - DIAN
Basado en listas oficiales TipoImpuesto-2.1.gc, TarifaImpuestoIVA-2.1.gc, TarifaImpuestoINC-2.1.gc
"""
from decimal import Decimal

# Códigos de tipos de impuestos según DIAN
TAX_CODES = {
    '01': 'IVA - Impuesto sobre las ventas',
    '02': 'IC - Impuesto al consumo',
    '03': 'ICA - Impuesto de industria y comercio',
    '04': 'INC - Impuesto nacional al consumo',
    '05': 'ReteIVA - Retención sobre el IVA',
    '06': 'ReteFuente - Retención en la fuente',
    '07': 'ReteICA - Retención ICA',
    '08': 'Bolsas - Impuesto nacional al consumo de bolsas plásticas',
    '09': 'Carbono - Impuesto nacional al carbono',
    '10': 'Combustibles - Impuesto nacional a la gasolina y al ACPM',
    '11': 'Sobretasa combustibles',
    '12': 'Sordicom',
    '13': 'Timbre',
    '20': 'FtoHorticultura',
    '21': 'INCBolsas',
    '22': 'INCCarbono',
    '23': 'INCCombustibles',
    '24': 'INCSobretasa',
    '25': 'Saludable',
    'ZZ': 'No causa',
}

# Tarifas de IVA vigentes en Colombia
IVA_RATES = {
    '01': {'rate': Decimal('19.00'), 'name': 'Tarifa general 19%'},
    '02': {'rate': Decimal('5.00'), 'name': 'Tarifa reducida 5%'},
    '03': {'rate': Decimal('0.00'), 'name': 'Exento'},
    '04': {'rate': Decimal('0.00'), 'name': 'Excluido'},
}

# Tarifas de INC (Impuesto Nacional al Consumo)
INC_RATES = {
    '01': {'rate': Decimal('4.00'), 'name': 'Tarifa 4%'},
    '02': {'rate': Decimal('8.00'), 'name': 'Tarifa 8%'},
    '03': {'rate': Decimal('16.00'), 'name': 'Tarifa 16%'},
    '04': {'rate': Decimal('0.00'), 'name': 'Exento'},
}

# Tarifas de Retención en la Fuente más comunes
RETEFUENTE_RATES = {
    '01': {'rate': Decimal('0.50'), 'name': 'Retención 0.5%'},
    '02': {'rate': Decimal('1.00'), 'name': 'Retención 1%'},
    '03': {'rate': Decimal('1.50'), 'name': 'Retención 1.5%'},
    '04': {'rate': Decimal('2.00'), 'name': 'Retención 2%'},
    '05': {'rate': Decimal('2.50'), 'name': 'Retención 2.5%'},
    '06': {'rate': Decimal('3.00'), 'name': 'Retención 3%'},
    '07': {'rate': Decimal('3.50'), 'name': 'Retención 3.5%'},
    '08': {'rate': Decimal('4.00'), 'name': 'Retención 4%'},
    '09': {'rate': Decimal('6.00'), 'name': 'Retención 6%'},
    '10': {'rate': Decimal('10.00'), 'name': 'Retención 10%'},
    '11': {'rate': Decimal('11.00'), 'name': 'Retención 11%'},
}

# Tarifas de Retención de IVA
RETEIVA_RATES = {
    '01': {'rate': Decimal('15.00'), 'name': 'Retención IVA 15%'},
    '02': {'rate': Decimal('0.00'), 'name': 'No aplica retención IVA'},
}

# Mapeo de códigos de impuestos a nombres cortos
TAX_CODE_NAMES = {
    '01': 'IVA',
    '02': 'IC',
    '03': 'ICA',
    '04': 'INC',
    '05': 'ReteIVA',
    '06': 'ReteFuente',
}


def get_tax_name(code: str) -> str:
    """
    Obtiene el nombre del tipo de impuesto según código DIAN.
    
    Args:
        code: Código DIAN del impuesto
    
    Returns:
        str: Nombre del impuesto
    """
    return TAX_CODES.get(code, 'Desconocido')


def get_tax_short_name(code: str) -> str:
    """
    Obtiene el nombre corto del impuesto.
    
    Args:
        code: Código DIAN del impuesto
    
    Returns:
        str: Nombre corto
    """
    return TAX_CODE_NAMES.get(code, code)


def validate_tax_code(code: str) -> bool:
    """
    Valida que un código de impuesto sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in TAX_CODES


def get_iva_rate(rate_code: str) -> Decimal:
    """
    Obtiene la tarifa de IVA según código.
    
    Args:
        rate_code: Código de tarifa IVA
    
    Returns:
        Decimal: Tarifa como decimal (ej: 0.19 para 19%)
    """
    rate_info = IVA_RATES.get(rate_code, {'rate': Decimal('19.00')})
    return rate_info['rate'] / Decimal('100')


def get_inc_rate(rate_code: str) -> Decimal:
    """
    Obtiene la tarifa de INC según código.
    
    Args:
        rate_code: Código de tarifa INC
    
    Returns:
        Decimal: Tarifa como decimal
    """
    rate_info = INC_RATES.get(rate_code, {'rate': Decimal('0.00')})
    return rate_info['rate'] / Decimal('100')


def get_retefuente_rate(rate_code: str) -> Decimal:
    """
    Obtiene la tarifa de retención en la fuente según código.
    
    Args:
        rate_code: Código de tarifa
    
    Returns:
        Decimal: Tarifa como decimal
    """
    rate_info = RETEFUENTE_RATES.get(rate_code, {'rate': Decimal('0.00')})
    return rate_info['rate'] / Decimal('100')


def get_reteiva_rate(rate_code: str) -> Decimal:
    """
    Obtiene la tarifa de retención de IVA según código.
    
    Args:
        rate_code: Código de tarifa
    
    Returns:
        Decimal: Tarifa como decimal
    """
    rate_info = RETEIVA_RATES.get(rate_code, {'rate': Decimal('0.00')})
    return rate_info['rate'] / Decimal('100')


# Estructura completa de impuestos para XML
TAX_RATES = {
    'IVA': IVA_RATES,
    'INC': INC_RATES,
    'ReteFuente': RETEFUENTE_RATES,
    'ReteIVA': RETEIVA_RATES,
}
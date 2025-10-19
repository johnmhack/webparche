"""
Catálogo de Medios y Formas de Pago - DIAN
Basado en listas oficiales MediosPago-2.1.gc y FormasPago-2.1.gc
"""

# Medios de pago según DIAN
PAYMENT_METHODS = {
    '1': 'Instrumento no definido',
    '2': 'Crédito ACH',
    '3': 'Débito ACH',
    '4': 'Reversión débito de demanda ACH',
    '5': 'Reversión crédito de demanda ACH',
    '6': 'Crédito de demanda ACH',
    '7': 'Débito de demanda ACH',
    '8': 'Mantener',
    '9': 'Clearing Nacional o Regional',
    '10': 'Efectivo',
    '11': 'Reversión Crédito Ahorro',
    '12': 'Reversión Débito Ahorro',
    '13': 'Crédito Ahorro',
    '14': 'Débito Ahorro',
    '15': 'Bookentry Crédito',
    '16': 'Bookentry Débito',
    '17': 'Crédito Interbancario',
    '18': 'Débito Interbancario',
    '19': 'Crédito SWIFT',
    '20': 'Débito SWIFT',
    '21': 'Crédito Fedwire',
    '22': 'Débito Fedwire',
    '23': 'Transferencia Crédito BACS',
    '24': 'Transferencia Débito BACS',
    '25': 'Crédito CHAPS',
    '26': 'Débito CHAPS',
    '27': 'Crédito Urgente BACS',
    '28': 'Débito Urgente BACS',
    '29': 'Crédito Urgente CHAPS',
    '30': 'Débito Urgente CHAPS',
    '31': 'Transferencia Crédito Interbancaria',
    '42': 'Tarjeta de Crédito',
    '47': 'Tarjeta Débito',
    '48': 'Consignación bancaria',
    '49': 'Tarjeta prepago',
}

# Formas de pago según DIAN
PAYMENT_FORMS = {
    '1': 'Contado',
    '2': 'Crédito',
    '3': 'Sin pago',  # Para documentos sin flujo de efectivo
}

# Medios de pago más comunes para talleres
COMMON_PAYMENT_METHODS = {
    '10': 'Efectivo',
    '42': 'Tarjeta de Crédito',
    '47': 'Tarjeta Débito',
    '48': 'Consignación bancaria',
    '31': 'Transferencia bancaria',
}


def get_payment_method_name(code: str) -> str:
    """
    Obtiene el nombre del medio de pago según código DIAN.
    
    Args:
        code: Código DIAN del medio de pago
    
    Returns:
        str: Nombre del medio de pago
    """
    return PAYMENT_METHODS.get(code, 'Desconocido')


def get_payment_form_name(code: str) -> str:
    """
    Obtiene el nombre de la forma de pago según código DIAN.
    
    Args:
        code: Código DIAN de la forma de pago
    
    Returns:
        str: Nombre de la forma de pago
    """
    return PAYMENT_FORMS.get(code, 'Desconocido')


def validate_payment_method(code: str) -> bool:
    """
    Valida que un código de medio de pago sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in PAYMENT_METHODS


def validate_payment_form(code: str) -> bool:
    """
    Valida que un código de forma de pago sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in PAYMENT_FORMS


# Mapeo de códigos internos a códigos DIAN
INTERNAL_TO_DIAN_PAYMENT = {
    'cash': '10',        # Efectivo
    'card': '42',        # Tarjeta de crédito
    'debit_card': '47',  # Tarjeta débito
    'transfer': '31',    # Transferencia
    'check': '20',       # Cheque (débito SWIFT)
    'other': '1',        # No definido
}


def convert_internal_payment_to_dian(internal_code: str) -> str:
    """
    Convierte código interno de pago a código DIAN.
    
    Args:
        internal_code: Código interno (cash, card, etc.)
    
    Returns:
        str: Código DIAN correspondiente
    """
    return INTERNAL_TO_DIAN_PAYMENT.get(internal_code, '10')  # Default: Efectivo
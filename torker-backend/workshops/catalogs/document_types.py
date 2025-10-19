"""
Catálogo de Tipos de Documento de Identificación Fiscal - DIAN
Basado en lista oficial TipoIdFiscal-2.1.gc
"""

# Tipos de documento según DIAN
DOCUMENT_TYPES = {
    '11': 'Registro civil',
    '12': 'Tarjeta de identidad',
    '13': 'Cédula de ciudadanía',
    '21': 'Tarjeta de extranjería',
    '22': 'Cédula de extranjería',
    '31': 'NIT',
    '41': 'Pasaporte',
    '42': 'Documento de identificación extranjero',
    '47': 'PEP (Permiso Especial de Permanencia)',
    '50': 'NIT de otro país',
    '91': 'NUIP (Número Único de Identificación Personal)',
}

# Mapeo de códigos internos a códigos DIAN
INTERNAL_TO_DIAN = {
    'cc': '13',  # Cédula de ciudadanía
    'ce': '22',  # Cédula de extranjería
    'nit': '31',  # NIT
    'ti': '12',  # Tarjeta de identidad
    'pasaporte': '41',  # Pasaporte
    'other': '42',  # Documento extranjero
}

# Mapeo inverso
DIAN_TO_INTERNAL = {v: k for k, v in INTERNAL_TO_DIAN.items()}


def get_document_type_name(code: str) -> str:
    """
    Obtiene el nombre del tipo de documento según código DIAN.
    
    Args:
        code: Código DIAN del tipo de documento
    
    Returns:
        str: Nombre del tipo de documento
    """
    return DOCUMENT_TYPES.get(code, 'Desconocido')


def validate_document_type(code: str) -> bool:
    """
    Valida que un código de tipo de documento sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in DOCUMENT_TYPES


def convert_internal_to_dian(internal_code: str) -> str:
    """
    Convierte código interno a código DIAN.
    
    Args:
        internal_code: Código interno (cc, ce, nit, etc.)
    
    Returns:
        str: Código DIAN correspondiente
    """
    return INTERNAL_TO_DIAN.get(internal_code, '42')


def convert_dian_to_internal(dian_code: str) -> str:
    """
    Convierte código DIAN a código interno.
    
    Args:
        dian_code: Código DIAN
    
    Returns:
        str: Código interno correspondiente
    """
    return DIAN_TO_INTERNAL.get(dian_code, 'other')
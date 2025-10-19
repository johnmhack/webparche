"""
Catálogo de Responsabilidades Fiscales - DIAN
Basado en lista oficial TipoResponsabilidad-2.1.gc
"""

# Responsabilidades fiscales según DIAN
TAX_RESPONSIBILITIES = {
    'O-13': 'Gran contribuyente',
    'O-15': 'Autorretenedor',
    'O-23': 'Agente de retención IVA',
    'O-47': 'Régimen simple de tributación - SIMPLE',
    'R-99-PN': 'No responsable de IVA',
    'O-07': 'Retenedor de IVA',
    'O-08': 'Régimen común',
    'O-09': 'Responsable del impuesto sobre las ventas - IVA',
    'O-10': 'Responsable del impuesto al consumo',
    'O-11': 'Agente retenedor en la fuente',
    'O-12': 'Informante de exógena',
    'O-14': 'Informante de ingresos y patrimonio',
    'O-16': 'Obligado a facturar electrónicamente',
    'O-17': 'Productor de bienes y/o servicios exentos',
    'O-18': 'Productor de bienes y/o servicios excluidos',
    'O-19': 'Responsable del impuesto nacional a la gasolina y al ACPM',
    'O-20': 'Responsable del impuesto nacional al carbono',
    'O-21': 'Responsable del impuesto nacional al consumo de bolsas plásticas',
    'O-22': 'Obligado a llevar contabilidad',
    'O-24': 'Declarante de renta',
    'O-25': 'Declarante de ingresos y patrimonio',
    'O-26': 'Declarante de activos en el exterior',
    'O-27': 'Declarante de precios de transferencia',
    'O-28': 'Declarante de información exógena',
    'O-29': 'Declarante de información país por país',
    'O-30': 'Declarante de información de beneficiarios finales',
    'O-31': 'Declarante de información de operaciones con vinculados',
    'O-32': 'Declarante de información de operaciones con paraísos fiscales',
    'O-33': 'Declarante de información de operaciones con zonas francas',
    'O-34': 'Declarante de información de operaciones con usuarios de zonas francas',
    'O-35': 'Declarante de información de operaciones con usuarios industriales de bienes exentos',
    'O-36': 'Declarante de información de operaciones con usuarios industriales de servicios exentos',
    'O-37': 'Declarante de información de operaciones con usuarios de servicios excluidos',
    'O-38': 'Declarante de información de operaciones con usuarios de bienes excluidos',
    'O-39': 'Declarante de información de operaciones con usuarios de servicios gravados',
    'O-40': 'Declarante de información de operaciones con usuarios de bienes gravados',
    'O-41': 'Declarante de información de operaciones con usuarios de servicios no gravados',
    'O-42': 'Declarante de información de operaciones con usuarios de bienes no gravados',
    'O-43': 'Declarante de información de operaciones con usuarios de servicios exentos del IVA',
    'O-44': 'Declarante de información de operaciones con usuarios de bienes exentos del IVA',
    'O-45': 'Declarante de información de operaciones con usuarios de servicios excluidos del IVA',
    'O-46': 'Declarante de información de operaciones con usuarios de bienes excluidos del IVA',
    'O-48': 'Impuesto sobre las ventas - IVA',
    'O-49': 'No responsable del IVA',
}

# Responsabilidades más comunes para talleres mecánicos
COMMON_WORKSHOP_RESPONSIBILITIES = [
    'O-08',  # Régimen común
    'O-09',  # Responsable de IVA
    'O-11',  # Agente retenedor en la fuente
    'O-13',  # Gran contribuyente (opcional)
    'O-15',  # Autorretenedor (opcional)
    'O-16',  # Obligado a facturar electrónicamente
    'O-22',  # Obligado a llevar contabilidad
    'O-23',  # Agente de retención IVA (opcional)
]


def get_responsibility_name(code: str) -> str:
    """
    Obtiene el nombre de la responsabilidad fiscal según código DIAN.
    
    Args:
        code: Código DIAN de la responsabilidad
    
    Returns:
        str: Nombre de la responsabilidad
    """
    return TAX_RESPONSIBILITIES.get(code, 'Desconocido')


def validate_responsibility(code: str) -> bool:
    """
    Valida que un código de responsabilidad fiscal sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in TAX_RESPONSIBILITIES


def get_common_responsibilities() -> list:
    """
    Obtiene las responsabilidades fiscales más comunes para talleres.
    
    Returns:
        list: Lista de códigos de responsabilidades comunes
    """
    return COMMON_WORKSHOP_RESPONSIBILITIES.copy()


def is_iva_responsible(responsibilities: list) -> bool:
    """
    Verifica si el contribuyente es responsable de IVA.
    
    Args:
        responsibilities: Lista de códigos de responsabilidades
    
    Returns:
        bool: True si es responsable de IVA
    """
    return 'O-09' in responsibilities or 'O-48' in responsibilities


def is_gran_contribuyente(responsibilities: list) -> bool:
    """
    Verifica si el contribuyente es gran contribuyente.
    
    Args:
        responsibilities: Lista de códigos de responsabilidades
    
    Returns:
        bool: True si es gran contribuyente
    """
    return 'O-13' in responsibilities


def is_autorretenedor(responsibilities: list) -> bool:
    """
    Verifica si el contribuyente es autorretenedor.
    
    Args:
        responsibilities: Lista de códigos de responsabilidades
    
    Returns:
        bool: True si es autorretenedor
    """
    return 'O-15' in responsibilities
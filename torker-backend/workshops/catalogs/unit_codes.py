"""
Catálogo de Unidades de Medida - DIAN
Basado en lista oficial UnidadesMedida-2.1.gc
Códigos según UN/ECE Recommendation 20
"""

# Unidades de medida más comunes para talleres mecánicos
UNIT_CODES = {
    # Unidades de cantidad
    'NIU': 'Número de artículos',
    'EA': 'Elemento',
    'SET': 'Conjunto',
    'PR': 'Par',
    'DZN': 'Docena',
    
    # Unidades de tiempo
    'HUR': 'Hora',
    'E48': 'Unidad de servicio',
    'MIN': 'Minuto',
    'DAY': 'Día',
    'WEE': 'Semana',
    'MON': 'Mes',
    
    # Unidades de longitud
    'MTR': 'Metro',
    'CMT': 'Centímetro',
    'MMT': 'Milímetro',
    'KMT': 'Kilómetro',
    'INH': 'Pulgada',
    'FOT': 'Pie',
    
    # Unidades de peso
    'KGM': 'Kilogramo',
    'GRM': 'Gramo',
    'MGM': 'Miligramo',
    'TNE': 'Tonelada métrica',
    'LBR': 'Libra',
    'ONZ': 'Onza',
    
    # Unidades de volumen
    'LTR': 'Litro',
    'MLT': 'Mililitro',
    'GLI': 'Galón (UK)',
    'GLL': 'Galón (US)',
    'MTQ': 'Metro cúbico',
    'CMQ': 'Centímetro cúbico',
    
    # Unidades de área
    'MTK': 'Metro cuadrado',
    'CMK': 'Centímetro cuadrado',
    
    # Unidades eléctricas
    'KWT': 'Kilovatio',
    'WHR': 'Vatio hora',
    'KWH': 'Kilovatio hora',
    'AMP': 'Amperio',
    'VLT': 'Voltio',
    
    # Otras unidades
    'ACT': 'Actividad',
    'KT': 'Kit',
    'CA': 'Lata',
    'BX': 'Caja',
    'PK': 'Paquete',
    'BG': 'Bolsa',
    'BO': 'Botella',
    'TU': 'Tubo',
    'RO': 'Rollo',
}

# Unidades más usadas en talleres mecánicos
COMMON_WORKSHOP_UNITS = {
    'NIU': 'Número de artículos',  # Repuestos, piezas
    'E48': 'Unidad de servicio',   # Servicios, mano de obra
    'HUR': 'Hora',                  # Horas de trabajo
    'LTR': 'Litro',                 # Aceites, líquidos
    'SET': 'Conjunto',              # Kits de repuestos
    'MTR': 'Metro',                 # Cables, mangueras
    'KGM': 'Kilogramo',             # Pesos
}


def get_unit_name(code: str) -> str:
    """
    Obtiene el nombre de la unidad de medida según código DIAN.
    
    Args:
        code: Código de unidad de medida
    
    Returns:
        str: Nombre de la unidad
    """
    return UNIT_CODES.get(code, 'Desconocido')


def validate_unit_code(code: str) -> bool:
    """
    Valida que un código de unidad de medida sea válido según DIAN.
    
    Args:
        code: Código a validar
    
    Returns:
        bool: True si es válido
    """
    return code in UNIT_CODES


def get_common_units() -> dict:
    """
    Obtiene las unidades más comunes para talleres mecánicos.
    
    Returns:
        dict: Diccionario de unidades comunes
    """
    return COMMON_WORKSHOP_UNITS.copy()
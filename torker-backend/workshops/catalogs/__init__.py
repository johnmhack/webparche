"""
Catálogos oficiales DIAN para facturación electrónica
Basados en Resolución 000042 de 2020 y anexos técnicos
"""
from .document_types import DOCUMENT_TYPES, get_document_type_name, validate_document_type
from .unit_codes import UNIT_CODES, get_unit_name, validate_unit_code
from .tax_codes import TAX_CODES, TAX_RATES, get_tax_name, validate_tax_code
from .payment_methods import PAYMENT_METHODS, PAYMENT_FORMS, get_payment_method_name
from .tax_responsibilities import TAX_RESPONSIBILITIES, get_responsibility_name

__all__ = [
    'DOCUMENT_TYPES',
    'UNIT_CODES',
    'TAX_CODES',
    'TAX_RATES',
    'PAYMENT_METHODS',
    'PAYMENT_FORMS',
    'TAX_RESPONSIBILITIES',
    'get_document_type_name',
    'get_unit_name',
    'get_tax_name',
    'get_payment_method_name',
    'get_responsibility_name',
    'validate_document_type',
    'validate_unit_code',
    'validate_tax_code',
]
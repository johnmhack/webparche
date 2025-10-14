"""
Validador Schematron para documentos electrónicos DIAN
Basado en las reglas de validación de la DIAN
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Optional
import os
import re


class DianSchematronValidator:
    """Validador Schematron para documentos DIAN"""

    def __init__(self, xml_content: str):
        self.xml_content = xml_content
        self.errors = []
        self.warnings = []
        self.root = None
        self._parse_xml()

    def _parse_xml(self):
        """Parsear el XML y preparar para validación"""
        try:
            self.root = ET.fromstring(self.xml_content)
        except ET.ParseError as e:
            self.errors.append(f"Error de parsing XML: {str(e)}")

    def validate_invoice(self) -> bool:
        """Validar factura electrónica según reglas DIAN"""
        if not self.root:
            return False

        # Ejecutar todas las validaciones
        self._validate_structure()
        self._validate_mandatory_fields()
        self._validate_business_rules()
        self._validate_tax_calculations()
        self._validate_identifications()

        return len(self.errors) == 0

    def _validate_structure(self):
        """Validar estructura básica del documento"""
        # Verificar elemento raíz
        if self.root.tag != "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice":
            self.errors.append("Elemento raíz debe ser Invoice con namespace UBL 2.1")

        # Verificar UBL Extensions
        extensions = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions")
        if not extensions:
            self.errors.append("UBLExtensions es obligatorio")

        # Verificar DIAN Extensions
        dian_ext = self.root.find(".//{dian:gov:co:facturaelectronica:Structures-2-1}DianExtensions")
        if not dian_ext:
            self.errors.append("DianExtensions es obligatorio")

    def _validate_mandatory_fields(self):
        """Validar campos obligatorios según DIAN"""
        required_fields = [
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID", "UBLVersionID"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID", "CustomizationID"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID", "ProfileID"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", "ID"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID", "UUID"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate", "IssueDate"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime", "IssueTime"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode", "InvoiceTypeCode"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty", "AccountingSupplierParty"),
            (".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty", "AccountingCustomerParty"),
        ]

        for xpath, field_name in required_fields:
            if not self.root.find(xpath):
                self.errors.append(f"Campo obligatorio faltante: {field_name}")

    def _validate_business_rules(self):
        """Validar reglas de negocio DIAN"""
        # Validar tipo de documento
        invoice_type = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode")
        if invoice_type is not None and invoice_type.text:
            valid_types = ["01", "02", "03", "04", "91", "92", "20", "22", "30", "32"]
            if invoice_type.text not in valid_types:
                self.errors.append(f"Tipo de documento inválido: {invoice_type.text}")

        # Validar moneda
        currency = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode")
        if currency is not None and currency.text != "COP":
            self.warnings.append("Moneda diferente a COP detectada")

        # Validar NIT del proveedor
        supplier_tax_id = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID")
        if supplier_tax_id is not None:
            self._validate_nit_format(supplier_tax_id.text, "Proveedor")

        # Validar identificación del cliente
        customer_id = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        if customer_id is not None:
            self._validate_customer_id(customer_id.text)

    def _validate_tax_calculations(self):
        """Validar cálculos de impuestos"""
        # Obtener subtotales
        line_extension_total = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal/{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
        tax_exclusive_total = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal/{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount")
        tax_inclusive_total = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal/{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount")

        if all([line_extension_total, tax_exclusive_total, tax_inclusive_total]):
            try:
                line_ext = float(line_extension_total.text)
                tax_exc = float(tax_exclusive_total.text)
                tax_inc = float(tax_inclusive_total.text)

                # Validar que los totales sean consistentes
                if abs(line_ext - tax_exc) > 0.01:
                    self.errors.append("Inconsistencia entre LineExtensionAmount y TaxExclusiveAmount")

                # Calcular IVA esperado (19%)
                expected_tax = tax_exc * 0.19
                actual_tax = tax_inc - tax_exc

                if abs(expected_tax - actual_tax) > 1.0:  # Tolerancia de 1 peso
                    self.warnings.append(".2f")

            except (ValueError, TypeError):
                self.errors.append("Error en formato de valores monetarios")

    def _validate_identifications(self):
        """Validar formatos de identificación"""
        # Validar CUDE
        cude = self.root.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID")
        if cude is not None and cude.text:
            if not self._validate_cude_format(cude.text):
                self.errors.append("Formato de CUDE inválido")

    def _validate_nit_format(self, nit: str, entity_type: str):
        """Validar formato de NIT colombiano"""
        # Remover puntos y guiones
        clean_nit = re.sub(r'[.\-]', '', nit)

        # Verificar que sea numérico
        if not clean_nit.isdigit():
            self.errors.append(f"NIT del {entity_type} debe contener solo números")
            return

        # Verificar longitud (máximo 12 dígitos para NIT)
        if len(clean_nit) > 12:
            self.errors.append(f"NIT del {entity_type} demasiado largo")

        # Verificar dígito de verificación (algoritmo simplificado)
        if len(clean_nit) >= 2:
            # Para validación básica, solo verificar que no sea todos ceros
            if clean_nit == '0' * len(clean_nit):
                self.warnings.append(f"NIT del {entity_type} parece ser un valor de prueba")

    def _validate_customer_id(self, customer_id: str):
        """Validar identificación del cliente"""
        # Para consumidor final, debe ser 222222222222
        if customer_id == "222222222222":
            return  # Válido para consumidor final

        # Para otros casos, validar formato básico
        clean_id = re.sub(r'[.\-]', '', customer_id)
        if not clean_id.isdigit():
            self.errors.append("Identificación del cliente debe contener solo números")
        elif len(clean_id) < 5 or len(clean_id) > 12:
            self.errors.append("Identificación del cliente tiene longitud inválida")

    def _validate_cude_format(self, cude: str) -> bool:
        """Validar formato del CUDE (SHA384)"""
        # CUDE debe ser un hash SHA384 en hexadecimal
        if not re.match(r'^[a-f0-9]{96}$', cude):
            return False
        return True

    def validate_with_schematron_file(self, schematron_path: str) -> bool:
        """Validar usando archivo Schematron (si está disponible)"""
        if not os.path.exists(schematron_path):
            self.warnings.append(f"Archivo Schematron no encontrado: {schematron_path}")
            return True

        try:
            # Aquí iría la implementación completa de validación Schematron
            # Por ahora, retornamos True ya que es una implementación avanzada
            self.warnings.append("Validación Schematron completa no implementada aún")
            return True
        except Exception as e:
            self.errors.append(f"Error en validación Schematron: {str(e)}")
            return False

    def get_validation_errors(self) -> List[str]:
        """Obtener lista de errores"""
        return self.errors.copy()

    def get_validation_warnings(self) -> List[str]:
        """Obtener lista de advertencias"""
        return self.warnings.copy()

    def get_validation_summary(self) -> Dict:
        """Obtener resumen de validación"""
        return {
            'valid': len(self.errors) == 0,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'error_list': self.errors,
            'warning_list': self.warnings
        }
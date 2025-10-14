"""
Generador de XML para Facturación Electrónica DIAN
Basado en estándares UBL 2.1 y especificaciones DIAN
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
import hashlib
import uuid
from decimal import Decimal
from typing import Dict, List, Optional
from .models import ElectronicInvoice, ElectronicInvoiceDetail, DianConfiguration


class DianXmlGenerator:
    """Generador de XML para documentos electrónicos DIAN"""

    # Namespaces UBL 2.1
    NSMAP = {
        'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        'ds': "http://www.w3.org/2000/09/xmldsig#",
        'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        'sts': "dian:gov:co:facturaelectronica:Structures-2-1",
        'xades': "http://uri.etsi.org/01903/v1.3.2#",
        'xades141': "http://uri.etsi.org/01903/v1.4.1#",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }

    def __init__(self, electronic_invoice: ElectronicInvoice):
        self.invoice = electronic_invoice
        self.config = electronic_invoice.workshop.dian_config
        self.root = None
        self._build_xml()

    def _build_xml(self):
        """Construir la estructura XML completa"""
        # Crear elemento raíz con namespace por defecto
        self.root = ET.Element("{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice")

        # Agregar atributos de namespace
        self.root.set("{http://www.w3.org/2000/xmlns/}cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
        self.root.set("{http://www.w3.org/2000/xmlns/}cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
        self.root.set("{http://www.w3.org/2000/xmlns/}ds", "http://www.w3.org/2000/09/xmldsig#")
        self.root.set("{http://www.w3.org/2000/xmlns/}ext", "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")
        self.root.set("{http://www.w3.org/2000/xmlns/}sts", "dian:gov:co:facturaelectronica:Structures-2-1")
        self.root.set("{http://www.w3.org/2000/xmlns/}xades", "http://uri.etsi.org/01903/v1.3.2#")
        self.root.set("{http://www.w3.org/2000/xmlns/}xades141", "http://uri.etsi.org/01903/v1.4.1#")
        self.root.set("{http://www.w3.org/2000/xmlns/}xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self.root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                     "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd")

        # Agregar schema location
        self.root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                     "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
                     "http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd")

        # Construir secciones
        self._add_ubl_extensions()
        self._add_ubl_version()
        self._add_customization_id()
        self._add_profile_info()
        self._add_id_and_uuid()
        self._add_issue_info()
        self._add_invoice_type()
        self._add_notes()
        self._add_currency()
        self._add_line_count()
        self._add_supplier_party()
        self._add_customer_party()
        self._add_payment_means()
        self._add_tax_totals()
        self._add_legal_monetary_total()
        self._add_invoice_lines()

    def _add_ubl_extensions(self):
        """Agregar extensiones UBL con información DIAN"""
        extensions = ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions")

        # Extensión DIAN
        extension = ET.SubElement(extensions, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension")
        content = ET.SubElement(extension, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent")
        dian_extensions = ET.SubElement(content, "{dian:gov:co:facturaelectronica:Structures-2-1}DianExtensions")

        # Invoice Control
        invoice_control = ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}InvoiceControl")
        ET.SubElement(invoice_control, "{dian:gov:co:facturaelectronica:Structures-2-1}InvoiceAuthorization").text = str(self.invoice.dian_resolution.resolution_number)
        ET.SubElement(invoice_control, "{dian:gov:co:facturaelectronica:Structures-2-1}AuthorizationPeriod")
        ET.SubElement(invoice_control, "{dian:gov:co:facturaelectronica:Structures-2-1}AuthorizedInvoices")

        # Invoice Source
        invoice_source = ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}InvoiceSource")
        ET.SubElement(invoice_source, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode",
                     listAgencyID="6",
                     listAgencyName="United Nations Economic Commission for Europe",
                     listSchemeURI="urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1").text = "CO"

        # Software Provider
        software_provider = ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}SoftwareProvider")
        ET.SubElement(software_provider, "{dian:gov:co:facturaelectronica:Structures-2-1}ProviderID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeID="1",
                     schemeName="31").text = self.invoice.workshop.nit or "2022516216"
        ET.SubElement(software_provider, "{dian:gov:co:facturaelectronica:Structures-2-1}SoftwareID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)").text = self.config.software_id

        # Software Security Code
        ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}SoftwareSecurityCode",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)").text = self.config.software_security_code

        # Authorization Provider
        auth_provider = ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}AuthorizationProvider")
        ET.SubElement(auth_provider, "{dian:gov:co:facturaelectronica:Structures-2-1}AuthorizationProviderID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeID="4",
                     schemeName="31").text = "800197268"

        # QR Code (placeholder)
        ET.SubElement(dian_extensions, "{dian:gov:co:facturaelectronica:Structures-2-1}QRCode").text = self._generate_qr_placeholder()

    def _add_ubl_version(self):
        """Versión UBL"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID").text = "UBL 2.1"

    def _add_customization_id(self):
        """ID de personalización"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID").text = "10"

    def _add_profile_info(self):
        """Información de perfil DIAN"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID").text = "DIAN 2.1: Documento Equivalente Electrónico"
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileExecutionID").text = "2"

    def _add_id_and_uuid(self):
        """ID de factura y UUID (CUDE)"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = self.invoice.invoice_number
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeID="2",
                     schemeName="CUDE-SHA384").text = self.invoice.cude

    def _add_issue_info(self):
        """Información de emisión"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate").text = self.invoice.issue_date.strftime("%Y-%m-%d")
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime").text = self.invoice.issue_time.strftime("%H:%M:%S-05:00")

        if self.invoice.due_date:
            ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DueDate").text = self.invoice.due_date.strftime("%Y-%m-%d")

    def _add_invoice_type(self):
        """Tipo de documento"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode", name="Factura Electrónica").text = "01"

    def _add_notes(self):
        """Notas de la factura"""
        # Nota técnica DIAN
        note_text = f"DPE001{self.invoice.issue_date.strftime('%Y-%m-%d%H:%M:%S-05:00')}{self.invoice.total:.2f}{self.invoice.subtotal:.2f}{self.invoice.tax_amount:.2f}{self.invoice.discount:.2f}{self.invoice.total:.2f}00374637222222222222222123452"
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Note").text = note_text

    def _add_currency(self):
        """Moneda del documento"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode").text = self.config.default_currency

    def _add_line_count(self):
        """Número de líneas"""
        ET.SubElement(self.root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineCountNumeric").text = str(self.invoice.details.count())

    def _add_supplier_party(self):
        """Información del proveedor (taller)"""
        supplier_party = ET.SubElement(self.root, "cac:AccountingSupplierParty")
        ET.SubElement(supplier_party, "cbc:AdditionalAccountID").text = "1"

        party = ET.SubElement(supplier_party, "cac:Party")

        # Industry Classification
        ET.SubElement(party, "cbc:IndustryClassificationCode").text = "453000"  # Comercio de motocicletas

        # Party Name
        party_name = ET.SubElement(party, "cac:PartyName")
        ET.SubElement(party_name, "cbc:Name").text = self.invoice.workshop_name

        # Physical Location
        physical_location = ET.SubElement(party, "cac:PhysicalLocation")
        address = ET.SubElement(physical_location, "cac:Address")
        ET.SubElement(address, "cbc:ID").text = "11001"  # Código postal Bogotá
        ET.SubElement(address, "cbc:CityName").text = self.invoice.workshop_city
        ET.SubElement(address, "cbc:PostalZone").text = "110111"
        ET.SubElement(address, "cbc:CountrySubentity").text = self.invoice.workshop_department
        ET.SubElement(address, "cbc:CountrySubentityCode").text = "11"  # Cundinamarca

        address_line = ET.SubElement(address, "cac:AddressLine")
        ET.SubElement(address_line, "cbc:Line").text = self.invoice.workshop_address

        country = ET.SubElement(address, "cac:Country")
        ET.SubElement(country, "cbc:IdentificationCode").text = "CO"
        ET.SubElement(country, "cbc:Name", languageID="es").text = "Colombia"

        # Party Tax Scheme
        tax_scheme = ET.SubElement(party, "cac:PartyTaxScheme")
        ET.SubElement(tax_scheme, "cbc:RegistrationName").text = self.invoice.workshop_name
        ET.SubElement(tax_scheme, "cbc:CompanyID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeID="1",
                     schemeName="31").text = self.invoice.workshop_nit
        ET.SubElement(tax_scheme, "cbc:TaxLevelCode", listName="48").text = "O-99"  # No responsable

        registration_address = ET.SubElement(tax_scheme, "cac:RegistrationAddress")
        ET.SubElement(registration_address, "cbc:ID").text = "11001"
        ET.SubElement(registration_address, "cbc:CityName").text = self.invoice.workshop_city
        ET.SubElement(registration_address, "cbc:PostalZone").text = "110111"
        ET.SubElement(registration_address, "cbc:CountrySubentity").text = self.invoice.workshop_department
        ET.SubElement(registration_address, "cbc:CountrySubentityCode").text = "11"

        address_line_reg = ET.SubElement(registration_address, "cac:AddressLine")
        ET.SubElement(address_line_reg, "cbc:Line").text = self.invoice.workshop_address

        country_reg = ET.SubElement(registration_address, "cac:Country")
        ET.SubElement(country_reg, "cbc:IdentificationCode").text = "CO"
        ET.SubElement(country_reg, "cbc:Name", languageID="es").text = "Colombia"

        tax_scheme_ref = ET.SubElement(tax_scheme, "cac:TaxScheme")
        ET.SubElement(tax_scheme_ref, "cbc:ID").text = "01"
        ET.SubElement(tax_scheme_ref, "cbc:Name").text = "IVA"

        # Party Legal Entity
        legal_entity = ET.SubElement(party, "cac:PartyLegalEntity")
        ET.SubElement(legal_entity, "cbc:RegistrationName").text = self.invoice.workshop_name
        ET.SubElement(legal_entity, "cbc:CompanyID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeID="1",
                     schemeName="31").text = self.invoice.workshop_nit

        corporate_scheme = ET.SubElement(legal_entity, "cac:CorporateRegistrationScheme")
        ET.SubElement(corporate_scheme, "cbc:ID").text = self.invoice.dian_resolution.prefix

        # Contact
        contact = ET.SubElement(party, "cac:Contact")
        if self.invoice.workshop_phone:
            ET.SubElement(contact, "cbc:Telephone").text = self.invoice.workshop_phone
        if self.invoice.workshop_email:
            ET.SubElement(contact, "cbc:ElectronicMail").text = self.invoice.workshop_email

    def _add_customer_party(self):
        """Información del cliente"""
        customer_party = ET.SubElement(self.root, "cac:AccountingCustomerParty")
        ET.SubElement(customer_party, "cbc:AdditionalAccountID").text = "2"

        party = ET.SubElement(customer_party, "cac:Party")

        # Party Identification
        party_identification = ET.SubElement(party, "cac:PartyIdentification")
        ET.SubElement(party_identification, "cbc:ID",
                     schemeID=self.invoice.customer_document_type,
                     schemeName="13",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)").text = self.invoice.customer_document

        # Party Name
        party_name = ET.SubElement(party, "cac:PartyName")
        ET.SubElement(party_name, "cbc:Name").text = self.invoice.customer_name

        # Physical Location (si hay dirección)
        if self.invoice.customer_address:
            physical_location = ET.SubElement(party, "cac:PhysicalLocation")
            address = ET.SubElement(physical_location, "cac:Address")
            ET.SubElement(address, "cbc:ID").text = "11001"
            ET.SubElement(address, "cbc:CityName").text = self.invoice.customer_city or "Bogotá, D.C."
            ET.SubElement(address, "cbc:CountrySubentity").text = self.invoice.customer_department or "Bogotá"
            ET.SubElement(address, "cbc:CountrySubentityCode").text = "11"

            address_line = ET.SubElement(address, "cac:AddressLine")
            ET.SubElement(address_line, "cbc:Line").text = self.invoice.customer_address

            country = ET.SubElement(address, "cac:Country")
            ET.SubElement(country, "cbc:IdentificationCode").text = "CO"
            ET.SubElement(country, "cbc:Name", languageID="es").text = "Colombia"

        # Party Tax Scheme
        tax_scheme = ET.SubElement(party, "cac:PartyTaxScheme")
        ET.SubElement(tax_scheme, "cbc:RegistrationName").text = self.invoice.customer_name
        ET.SubElement(tax_scheme, "cbc:CompanyID",
                     schemeAgencyID="195",
                     schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                     schemeName="13").text = self.invoice.customer_document

        tax_scheme_ref = ET.SubElement(tax_scheme, "cac:TaxScheme")
        ET.SubElement(tax_scheme_ref, "cbc:ID").text = "01"
        ET.SubElement(tax_scheme_ref, "cbc:Name").text = "IVA"

        # Party Legal Entity (solo si es empresa)
        if self.invoice.customer_document_type in ['nit']:
            legal_entity = ET.SubElement(party, "cac:PartyLegalEntity")
            ET.SubElement(legal_entity, "cbc:RegistrationName").text = self.invoice.customer_name
            ET.SubElement(legal_entity, "cbc:CompanyID",
                         schemeAgencyID="195",
                         schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
                         schemeName="13").text = self.invoice.customer_document

        # Contact (si hay información)
        if self.invoice.customer_phone or self.invoice.customer_email:
            contact = ET.SubElement(party, "cac:Contact")
            if self.invoice.customer_phone:
                ET.SubElement(contact, "cbc:Telephone").text = self.invoice.customer_phone
            if self.invoice.customer_email:
                ET.SubElement(contact, "cbc:ElectronicMail").text = self.invoice.customer_email

    def _add_payment_means(self):
        """Medios de pago"""
        payment_means = ET.SubElement(self.root, "cac:PaymentMeans")
        ET.SubElement(payment_means, "cbc:ID").text = "1"
        ET.SubElement(payment_means, "cbc:PaymentMeansCode").text = "10"  # Efectivo

        if self.invoice.due_date:
            ET.SubElement(payment_means, "cbc:PaymentDueDate").text = self.invoice.due_date.strftime("%Y-%m-%d")

    def _add_tax_totals(self):
        """Totales de impuestos"""
        # IVA
        tax_total = ET.SubElement(self.root, "cac:TaxTotal")
        ET.SubElement(tax_total, "cbc:TaxAmount", currencyID="COP").text = f"{self.invoice.tax_amount:.2f}"

        tax_subtotal = ET.SubElement(tax_total, "cac:TaxSubtotal")
        ET.SubElement(tax_subtotal, "cbc:TaxableAmount", currencyID="COP").text = f"{self.invoice.subtotal:.2f}"
        ET.SubElement(tax_subtotal, "cbc:TaxAmount", currencyID="COP").text = f"{self.invoice.tax_amount:.2f}"

        tax_category = ET.SubElement(tax_subtotal, "cac:TaxCategory")
        ET.SubElement(tax_category, "cbc:Percent").text = "19.00"

        tax_scheme = ET.SubElement(tax_category, "cac:TaxScheme")
        ET.SubElement(tax_scheme, "cbc:ID").text = "01"
        ET.SubElement(tax_scheme, "cbc:Name").text = "IVA"

    def _add_legal_monetary_total(self):
        """Totales monetarios"""
        legal_total = ET.SubElement(self.root, "cac:LegalMonetaryTotal")
        ET.SubElement(legal_total, "cbc:LineExtensionAmount", currencyID="COP").text = f"{self.invoice.subtotal:.2f}"
        ET.SubElement(legal_total, "cbc:TaxExclusiveAmount", currencyID="COP").text = f"{self.invoice.subtotal:.2f}"
        ET.SubElement(legal_total, "cbc:TaxInclusiveAmount", currencyID="COP").text = f"{self.invoice.total:.2f}"
        ET.SubElement(legal_total, "cbc:PayableAmount", currencyID="COP").text = f"{self.invoice.total:.2f}"

    def _add_invoice_lines(self):
        """Líneas de la factura"""
        for detail in self.invoice.details.all():
            invoice_line = ET.SubElement(self.root, "cac:InvoiceLine")
            ET.SubElement(invoice_line, "cbc:ID").text = str(detail.id)
            ET.SubElement(invoice_line, "cbc:InvoicedQuantity", unitCode="NIU").text = f"{detail.quantity:.2f}"
            ET.SubElement(invoice_line, "cbc:LineExtensionAmount", currencyID="COP").text = f"{detail.subtotal:.2f}"
            ET.SubElement(invoice_line, "cbc:FreeOfChargeIndicator").text = "false"

            # Tax Total
            tax_total = ET.SubElement(invoice_line, "cac:TaxTotal")
            ET.SubElement(tax_total, "cbc:TaxAmount", currencyID="COP").text = f"{detail.tax_amount:.2f}"

            tax_subtotal = ET.SubElement(tax_total, "cac:TaxSubtotal")
            ET.SubElement(tax_subtotal, "cbc:TaxableAmount", currencyID="COP").text = f"{detail.subtotal:.2f}"
            ET.SubElement(tax_subtotal, "cbc:TaxAmount", currencyID="COP").text = f"{detail.tax_amount:.2f}"

            tax_category = ET.SubElement(tax_subtotal, "cac:TaxCategory")
            ET.SubElement(tax_category, "cbc:Percent").text = f"{detail.tax_rate:.2f}"

            tax_scheme = ET.SubElement(tax_category, "cac:TaxScheme")
            ET.SubElement(tax_scheme, "cbc:ID").text = "01"
            ET.SubElement(tax_scheme, "cbc:Name").text = "IVA"

            # Item
            item = ET.SubElement(invoice_line, "cac:Item")
            ET.SubElement(item, "cbc:Description").text = detail.description

            if detail.brand_name:
                ET.SubElement(item, "cbc:BrandName").text = detail.brand_name
            if detail.model_name:
                ET.SubElement(item, "cbc:ModelName").text = detail.model_name

            # Standard Item Identification
            if detail.part_number:
                std_id = ET.SubElement(item, "cac:StandardItemIdentification")
                ET.SubElement(std_id, "cbc:ID", schemeID="999", schemeName="EAN13").text = detail.part_number

            # Price
            price = ET.SubElement(invoice_line, "cac:Price")
            ET.SubElement(price, "cbc:PriceAmount", currencyID="COP").text = f"{detail.unit_price:.2f}"
            ET.SubElement(price, "cbc:BaseQuantity", unitCode="NIU").text = "1.00"

    def _generate_qr_placeholder(self) -> str:
        """Generar placeholder para código QR"""
        # En producción, esto sería generado por DIAN
        return f"https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={self.invoice.cude}"

    def get_xml_string(self, pretty_print: bool = True) -> str:
        """Obtener XML como string"""
        # Crear XML manualmente para tener control total sobre namespaces
        xml_parts = []

        # Declaración XML
        xml_parts.append('<?xml version="1.0" encoding="utf-8" standalone="no"?>')

        # Elemento raíz con namespaces
        root_attrs = []
        root_attrs.append('xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"')
        root_attrs.append('xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"')
        root_attrs.append('xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"')
        root_attrs.append('xmlns:ds="http://www.w3.org/2000/09/xmldsig#"')
        root_attrs.append('xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"')
        root_attrs.append('xmlns:sts="dian:gov:co:facturaelectronica:Structures-2-1"')
        root_attrs.append('xmlns:xades="http://uri.etsi.org/01903/v1.3.2#"')
        root_attrs.append('xmlns:xades141="http://uri.etsi.org/01903/v1.4.1#"')
        root_attrs.append('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
        root_attrs.append('xsi:schemaLocation="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd"')

        xml_parts.append(f'<Invoice {" ".join(root_attrs)}>')

        # Agregar extensiones UBL primero
        xml_parts.append('  <ext:UBLExtensions>')
        xml_parts.append('    <ext:UBLExtension>')
        xml_parts.append('      <ext:ExtensionContent>')
        xml_parts.append('        <sts:DianExtensions>')
        xml_parts.append('          <sts:InvoiceSource>')
        xml_parts.append('            <cbc:IdentificationCode listAgencyID="6" listAgencyName="United Nations Economic Commission for Europe" listSchemeURI="urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1">CO</cbc:IdentificationCode>')
        xml_parts.append('          </sts:InvoiceSource>')
        xml_parts.append('          <sts:SoftwareProvider>')
        xml_parts.append(f'            <sts:ProviderID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeID="1" schemeName="31">{self.invoice.workshop.nit or "2022516216"}</sts:ProviderID>')
        xml_parts.append(f'            <sts:SoftwareID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)">{self.config.software_id}</sts:SoftwareID>')
        xml_parts.append(f'            <sts:SoftwareSecurityCode schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)">{self.config.software_security_code}</sts:SoftwareSecurityCode>')
        xml_parts.append('            <sts:AuthorizationProvider>')
        xml_parts.append('              <sts:AuthorizationProviderID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeID="4" schemeName="31">800197268</sts:AuthorizationProviderID>')
        xml_parts.append('            </sts:AuthorizationProvider>')
        xml_parts.append(f'            <sts:QRCode>https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={self.invoice.cude}</sts:QRCode>')
        xml_parts.append('          </sts:SoftwareProvider>')
        xml_parts.append('        </sts:DianExtensions>')
        xml_parts.append('      </ext:ExtensionContent>')
        xml_parts.append('    </ext:UBLExtension>')
        xml_parts.append('  </ext:UBLExtensions>')

        # Agregar elementos principales después de las extensiones
        xml_parts.append('  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>')
        xml_parts.append('  <cbc:CustomizationID>10</cbc:CustomizationID>')
        xml_parts.append('  <cbc:ProfileID>DIAN 2.1: Documento Equivalente Electrónico</cbc:ProfileID>')
        xml_parts.append('  <cbc:ProfileExecutionID>2</cbc:ProfileExecutionID>')
        xml_parts.append(f'  <cbc:ID>{self.invoice.invoice_number}</cbc:ID>')
        xml_parts.append(f'  <cbc:UUID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeID="2" schemeName="CUDE-SHA384">{self.invoice.cude}</cbc:UUID>')
        xml_parts.append(f'  <cbc:IssueDate>{self.invoice.issue_date.strftime("%Y-%m-%d")}</cbc:IssueDate>')
        xml_parts.append(f'  <cbc:IssueTime>{self.invoice.issue_time.strftime("%H:%M:%S-05:00")}</cbc:IssueTime>')
        xml_parts.append('  <cbc:InvoiceTypeCode name="Factura Electrónica">01</cbc:InvoiceTypeCode>')
        xml_parts.append(f'  <cbc:Note>DPE001{self.invoice.issue_date.strftime("%Y-%m-%d%H:%M:%S-05:00")}{self.invoice.total:.2f}{self.invoice.subtotal:.2f}{self.invoice.tax_amount:.2f}{self.invoice.discount:.2f}{self.invoice.total:.2f}00374637222222222222222123452</cbc:Note>')
        xml_parts.append('  <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>')
        xml_parts.append(f'  <cbc:LineCountNumeric>{self.invoice.details.count()}</cbc:LineCountNumeric>')

        # Información del proveedor (taller)
        xml_parts.append('  <cac:AccountingSupplierParty>')
        xml_parts.append('    <cbc:AdditionalAccountID>1</cbc:AdditionalAccountID>')
        xml_parts.append('    <cac:Party>')
        xml_parts.append('      <cbc:IndustryClassificationCode>453000</cbc:IndustryClassificationCode>')
        xml_parts.append(f'      <cac:PartyName><cbc:Name>{self.invoice.workshop_name}</cbc:Name></cac:PartyName>')
        xml_parts.append('      <cac:PhysicalLocation>')
        xml_parts.append('        <cac:Address>')
        xml_parts.append('          <cbc:ID>11001</cbc:ID>')
        xml_parts.append(f'          <cbc:CityName>{self.invoice.workshop_city}</cbc:CityName>')
        xml_parts.append('          <cbc:PostalZone>110111</cbc:PostalZone>')
        xml_parts.append(f'          <cbc:CountrySubentity>{self.invoice.workshop_department}</cbc:CountrySubentity>')
        xml_parts.append('          <cbc:CountrySubentityCode>11</cbc:CountrySubentityCode>')
        xml_parts.append(f'          <cac:AddressLine><cbc:Line>{self.invoice.workshop_address}</cbc:Line></cac:AddressLine>')
        xml_parts.append('          <cac:Country>')
        xml_parts.append('            <cbc:IdentificationCode>CO</cbc:IdentificationCode>')
        xml_parts.append('            <cbc:Name languageID="es">Colombia</cbc:Name>')
        xml_parts.append('          </cac:Country>')
        xml_parts.append('        </cac:Address>')
        xml_parts.append('      </cac:PhysicalLocation>')
        xml_parts.append('      <cac:PartyTaxScheme>')
        xml_parts.append(f'        <cbc:RegistrationName>{self.invoice.workshop_name}</cbc:RegistrationName>')
        xml_parts.append(f'        <cbc:CompanyID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeID="1" schemeName="31">{self.invoice.workshop_nit}</cbc:CompanyID>')
        xml_parts.append('        <cbc:TaxLevelCode listName="48">O-99</cbc:TaxLevelCode>')
        xml_parts.append('        <cac:RegistrationAddress>')
        xml_parts.append('          <cbc:ID>11001</cbc:ID>')
        xml_parts.append(f'          <cbc:CityName>{self.invoice.workshop_city}</cbc:CityName>')
        xml_parts.append('          <cbc:PostalZone>110111</cbc:PostalZone>')
        xml_parts.append(f'          <cbc:CountrySubentity>{self.invoice.workshop_department}</cbc:CountrySubentity>')
        xml_parts.append('          <cbc:CountrySubentityCode>11</cbc:CountrySubentityCode>')
        xml_parts.append(f'          <cac:AddressLine><cbc:Line>{self.invoice.workshop_address}</cbc:Line></cac:AddressLine>')
        xml_parts.append('          <cac:Country>')
        xml_parts.append('            <cbc:IdentificationCode>CO</cbc:IdentificationCode>')
        xml_parts.append('            <cbc:Name languageID="es">Colombia</cbc:Name>')
        xml_parts.append('          </cac:Country>')
        xml_parts.append('        </cac:RegistrationAddress>')
        xml_parts.append('        <cac:TaxScheme>')
        xml_parts.append('          <cbc:ID>01</cbc:ID>')
        xml_parts.append('          <cbc:Name>IVA</cbc:Name>')
        xml_parts.append('        </cac:TaxScheme>')
        xml_parts.append('      </cac:PartyTaxScheme>')
        xml_parts.append('      <cac:PartyLegalEntity>')
        xml_parts.append(f'        <cbc:RegistrationName>{self.invoice.workshop_name}</cbc:RegistrationName>')
        xml_parts.append(f'        <cbc:CompanyID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeID="1" schemeName="31">{self.invoice.workshop_nit}</cbc:CompanyID>')
        xml_parts.append('        <cac:CorporateRegistrationScheme>')
        xml_parts.append(f'          <cbc:ID>{self.invoice.dian_resolution.prefix}</cbc:ID>')
        xml_parts.append('        </cac:CorporateRegistrationScheme>')
        xml_parts.append('      </cac:PartyLegalEntity>')
        if self.invoice.workshop_phone:
            xml_parts.append(f'      <cac:Contact><cbc:Telephone>{self.invoice.workshop_phone}</cbc:Telephone></cac:Contact>')
        xml_parts.append('    </cac:Party>')
        xml_parts.append('  </cac:AccountingSupplierParty>')

        # Información del cliente
        xml_parts.append('  <cac:AccountingCustomerParty>')
        xml_parts.append('    <cbc:AdditionalAccountID>2</cbc:AdditionalAccountID>')
        xml_parts.append('    <cac:Party>')
        xml_parts.append('      <cac:PartyIdentification>')
        xml_parts.append(f'        <cbc:ID schemeID="{self.invoice.customer_document_type}" schemeName="13" schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)">{self.invoice.customer_document}</cbc:ID>')
        xml_parts.append('      </cac:PartyIdentification>')
        xml_parts.append(f'      <cac:PartyName><cbc:Name>{self.invoice.customer_name}</cbc:Name></cac:PartyName>')
        xml_parts.append('      <cac:PartyTaxScheme>')
        xml_parts.append(f'        <cbc:RegistrationName>{self.invoice.customer_name}</cbc:RegistrationName>')
        xml_parts.append(f'        <cbc:CompanyID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)" schemeName="13">{self.invoice.customer_document}</cbc:CompanyID>')
        xml_parts.append('        <cac:TaxScheme>')
        xml_parts.append('          <cbc:ID>01</cbc:ID>')
        xml_parts.append('          <cbc:Name>IVA</cbc:Name>')
        xml_parts.append('        </cac:TaxScheme>')
        xml_parts.append('      </cac:PartyTaxScheme>')
        xml_parts.append('    </cac:Party>')
        xml_parts.append('  </cac:AccountingCustomerParty>')

        # Medios de pago
        xml_parts.append('  <cac:PaymentMeans>')
        xml_parts.append('    <cbc:ID>1</cbc:ID>')
        xml_parts.append('    <cbc:PaymentMeansCode>10</cbc:PaymentMeansCode>')
        xml_parts.append('  </cac:PaymentMeans>')

        # Impuestos
        xml_parts.append('  <cac:TaxTotal>')
        xml_parts.append(f'    <cbc:TaxAmount currencyID="COP">{self.invoice.tax_amount:.2f}</cbc:TaxAmount>')
        xml_parts.append('    <cac:TaxSubtotal>')
        xml_parts.append(f'      <cbc:TaxableAmount currencyID="COP">{self.invoice.subtotal:.2f}</cbc:TaxableAmount>')
        xml_parts.append(f'      <cbc:TaxAmount currencyID="COP">{self.invoice.tax_amount:.2f}</cbc:TaxAmount>')
        xml_parts.append('      <cac:TaxCategory>')
        xml_parts.append('        <cbc:Percent>19.00</cbc:Percent>')
        xml_parts.append('        <cac:TaxScheme>')
        xml_parts.append('          <cbc:ID>01</cbc:ID>')
        xml_parts.append('          <cbc:Name>IVA</cbc:Name>')
        xml_parts.append('        </cac:TaxScheme>')
        xml_parts.append('      </cac:TaxCategory>')
        xml_parts.append('    </cac:TaxSubtotal>')
        xml_parts.append('  </cac:TaxTotal>')

        # Totales legales
        xml_parts.append('  <cac:LegalMonetaryTotal>')
        xml_parts.append(f'    <cbc:LineExtensionAmount currencyID="COP">{self.invoice.subtotal:.2f}</cbc:LineExtensionAmount>')
        xml_parts.append(f'    <cbc:TaxExclusiveAmount currencyID="COP">{self.invoice.subtotal:.2f}</cbc:TaxExclusiveAmount>')
        xml_parts.append(f'    <cbc:TaxInclusiveAmount currencyID="COP">{self.invoice.total:.2f}</cbc:TaxInclusiveAmount>')
        xml_parts.append(f'    <cbc:PayableAmount currencyID="COP">{self.invoice.total:.2f}</cbc:PayableAmount>')
        xml_parts.append('  </cac:LegalMonetaryTotal>')

        # Líneas de factura
        for detail in self.invoice.details.all():
            xml_parts.append('  <cac:InvoiceLine>')
            xml_parts.append(f'    <cbc:ID>{detail.id}</cbc:ID>')
            xml_parts.append(f'    <cbc:InvoicedQuantity unitCode="NIU">{detail.quantity:.2f}</cbc:InvoicedQuantity>')
            xml_parts.append(f'    <cbc:LineExtensionAmount currencyID="COP">{detail.subtotal:.2f}</cbc:LineExtensionAmount>')
            xml_parts.append('    <cbc:FreeOfChargeIndicator>false</cbc:FreeOfChargeIndicator>')
            xml_parts.append('    <cac:TaxTotal>')
            xml_parts.append(f'      <cbc:TaxAmount currencyID="COP">{detail.tax_amount:.2f}</cbc:TaxAmount>')
            xml_parts.append('      <cac:TaxSubtotal>')
            xml_parts.append(f'        <cbc:TaxableAmount currencyID="COP">{detail.subtotal:.2f}</cbc:TaxableAmount>')
            xml_parts.append(f'        <cbc:TaxAmount currencyID="COP">{detail.tax_amount:.2f}</cbc:TaxAmount>')
            xml_parts.append('        <cac:TaxCategory>')
            xml_parts.append(f'          <cbc:Percent>{detail.tax_rate:.2f}</cbc:Percent>')
            xml_parts.append('          <cac:TaxScheme>')
            xml_parts.append('            <cbc:ID>01</cbc:ID>')
            xml_parts.append('            <cbc:Name>IVA</cbc:Name>')
            xml_parts.append('          </cac:TaxScheme>')
            xml_parts.append('        </cac:TaxCategory>')
            xml_parts.append('      </cac:TaxSubtotal>')
            xml_parts.append('    </cac:TaxTotal>')
            xml_parts.append('    <cac:Item>')
            xml_parts.append(f'      <cbc:Description>{detail.description}</cbc:Description>')
            xml_parts.append('    </cac:Item>')
            xml_parts.append('    <cac:Price>')
            xml_parts.append(f'      <cbc:PriceAmount currencyID="COP">{detail.unit_price:.2f}</cbc:PriceAmount>')
            xml_parts.append('      <cbc:BaseQuantity unitCode="NIU">1.00</cbc:BaseQuantity>')
            xml_parts.append('    </cac:Price>')
            xml_parts.append('  </cac:InvoiceLine>')

        xml_parts.append('</Invoice>')

        return '\n'.join(xml_parts)

    def _element_to_string(self, element: ET.Element, indent: int = 1) -> str:
        """Convertir elemento ET a string con formato correcto"""
        indent_str = '  ' * indent
        tag_name = element.tag.split('}')[-1]  # Obtener nombre sin namespace

        # Si es elemento DIAN, usar prefijo sts
        if 'dian:gov:co:facturaelectronica:Structures-2-1' in element.tag:
            tag_name = f'sts:{tag_name}'
        elif 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2' in element.tag:
            tag_name = f'ext:{tag_name}'
        elif 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2' in element.tag:
            tag_name = f'cac:{tag_name}'
        elif 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2' in element.tag:
            tag_name = f'cbc:{tag_name}'

        # Atributos
        attrs = []
        for key, value in element.attrib.items():
            if '}' in key:
                # Namespace attribute
                prefix = key.split('}')[0].split('{')[-1]
                attr_name = key.split('}')[-1]
                if prefix == "http://www.w3.org/2001/XMLSchema-instance":
                    attrs.append(f'xsi:{attr_name}="{value}"')
                else:
                    attrs.append(f'{key}="{value}"')
            else:
                attrs.append(f'{key}="{value}"')

        attr_str = f' {" ".join(attrs)}' if attrs else ''

        if element.text and element.text.strip():
            if element:
                # Tiene hijos
                child_strs = []
                for child in element:
                    child_strs.append(self._element_to_string(child, indent + 1))
                children = f'\n{"  " * (indent + 1)}'.join(child_strs)
                return f'{indent_str}<{tag_name}{attr_str}>\n{children}\n{indent_str}</{tag_name}>'
            else:
                # Solo texto
                return f'{indent_str}<{tag_name}{attr_str}>{element.text}</{tag_name}>'
        else:
            if element:
                # Tiene hijos
                child_strs = []
                for child in element:
                    child_strs.append(self._element_to_string(child, indent + 1))
                children = f'\n'.join(child_strs)
                return f'{indent_str}<{tag_name}{attr_str}>\n{children}\n{indent_str}</{tag_name}>'
            else:
                # Elemento vacío
                return f'{indent_str}<{tag_name}{attr_str}/>'

    def save_xml_file(self, filepath: str):
        """Guardar XML en archivo"""
        xml_content = self.get_xml_string()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        return filepath


class DianXmlValidator:
    """Validador básico de XML DIAN"""

    def __init__(self, xml_content: str):
        self.xml_content = xml_content
        self.errors = []

    def validate_basic_structure(self) -> bool:
        """Validación básica de estructura XML"""
        try:
            root = ET.fromstring(self.xml_content)

            # Verificar namespaces
            if not root.tag.endswith('Invoice'):
                self.errors.append("Elemento raíz debe ser 'Invoice'")
                return False

            # Verificar elementos obligatorios
            required_elements = [
                './/cbc:UBLVersionID',
                './/cbc:CustomizationID',
                './/cbc:ProfileID',
                './/cbc:ID',
                './/cbc:UUID',
                './/cbc:IssueDate',
                './/cbc:InvoiceTypeCode',
                './/cac:AccountingSupplierParty',
                './/cac:AccountingCustomerParty'
            ]

            for xpath in required_elements:
                if not root.find(xpath, DianXmlGenerator.NSMAP):
                    self.errors.append(f"Elemento requerido faltante: {xpath}")
                    return False

            return True

        except ET.ParseError as e:
            self.errors.append(f"Error de parsing XML: {str(e)}")
            return False

    def get_validation_errors(self) -> List[str]:
        """Obtener lista de errores de validación"""
        return self.errors.copy()
"""
Generador de XML UBL 2.1 para Facturación Electrónica DIAN
Basado en Anexo Técnico Documento Equivalente Electrónico V1.0
"""
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


# Namespaces UBL 2.1 según especificación DIAN
NAMESPACES = {
    '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ccts': 'urn:un:unece:uncefact:documentation:2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'qdt': 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2',
    'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
    'udt': 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


def register_namespaces():
    """Registra los namespaces XML para generación correcta"""
    try:
        from xml.etree.ElementTree import register_namespace
        for prefix, uri in NAMESPACES.items():
            if prefix:  # No registrar el namespace por defecto
                register_namespace(prefix, uri)
    except ImportError:
        pass


def create_element(tag: str, text: Optional[str] = None, attribs: Optional[Dict] = None) -> Element:
    """
    Crea un elemento XML con namespace correcto.
    
    Args:
        tag: Nombre del tag (puede incluir prefijo namespace como 'cbc:ID')
        text: Texto del elemento
        attribs: Atributos del elemento
    
    Returns:
        Element: Elemento XML creado
    """
    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        namespace = NAMESPACES.get(prefix, '')
        full_tag = f"{{{namespace}}}{local_name}"
    else:
        namespace = NAMESPACES.get('', '')
        full_tag = f"{{{namespace}}}{tag}"
    
    elem = Element(full_tag, attribs or {})
    if text is not None:
        elem.text = str(text)
    
    return elem


def add_subelement(parent: Element, tag: str, text: Optional[str] = None, attribs: Optional[Dict] = None) -> Element:
    """
    Agrega un subelemento a un elemento padre.
    
    Args:
        parent: Elemento padre
        tag: Nombre del tag
        text: Texto del elemento
        attribs: Atributos del elemento
    
    Returns:
        Element: Subelemento creado
    """
    if ':' in tag:
        prefix, local_name = tag.split(':', 1)
        namespace = NAMESPACES.get(prefix, '')
        full_tag = f"{{{namespace}}}{local_name}"
    else:
        namespace = NAMESPACES.get('', '')
        full_tag = f"{{{namespace}}}{tag}"
    
    elem = SubElement(parent, full_tag, attribs or {})
    if text is not None:
        elem.text = str(text)
    
    return elem


def format_decimal(value: Decimal, decimals: int = 2) -> str:
    """
    Formatea un valor decimal para XML según DIAN.
    
    Args:
        value: Valor a formatear
        decimals: Cantidad de decimales
    
    Returns:
        str: Valor formateado
    """
    return f"{value:.{decimals}f}"


def format_date(date_obj: date) -> str:
    """Formatea una fecha para XML según DIAN (YYYY-MM-DD)"""
    return date_obj.strftime('%Y-%m-%d')


def format_time(time_obj: datetime) -> str:
    """Formatea una hora para XML según DIAN (HH:MM:SS-05:00)"""
    return time_obj.strftime('%H:%M:%S-05:00')


def generate_electronic_invoice_xml(invoice) -> str:
    """
    Genera XML UBL 2.1 completo para una factura electrónica DIAN.
    
    Args:
        invoice: Instancia de ElectronicInvoice
    
    Returns:
        str: XML formateado
    """
    register_namespaces()
    
    # Crear elemento raíz Invoice
    root = create_element('Invoice', attribs={
        f'{{{NAMESPACES["xsi"]}}}schemaLocation': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd'
    })
    
    # Agregar namespaces al elemento raíz
    for prefix, uri in NAMESPACES.items():
        if prefix:
            root.set(f'xmlns:{prefix}', uri)
        else:
            root.set('xmlns', uri)
    
    # ========================================================================
    # SECCIÓN 1: EXTENSIONES (para firma digital - se implementará después)
    # ========================================================================
    ext_root = add_subelement(root, 'ext:UBLExtensions')
    ext_item = add_subelement(ext_root, 'ext:UBLExtension')
    ext_content = add_subelement(ext_item, 'ext:ExtensionContent')
    # Aquí irá la firma digital cuando se implemente Camerfirma
    
    # ========================================================================
    # SECCIÓN 2: INFORMACIÓN GENERAL DEL DOCUMENTO
    # ========================================================================
    add_subelement(root, 'cbc:UBLVersionID', 'UBL 2.1')
    add_subelement(root, 'cbc:CustomizationID', 'Documento Equivalente Electrónico')
    add_subelement(root, 'cbc:ProfileID', 'DIAN 2.1: Documento Equivalente Electrónico')
    add_subelement(root, 'cbc:ProfileExecutionID', '2' if hasattr(invoice.workshop, 'dian_config') and invoice.workshop.dian_config.environment == 'production' else '1')
    add_subelement(root, 'cbc:ID', invoice.invoice_number)
    add_subelement(root, 'cbc:UUID', invoice.cude, {
        'schemeName': 'CUDE-SHA384',
        'schemeID': invoice.invoice_number
    })
    add_subelement(root, 'cbc:IssueDate', format_date(invoice.issue_date.date()))
    add_subelement(root, 'cbc:IssueTime', format_time(invoice.issue_date))
    
    # Tipo de documento (01 = Factura)
    add_subelement(root, 'cbc:InvoiceTypeCode', '01')
    
    # Notas del documento
    if invoice.notes:
        add_subelement(root, 'cbc:Note', invoice.notes)
    
    # Moneda del documento
    add_subelement(root, 'cbc:DocumentCurrencyCode', 'COP', {'listID': 'ISO 4217 Alpha', 'listName': 'Currency'})
    
    # Número de líneas
    line_count = invoice.details.count()
    add_subelement(root, 'cbc:LineCountNumeric', str(line_count))
    
    # ========================================================================
    # SECCIÓN 3: PERÍODO DE FACTURACIÓN (opcional)
    # ========================================================================
    invoice_period = add_subelement(root, 'cac:InvoicePeriod')
    add_subelement(invoice_period, 'cbc:StartDate', format_date(invoice.issue_date.date()))
    add_subelement(invoice_period, 'cbc:EndDate', format_date(invoice.issue_date.date()))
    
    # ========================================================================
    # SECCIÓN 4: REFERENCIA A RESOLUCIÓN DIAN
    # ========================================================================
    billing_reference = add_subelement(root, 'cac:BillingReference')
    invoice_doc_ref = add_subelement(billing_reference, 'cac:InvoiceDocumentReference')
    add_subelement(invoice_doc_ref, 'cbc:ID', invoice.dian_resolution.resolution_number)
    add_subelement(invoice_doc_ref, 'cbc:UUID', invoice.dian_resolution.resolution_number, {'schemeName': 'CUDE-SHA384'})
    add_subelement(invoice_doc_ref, 'cbc:IssueDate', format_date(invoice.dian_resolution.resolution_date))
    
    # ========================================================================
    # SECCIÓN 5: INFORMACIÓN DEL PROVEEDOR (TALLER)
    # ========================================================================
    supplier_party = add_subelement(root, 'cac:AccountingSupplierParty')
    supplier_additional_id = add_subelement(supplier_party, 'cbc:AdditionalAccountID', '1')  # 1 = Persona Jurídica, 2 = Persona Natural
    
    # Información de la parte (Party)
    party = add_subelement(supplier_party, 'cac:Party')
    
    # Identificación del proveedor
    party_identification = add_subelement(party, 'cac:PartyIdentification')
    party_id = add_subelement(party_identification, 'cbc:ID', invoice.workshop_nit, {
        'schemeName': '31',  # 31 = NIT
        'schemeID': invoice.workshop_nit,
        'schemeAgencyID': '195',
        'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'
    })
    
    # Nombre comercial
    party_name = add_subelement(party, 'cac:PartyName')
    add_subelement(party_name, 'cbc:Name', invoice.workshop_name)
    
    # Dirección física
    physical_location = add_subelement(party, 'cac:PhysicalLocation')
    address = add_subelement(physical_location, 'cac:Address')
    add_subelement(address, 'cbc:ID', '11001')  # Código de municipio (Bogotá por defecto)
    add_subelement(address, 'cbc:CityName', invoice.workshop_city or 'Bogotá')
    add_subelement(address, 'cbc:CountrySubentity', invoice.workshop_department or 'Cundinamarca')
    add_subelement(address, 'cbc:CountrySubentityCode', '11')  # Código de departamento
    
    address_line = add_subelement(address, 'cac:AddressLine')
    add_subelement(address_line, 'cbc:Line', invoice.workshop_address)
    
    country = add_subelement(address, 'cac:Country')
    add_subelement(country, 'cbc:IdentificationCode', 'CO', {'listAgencyID': '6', 'listName': 'Country'})
    add_subelement(country, 'cbc:Name', 'Colombia', {'languageID': 'es'})
    
    # Información legal del proveedor
    party_tax_scheme = add_subelement(party, 'cac:PartyTaxScheme')
    add_subelement(party_tax_scheme, 'cbc:RegistrationName', invoice.workshop_name)
    add_subelement(party_tax_scheme, 'cbc:CompanyID', invoice.workshop_nit, {
        'schemeName': '31',
        'schemeID': invoice.workshop_nit,
        'schemeAgencyID': '195',
        'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'
    })
    
    # Régimen fiscal
    tax_level_code = add_subelement(party_tax_scheme, 'cbc:TaxLevelCode', 'O-13', {'listName': 'Responsabilidad Fiscal'})
    
    # Esquema de impuestos
    tax_scheme = add_subelement(party_tax_scheme, 'cac:TaxScheme')
    add_subelement(tax_scheme, 'cbc:ID', '01')  # 01 = IVA
    add_subelement(tax_scheme, 'cbc:Name', 'IVA')
    
    # Información legal
    party_legal = add_subelement(party, 'cac:PartyLegalEntity')
    add_subelement(party_legal, 'cbc:RegistrationName', invoice.workshop_name)
    add_subelement(party_legal, 'cbc:CompanyID', invoice.workshop_nit, {
        'schemeName': '31',
        'schemeID': invoice.workshop_nit,
        'schemeAgencyID': '195',
        'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'
    })
    
    # Información de contacto
    contact = add_subelement(party, 'cac:Contact')
    if invoice.workshop_phone:
        add_subelement(contact, 'cbc:Telephone', invoice.workshop_phone)
    if invoice.workshop_email:
        add_subelement(contact, 'cbc:ElectronicMail', invoice.workshop_email)
    
    # ========================================================================
    # SECCIÓN 6: INFORMACIÓN DEL CLIENTE
    # ========================================================================
    customer_party = add_subelement(root, 'cac:AccountingCustomerParty')
    add_subelement(customer_party, 'cbc:AdditionalAccountID', '1')  # 1 = Persona Jurídica, 2 = Persona Natural
    
    # Información de la parte (Party)
    cust_party = add_subelement(customer_party, 'cac:Party')
    
    # Identificación del cliente
    cust_party_identification = add_subelement(cust_party, 'cac:PartyIdentification')
    from .catalogs.document_types import convert_internal_to_dian
    doc_type_code = convert_internal_to_dian(invoice.customer_document_type)
    
    add_subelement(cust_party_identification, 'cbc:ID', invoice.customer_document, {
        'schemeName': doc_type_code,
        'schemeID': invoice.customer_document,
        'schemeAgencyID': '195',
        'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'
    })
    
    # Nombre del cliente
    cust_party_name = add_subelement(cust_party, 'cac:PartyName')
    add_subelement(cust_party_name, 'cbc:Name', invoice.customer_name)
    
    # Dirección física del cliente
    if invoice.customer_address:
        cust_physical_location = add_subelement(cust_party, 'cac:PhysicalLocation')
        cust_address = add_subelement(cust_physical_location, 'cac:Address')
        add_subelement(cust_address, 'cbc:ID', '11001')  # Código de municipio
        add_subelement(cust_address, 'cbc:CityName', invoice.customer_city or 'Bogotá')
        add_subelement(cust_address, 'cbc:CountrySubentity', invoice.customer_department or 'Cundinamarca')
        add_subelement(cust_address, 'cbc:CountrySubentityCode', '11')
        
        cust_address_line = add_subelement(cust_address, 'cac:AddressLine')
        add_subelement(cust_address_line, 'cbc:Line', invoice.customer_address)
        
        cust_country = add_subelement(cust_address, 'cac:Country')
        add_subelement(cust_country, 'cbc:IdentificationCode', 'CO')
        add_subelement(cust_country, 'cbc:Name', 'Colombia')
    
    # Información fiscal del cliente
    cust_party_tax_scheme = add_subelement(cust_party, 'cac:PartyTaxScheme')
    add_subelement(cust_party_tax_scheme, 'cbc:RegistrationName', invoice.customer_name)
    add_subelement(cust_party_tax_scheme, 'cbc:CompanyID', invoice.customer_document, {
        'schemeName': doc_type_code,
        'schemeID': invoice.customer_document
    })
    
    cust_tax_scheme = add_subelement(cust_party_tax_scheme, 'cac:TaxScheme')
    add_subelement(cust_tax_scheme, 'cbc:ID', '01')
    add_subelement(cust_tax_scheme, 'cbc:Name', 'IVA')
    
    # Información legal del cliente
    cust_party_legal = add_subelement(cust_party, 'cac:PartyLegalEntity')
    add_subelement(cust_party_legal, 'cbc:RegistrationName', invoice.customer_name)
    add_subelement(cust_party_legal, 'cbc:CompanyID', invoice.customer_document, {
        'schemeName': doc_type_code,
        'schemeID': invoice.customer_document
    })
    
    # Contacto del cliente
    if invoice.customer_phone or invoice.customer_email:
        cust_contact = add_subelement(cust_party, 'cac:Contact')
        if invoice.customer_phone:
            add_subelement(cust_contact, 'cbc:Telephone', invoice.customer_phone)
        if invoice.customer_email:
            add_subelement(cust_contact, 'cbc:ElectronicMail', invoice.customer_email)
    
    # ========================================================================
    # SECCIÓN 7: CONDICIONES DE PAGO
    # ========================================================================
    from .catalogs.payment_methods import convert_internal_payment_to_dian
    payment_means_code = convert_internal_payment_to_dian(invoice.payment_method or 'cash')
    
    payment_means = add_subelement(root, 'cac:PaymentMeans')
    add_subelement(payment_means, 'cbc:ID', '1')
    add_subelement(payment_means, 'cbc:PaymentMeansCode', payment_means_code)
    if invoice.due_date:
        add_subelement(payment_means, 'cbc:PaymentDueDate', format_date(invoice.due_date))
    
    # ========================================================================
    # SECCIÓN 8: TOTALES DE IMPUESTOS
    # ========================================================================
    tax_total = add_subelement(root, 'cac:TaxTotal')
    add_subelement(tax_total, 'cbc:TaxAmount', format_decimal(invoice.tax_amount), {'currencyID': 'COP'})
    
    # Subtotal de IVA
    tax_subtotal = add_subelement(tax_total, 'cac:TaxSubtotal')
    add_subelement(tax_subtotal, 'cbc:TaxableAmount', format_decimal(invoice.subtotal - invoice.discount), {'currencyID': 'COP'})
    add_subelement(tax_subtotal, 'cbc:TaxAmount', format_decimal(invoice.tax_amount), {'currencyID': 'COP'})
    
    tax_category = add_subelement(tax_subtotal, 'cac:TaxCategory')
    add_subelement(tax_category, 'cbc:Percent', format_decimal(invoice.tax_rate, 2))
    
    tax_scheme_iva = add_subelement(tax_category, 'cac:TaxScheme')
    add_subelement(tax_scheme_iva, 'cbc:ID', '01')  # 01 = IVA
    add_subelement(tax_scheme_iva, 'cbc:Name', 'IVA')
    
    # ========================================================================
    # SECCIÓN 9: TOTALES LEGALES DEL DOCUMENTO
    # ========================================================================
    legal_monetary_total = add_subelement(root, 'cac:LegalMonetaryTotal')
    add_subelement(legal_monetary_total, 'cbc:LineExtensionAmount', format_decimal(invoice.subtotal), {'currencyID': 'COP'})
    add_subelement(legal_monetary_total, 'cbc:TaxExclusiveAmount', format_decimal(invoice.subtotal - invoice.discount), {'currencyID': 'COP'})
    add_subelement(legal_monetary_total, 'cbc:TaxInclusiveAmount', format_decimal(invoice.total), {'currencyID': 'COP'})
    add_subelement(legal_monetary_total, 'cbc:AllowanceTotalAmount', format_decimal(invoice.discount), {'currencyID': 'COP'})
    add_subelement(legal_monetary_total, 'cbc:PayableAmount', format_decimal(invoice.total), {'currencyID': 'COP'})
    
    # ========================================================================
    # SECCIÓN 10: LÍNEAS DE DETALLE DE LA FACTURA
    # ========================================================================
    for index, detail in enumerate(invoice.details.all(), start=1):
        invoice_line = add_subelement(root, 'cac:InvoiceLine')
        add_subelement(invoice_line, 'cbc:ID', str(index))
        add_subelement(invoice_line, 'cbc:InvoicedQuantity', format_decimal(detail.quantity, 2), {'unitCode': detail.unit_code or 'NIU'})
        add_subelement(invoice_line, 'cbc:LineExtensionAmount', format_decimal(detail.subtotal), {'currencyID': 'COP'})
        
        # Información del producto/servicio
        item = add_subelement(invoice_line, 'cac:Item')
        add_subelement(item, 'cbc:Description', detail.description)
        
        # Código del producto (UNSPSC si existe)
        if detail.unspsc_code:
            sellers_item_id = add_subelement(item, 'cac:SellersItemIdentification')
            add_subelement(sellers_item_id, 'cbc:ID', detail.unspsc_code)
        
        # Código estándar del producto
        if detail.part_number:
            standard_item_id = add_subelement(item, 'cac:StandardItemIdentification')
            add_subelement(standard_item_id, 'cbc:ID', detail.part_number, {'schemeID': '999', 'schemeName': 'Estándar de adopción del contribuyente'})
        
        # Marca y modelo
        if detail.brand_name:
            add_subelement(item, 'cbc:BrandName', detail.brand_name)
        if detail.model_name:
            add_subelement(item, 'cbc:ModelName', detail.model_name)
        
        # Precio unitario
        price = add_subelement(invoice_line, 'cac:Price')
        add_subelement(price, 'cbc:PriceAmount', format_decimal(detail.unit_price), {'currencyID': 'COP'})
        add_subelement(price, 'cbc:BaseQuantity', format_decimal(Decimal('1.00'), 2), {'unitCode': detail.unit_code or 'NIU'})
    
    # Convertir a string XML
    xml_string = tostring(root, encoding='utf-8', method='xml')
    
    # Formatear con indentación
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8')
    
    return pretty_xml.decode('utf-8')


def validate_xml_structure(xml_string: str) -> tuple:
    """
    Valida la estructura básica del XML generado.
    
    Args:
        xml_string: XML a validar
    
    Returns:
        tuple: (es_válido, mensaje)
    """
    try:
        from xml.etree import ElementTree as ET
        ET.fromstring(xml_string.encode('utf-8'))
        return True, "XML válido"
    except Exception as e:
        return False, f"XML inválido: {str(e)}"
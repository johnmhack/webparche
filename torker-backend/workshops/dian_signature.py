"""
Módulo de Firma Digital para Facturación Electrónica DIAN
Implementa firma XMLDSig con certificados Camerfirma
"""
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict
from xml.etree.ElementTree import Element, SubElement, tostring
from decimal import Decimal


class DIANSignature:
    """Maneja la firma digital de documentos electrónicos DIAN"""
    
    def __init__(self, certificate_path: str, certificate_password: str):
        """
        Inicializa el firmador con certificado digital.
        
        Args:
            certificate_path: Ruta al archivo .p12/.pfx
            certificate_password: Contraseña del certificado
        """
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password
        self.certificate = None
        self.private_key = None
        
    def load_certificate(self):
        """Carga el certificado digital desde archivo .p12"""
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.backends import default_backend
            
            with open(self.certificate_path, 'rb') as f:
                pfx_data = f.read()
            
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.certificate_password.encode(),
                backend=default_backend()
            )
            
            self.private_key = private_key
            self.certificate = certificate
            
            return True
        except Exception as e:
            raise Exception(f"Error cargando certificado: {str(e)}")
    
    def get_certificate_info(self) -> Dict:
        """Obtiene información del certificado"""
        if not self.certificate:
            self.load_certificate()
        
        return {
            'subject': self.certificate.subject.rfc4514_string(),
            'issuer': self.certificate.issuer.rfc4514_string(),
            'serial_number': str(self.certificate.serial_number),
            'not_valid_before': self.certificate.not_valid_before,
            'not_valid_after': self.certificate.not_valid_after,
        }
    
    def create_signature_extensions(self, invoice_data: Dict) -> Element:
        """
        Crea las extensiones UBL con firma digital según DIAN.
        
        Args:
            invoice_data: Datos de la factura para firma
            
        Returns:
            Element: Extensiones UBL con firma
        """
        from xml.etree.ElementTree import Element, SubElement
        
        # Namespaces
        NS_EXT = 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'
        NS_DS = 'http://www.w3.org/2000/09/xmldsig#'
        NS_XADES = 'http://uri.etsi.org/01903/v1.3.2#'
        NS_STS = 'http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures'
        
        # Crear extensiones
        extensions = Element(f'{{{NS_EXT}}}UBLExtensions')
        
        # Extensión 1: Información DIAN
        ext1 = SubElement(extensions, f'{{{NS_EXT}}}UBLExtension')
        ext1_content = SubElement(ext1, f'{{{NS_EXT}}}ExtensionContent')
        
        dian_ext = SubElement(ext1_content, f'{{{NS_STS}}}DianExtensions')
        
        # Control de factura
        invoice_control = SubElement(dian_ext, f'{{{NS_STS}}}InvoiceControl')
        SubElement(invoice_control, f'{{{NS_STS}}}InvoiceAuthorization').text = invoice_data['authorization']
        
        auth_period = SubElement(invoice_control, f'{{{NS_STS}}}AuthorizationPeriod')
        SubElement(auth_period, 'cbc:StartDate', {'xmlns:cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text = invoice_data['auth_start_date']
        SubElement(auth_period, 'cbc:EndDate', {'xmlns:cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text = invoice_data['auth_end_date']
        
        # Software provider
        software_provider = SubElement(dian_ext, f'{{{NS_STS}}}SoftwareProvider')
        SubElement(software_provider, f'{{{NS_STS}}}ProviderID', {
            'schemeAgencyID': '195',
            'schemeID': '4',
            'schemeName': '31'
        }).text = invoice_data['provider_nit']
        SubElement(software_provider, f'{{{NS_STS}}}SoftwareID', {
            'schemeAgencyID': '195'
        }).text = invoice_data['software_id']
        
        # Security code
        SubElement(dian_ext, f'{{{NS_STS}}}SoftwareSecurityCode', {
            'schemeAgencyID': '195'
        }).text = invoice_data['security_code']
        
        # QR Code
        SubElement(dian_ext, f'{{{NS_STS}}}QRCode').text = invoice_data['qr_code']
        
        # Extensión 2: Firma digital (placeholder)
        ext2 = SubElement(extensions, f'{{{NS_EXT}}}UBLExtension')
        ext2_content = SubElement(ext2, f'{{{NS_EXT}}}ExtensionContent')
        
        # Aquí se insertará la firma digital cuando se implemente
        # signature = self._create_xmldsig_signature(invoice_data)
        # ext2_content.append(signature)
        
        return extensions
    
    def sign_xml(self, xml_content: str) -> str:
        """
        Firma un XML con el certificado digital.
        
        Args:
            xml_content: Contenido XML a firmar
            
        Returns:
            str: XML firmado
        """
        if not self.certificate:
            self.load_certificate()
        
        try:
            from signxml import XMLSigner
            from lxml import etree
            
            # Parsear XML
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Configurar firmador
            signer = XMLSigner(
                method=signxml.methods.enveloped,
                signature_algorithm='rsa-sha256',
                digest_algorithm='sha256',
                c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
            )
            
            # Firmar
            signed_root = signer.sign(
                root,
                key=self.private_key,
                cert=self.certificate
            )
            
            # Convertir a string
            signed_xml = etree.tostring(
                signed_root,
                encoding='utf-8',
                xml_declaration=True
            ).decode('utf-8')
            
            return signed_xml
            
        except ImportError:
            raise Exception(
                "Librería 'signxml' no instalada. "
                "Ejecuta: pip install signxml lxml cryptography"
            )
        except Exception as e:
            raise Exception(f"Error firmando XML: {str(e)}")
    
    def verify_signature(self, signed_xml: str) -> bool:
        """
        Verifica la firma digital de un XML.
        
        Args:
            signed_xml: XML firmado
            
        Returns:
            bool: True si la firma es válida
        """
        try:
            from signxml import XMLVerifier
            from lxml import etree
            
            root = etree.fromstring(signed_xml.encode('utf-8'))
            
            verifier = XMLVerifier()
            verified_data = verifier.verify(
                root,
                x509_cert=self.certificate
            )
            
            return True
        except Exception as e:
            print(f"Error verificando firma: {str(e)}")
            return False
    
    def calculate_digest(self, data: str, algorithm: str = 'sha256') -> str:
        """
        Calcula el digest de datos según algoritmo.
        
        Args:
            data: Datos a procesar
            algorithm: Algoritmo (sha256, sha384, sha512)
            
        Returns:
            str: Digest en base64
        """
        if algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha384':
            hash_obj = hashlib.sha384()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")
        
        hash_obj.update(data.encode('utf-8'))
        digest = base64.b64encode(hash_obj.digest()).decode('utf-8')
        
        return digest


def prepare_invoice_for_signature(invoice) -> Dict:
    """
    Prepara los datos de una factura para firma digital.
    
    Args:
        invoice: Instancia de ElectronicInvoice
        
    Returns:
        Dict: Datos preparados para firma
    """
    dian_config = invoice.workshop.dian_config
    resolution = invoice.dian_resolution
    
    return {
        'authorization': resolution.resolution_number,
        'auth_start_date': resolution.valid_from.strftime('%Y-%m-%d'),
        'auth_end_date': resolution.valid_until.strftime('%Y-%m-%d'),
        'provider_nit': invoice.workshop_nit,
        'software_id': dian_config.software_id,
        'security_code': dian_config.software_pin,
        'qr_code': invoice.qr_code_data or '',
        'invoice_number': invoice.invoice_number,
        'cufe': invoice.cude,
        'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
        'issue_time': invoice.issue_date.strftime('%H:%M:%S-05:00'),
    }


# Ejemplo de uso (cuando tengas el certificado):
"""
# 1. Inicializar firmador
signer = DIANSignature(
    certificate_path='workshops/certificates/certificado.p12',
    certificate_password='tu_contraseña'
)

# 2. Cargar certificado
signer.load_certificate()

# 3. Obtener info del certificado
cert_info = signer.get_certificate_info()
print(f"Certificado válido hasta: {cert_info['not_valid_after']}")

# 4. Preparar datos de factura
invoice_data = prepare_invoice_for_signature(invoice)

# 5. Crear extensiones con firma
extensions = signer.create_signature_extensions(invoice_data)

# 6. Firmar XML completo
signed_xml = signer.sign_xml(xml_content)

# 7. Verificar firma
is_valid = signer.verify_signature(signed_xml)
"""
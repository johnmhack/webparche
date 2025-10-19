"""
Generador de códigos QR para facturas electrónicas DIAN
Implementa formato oficial según especificación DIAN
"""
import qrcode
from io import BytesIO
from PIL import Image
import logging
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)


def generate_qr_code_image(qr_data: str, size: int = 300) -> BytesIO:
    """
    Genera imagen de código QR a partir de datos.
    
    Args:
        qr_data: Cadena de datos para el QR
        size: Tamaño de la imagen en píxeles (default: 300x300)
    
    Returns:
        BytesIO: Buffer con la imagen PNG del QR
    """
    try:
        # Crear objeto QR con configuración óptima
        qr = qrcode.QRCode(
            version=None,  # Auto-ajustar versión según datos
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% de corrección
            box_size=10,
            border=4,
        )
        
        # Agregar datos
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionar si es necesario
        if size != 300:
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Guardar en buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.info(f"QR code generado exitosamente, tamaño: {size}x{size}")
        return buffer
        
    except Exception as e:
        logger.error(f"Error generando QR code: {str(e)}")
        raise ValueError(f"Error generando código QR: {str(e)}")


def generate_invoice_qr_code(invoice) -> BytesIO:
    """
    Genera código QR para una factura electrónica según formato DIAN.
    
    Args:
        invoice: Instancia de ElectronicInvoice
    
    Returns:
        BytesIO: Buffer con la imagen PNG del QR
    """
    from .dian_utils import generate_qr_data
    from .catalogs.document_types import convert_internal_to_dian
    
    try:
        # Convertir tipo de documento a código DIAN
        doc_type_code = convert_internal_to_dian(invoice.customer_document_type)
        
        # Generar datos del QR según formato DIAN
        qr_data = generate_qr_data(
            invoice_number=invoice.invoice_number,
            issue_date=invoice.issue_date.date() if hasattr(invoice.issue_date, 'date') else invoice.issue_date,
            supplier_nit=invoice.workshop_nit,
            customer_document_type=doc_type_code,
            customer_document=invoice.customer_document,
            invoice_total=invoice.subtotal - invoice.discount,
            iva_total=invoice.tax_amount,
            other_tax_total=Decimal('0.00'),  # Otros impuestos (INC, ICA, etc.)
            total_with_tax=invoice.total,
            cufe=invoice.cude,
            validation_url="https://catalogo-vpfe.dian.gov.co/document/searchqr"
        )
        
        # Generar imagen QR
        qr_image = generate_qr_code_image(qr_data, size=300)
        
        logger.info(f"QR code generado para factura {invoice.invoice_number}")
        return qr_image
        
    except Exception as e:
        logger.error(f"Error generando QR para factura {invoice.invoice_number}: {str(e)}")
        raise ValueError(f"Error generando QR code: {str(e)}")


def save_qr_code_to_invoice(invoice, qr_image_buffer: BytesIO) -> str:
    """
    Guarda el código QR generado en el modelo de factura.
    
    Args:
        invoice: Instancia de ElectronicInvoice
        qr_image_buffer: Buffer con la imagen del QR
    
    Returns:
        str: Path relativo de la imagen guardada
    """
    from django.core.files.base import ContentFile
    
    try:
        # Generar nombre de archivo único
        filename = f"qr_{invoice.invoice_number}_{invoice.cude[:8]}.png"
        
        # Guardar imagen en el campo ImageField
        invoice.qr_code_image.save(
            filename,
            ContentFile(qr_image_buffer.getvalue()),
            save=True
        )
        
        logger.info(f"QR code guardado: {filename}")
        return invoice.qr_code_image.url
        
    except Exception as e:
        logger.error(f"Error guardando QR code: {str(e)}")
        raise ValueError(f"Error guardando código QR: {str(e)}")


def generate_and_save_qr_code(invoice) -> str:
    """
    Genera y guarda el código QR para una factura electrónica.
    Función de conveniencia que combina generación y guardado.
    
    Args:
        invoice: Instancia de ElectronicInvoice
    
    Returns:
        str: URL de la imagen del QR guardada
    """
    try:
        # Generar QR
        qr_image = generate_invoice_qr_code(invoice)
        
        # Guardar en modelo
        qr_url = save_qr_code_to_invoice(invoice, qr_image)
        
        # Actualizar URL del QR en el modelo
        invoice.qr_code_url = f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={invoice.cude}"
        invoice.save(update_fields=['qr_code_url'])
        
        logger.info(f"QR code completo para factura {invoice.invoice_number}")
        return qr_url
        
    except Exception as e:
        logger.error(f"Error en proceso completo de QR: {str(e)}")
        raise


def validate_qr_data(qr_data: str) -> bool:
    """
    Valida que los datos del QR cumplan con el formato DIAN.
    
    Args:
        qr_data: Cadena de datos del QR
    
    Returns:
        bool: True si es válido
    """
    required_fields = [
        'NumFac=',
        'FecFac=',
        'NitFac=',
        'DocAdq=',
        'NitAdq=',
        'ValFac=',
        'ValIva=',
        'ValOtroIm=',
        'ValTotal=',
        'CUFE=',
        'URL='
    ]
    
    for field in required_fields:
        if field not in qr_data:
            logger.warning(f"Campo faltante en QR data: {field}")
            return False
    
    return True
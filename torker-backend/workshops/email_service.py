"""
Servicio de envío de emails para facturas electrónicas
Implementa envío profesional con plantillas HTML
"""
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def send_invoice_email(invoice, recipient_email=None):
    """
    Envía factura electrónica por email al cliente.
    
    Args:
        invoice: Instancia de ElectronicInvoice
        recipient_email: Email del destinatario (opcional, usa el del cliente por defecto)
    
    Returns:
        bool: True si se envió exitosamente
    """
    try:
        # Determinar destinatario
        to_email = recipient_email or invoice.customer_email
        
        if not to_email:
            raise ValueError("No hay email del cliente configurado")
        
        # Generar PDF
        from .pdf_generator import generate_electronic_invoice_pdf
        pdf_data = generate_electronic_invoice_pdf(invoice.id)
        
        # Crear asunto
        subject = f"Factura Electrónica {invoice.invoice_number} - {invoice.workshop_name}"
        
        # Crear cuerpo del email (HTML)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .invoice-details {{
                    background-color: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #3498db;
                }}
                .invoice-details h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .total {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #27ae60;
                    text-align: right;
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 2px solid #27ae60;
                }}
                .footer {{
                    background-color: #ecf0f1;
                    padding: 20px;
                    text-align: center;
                    font-size: 0.9em;
                    color: #7f8c8d;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{invoice.workshop_name}</h1>
                <p>Factura Electrónica de Venta</p>
            </div>
            
            <div class="content">
                <p>Estimado(a) <strong>{invoice.customer_name}</strong>,</p>
                
                <p>Adjunto encontrará su factura electrónica correspondiente al servicio realizado en su vehículo.</p>
                
                <div class="invoice-details">
                    <h3>Detalles de la Factura</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">Número de Factura:</span>
                        <span>{invoice.invoice_number}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Fecha de Emisión:</span>
                        <span>{invoice.issue_date.strftime('%d/%m/%Y')}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Subtotal:</span>
                        <span>${invoice.subtotal:,.0f}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">IVA ({invoice.tax_rate}%):</span>
                        <span>${invoice.tax_amount:,.0f}</span>
                    </div>
                    
                    <div class="total">
                        TOTAL: ${invoice.total:,.0f} COP
                    </div>
                </div>
                
                <p>Esta factura electrónica ha sido generada conforme a la normativa DIAN vigente.</p>
                
                <p><strong>CUFE:</strong><br/>
                <small style="word-break: break-all;">{invoice.cude}</small></p>
                
                <p>Puede validar esta factura en el portal de la DIAN usando el código CUFE.</p>
                
                <p>Gracias por confiar en nosotros.</p>
            </div>
            
            <div class="footer">
                <p><strong>{invoice.workshop_name}</strong></p>
                <p>NIT: {invoice.workshop_nit}</p>
                <p>{invoice.workshop_address}</p>
                <p>Tel: {invoice.workshop_phone} | Email: {invoice.workshop_email}</p>
                <p style="margin-top: 15px; font-size: 0.8em;">
                    Este es un correo automático, por favor no responder.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Crear email
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            reply_to=[invoice.workshop_email] if invoice.workshop_email else None
        )
        
        # Configurar como HTML
        email.content_subtype = 'html'
        
        # Adjuntar PDF
        email.attach(
            f'Factura_{invoice.invoice_number}.pdf',
            pdf_data,
            'application/pdf'
        )
        
        # Enviar
        email.send(fail_silently=False)
        
        logger.info(f"Email enviado exitosamente a {to_email} para factura {invoice.invoice_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email para factura {invoice.invoice_number}: {str(e)}")
        raise ValueError(f"Error enviando email: {str(e)}")


def send_invoice_email_multiple(invoice, recipients):
    """
    Envía factura a múltiples destinatarios.
    
    Args:
        invoice: Instancia de ElectronicInvoice
        recipients: Lista de emails
    
    Returns:
        dict: Resultado del envío por cada destinatario
    """
    results = {}
    
    for email in recipients:
        try:
            send_invoice_email(invoice, email)
            results[email] = {'success': True, 'message': 'Enviado exitosamente'}
        except Exception as e:
            results[email] = {'success': False, 'message': str(e)}
    
    return results
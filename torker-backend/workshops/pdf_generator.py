"""
Generador de PDF estilo Siigo para facturas electrónicas DIAN
Estructura profesional optimizada para una sola página
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def generate_electronic_invoice_pdf_siigo(invoice_id):
    """
    Genera PDF de factura electrónica con estructura estilo Siigo.
    Optimizado para caber en una sola página.
    
    Estructura:
    1. Encabezado con datos del taller + QR en esquina
    2. Título "Factura electrónica de venta" + número
    3. Datos transaccionales (fecha, mecánico, cliente, placa)
    4. Tabla de productos/servicios
    5. Resumen de impuestos
    6. Forma de pago y total
    7. Pie de página legal + CUFE
    """
    from .models import ElectronicInvoice
    from .dian_utils import format_nit
    
    try:
        # Obtener factura
        invoice = ElectronicInvoice.objects.select_related(
            'workshop', 'customer', 'work_order', 'dian_resolution'
        ).prefetch_related('details').get(id=invoice_id)
        
        # Crear buffer
        buffer = BytesIO()
        
        # Documento con márgenes ajustados
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=30,
            bottomMargin=30
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # ================================================================
        # ENCABEZADO CON QR CODE
        # ================================================================
        
        # Formatear NIT
        nit_display = format_nit(invoice.workshop_nit) if invoice.workshop_nit else 'N/A'
        
        # Crear tabla de encabezado con QR
        header_content = Paragraph(f"""
            <para align=center>
            <b><font size=12>{invoice.workshop_name.upper()}</font></b><br/>
            <font size=9>NIT: {nit_display}</font><br/>
            <font size=8>{invoice.workshop_address}</font><br/>
            <font size=8>{invoice.workshop_city} - Tel: {invoice.workshop_phone}</font><br/>
            <font size=8>{invoice.workshop_email}</font><br/>
            <font size=8>https://elestablocolombia.com</font>
            </para>
        """, styles['Normal'])
        
        # QR Code (si existe)
        qr_cell = ""
        if hasattr(invoice, 'qr_code_image') and invoice.qr_code_image:
            try:
                qr_img = RLImage(invoice.qr_code_image.path, width=1.2*inch, height=1.2*inch)
                qr_cell = qr_img
            except:
                qr_cell = Paragraph("<font size=6>QR</font>", styles['Normal'])
        else:
            qr_cell = Paragraph("<font size=6>[QR]</font>", styles['Normal'])
        
        header_table = Table([[header_content, qr_cell]], colWidths=[5.5*inch, 1.7*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 10))
        
        # ================================================================
        # TÍTULO DEL DOCUMENTO
        # ================================================================
        
        title = Paragraph(f"""
            <para align=center>
            <b><font size=11>Factura electrónica de venta</font></b><br/>
            <font size=10>No. {invoice.invoice_number}</font>
            </para>
        """, styles['Normal'])
        story.append(title)
        story.append(Spacer(1, 8))
        
        # ================================================================
        # DATOS TRANSACCIONALES
        # ================================================================
        
        # Obtener mecánico y placa
        mechanic_name = "N/A"
        vehicle_plate = "N/A"
        
        if invoice.work_order:
            if invoice.work_order.assigned_mechanic:
                mechanic_name = invoice.work_order.assigned_mechanic.full_name
            if invoice.work_order.vehicle:
                vehicle_plate = invoice.work_order.vehicle.license_plate or "N/A"
        
        trans_data = [
            ['Fecha', invoice.issue_date.strftime('%Y-%m-%d')],
            ['Mecánico', mechanic_name],
            ['Cliente', invoice.customer_name],
            ['NIT / C.C.', f"{invoice.customer_document_type.upper()} {invoice.customer_document}"],
            ['Dirección', invoice.customer_address or 'N/A'],
            ['Vehículo', f"Placa: {vehicle_plate}"],
        ]
        
        trans_table = Table(trans_data, colWidths=[1.2*inch, 6*inch])
        trans_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.7)),  # Amarillo claro
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(trans_table)
        story.append(Spacer(1, 8))
        
        # ================================================================
        # TABLA DE PRODUCTOS/SERVICIOS
        # ================================================================
        
        products_data = [['Código', 'Descripción', 'Cant.', 'Impto. cargo', 'Vr. Total']]
        
        for detail in invoice.details.all():
            products_data.append([
                detail.part_number or detail.unspsc_code or 'N/A',
                detail.description[:60],
                f"{detail.quantity:.2f}",
                f"{detail.tax_rate:.0f}%",
                f"${detail.total:,.0f}"
            ])
        
        products_table = Table(products_data, colWidths=[1*inch, 3.5*inch, 0.7*inch, 0.9*inch, 1.1*inch])
        products_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(products_table)
        story.append(Spacer(1, 8))
        
        # ================================================================
        # RESUMEN DE IMPUESTOS
        # ================================================================
        
        tax_summary = Paragraph("<b>Resumen Impuestos</b>", ParagraphStyle(
            'TaxTitle', parent=styles['Normal'], fontSize=9, alignment=1
        ))
        story.append(tax_summary)
        story.append(Spacer(1, 4))
        
        tax_data = [[
            'Tarifa',
            'Vr. Base',
            'Valor'
        ], [
            f"{invoice.tax_rate:.2f}%",
            f"${invoice.subtotal - invoice.discount:,.0f}",
            f"${invoice.tax_amount:,.0f}"
        ]]
        
        tax_table = Table(tax_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        tax_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(tax_table)
        story.append(Spacer(1, 8))
        
        # ================================================================
        # FORMA DE PAGO Y TOTAL
        # ================================================================
        
        payment_method_display = {
            'cash': 'Efectivo - CONTADO',
            'card': 'Tarjeta - CONTADO',
            'transfer': 'Transferencia - CONTADO',
        }.get(invoice.payment_method, 'Efectivo - CONTADO')
        
        payment_data = [[
            'Forma de Pago',
            payment_method_display,
            '',
            f"${invoice.total:,.0f}"
        ]]
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1.7*inch])
        payment_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 10))
        
        # ================================================================
        # PIE DE PÁGINA LEGAL
        # ================================================================
        
        legal_text = f"""
        <para align=justify fontSize=6>
        A esta factura de venta aplican las normas relativas a la letra de cambio (artículo 5 Ley 1231 de 2008). 
        Con esta el Comprador declara haber recibido real y materialmente las mercancías o prestación de servicios 
        descritos en este título - Valor. <b>Número Autorización Electrónica {invoice.dian_resolution.resolution_number if invoice.dian_resolution else 'N/A'}</b> 
        aprobado en {invoice.dian_resolution.resolution_date.strftime('%Y%m%d') if invoice.dian_resolution else 'N/A'} 
        prefijo {invoice.dian_resolution.prefix if invoice.dian_resolution else 'N/A'} desde el número 
        {invoice.dian_resolution.from_number if invoice.dian_resolution else 'N/A'} al 
        {invoice.dian_resolution.to_number if invoice.dian_resolution else 'N/A'} 
        Vigencia: {invoice.dian_resolution.expires_date.strftime('%Y-%m-%d') if invoice.dian_resolution else 'N/A'}<br/>
        Responsable de IVA - Actividad Económica 4631 Comercio al por mayor de productos alimenticios Tarifa 5/1000
        </para>
        """
        
        story.append(Paragraph(legal_text, styles['Normal']))
        story.append(Spacer(1, 6))
        
        # CUFE
        cufe_text = f"""
        <para align=center fontSize=5>
        <b>CUFE:</b> {invoice.cude}
        </para>
        """
        
        story.append(Paragraph(cufe_text, styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"PDF Siigo style generado: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        logger.error(f"Error generando PDF Siigo style: {str(e)}")
        raise ValueError(f"Error generando PDF: {str(e)}")

# Alias para compatibilidad con código existente
def generate_electronic_invoice_pdf(invoice_id):
    """
    Alias de generate_electronic_invoice_pdf_siigo para compatibilidad.
    """
    return generate_electronic_invoice_pdf_siigo(invoice_id)


def generate_invoice_pdf(invoice_id):
    """
    Genera PDF para facturas regulares (no electrónicas).
    Por ahora usa el mismo generador que las electrónicas.
    """
    # TODO: Implementar generador específico para facturas regulares si es necesario
    return generate_electronic_invoice_pdf_siigo(invoice_id)
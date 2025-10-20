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
        # ENCABEZADO EXACTO ESTILO CAMERFIRMA
        # ================================================================
        
        import os
        from django.conf import settings
        
        # Formatear NIT
        nit_display = format_nit(invoice.workshop_nit) if invoice.workshop_nit else 'N/A'
        
        # FILA 1: Logo + Info Empresa + QR
        logo_path = os.path.join(settings.BASE_DIR, 'workshops', 'static', 'logos', 'servimotos.png')
        
        # Columna 1: Logo + Nombre empresa
        if os.path.exists(logo_path):
            try:
                logo_img = RLImage(logo_path, width=2*inch, height=0.8*inch)
            except:
                logo_img = Paragraph("<font size=8>[LOGO]</font>", styles['Normal'])
        else:
            logo_img = Paragraph("<font size=8>[LOGO]</font>", styles['Normal'])
        
        # Columna 2: Dirección y contacto
        contact_section = Paragraph(f"""
            <para align=center>
            <font size=9><b>MERCY MELENDEZ AHUANARI</b></font><br/>
            <font size=8>NIT: 21.114.493-4</font><br/>
            <font size=7>No Responsable de IVA</font><br/>
            <font size=8>Carrera 5 # 7-17</font><br/>
            <font size=8>Villeta/CUND</font><br/>
            <font size=8>Tel: 3192589035</font>
            </para>
        """, styles['Normal'])
        
        # Columna 3: QR Code (ajustado al tamaño del contenido)
        if hasattr(invoice, 'qr_code_image') and invoice.qr_code_image:
            try:
                qr_img = RLImage(invoice.qr_code_image.path, width=1*inch, height=1*inch)
            except:
                qr_img = Paragraph("<font size=6>QR</font>", styles['Normal'])
        else:
            qr_img = Paragraph("<font size=6>[QR]</font>", styles['Normal'])
        
        # Tabla de encabezado (una sola fila)
        header_table = Table([[logo_img, contact_section, qr_img]], colWidths=[2.2*inch, 3.3*inch, 1.7*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 6))
        
        # CUFE/CUDE
        cufe_para = Paragraph(f"""
            <para align=left fontSize=6>
            <b>CUFE/CUDE:</b> {invoice.cude}
            </para>
        """, styles['Normal'])
        
        cufe_table = Table([[cufe_para]], colWidths=[7.2*inch])
        cufe_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(cufe_table)
        story.append(Spacer(1, 6))
        
        # FILA 2: Info Cliente | Info Factura
        # Obtener mecánico y placa
        mechanic_name = "N/A"
        vehicle_plate = "N/A"
        
        if invoice.work_order:
            if invoice.work_order.assigned_mechanic:
                mechanic_name = invoice.work_order.assigned_mechanic.full_name
            if invoice.work_order.vehicle:
                vehicle_plate = invoice.work_order.vehicle.license_plate or "N/A"
        
        # Columna izquierda: Datos del adquiriente
        client_info = Paragraph(f"""
            <para fontSize=7>
            <b>Cliente:</b> {invoice.customer_name}<br/>
            <b>NIT:</b> {invoice.customer_document}<br/>
            <b>Tel:</b> {invoice.customer_phone or 'N/A'}<br/>
            <b>Dirección:</b> {invoice.customer_address or 'N/A'}<br/>
            <b>Email:</b> {invoice.customer_email or 'N/A'}<br/>
            <b>Establecimiento:</b> {invoice.customer_name}<br/>
            <b>Orden de Pedido:</b> {invoice.work_order.order_number if invoice.work_order else 'N/A'}
            </para>
        """, styles['Normal'])
        
        # Columna derecha: Datos del emisor (info completa)
        invoice_info = Paragraph(f"""
            <para fontSize=7>
            <b>Razón Social:</b> Mercy Melendez Ahuanari<br/>
            <b>Nombre Comercial:</b> SERVIMOTOS - CENTRO<br/>
            <b>Nit del Emisor:</b> 21.114.493-4<br/>
            <b>Tipo de Contribuyente:</b> Persona Natural<br/>
            <b>Actividad Económica:</b> G4541<br/>
            <b>Correo:</b> 123mercym@gmail.com<br/>
            <b>Móvil:</b> 3192589035<br/>
            <b>Dirección:</b> Carrera 5 # 7-17<br/>
            Villeta/CUND
            </para>
        """, styles['Normal'])
        
        # Títulos con fondo gris
        title_adquiriente = Paragraph("<b>DATOS DEL ADQUIRIENTE</b>", ParagraphStyle(
            'TitleAdq', parent=styles['Normal'], fontSize=8, alignment=1
        ))
        title_emisor = Paragraph("<b>DATOS DEL EMISOR</b>", ParagraphStyle(
            'TitleEmi', parent=styles['Normal'], fontSize=8, alignment=1
        ))
        
        info_data = [
            [title_adquiriente, title_emisor],
            [client_info, invoice_info]
        ]
        
        info_table = Table(info_data, colWidths=[3.6*inch, 3.6*inch])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 1), (-1, 1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 6))
        
        # ================================================================
        # DATOS DEL DOCUMENTO (Título + 2 columnas)
        # ================================================================
        
        # Obtener mecánico
        mechanic_name = "N/A"
        if invoice.work_order and invoice.work_order.assigned_mechanic:
            mechanic_name = invoice.work_order.assigned_mechanic.full_name
        
        # Título
        doc_title = Paragraph("<b>DATOS DEL DOCUMENTO</b>", ParagraphStyle(
            'DocTitle', parent=styles['Normal'], fontSize=8, alignment=1
        ))
        
        # Columna izquierda (3 items)
        doc_col1 = Paragraph(f"""
            <para fontSize=7>
            <b>Factura Electronica de venta No. <font color="red">{invoice.invoice_number}</font></b><br/>
            <b>F.E:</b> {invoice.issue_date.strftime('%Y-%m-%d')}<br/>
            <b>F.V:</b> {invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A'}
            </para>
        """, styles['Normal'])
        
        # Columna derecha (3 items)
        doc_col2 = Paragraph(f"""
            <para fontSize=7>
            <b>Tipo de negociación:</b> Contado<br/>
            <b>Medio de Pago:</b> Efectivo<br/>
            <b>Fecha firmado:</b> {invoice.issue_date.strftime('%Y-%m-%d %H:%M:%S')}
            </para>
        """, styles['Normal'])
        
        doc_data = [
            [doc_title],
            [doc_col1, doc_col2]
        ]
        
        doc_table = Table(doc_data, colWidths=[3.6*inch, 3.6*inch])
        doc_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 1), (-1, 1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(doc_table)
        story.append(Spacer(1, 8))
        
        # ================================================================
        # TABLA DE PRODUCTOS/SERVICIOS
        # ================================================================
        
        products_data = [['Código', 'Descripción', 'UND', 'Cant.', 'Vr. Unit', 'Vr. Total']]
        
        for detail in invoice.details.all():
            # Calcular precio unitario sin impuestos
            unit_price_no_tax = detail.subtotal / detail.quantity if detail.quantity > 0 else detail.unit_price
            total_no_tax = detail.subtotal
            
            products_data.append([
                detail.part_number or detail.unspsc_code or 'N/A',
                detail.description[:45],
                detail.unit_code or 'UND',
                f"{detail.quantity:.0f}",
                f"${unit_price_no_tax:,.0f}",
                f"${total_no_tax:,.0f}"
            ])
        
        products_table = Table(products_data, colWidths=[0.7*inch, 2.5*inch, 0.5*inch, 0.5*inch, 1*inch, 1*inch])
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
        story.append(Spacer(1, 4))
        
        # Forma de pago y total (debajo de productos)
        payment_data = [[
            'Forma de Pago',
            'Efectivo - CONTADO',
            'Total',
            f"${invoice.subtotal:,.0f}"  # Subtotal sin IVA
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
        story.append(Spacer(1, 6))
        
        # Observaciones
        obs_text = Paragraph("<b>Observaciones:</b>", ParagraphStyle('Obs', parent=styles['Normal'], fontSize=7))
        story.append(obs_text)
        story.append(Spacer(1, 2))
        
        # Valor en letras
        valor_letras = Paragraph("<b>VALOR EN LETRAS:</b> CIENTO SETENTA Y OCHO MIL QUINIENTOS PESOS M/CTE",
                                ParagraphStyle('ValorLetras', parent=styles['Normal'], fontSize=7))
        story.append(valor_letras)
        story.append(Spacer(1, 10))
        
        # ================================================================
        # PIE DE PÁGINA LEGAL
        # ================================================================
        
        legal_text = """
        <para align=justify fontSize=6>
        <b>LA PRESENTE FACTURA ES UN TITULO VALOR DE ACUERDO A LO ESTABLECIDO EN EL ARTÍCULO 772 DEL CÓDIGO DE COMERCIO Y LEY 1231/08</b><br/><br/>
        <b>Resolución DIAN No. 18764100117389 del 15/10/2025 – Vigencia hasta el 15/10/2027.</b><br/>
        <b>Rango autorizado: SMFE0001 al SMFE2000.</b><br/>
        No responsable de IVA – Art. 437 E.T.<br/>
        Actividad Económica: G4541 – Venta de partes, piezas y accesorios (repuestos) para vehículos automotores y motocicletas.
        </para>
        """
        
        story.append(Paragraph(legal_text, styles['Normal']))
        
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
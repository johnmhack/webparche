from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os
import logging

from .models import Invoice, InvoiceDetail, ElectronicInvoice, ElectronicInvoiceDetail

# Configurar logging
logger = logging.getLogger(__name__)


def generate_invoice_pdf(invoice_id):
    """
    Genera un PDF de factura con mejor layout y manejo de errores
    """
    try:
        logger.info(f"Generando PDF para factura ID: {invoice_id}")

        # Validar entrada
        if not invoice_id:
            raise ValueError("ID de factura requerido")

        # Obtener factura con validaciones
        try:
            invoice = Invoice.objects.select_related('workshop', 'customer').prefetch_related('details').get(id=invoice_id)
        except Invoice.DoesNotExist:
            logger.error(f"Factura con ID {invoice_id} no encontrada")
            raise ValueError("Factura no encontrada")
        except Exception as e:
            logger.error(f"Error obteniendo factura {invoice_id}: {str(e)}")
            raise ValueError(f"Error accediendo a la factura: {str(e)}")

        logger.info(f"Factura encontrada: {invoice.invoice_number}, detalles: {invoice.details.count()}")

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Crear documento con mejor configuración
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        # Estilos mejorados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=1,  # Centrado
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            leading=12
        )

        company_style = ParagraphStyle(
            'Company',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=14
        )

        # Contenido del PDF
        story = []

        # Encabezado con logo y título
        header_data = [
            [
                Paragraph(f"""
                <b>{invoice.workshop_name or 'TALLER MECÁNICO'}</b><br/>
                NIT: {invoice.workshop_nit or 'N/A'}<br/>
                {invoice.workshop_address or 'Dirección no especificada'}<br/>
                Tel: {invoice.workshop_phone or 'N/A'} | Email: {invoice.workshop_email or 'N/A'}
                """, company_style),
                Paragraph(f"""
                <b>FACTURA DE VENTA</b><br/>
                <br/>
                <b>N° Factura:</b> {invoice.invoice_number}<br/>
                <b>Fecha Emisión:</b> {invoice.issue_date.strftime('%d/%m/%Y %H:%M')}<br/>
                <b>Fecha Vencimiento:</b> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}
                """, header_style)
            ]
        ]

        header_table = Table(header_data, colWidths=[4*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 20))

        # Información del cliente en formato mejorado
        customer_title = Paragraph("<b>INFORMACIÓN DEL CLIENTE</b>", styles['Heading2'])
        story.append(customer_title)
        story.append(Spacer(1, 10))

        customer_data = [
            [
                Paragraph(f"""
                <b>Nombre/Razón Social:</b><br/>
                {invoice.customer_name or 'Cliente no especificado'}<br/>
                <br/>
                <b>Documento:</b><br/>
                {invoice.customer_document or 'N/A'}<br/>
                <br/>
                <b>Dirección:</b><br/>
                {invoice.customer_address or 'Dirección no especificada'}
                """, header_style),
                Paragraph(f"""
                <b>Teléfono:</b><br/>
                {invoice.customer_phone or 'N/A'}<br/>
                <br/>
                <b>Email:</b><br/>
                {invoice.customer_email or 'N/A'}<br/>
                <br/>
                <b>Ciudad:</b><br/>
                {getattr(invoice.customer, 'city', 'N/A') if hasattr(invoice, 'customer') and invoice.customer else 'N/A'}
                """, header_style)
            ]
        ]

        customer_table = Table(customer_data, colWidths=[3.5*inch, 3.5*inch])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        story.append(customer_table)
        story.append(Spacer(1, 20))

        # Detalles de productos/servicios
        details_title = Paragraph("<b>DETALLE DE PRODUCTOS/SERVICIOS</b>", styles['Heading2'])
        story.append(details_title)
        story.append(Spacer(1, 10))

        # Tabla de productos mejorada
        table_data = [
            ['Código', 'Descripción', 'Cant.', 'V. Unitario', 'Descuento', 'IVA', 'Total']
        ]

        for detail in invoice.details.all():
            try:
                table_data.append([
                    detail.part_number or detail.part.part_number if hasattr(detail, 'part') and detail.part else 'N/A',
                    detail.description[:60] + '...' if len(detail.description) > 60 else detail.description,
                    f"{detail.quantity:.2f}",
                    f"${detail.unit_price:,.0f}",
                    f"${detail.discount:,.0f}",
                    f"${detail.tax_amount:,.0f}",
                    f"${detail.total:,.0f}"
                ])
            except Exception as e:
                logger.warning(f"Error procesando detalle de factura: {str(e)}")
                continue

        # Estilos de tabla mejorados
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ])

        col_widths = [1*inch, 3*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch]
        details_table = Table(table_data, colWidths=col_widths)
        details_table.setStyle(table_style)

        story.append(details_table)
        story.append(Spacer(1, 15))

        # Totales mejorados
        totals_title = Paragraph("<b>TOTALES</b>", styles['Heading2'])
        story.append(totals_title)
        story.append(Spacer(1, 10))

        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:,.0f}"],
            [f'IVA ({invoice.tax_rate}%):', f"${invoice.tax_amount:,.0f}"],
            ['Descuentos:', f"${invoice.discount:,.0f}"],
            ['TOTAL A PAGAR:', f"${invoice.total:,.0f}"]
        ]

        totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.darkblue),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))

        story.append(totals_table)
        story.append(Spacer(1, 20))

        # Información adicional y pie de página
        footer_info = f"""
        <b>Forma de Pago:</b> {invoice.get_payment_method_display() if hasattr(invoice, 'get_payment_method_display') else 'N/A'}<br/>
        <b>Estado:</b> {invoice.get_payment_status_display() if hasattr(invoice, 'get_payment_status_display') else 'N/A'}<br/>
        <br/>
        <i>Esta factura se emite conforme a la legislación colombiana vigente.</i><br/>
        <i>Factura generada electrónicamente - No requiere firma manuscrita.</i>
        """

        if hasattr(invoice, 'workshop') and invoice.workshop and invoice.workshop.invoice_footer:
            footer_info += f"<br/><br/>{invoice.workshop.invoice_footer}"

        if invoice.notes:
            footer_info += f"<br/><br/><b>Notas:</b> {invoice.notes}"

        story.append(Paragraph(footer_info, styles['Normal']))

        # Generar PDF con manejo de errores
        try:
            logger.info(f"Construyendo PDF con {len(story)} elementos")
            doc.build(story)

            # Obtener el PDF del buffer
            pdf_data = buffer.getvalue()
            buffer.close()

            logger.info(f"PDF generado exitosamente, tamaño: {len(pdf_data)} bytes")
            return pdf_data

        except Exception as e:
            logger.error(f"Error construyendo PDF: {str(e)}")
            buffer.close()
            raise ValueError(f"Error generando el archivo PDF: {str(e)}")

    except ValueError:
        # Re-lanzar errores de validación
        raise
    except Exception as e:
        logger.error(f"Error inesperado generando PDF para factura {invoice_id}: {str(e)}")
        raise ValueError(f"Error generando PDF: {str(e)}")


def generate_electronic_invoice_pdf(invoice_id):
    """
    Genera un PDF de factura electrónica DIAN con mejor layout y manejo de errores
    """
    try:
        logger.info(f"Generando PDF electrónico para factura ID: {invoice_id}")

        # Validar entrada
        if not invoice_id:
            raise ValueError("ID de factura electrónica requerido")

        # Obtener factura con validaciones
        try:
            invoice = ElectronicInvoice.objects.select_related('workshop', 'customer', 'work_order').prefetch_related('details').get(id=invoice_id)
        except ElectronicInvoice.DoesNotExist:
            logger.error(f"Factura electrónica con ID {invoice_id} no encontrada")
            raise ValueError("Factura electrónica no encontrada")
        except Exception as e:
            logger.error(f"Error obteniendo factura electrónica {invoice_id}: {str(e)}")
            raise ValueError(f"Error accediendo a la factura electrónica: {str(e)}")

        logger.info(f"Factura electrónica encontrada: {invoice.invoice_number}, detalles: {invoice.details.count()}")

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Crear documento con mejor configuración
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        # Estilos mejorados para facturas electrónicas
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Centrado
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            leading=11
        )

        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )

        # Contenido del PDF
        story = []

        # Título principal mejorado
        story.append(Paragraph("FACTURA ELECTRÓNICA DE VENTA", title_style))
        story.append(Paragraph("Representación Gráfica", ParagraphStyle('CenterNormal', parent=styles['Normal'], alignment=1, fontSize=8, spaceAfter=15)))

        # Sección "Datos del Documento" mejorada
        story.append(Paragraph("<b>DATOS DEL DOCUMENTO</b>", section_style))

        # CUFE destacado
        if invoice.cude:
            cufe_data = [[f"Código Único de Factura Electrónica - CUFE: {invoice.cude}"]]
            cufe_table = Table(cufe_data, colWidths=[7*inch])
            cufe_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(cufe_table)
            story.append(Spacer(1, 8))

        # Datos del documento mejorados
        doc_table_data = [
            [Paragraph("Número de Factura:", header_style), Paragraph(f"<b>{invoice.invoice_number}</b>", header_style), Paragraph("Forma de pago:", header_style), Paragraph(f"<b>{invoice.get_payment_method_display() if hasattr(invoice, 'get_payment_method_display') else 'Contado'}</b>", header_style)],
            [Paragraph("Fecha de Emisión:", header_style), Paragraph(f"<b>{invoice.issue_date.strftime('%d/%m/%Y %H:%M')}</b>", header_style), Paragraph("Medio de Pago:", header_style), Paragraph(f"<b>{invoice.payment_method.title() if invoice.payment_method else 'Efectivo'}</b>", header_style)],
            [Paragraph("Fecha de Vencimiento:", header_style), Paragraph(f"<b>{invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}</b>", header_style), Paragraph("Estado DIAN:", header_style), Paragraph(f"<b>{invoice.get_dian_status_display() if hasattr(invoice, 'get_dian_status_display') else invoice.dian_status.title()}</b>", header_style)],
            [Paragraph("Tipo de Operación:", header_style), Paragraph("<b>10 - Estándar</b>", header_style), Paragraph("Moneda:", header_style), Paragraph("<b>COP - Peso Colombiano</b>", header_style)]
        ]

        doc_table = Table(doc_table_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        doc_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(doc_table)
        story.append(Spacer(1, 8))

        # Sección "Datos del Emisor / Vendedor" mejorada
        story.append(Paragraph("<b>DATOS DEL EMISOR / VENDEDOR</b>", section_style))

        workshop_table_data = [
            [Paragraph("Razón Social:", header_style), Paragraph(f"<b>{invoice.workshop_name}</b>", header_style), Paragraph("Nombre Comercial:", header_style), Paragraph(f"<b>{invoice.workshop_name}</b>", header_style)],
            [Paragraph("NIT del Emisor:", header_style), Paragraph(f"<b>{invoice.workshop_nit}</b>", header_style), Paragraph("País:", header_style), Paragraph("<b>Colombia</b>", header_style)],
            [Paragraph("Tipo de Contribuyente:", header_style), Paragraph("<b>Persona Jurídica</b>", header_style), Paragraph("Departamento:", header_style), Paragraph(f"<b>{invoice.workshop_department or 'N/A'}</b>", header_style)],
            [Paragraph("Régimen Fiscal:", header_style), Paragraph("<b>Responsable de IVA</b>", header_style), Paragraph("Municipio / Ciudad:", header_style), Paragraph(f"<b>{invoice.workshop_city or 'N/A'}</b>", header_style)],
            [Paragraph("Responsabilidad tributaria:", header_style), Paragraph("<b>01 - IVA</b>", header_style), Paragraph("Dirección:", header_style), Paragraph(f"<b>{invoice.workshop_address or 'N/A'}</b>", header_style)],
            [Paragraph("Actividad Económica:", header_style), Paragraph("<b>Servicios de reparación de vehículos</b>", header_style), Paragraph("Teléfono / Móvil:", header_style), Paragraph(f"<b>{invoice.workshop_phone or 'N/A'}</b>", header_style)],
            [Paragraph("Correo:", header_style), Paragraph(f"<b>{invoice.workshop_email or 'N/A'}</b>", header_style), "", ""]
        ]

        workshop_table = Table(workshop_table_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 2*inch])
        workshop_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(workshop_table)
        story.append(Spacer(1, 8))

        # Sección "Datos del Adquiriente / Comprador" mejorada
        story.append(Paragraph("<b>DATOS DEL ADQUIRENTE / COMPRADOR</b>", section_style))

        customer_table_data = [
            [Paragraph("Nombre o Razón Social:", header_style), Paragraph(f"<b>{invoice.customer_name}</b>", header_style), Paragraph("Tipo de Documento:", header_style), Paragraph(f"<b>{invoice.customer_document_type.upper()}</b>", header_style)],
            [Paragraph("Número Documento:", header_style), Paragraph(f"<b>{invoice.customer_document}</b>", header_style), Paragraph("País:", header_style), Paragraph("<b>Colombia</b>", header_style)],
            [Paragraph("Departamento:", header_style), Paragraph(f"<b>{invoice.customer_department or 'N/A'}</b>", header_style), Paragraph("Tipo de Contribuyente:", header_style), Paragraph("<b>Persona Natural</b>", header_style)],
            [Paragraph("Municipio / Ciudad:", header_style), Paragraph(f"<b>{invoice.customer_city or 'N/A'}</b>", header_style), Paragraph("Régimen fiscal:", header_style), Paragraph("<b>R-99-PN</b>", header_style)],
            [Paragraph("Dirección:", header_style), Paragraph(f"<b>{invoice.customer_address or 'N/A'}</b>", header_style), Paragraph("Responsabilidad tributaria:", header_style), Paragraph("<b>01 - IVA</b>", header_style)],
            [Paragraph("Teléfono / Móvil:", header_style), Paragraph(f"<b>{invoice.customer_phone or 'N/A'}</b>", header_style), Paragraph("Correo:", header_style), Paragraph(f"<b>{invoice.customer_email or 'N/A'}</b>", header_style)]
        ]

        customer_table = Table(customer_table_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 2*inch])
        customer_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(customer_table)
        story.append(Spacer(1, 2))

        # Información de la orden de trabajo si existe
        if invoice.work_order:
            work_order_info = f"""
            <b>Orden de Trabajo:</b> {invoice.work_order.order_number}<br/>
            <b>Descripción:</b> {invoice.work_order.description[:100]}...
            """
            story.append(Paragraph(work_order_info, ParagraphStyle('WorkOrder', parent=styles['Normal'], fontSize=8)))
            story.append(Spacer(1, 6))

        # Sección "Detalles de Productos/Servicios" mejorada
        story.append(Paragraph("<b>DETALLE DE PRODUCTOS/SERVICIOS</b>", section_style))

        # Tabla de productos mejorada
        table_data = [
            ['Nro.', 'Código', 'Descripción', 'U/M', 'Cant.', 'Precio Unit.', 'Descuento', 'IVA', 'Total']
        ]

        for i, detail in enumerate(invoice.details.all(), 1):
            try:
                table_data.append([
                    str(i),  # Nro.
                    detail.unspsc_code or detail.part_number or 'N/A',  # Código
                    detail.description[:50] + '...' if len(detail.description) > 50 else detail.description,  # Descripción
                    detail.unit_code or 'EA',  # U/M
                    f"{detail.quantity:.2f}",  # Cantidad
                    f"${detail.unit_price:,.0f}",  # Precio unitario
                    f"${detail.discount:,.0f}",  # Descuento
                    f"${detail.tax_amount:,.0f}",  # IVA
                    f"${detail.total:,.0f}"  # Total
                ])
            except Exception as e:
                logger.warning(f"Error procesando detalle electrónico {i}: {str(e)}")
                continue

        # Crear tabla con anchos mejorados
        col_widths = [0.4*inch, 0.8*inch, 2.8*inch, 0.5*inch, 0.6*inch, 0.9*inch, 0.8*inch, 0.7*inch, 0.9*inch]
        details_table = Table(table_data, colWidths=col_widths)
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))

        story.append(details_table)
        story.append(Spacer(1, 20))

        # Sección "Datos Totales" mejorada
        story.append(Paragraph("<b>DATOS TOTALES</b>", section_style))

        # Código QR si existe
        if hasattr(invoice, 'qr_code_image') and invoice.qr_code_image:
            try:
                from reportlab.platypus import Image
                qr_image = Image(invoice.qr_code_image.path, width=1.2*inch, height=1.2*inch)
                qr_image.hAlign = 'LEFT'

                qr_table_data = [[qr_image]]
                qr_table = Table(qr_table_data, colWidths=[1.2*inch])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(qr_table)
                story.append(Spacer(1, 8))
            except Exception as e:
                logger.warning(f"Error cargando QR code: {str(e)}")

        # Información de timestamps mejorada
        timestamp_table_data = [
            [f"Documento generado el: {invoice.issue_date.strftime('%d/%m/%Y %H:%M:%S')}"],
            [f"Documento validado por la DIAN: {invoice.issue_date.strftime('%d/%m/%Y %H:%M:%S')}"],
            [f"XML Generado por: Software Propio {invoice.workshop_nit}"],
            [f"PDF Generado por: Solución Propia NIT: {invoice.workshop_nit}"]
        ]

        timestamp_table = Table(timestamp_table_data, colWidths=[7*inch])
        timestamp_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(timestamp_table)
        story.append(Spacer(1, 6))

        # Tabla de subtotales mejorada
        totals_data1 = [
            ['Subtotal bruto', f"${invoice.subtotal:,.0f}"],
            ['Descuento global', f"${invoice.discount:,.0f}"],
            ['Recargo global', '0,00'],
            ['Subtotal neto', f"${invoice.subtotal - invoice.discount:,.0f}"]
        ]

        totals_table1 = Table(totals_data1, colWidths=[2*inch, 1.5*inch])
        totals_table1.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(totals_table1)
        story.append(Spacer(1, 10))

        # Tabla de desglose de impuestos mejorada
        tax_breakdown_data = [
            ['Base gravable IVA', f"${invoice.subtotal - invoice.discount:,.0f}"],
            [f'IVA ({invoice.tax_rate}%)', f"${invoice.tax_amount:,.0f}"],
            ['INC (Impuesto Nacional al Consumo)', '0,00'],
            ['Impuesto a las Bolsas Plásticas', '0,00'],
            ['Otros impuestos', '0,00'],
            ['Total impuestos', f"${invoice.tax_amount:,.0f}"]
        ]

        tax_breakdown_table = Table(tax_breakdown_data, colWidths=[2*inch, 1.5*inch])
        tax_breakdown_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tax_breakdown_table)
        story.append(Spacer(1, 10))

        # Tabla final: Total a pagar
        final_totals_data = [
            ['Total neto factura (=)', f"${invoice.subtotal - invoice.discount:,.0f}"],
            ['Total impuestos (+)', f"${invoice.tax_amount:,.0f}"],
            ['Total factura (=) COP', f"${invoice.total:,.0f}"]
        ]

        final_totals_table = Table(final_totals_data, colWidths=[2*inch, 1.5*inch])
        final_totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.darkblue),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(final_totals_table)
        story.append(Spacer(1, 10))


        story.append(Spacer(1, 10))

        # Título "Valores Informativos" en negrita arriba de la tabla de anticipos
        story.append(Paragraph("<b>Valores Informativos</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        # Tabla de anticipos
        anticipos_data = [
            ['ANTICIPOS', '0,00'],
            ['Anticipos', '0,00']
        ]

        anticipos_table = Table(anticipos_data, colWidths=[2*inch, 1.5*inch])
        anticipos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # ANTICIPOS en gris
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(anticipos_table)
        story.append(Spacer(1, 10))

        # Tabla de retenciones
        retenciones_data = [
            ['RETENCIONES', '0,00'],
            ['Rete fuente', '0,00'],
            ['Rete IVA', '0,00'],
            ['Rete ICA', '0,00']
        ]

        retenciones_table = Table(retenciones_data, colWidths=[2*inch, 1.5*inch])
        retenciones_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # RETENCIONES en gris
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(retenciones_table)
        story.append(Spacer(1, 6))

        # Información de autorización DIAN mejorada
        authorization_text = f"""
        <b>Información de Autorización DIAN</b><br/>
        Número de Resolución: {getattr(invoice.dian_resolution, 'resolution_number', 'N/A')}<br/>
        Fecha de Resolución: {getattr(invoice.dian_resolution, 'resolution_date', 'N/A')}<br/>
        Rango autorizado: {getattr(invoice.dian_resolution, 'from_number', 'N/A')} - {getattr(invoice.dian_resolution, 'to_number', 'N/A')}<br/>
        Vigencia hasta: {getattr(invoice.dian_resolution, 'expires_date', 'N/A')}
        """

        story.append(Paragraph(authorization_text, ParagraphStyle('Authorization', parent=styles['Normal'], fontSize=7, spaceAfter=8)))

        # Información adicional de cumplimiento
        compliance_text = """
        <i>Esta factura electrónica cumple con la Resolución 0001 de 2024 de la DIAN.<br/>
        Puede ser validada en el portal de la DIAN usando el CUFE.</i>
        """

        story.append(Paragraph(compliance_text, ParagraphStyle('Compliance', parent=styles['Normal'], fontSize=6, spaceAfter=10)))

        # Generar PDF con manejo de errores mejorado
        try:
            logger.info(f"Construyendo PDF electrónico con {len(story)} elementos")
            doc.build(story)

            # Obtener el PDF del buffer
            pdf_data = buffer.getvalue()
            buffer.close()

            logger.info(f"PDF electrónico generado exitosamente, tamaño: {len(pdf_data)} bytes")
            return pdf_data

        except Exception as e:
            logger.error(f"Error construyendo PDF electrónico: {str(e)}")
            buffer.close()
            raise ValueError(f"Error generando el archivo PDF electrónico: {str(e)}")

    except ValueError:
        # Re-lanzar errores de validación
        raise
    except Exception as e:
        logger.error(f"Error inesperado generando PDF electrónico para factura {invoice_id}: {str(e)}")
        raise ValueError(f"Error generando PDF electrónico: {str(e)}")


def generate_credit_note_pdf(credit_note_id):
    """
    Genera un PDF de nota de crédito
    """
    # Implementación similar pero para notas de crédito
    # Por ahora retorna un placeholder
    raise NotImplementedError("Nota de crédito PDF no implementado aún")


def generate_debit_note_pdf(debit_note_id):
    """
    Genera un PDF de nota de débito
    """
    # Implementación similar pero para notas de débito
    # Por ahora retorna un placeholder
    raise NotImplementedError("Nota de débito PDF no implementado aún")
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os

from .models import Invoice, InvoiceDetail


def generate_invoice_pdf(invoice_id):
    """
    Genera un PDF de factura
    """
    try:
        invoice = Invoice.objects.select_related('workshop', 'customer').prefetch_related('details').get(id=invoice_id)

        # Crear buffer para el PDF
        buffer = BytesIO()

        # Crear documento
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()

        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Centrado
            textColor=colors.darkblue
        )

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black
        )

        # Contenido del PDF
        story = []

        # Título
        story.append(Paragraph("FACTURA", title_style))
        story.append(Spacer(1, 12))

        # Información del taller (encabezado izquierdo)
        workshop_info = f"""
        <b>{invoice.workshop_name}</b><br/>
        NIT: {invoice.workshop_nit}<br/>
        Dirección: {invoice.workshop_address}<br/>
        Teléfono: {invoice.workshop_phone}<br/>
        Email: {invoice.workshop_email}
        """

        # Información de la factura (encabezado derecho)
        invoice_info = f"""
        <b>N° Factura:</b> {invoice.invoice_number}<br/>
        <b>Fecha:</b> {invoice.issue_date.strftime('%d/%m/%Y %H:%M')}<br/>
        <b>Fecha Vencimiento:</b> {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}
        """

        # Crear tabla para el encabezado
        header_data = [
            [Paragraph(workshop_info, header_style), Paragraph(invoice_info, header_style)]
        ]

        header_table = Table(header_data, colWidths=[4*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 20))

        # Información del cliente
        customer_title = Paragraph("<b>Información del Cliente</b>", styles['Heading2'])
        story.append(customer_title)

        customer_info = f"""
        <b>Nombre:</b> {invoice.customer_name}<br/>
        <b>Documento:</b> {invoice.customer_document}<br/>
        <b>Dirección:</b> {invoice.customer_address}<br/>
        <b>Teléfono:</b> {invoice.customer_phone}<br/>
        <b>Email:</b> {invoice.customer_email}
        """

        story.append(Paragraph(customer_info, header_style))
        story.append(Spacer(1, 20))

        # Detalles de la factura
        details_title = Paragraph("<b>Detalles de la Factura</b>", styles['Heading2'])
        story.append(details_title)
        story.append(Spacer(1, 12))

        # Tabla de productos/servicios
        table_data = [
            ['Descripción', 'Cant.', 'V. Unitario', 'Descuento', 'IVA', 'Total']
        ]

        for detail in invoice.details.all():
            table_data.append([
                detail.description[:50] + '...' if len(detail.description) > 50 else detail.description,
                f"{detail.quantity:.2f}",
                f"${detail.unit_price:,.0f}",
                f"${detail.discount:,.0f}",
                f"${detail.tax_amount:,.0f}",
                f"${detail.total:,.0f}"
            ])

        # Estilos de tabla
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ])

        # Crear tabla
        col_widths = [2.5*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch]
        details_table = Table(table_data, colWidths=col_widths)
        details_table.setStyle(table_style)

        story.append(details_table)
        story.append(Spacer(1, 20))

        # Totales
        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:,.0f}"],
            ['IVA ({invoice.tax_rate}%):', f"${invoice.tax_amount:,.0f}"],
            ['Total:', f"${invoice.total:,.0f}"]
        ]

        totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 2), 10),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.darkblue),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(totals_table)
        story.append(Spacer(1, 20))

        # Información adicional
        footer_info = f"""
        <b>Forma de Pago:</b> {invoice.get_payment_method_display()}<br/>
        <b>Estado:</b> {invoice.get_payment_status_display()}<br/>
        <br/>
        <i>Esta factura se emite conforme a la legislación colombiana.</i>
        """

        if invoice.workshop.invoice_footer:
            footer_info += f"<br/><br/>{invoice.workshop.invoice_footer}"

        story.append(Paragraph(footer_info, styles['Normal']))

        # Generar PDF
        doc.build(story)

        # Obtener el PDF del buffer
        pdf_data = buffer.getvalue()
        buffer.close()

        return pdf_data

    except Invoice.DoesNotExist:
        raise ValueError("Factura no encontrada")
    except Exception as e:
        raise ValueError(f"Error generando PDF: {str(e)}")


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
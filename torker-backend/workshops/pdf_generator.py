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

from .models import Invoice, InvoiceDetail, ElectronicInvoice, ElectronicInvoiceDetail


def generate_invoice_pdf(invoice_id):
    """
    Genera un PDF de factura
    """
    try:
        print(f"DEBUG: Iniciando generación de PDF para invoice_id: {invoice_id}")
        invoice = Invoice.objects.select_related('workshop', 'customer').prefetch_related('details').get(id=invoice_id)
        print(f"DEBUG: Factura encontrada: {invoice.invoice_number}, detalles: {invoice.details.count()}")

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

        for i, detail in enumerate(invoice.details.all(), 1):
            print(f"DEBUG: Procesando detalle {i}: {detail.description}, cantidad: {detail.quantity}, precio: {detail.unit_price}")
            table_data.append([
                '',  # IMPUESTOS
                f"${detail.unit_price:,.0f}",  # Precio unitario de venta
                str(i),  # Nro.
                detail.unspsc_code or '',  # Código
                detail.description[:50] + '...' if len(detail.description) > 50 else detail.description,  # Descripción
                'NIU' if detail.quantity.is_integer() else 'E48',  # U/M
                f"{detail.quantity:.2f}",  # Cantidad
                f"${detail.unit_price:,.0f}",  # Precio unitario
                f"${detail.discount:,.0f}",  # Descuento detalle
                '0,00',  # Recargo detalle
                f"{invoice.tax_rate:.0f}",  # IVA %
                '0.00'  # INC %
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

        # Crear tabla con anchos ajustados para formato DIAN
        col_widths = [0.5*inch, 0.8*inch, 0.4*inch, 0.8*inch, 2.5*inch, 0.5*inch, 0.6*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.5*inch]
        details_table = Table(table_data, colWidths=col_widths)
        details_table.setStyle(table_style)

        story.append(details_table)
        story.append(Spacer(1, 8))

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
        print(f"DEBUG: Construyendo PDF con {len(story)} elementos")
        doc.build(story)

        # Obtener el PDF del buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        print(f"DEBUG: PDF generado exitosamente, tamaño: {len(pdf_data)} bytes")

        return pdf_data

    except Invoice.DoesNotExist:
        raise ValueError("Factura no encontrada")
    except Exception as e:
        raise ValueError(f"Error generando PDF: {str(e)}")


def generate_electronic_invoice_pdf(invoice_id):
    """
    Genera un PDF de factura electrónica DIAN
    """
    try:
        invoice = ElectronicInvoice.objects.select_related('workshop', 'customer', 'work_order').prefetch_related('details').get(id=invoice_id)

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

        # Título principal centrado
        story.append(Paragraph("FACTURA ELECTRÓNICA DE VENTA", ParagraphStyle('CenterTitle', parent=styles['Heading1'], fontSize=12, alignment=1, spaceAfter=10)))
        story.append(Paragraph("Representación Gráfica", ParagraphStyle('CenterNormal', parent=styles['Normal'], alignment=1, fontSize=8)))
        story.append(Spacer(1, 2))

        # Sección "Datos del Documento" - Formato de tabla con CUFE separado
        story.append(Paragraph("<b>Datos del Documento</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        # CUFE en línea separada con fuente más pequeña
        cufe_table_data = [
            [f"Código Único de Factura - CUFE: {invoice.cude}"]
        ]

        cufe_table = Table(cufe_table_data, colWidths=[7*inch])
        cufe_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))

        story.append(cufe_table)
        story.append(Spacer(1, 3))

        # Resto de datos del documento
        doc_table_data = [
            [Paragraph("Número de Factura:", styles['Normal']), Paragraph(f"<b>{invoice.invoice_number}</b>", styles['Normal']), Paragraph("Forma de pago:", styles['Normal']), Paragraph("<b>Contado</b>", styles['Normal'])],
            [Paragraph("Fecha de Emisión:", styles['Normal']), Paragraph(f"<b>{invoice.issue_date.strftime('%d/%m/%Y %H:%M')}</b>", styles['Normal']), Paragraph("Medio de Pago:", styles['Normal']), Paragraph("<b>Efectivo</b>", styles['Normal'])],
            [Paragraph("Fecha de Vencimiento:", styles['Normal']), Paragraph(f"<b>{invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}</b>", styles['Normal']), Paragraph("Orden de pedido:", styles['Normal']), Paragraph("<b></b>", styles['Normal'])],
            [Paragraph("Tipo de Operación:", styles['Normal']), Paragraph("<b>10 - Estándar</b>", styles['Normal']), Paragraph("Fecha de orden de pedido:", styles['Normal']), Paragraph("<b></b>", styles['Normal'])]
        ]

        doc_table = Table(doc_table_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        doc_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(doc_table)
        story.append(Spacer(1, 8))

        # Sección "Datos del Emisor / Vendedor" - Formato de tabla de 2 columnas
        story.append(Paragraph("<b>Datos del Emisor / Vendedor</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        workshop_table_data = [
            [Paragraph("Razón Social:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_name}</b>", styles['Normal']), Paragraph("Nombre Comercial:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_name}</b>", styles['Normal'])],
            [Paragraph("Nit del Emisor:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_nit}</b>", styles['Normal']), Paragraph("País:", styles['Normal']), Paragraph("<b>Colombia</b>", styles['Normal'])],
            [Paragraph("Tipo de Contribuyente:", styles['Normal']), Paragraph("<b>Persona Jurídica</b>", styles['Normal']), Paragraph("Departamento:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_department}</b>", styles['Normal'])],
            [Paragraph("Régimen Fiscal:", styles['Normal']), Paragraph("<b>Responsable de IVA</b>", styles['Normal']), Paragraph("Municipio / Ciudad:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_city}</b>", styles['Normal'])],
            [Paragraph("Responsabilidad tributaria:", styles['Normal']), Paragraph("<b>01 - IVA</b>", styles['Normal']), Paragraph("Dirección:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_address}</b>", styles['Normal'])],
            [Paragraph("Actividad Económica:", styles['Normal']), Paragraph("<b>Servicios de reparación de vehículos</b>", styles['Normal']), Paragraph("Teléfono / Móvil:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_phone}</b>", styles['Normal'])],
            [Paragraph("Correo:", styles['Normal']), Paragraph(f"<b>{invoice.workshop_email}</b>", styles['Normal']), "", ""]
        ]

        workshop_table = Table(workshop_table_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 2*inch])
        workshop_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(workshop_table)
        story.append(Spacer(1, 8))

        # Sección "Datos del Adquiriente / Comprador" - Formato de tabla de 4 columnas
        story.append(Paragraph("<b>Datos del Adquiriente / Comprador</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        customer_table_data = [
            [Paragraph("Nombre o Razón Social:", styles['Normal']), Paragraph(f"<b>{invoice.customer_name}</b>", styles['Normal']), Paragraph("Tipo de Documento:", styles['Normal']), Paragraph(f"<b>{invoice.customer_document_type.upper()}</b>", styles['Normal'])],
            [Paragraph("Número Documento:", styles['Normal']), Paragraph(f"<b>{invoice.customer_document}</b>", styles['Normal']), Paragraph("País:", styles['Normal']), Paragraph("<b>Colombia</b>", styles['Normal'])],
            [Paragraph("Departamento:", styles['Normal']), Paragraph(f"<b>{invoice.customer_department}</b>", styles['Normal']), Paragraph("Tipo de Contribuyente:", styles['Normal']), Paragraph("<b>Persona Natural</b>", styles['Normal'])],
            [Paragraph("Municipio / Ciudad:", styles['Normal']), Paragraph(f"<b>{invoice.customer_city}</b>", styles['Normal']), Paragraph("Régimen fiscal:", styles['Normal']), Paragraph("<b>R-99-PN</b>", styles['Normal'])],
            [Paragraph("Dirección:", styles['Normal']), Paragraph(f"<b>{invoice.customer_address}</b>", styles['Normal']), Paragraph("Responsabilidad tributaria:", styles['Normal']), Paragraph("<b>01 - IVA</b>", styles['Normal'])],
            [Paragraph("Teléfono / Móvil:", styles['Normal']), Paragraph(f"<b>{invoice.customer_phone}</b>", styles['Normal']), Paragraph("Correo:", styles['Normal']), Paragraph(f"<b>{invoice.customer_email}</b>", styles['Normal'])]
        ]

        customer_table = Table(customer_table_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 2*inch])
        customer_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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

        # Sección "Detalles de Productos"
        story.append(Paragraph("<b>Detalles de Productos</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        # Tabla de productos con formato DIAN completo
        table_data = [
            ['Nro.', 'Código', 'Descripción', 'U/M', 'Cant.', 'Precio unit.', 'Descuento\ndetalle', 'Recargo\ndetalle', 'IVA %', 'INC %']
        ]

        for i, detail in enumerate(invoice.details.all(), 1):
            table_data.append([
                str(i),  # Nro.
                'T843',  # Código (como en el ejemplo)
                detail.description[:50] + '...' if len(detail.description) > 50 else detail.description,  # Descripción
                '94',  # U/M (como en el ejemplo)
                f"{detail.quantity:.2f}",  # Cantidad
                f"{detail.unit_price:,.0f}",  # Precio unitario
                '0,00',  # Descuento detalle
                '0,00',  # Recargo detalle
                '0.00',  # IVA %
                '0.00'  # INC %
            ])

        # Crear tabla con anchos apropiados
        col_widths = [0.4*inch, 0.8*inch, 2.5*inch, 0.5*inch, 0.6*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.5*inch]
        details_table = Table(table_data, colWidths=col_widths)
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(details_table)
        story.append(Spacer(1, 20))

        # Sección "Datos Totales"
        story.append(Paragraph("<b>Datos Totales</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=9, spaceAfter=2)))
        story.append(Spacer(1, 2))

        # Código QR debajo del título "Datos Totales"
        if invoice.qr_code_image:
            from reportlab.platypus import Image

            # Crear imagen QR
            qr_image = Image(invoice.qr_code_image.path, width=1.2*inch, height=1.2*inch)
            qr_image.hAlign = 'LEFT'

            # Tabla para el QR
            qr_table_data = [[qr_image]]
            qr_table = Table(qr_table_data, colWidths=[1.2*inch])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))

            story.append(qr_table)
            story.append(Spacer(1, 6))

        # Información de timestamps en tabla
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
        ]))

        story.append(timestamp_table)
        story.append(Spacer(1, 6))

        # Primera tabla: Subtotal, descuentos y recargos
        totals_data1 = [
            ['Subtotal', f"${invoice.subtotal:,.0f}"],
            ['Descuento detalle', '0,00'],
            ['Recargo detalle', '0,00'],
            ['Total', f"${invoice.subtotal:,.0f}"]
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

        # Tabla intermedia: Desglose de impuestos
        tax_breakdown_data = [
            ['Total bruto factura', f"${invoice.subtotal:,.0f}"],
            ['IVA', f"${invoice.tax_amount:,.0f}"],
            ['INC', '0,00'],
            ['Bolsas', '0,00'],
            ['Otros impuestos', '0,00'],
            ['Total impuesto (=)', f"${invoice.total:,.0f}"]
        ]

        tax_breakdown_table = Table(tax_breakdown_data, colWidths=[2*inch, 1.5*inch])
        tax_breakdown_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Total bruto en gris
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Total impuesto en gris
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tax_breakdown_table)
        story.append(Spacer(1, 10))

        # Tabla final: Total neto, descuentos globales y total final
        final_totals_data = [
            ['Total neto factura (=)', f"${invoice.subtotal:,.0f}"],
            ['Descuento global (-)', '0,00'],
            ['Recargo global (+)', '0,00'],
            ['Total factura (=) COP $', f"${invoice.total:,.0f}"]
        ]

        final_totals_table = Table(final_totals_data, colWidths=[2*inch, 1.5*inch])
        final_totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Total neto en gris
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Total factura en gris
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

        # Información de autorización DIAN en texto plano con más separación
        authorization_text = """
        Número de Autorización: 18764100117389<br/><br/>
        Rango desde: 1<br/><br/>
        Rango hasta: 2000<br/><br/>
        Vigencia: 2026-10-15
        """

        story.append(Paragraph(authorization_text, ParagraphStyle('Authorization', parent=styles['Normal'], fontSize=8, spaceAfter=6)))
        story.append(Spacer(1, 6))

        # Generar PDF
        doc.build(story)

        # Obtener el PDF del buffer
        pdf_data = buffer.getvalue()
        buffer.close()

        return pdf_data

    except ElectronicInvoice.DoesNotExist:
        raise ValueError("Factura electrónica no encontrada")
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
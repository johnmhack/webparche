#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para listar y generar PDFs de facturas existentes
Uso: python generate_test_invoice_pdf.py
"""
import os
import sys
import django

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from workshops.models import Invoice, ElectronicInvoice
from workshops.pdf_generator import generate_invoice_pdf, generate_electronic_invoice_pdf


def list_invoices():
    """Listar todas las facturas normales"""
    print("\n" + "="*80)
    print("FACTURAS NORMALES")
    print("="*80)
    
    invoices = Invoice.objects.all().order_by('-issue_date')[:10]
    
    if not invoices:
        print("[X] No hay facturas normales en la base de datos")
        return None
    
    for i, invoice in enumerate(invoices, 1):
        print(f"\n{i}. ID: {invoice.id}")
        print(f"   Número: {invoice.invoice_number}")
        print(f"   Cliente: {invoice.customer_name}")
        print(f"   Fecha: {invoice.issue_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Total: ${invoice.total:,.2f}")
        print(f"   Estado: {invoice.get_payment_status_display()}")
    
    return invoices


def list_electronic_invoices():
    """Listar todas las facturas electrónicas"""
    print("\n" + "="*80)
    print("FACTURAS ELECTRÓNICAS DIAN")
    print("="*80)
    
    e_invoices = ElectronicInvoice.objects.all().order_by('-issue_date')[:10]
    
    if not e_invoices:
        print("[X] No hay facturas electronicas en la base de datos")
        return None
    
    for i, invoice in enumerate(e_invoices, 1):
        print(f"\n{i}. ID: {invoice.id}")
        print(f"   Número: {invoice.invoice_number}")
        print(f"   Cliente: {invoice.customer_name}")
        print(f"   Fecha: {invoice.issue_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Total: ${invoice.total:,.2f}")
        print(f"   Estado DIAN: {invoice.get_dian_status_display()}")
        print(f"   CUDE: {invoice.cude[:20]}..." if invoice.cude else "   CUDE: No generado")
    
    return e_invoices


def generate_pdf(invoice_type='electronic'):
    """Generar PDF de la factura más reciente"""
    
    if invoice_type == 'electronic':
        invoices = ElectronicInvoice.objects.all().order_by('-issue_date')
        if not invoices:
            print("\n[X] No hay facturas electronicas para generar PDF")
            return
        
        invoice = invoices.first()
        print(f"\n[PDF] Generando PDF de factura electronica: {invoice.invoice_number}")
        
        try:
            pdf_data = generate_electronic_invoice_pdf(invoice.id)
            filename = f"factura_electronica_{invoice.invoice_number}.pdf"
            
            with open(filename, 'wb') as f:
                f.write(pdf_data)
            
            print(f"[OK] PDF generado exitosamente: {filename}")
            print(f"   Tamano: {len(pdf_data):,} bytes")
            print(f"   Ubicacion: {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"[ERROR] Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()
    
    else:  # normal invoice
        invoices = Invoice.objects.all().order_by('-issue_date')
        if not invoices:
            print("\n[X] No hay facturas normales para generar PDF")
            return
        
        invoice = invoices.first()
        print(f"\n[PDF] Generando PDF de factura normal: {invoice.invoice_number}")
        
        try:
            pdf_data = generate_invoice_pdf(invoice.id)
            filename = f"factura_{invoice.invoice_number}.pdf"
            
            with open(filename, 'wb') as f:
                f.write(pdf_data)
            
            print(f"[OK] PDF generado exitosamente: {filename}")
            print(f"   Tamano: {len(pdf_data):,} bytes")
            print(f"   Ubicacion: {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"[ERROR] Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """Función principal"""
    print("\n" + "="*80)
    print("GENERADOR DE PDFs DE FACTURAS")
    print("="*80)
    
    # Listar facturas normales
    normal_invoices = list_invoices()
    
    # Listar facturas electrónicas
    electronic_invoices = list_electronic_invoices()
    
    # Determinar qué tipo generar
    if electronic_invoices:
        print("\n" + "="*80)
        print("GENERANDO PDF DE LA FACTURA ELECTRÓNICA MÁS RECIENTE")
        print("="*80)
        generate_pdf('electronic')
    elif normal_invoices:
        print("\n" + "="*80)
        print("GENERANDO PDF DE LA FACTURA NORMAL MÁS RECIENTE")
        print("="*80)
        generate_pdf('normal')
    else:
        print("\n[X] No hay facturas en la base de datos")
        print("\n[INFO] Sugerencia: Crea una factura primero usando el API o Django admin")
    
    print("\n" + "="*80)
    print("PROCESO COMPLETADO")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
"""
Script de prueba para certificado digital Camerfirma
NO modifica el generador de PDF existente
"""
import os
import sys
import django

# Configurar encoding UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from django.conf import settings
from workshops.dian_signature import DIANSignature


def test_certificate():
    """Prueba carga y validación del certificado"""
    print("\n" + "="*80)
    print("PRUEBA DE CERTIFICADO DIGITAL CAMERFIRMA")
    print("="*80)
    
    cert_path = os.path.join(settings.BASE_DIR, settings.DIAN_CERTIFICATE_PATH)
    cert_password = settings.DIAN_CERTIFICATE_PASSWORD
    
    print(f"\n[1] Ruta certificado: {cert_path}")
    print(f"[2] Archivo existe: {os.path.exists(cert_path)}")
    
    if not os.path.exists(cert_path):
        print("\n[X] ERROR: Certificado no encontrado")
        return False
    
    try:
        # Inicializar firmador
        print("\n[3] Inicializando firmador...")
        signer = DIANSignature(cert_path, cert_password)
        
        # Cargar certificado
        print("[4] Cargando certificado...")
        signer.load_certificate()
        print("[OK] Certificado cargado exitosamente")
        
        # Obtener información
        print("\n[5] Informacion del certificado:")
        cert_info = signer.get_certificate_info()
        
        print(f"   - Subject: {cert_info['subject']}")
        print(f"   - Issuer: {cert_info['issuer']}")
        print(f"   - Serial: {cert_info['serial_number']}")
        print(f"   - Valido desde: {cert_info['not_valid_before']}")
        print(f"   - Valido hasta: {cert_info['not_valid_after']}")
        
        # Verificar vigencia
        from datetime import datetime
        now = datetime.now()
        
        if now < cert_info['not_valid_before']:
            print("\n[!] ADVERTENCIA: Certificado aun no valido")
        elif now > cert_info['not_valid_after']:
            print("\n[X] ERROR: Certificado expirado")
        else:
            print("\n[OK] Certificado vigente")
        
        print("\n" + "="*80)
        print("PRUEBA COMPLETADA EXITOSAMENTE")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        print("\n" + "="*80)
        print("PRUEBA FALLIDA")
        print("="*80 + "\n")
        return False


if __name__ == '__main__':
    test_certificate()
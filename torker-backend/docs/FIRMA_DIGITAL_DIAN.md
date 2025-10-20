# Guía de Firma Digital para Facturación Electrónica DIAN

## 📋 Resumen

Este documento explica cómo integrar el certificado digital de Camerfirma para firmar facturas electrónicas según los requisitos de la DIAN.

## 🔐 Certificado Digital Camerfirma

### ¿Qué es?

El certificado digital es un archivo `.p12` o `.pfx` que contiene:
- Tu clave privada (para firmar)
- Tu certificado público (para validar)
- Cadena de certificados de Camerfirma

### ¿Dónde obtenerlo?

1. **Email de Camerfirma**: Revisa el correo de confirmación de compra
2. **Portal Camerfirma**: Descarga desde tu cuenta
3. **Soporte**: Contacta a soporte@camerfirma.com

## 📦 Instalación

### 1. Instalar dependencias

```bash
pip install cryptography signxml lxml
```

### 2. Guardar certificado

```bash
# Crear carpeta si no existe
mkdir -p torker-backend/workshops/certificates

# Copiar tu certificado
cp /ruta/a/tu/certificado.p12 torker-backend/workshops/certificates/
```

### 3. Configurar variables de entorno

Edita `torker-backend/.env`:

```env
# Certificado Digital Camerfirma
DIAN_CERTIFICATE_PATH=workshops/certificates/certificado.p12
DIAN_CERTIFICATE_PASSWORD=tu_contraseña_aqui
```

## 🚀 Uso

### Ejemplo básico

```python
from workshops.dian_signature import DIANSignature, prepare_invoice_for_signature
from workshops.dian_xml_generator import generate_electronic_invoice_xml

# 1. Generar XML sin firma
xml_content = generate_electronic_invoice_xml(invoice)

# 2. Inicializar firmador
signer = DIANSignature(
    certificate_path='workshops/certificates/certificado.p12',
    certificate_password='tu_contraseña'
)

# 3. Cargar certificado
signer.load_certificate()

# 4. Verificar validez del certificado
cert_info = signer.get_certificate_info()
print(f"Certificado válido hasta: {cert_info['not_valid_after']}")

# 5. Firmar XML
signed_xml = signer.sign_xml(xml_content)

# 6. Verificar firma
is_valid = signer.verify_signature(signed_xml)
print(f"Firma válida: {is_valid}")
```

### Integración en el flujo de facturación

```python
from workshops.models import ElectronicInvoice
from workshops.dian_signature import DIANSignature
from workshops.dian_xml_generator import generate_electronic_invoice_xml

def create_and_sign_invoice(invoice_id):
    # Obtener factura
    invoice = ElectronicInvoice.objects.get(id=invoice_id)
    
    # Generar XML
    xml_content = generate_electronic_invoice_xml(invoice)
    
    # Firmar
    signer = DIANSignature(
        certificate_path=settings.DIAN_CERTIFICATE_PATH,
        certificate_password=settings.DIAN_CERTIFICATE_PASSWORD
    )
    signer.load_certificate()
    signed_xml = signer.sign_xml(xml_content)
    
    # Guardar XML firmado
    invoice.signed_xml = signed_xml
    invoice.save()
    
    return signed_xml
```

## 📝 Estructura del XML Firmado

El XML firmado incluye:

### 1. Extensiones UBL

```xml
<ext:UBLExtensions>
  <ext:UBLExtension>
    <ext:ExtensionContent>
      <!-- Información DIAN -->
      <sts:DianExtensions>
        <sts:InvoiceControl>...</sts:InvoiceControl>
        <sts:SoftwareProvider>...</sts:SoftwareProvider>
        <sts:QRCode>...</sts:QRCode>
      </sts:DianExtensions>
    </ext:ExtensionContent>
  </ext:UBLExtension>
  
  <ext:UBLExtension>
    <ext:ExtensionContent>
      <!-- Firma Digital XMLDSig -->
      <ds:Signature>
        <ds:SignedInfo>...</ds:SignedInfo>
        <ds:SignatureValue>...</ds:SignatureValue>
        <ds:KeyInfo>...</ds:KeyInfo>
      </ds:Signature>
    </ext:ExtensionContent>
  </ext:UBLExtension>
</ext:UBLExtensions>
```

### 2. Firma XMLDSig

La firma incluye:
- **SignedInfo**: Información de lo que se firma
- **SignatureValue**: Valor de la firma digital
- **KeyInfo**: Certificado X.509
- **XAdES**: Propiedades firmadas (timestamp, política)

## 🔍 Validación

### Verificar certificado

```python
signer = DIANSignature(cert_path, cert_password)
signer.load_certificate()

cert_info = signer.get_certificate_info()

# Verificar vigencia
from datetime import datetime
now = datetime.now()

if now < cert_info['not_valid_before']:
    print("⚠️ Certificado aún no válido")
elif now > cert_info['not_valid_after']:
    print("❌ Certificado expirado")
else:
    print("✅ Certificado válido")
```

### Verificar firma

```python
is_valid = signer.verify_signature(signed_xml)

if is_valid:
    print("✅ Firma válida")
else:
    print("❌ Firma inválida")
```

## 🛡️ Seguridad

### ⚠️ IMPORTANTE

1. **NUNCA** subir el certificado `.p12` al repositorio
2. **NUNCA** compartir la contraseña del certificado
3. **SIEMPRE** usar variables de entorno
4. **SIEMPRE** agregar `*.p12` y `*.pfx` al `.gitignore`

### Buenas prácticas

```bash
# .gitignore
*.p12
*.pfx
certificates/*.p12
certificates/*.pfx
```

### Rotación de certificados

Los certificados tienen vigencia limitada (1-2 años):

1. Antes de expirar, solicita renovación a Camerfirma
2. Descarga el nuevo certificado
3. Actualiza la ruta en `.env`
4. Verifica que funcione en ambiente de pruebas
5. Despliega a producción

## 🧪 Testing

### Test básico

```python
from workshops.dian_signature import DIANSignature

def test_certificate_loading():
    signer = DIANSignature(
        'workshops/certificates/test_cert.p12',
        'test_password'
    )
    
    try:
        signer.load_certificate()
        cert_info = signer.get_certificate_info()
        assert cert_info is not None
        print("✅ Certificado cargado correctamente")
    except Exception as e:
        print(f"❌ Error: {e}")
```

### Test de firma

```python
def test_xml_signing():
    # XML de prueba
    test_xml = """<?xml version="1.0"?>
    <Invoice>
        <ID>TEST001</ID>
    </Invoice>"""
    
    signer = DIANSignature(cert_path, cert_password)
    signer.load_certificate()
    
    # Firmar
    signed = signer.sign_xml(test_xml)
    assert '<ds:Signature' in signed
    
    # Verificar
    is_valid = signer.verify_signature(signed)
    assert is_valid
    
    print("✅ Firma y verificación exitosas")
```

## 📚 Referencias

- [Anexo Técnico DIAN](../docs/DIAN/Anexo-Tecnico-Documento-Equivalente-Electronico-V1-0-final.pdf)
- [Política de Firma DIAN](https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf)
- [Documentación Camerfirma](https://www.camerfirma.com)
- [XMLDSig Specification](https://www.w3.org/TR/xmldsig-core/)

## 🆘 Solución de Problemas

### Error: "No se puede cargar el certificado"

```python
# Verificar que el archivo existe
import os
cert_path = 'workshops/certificates/certificado.p12'
if not os.path.exists(cert_path):
    print(f"❌ Archivo no encontrado: {cert_path}")

# Verificar permisos
if not os.access(cert_path, os.R_OK):
    print(f"❌ Sin permisos de lectura: {cert_path}")
```

### Error: "Contraseña incorrecta"

- Verifica la contraseña en el email de Camerfirma
- Prueba sin espacios al inicio/final
- Contacta a soporte si olvidaste la contraseña

### Error: "Certificado expirado"

- Solicita renovación a Camerfirma
- Mientras tanto, usa ambiente de pruebas

### Error: "Firma inválida"

- Verifica que el XML no se modificó después de firmar
- Asegúrate de usar el mismo certificado para firmar y verificar
- Revisa que los namespaces XML sean correctos

## 📞 Soporte

- **Camerfirma**: soporte@camerfirma.com
- **DIAN**: https://www.dian.gov.co
- **Documentación**: Este repositorio

## ✅ Checklist de Implementación

- [ ] Certificado .p12 obtenido de Camerfirma
- [ ] Certificado guardado en `workshops/certificates/`
- [ ] Variables de entorno configuradas en `.env`
- [ ] Dependencias instaladas (`pip install cryptography signxml lxml`)
- [ ] `.gitignore` actualizado para excluir certificados
- [ ] Certificado cargado exitosamente
- [ ] Firma de XML funcional
- [ ] Verificación de firma funcional
- [ ] Tests pasando
- [ ] Documentación revisada
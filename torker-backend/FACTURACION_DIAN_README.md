# 📄 Sistema de Facturación Electrónica DIAN - Torker

## 🎯 Configuración del Taller

### 1. Datos Fiscales Requeridos

El taller debe configurar en su perfil:

**Información Básica:**
- NIT (con dígito de verificación)
- Razón Social
- Dirección completa
- Ciudad y Departamento
- Teléfono y Email

**Información Tributaria:**
- Régimen Fiscal (común, simplificado, especial)
- Responsabilidades Fiscales (ej: O-08, O-09, O-16, O-22)
- Tipo de Organización (Persona Jurídica / Natural)
- Tarifa IVA (0%, 5%, 19%)
- Actividad Económica (código CIIU)

### 2. Resolución DIAN

Cada taller debe registrar su resolución DIAN:

- **Número de Resolución** (ej: 18764000000001)
- **Fecha de Expedición**
- **Fecha de Vencimiento**
- **Prefijo** (ej: SMFE, F, NC)
- **Rango Autorizado** (ej: del 1 al 5000)
- **Tipo de Documento** (Factura, Nota Crédito, Nota Débito)

---

## 🚀 Uso del Sistema

### Generar Factura Electrónica

```http
POST /api/electronic-invoices/create_from_work_order/
Content-Type: application/json
Authorization: Bearer {token}

{
  "work_order_id": "uuid-de-la-orden",
  "payment_method": "cash"
}
```

**Respuesta:**
```json
{
  "id": "uuid",
  "invoice_number": "SMFE0001",
  "cude": "8eee5863...",
  "total": "178500.00",
  "qr_code_url": "https://...",
  "pdf_download_url": "/api/electronic-invoices/{id}/download_pdf/"
}
```

### Enviar Factura por Email

```http
POST /api/electronic-invoices/{id}/send_email/
Content-Type: application/json

{
  "email": "cliente@email.com"  // Opcional, usa el del cliente por defecto
}
```

### Verificar Configuración DIAN

```http
GET /api/workshops/{id}/dian_configuration_status/
```

**Respuesta:**
```json
{
  "is_complete": false,
  "missing_fields": ["NIT", "Resolución DIAN activa"],
  "warnings": [],
  "can_generate_invoices": false
}
```

---

## ⚙️ Configuración de Email

Agregar en `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=facturacion@taller.com
EMAIL_HOST_PASSWORD=contraseña_aplicacion
DEFAULT_FROM_EMAIL=facturacion@taller.com
```

---

## 📋 Validaciones Automáticas

El sistema valida automáticamente:

✅ Configuración DIAN completa  
✅ Resolución vigente  
✅ Números disponibles en resolución  
✅ Suscripción activa  
✅ Datos del cliente completos  

Si falta algo, retorna error con campos faltantes.

---

## 🔒 Seguridad

- Aislamiento completo entre talleres
- Middleware de validación
- Auditoría de operaciones
- Logging estructurado
- Prevención acceso cross-taller

---

## 📊 Monitoreo

**Alertas automáticas:**
- Al 75% de uso de resolución
- Resolución próxima a vencer
- Suscripción por expirar

**Logs:**
- Generación de facturas
- Envío de emails
- Errores y excepciones
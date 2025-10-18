# 🔒 GUÍA DE SEGURIDAD - TORKER BACKEND

## 📋 Índice

1. [Configuración Inicial](#configuración-inicial)
2. [Variables de Entorno](#variables-de-entorno)
3. [Seguridad en Producción](#seguridad-en-producción)
4. [Mejores Prácticas](#mejores-prácticas)
5. [Checklist de Despliegue](#checklist-de-despliegue)

---

## 🚀 Configuración Inicial

### 1. Generar SECRET_KEY Seguro

**NUNCA** uses la clave por defecto en producción. Genera una nueva:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado y agrégalo a tu archivo `.env`:

```env
SECRET_KEY=tu-clave-super-secreta-generada-aqui
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita `.env` y configura todas las variables requeridas.

---

## 🔐 Variables de Entorno

### Variables Críticas (REQUERIDAS)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-...` |
| `ENVIRONMENT` | Entorno de ejecución | `production` |
| `DEBUG` | Modo debug (False en prod) | `False` |
| `ALLOWED_HOSTS` | Hosts permitidos | `midominio.com,www.midominio.com` |
| `DATABASE_URL` | URL de base de datos | `postgresql://user:pass@host:5432/db` |

### Variables de Seguridad

| Variable | Producción | Desarrollo |
|----------|------------|------------|
| `SECURE_SSL_REDIRECT` | `True` | `False` |
| `SESSION_COOKIE_SECURE` | `True` | `False` |
| `CSRF_COOKIE_SECURE` | `True` | `False` |
| `SECURE_HSTS_SECONDS` | `31536000` | `0` |

### Variables de CORS

```env
# ❌ NUNCA en producción
CORS_ALLOW_ALL_ORIGINS=False

# ✅ Especificar orígenes permitidos
CORS_ALLOWED_ORIGINS=https://miapp.com,https://www.miapp.com
```

---

## 🛡️ Seguridad en Producción

### Checklist Pre-Despliegue

- [ ] `SECRET_KEY` único y seguro generado
- [ ] `DEBUG=False`
- [ ] `ENVIRONMENT=production`
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] CORS configurado con orígenes específicos
- [ ] HTTPS habilitado (`SECURE_SSL_REDIRECT=True`)
- [ ] Cookies seguras habilitadas
- [ ] HSTS configurado
- [ ] Base de datos PostgreSQL (no SQLite)
- [ ] Variables sensibles en variables de entorno
- [ ] Logs configurados correctamente
- [ ] Backups automatizados configurados

### Configuración HTTPS

```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Configuración de Base de Datos

**Desarrollo:**
```env
DATABASE_URL=sqlite:///db.sqlite3
```

**Producción (PostgreSQL):**
```env
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db
```

**Railway/Heroku:**
```env
# Se configura automáticamente, no modificar
DATABASE_URL=${DATABASE_URL}
```

---

## 🔒 Mejores Prácticas

### 1. Gestión de Secretos

✅ **HACER:**
- Usar variables de entorno para secretos
- Generar claves únicas por entorno
- Rotar credenciales regularmente
- Usar servicios de gestión de secretos (AWS Secrets Manager, etc.)

❌ **NO HACER:**
- Hardcodear secretos en código
- Subir archivos `.env` al repositorio
- Compartir credenciales por email/chat
- Usar la misma clave en múltiples entornos

### 2. Autenticación y Autorización

✅ **HACER:**
- Usar JWT con tiempos de expiración cortos
- Implementar refresh tokens
- Validar permisos en cada endpoint
- Implementar rate limiting

❌ **NO HACER:**
- Tokens sin expiración
- Permisos a nivel de frontend únicamente
- Permitir acceso sin autenticación a endpoints sensibles

### 3. Validación de Datos

✅ **HACER:**
- Validar todos los inputs del usuario
- Sanitizar datos antes de guardar
- Usar serializers de DRF con validaciones
- Implementar validaciones a nivel de modelo

❌ **NO HACER:**
- Confiar en validaciones del frontend
- Ejecutar queries raw con input del usuario
- Permitir campos sin validación

### 4. CORS y CSP

✅ **HACER:**
```python
# Especificar orígenes permitidos
CORS_ALLOWED_ORIGINS = [
    'https://miapp.com',
    'https://www.miapp.com',
]
```

❌ **NO HACER:**
```python
# NUNCA en producción
CORS_ALLOW_ALL_ORIGINS = True
```

### 5. Logging y Monitoreo

✅ **HACER:**
- Loggear intentos de acceso fallidos
- Monitorear errores con Sentry
- Revisar logs regularmente
- Configurar alertas para eventos críticos

❌ **NO HACER:**
- Loggear información sensible (passwords, tokens)
- Ignorar errores en producción
- Logs sin rotación (llenan disco)

---

## 📝 Checklist de Despliegue

### Pre-Despliegue

```bash
# 1. Verificar configuración
python manage.py check --deploy

# 2. Ejecutar tests
python manage.py test

# 3. Recolectar archivos estáticos
python manage.py collectstatic --noinput

# 4. Verificar migraciones
python manage.py showmigrations
python manage.py migrate --check
```

### Configuración de Producción

#### Railway

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Crear proyecto
railway init

# 4. Agregar PostgreSQL
railway add postgresql

# 5. Configurar variables
railway variables set SECRET_KEY="tu-clave-aqui"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="False"

# 6. Desplegar
railway up
```

#### Heroku

```bash
# 1. Crear app
heroku create torker-backend

# 2. Agregar PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 3. Configurar variables
heroku config:set SECRET_KEY="tu-clave-aqui"
heroku config:set ENVIRONMENT="production"
heroku config:set DEBUG="False"

# 4. Desplegar
git push heroku main

# 5. Migrar base de datos
heroku run python manage.py migrate
```

### Post-Despliegue

- [ ] Verificar que el sitio carga correctamente
- [ ] Probar login/registro
- [ ] Verificar endpoints críticos
- [ ] Revisar logs por errores
- [ ] Configurar monitoreo (Sentry, etc.)
- [ ] Configurar backups automáticos
- [ ] Documentar URLs y credenciales

---

## 🚨 Respuesta a Incidentes

### Si se compromete SECRET_KEY:

1. **Generar nueva clave inmediatamente**
2. **Actualizar en todas las instancias**
3. **Invalidar todas las sesiones activas**
4. **Rotar tokens JWT**
5. **Notificar a usuarios si es necesario**
6. **Revisar logs por accesos sospechosos**

### Si se detecta acceso no autorizado:

1. **Bloquear acceso inmediatamente**
2. **Revisar logs de acceso**
3. **Cambiar todas las credenciales**
4. **Auditar cambios en base de datos**
5. **Notificar a usuarios afectados**
6. **Implementar medidas preventivas**

---

## 📚 Recursos Adicionales

- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django REST Framework Security](https://www.django-rest-framework.org/topics/security/)
- [12 Factor App](https://12factor.net/)

---

## 📞 Contacto

Para reportar vulnerabilidades de seguridad:
- Email: security@torker.com
- No publicar vulnerabilidades públicamente
- Esperar respuesta antes de divulgar

---

**Última actualización:** 18 de Octubre, 2025
**Versión:** 1.0
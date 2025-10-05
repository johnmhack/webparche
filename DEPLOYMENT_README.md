# 🚀 Despliegue Parche + Torker

## Arquitectura Separada

### ✅ **Frontend (Parche)** → Netlify/Vercel
- **Archivos:** `index.html`, `pages/`, `assets/`
- **Hosting:** Netlify (gratis)
- **Dominio:** `appparche.com`

### ✅ **Backend (Torker API)** → Railway
- **Archivos:** `torker-backend/`
- **Hosting:** Railway (gratis)
- **API:** `https://[dominio].up.railway.app/api/`

## 📋 Pasos de Despliegue

### 1. **Desplegar Backend en Railway**
```bash
# Ya está configurado
# Railway redeploy automáticamente
```

### 2. **Desplegar Frontend en Netlify**
```bash
# Crear cuenta en netlify.com
# Conectar repositorio GitHub
# Netlify detecta netlify.toml automáticamente
```

### 3. **Configurar API URL**
```javascript
// En pages/torker/assets/js/torker.js
const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000/api'
  : 'https://[TU_DOMINIO_RAILWAY].up.railway.app/api';
```

## 🌐 Acceso Final

### **Desde appparche.com:**
- ✅ **Parche principal** funciona normalmente
- ✅ **Botón "Torker"** redirige a Railway
- ✅ **API calls** van a Railway automáticamente

### **URLs:**
- **Parche:** `https://appparche.com/`
- **Torker:** `https://appparche.com/pages/torker/` (redirige)
- **API:** `https://[railway].up.railway.app/api/`

## 🎯 Ventajas

- ✅ **Frontend rápido** (Netlify CDN)
- ✅ **Backend escalable** (Railway + PostgreSQL)
- ✅ **Dominio unificado** (appparche.com)
- ✅ **CORS configurado**
- ✅ **SSL automático** en ambos
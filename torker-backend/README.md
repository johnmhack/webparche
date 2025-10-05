# Torker Backend - API REST

**Backend de Torker** - Sistema de gestión integral para talleres de motos construido con Django REST Framework.

## 🚀 Características

- ✅ **Autenticación JWT** completa
- ✅ **Sistema de talleres** con múltiples roles
- ✅ **Gestión de clientes y motos**
- ✅ **Órdenes de trabajo** y repuestos
- ✅ **Sistema de suscripciones** (Trial → Básico → Premium)
- ✅ **API RESTful** completa
- ✅ **CORS configurado** para frontend
- ✅ **Base de datos PostgreSQL** (listo para Railway)

## 🛠️ Tecnologías

- **Django 5.2** - Framework web
- **Django REST Framework** - API REST
- **Simple JWT** - Autenticación
- **PostgreSQL** - Base de datos
- **Railway** - Despliegue

## 📋 Instalación Local

### 1. Clonar y configurar entorno
```bash
cd torker-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variables de entorno
Crear archivo `.env`:
```env
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///db.sqlite3  # Para desarrollo local
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Migraciones y servidor
```bash
python manage.py migrate
python manage.py runserver
```

## 🔐 API Endpoints

### Autenticación
```
POST /api/auth/register/     - Registro de usuario/taller
POST /api/auth/login/        - Login con JWT
POST /api/auth/refresh/      - Refresh token
```

### Dashboard
```
GET /api/dashboard/          - Dashboard con estadísticas
```

### Gestión de Talleres
```
GET|POST /api/workshops/     - Lista/Crear talleres
GET|PUT|DELETE /api/workshops/{id}/ - Detalle/Actualizar/Eliminar
```

### Gestión de Datos
```
GET|POST /api/customers/     - Clientes
GET|POST /api/motorcycles/   - Motos
GET|POST /api/employees/     - Empleados
GET|POST /api/parts/         - Repuestos
GET|POST /api/work-orders/   - Órdenes de trabajo
GET|POST /api/appointments/  - Citas
```

## 📊 Modelo de Datos

### Usuario → Taller (1:1)
- **Usuario**: Dueño del taller (email, nombre, teléfono)
- **Taller**: Información del negocio (nombre, dirección, NIT)

### Taller → Empleados (1:N)
- **Empleados**: Mecánicos, administradores, recepcionistas

### Taller → Clientes/Motos/Repuestos/Órdenes (1:N)
- **Clientes**: Información de los clientes
- **Motos**: Vehículos de los clientes
- **Repuestos**: Inventario de partes
- **Órdenes**: Trabajo realizado

## 🔑 Sistema de Suscripciones

### Trial (30 días gratis)
- ✅ Dashboard básico
- ✅ Gestión de clientes
- ❌ Órdenes de trabajo
- ❌ Inventario
- ❌ Reportes

### Básico ($29/mes)
- ✅ Todo lo de Trial
- ✅ Órdenes de trabajo
- ✅ Inventario básico
- ❌ Reportes avanzados
- ❌ Múltiples usuarios

### Premium ($59/mes)
- ✅ Todo lo de Básico
- ✅ Reportes avanzados
- ✅ Múltiples usuarios
- ✅ API externa
- ✅ Soporte prioritario

## 🚀 Despliegue en Colombia (Railway)

### **Opción A: Script Automático (Recomendado)**
```bash
# Desde la raíz del proyecto
chmod +x deploy_railway.sh
./deploy_railway.sh
```

### **Opción B: Manual**

#### 1. Instalar Railway CLI
```bash
npm install -g @railway/cli
# o descarga desde: https://docs.railway.app/develop/cli
```

#### 2. Autenticarse y crear proyecto
```bash
railway login
cd torker-backend
railway init torker-backend
```

#### 3. Agregar PostgreSQL
```bash
railway add postgresql
```

#### 4. Configurar variables de entorno
```bash
railway variables set DEBUG=False
railway variables set SECRET_KEY="$(openssl rand -hex 32)"
railway variables set DATABASE_URL="${DATABASE_URL}"
railway variables set ALLOWED_HOSTS="${RAILWAY_STATIC_URL}"
```

#### 5. Desplegar
```bash
railway up
```

#### 6. Crear superusuario
```bash
railway run python manage.py createsuperuser
```

### **URLs después del despliegue**
- **API Base**: `https://[tu-proyecto].up.railway.app/api/`
- **Admin Django**: `https://[tu-proyecto].up.railway.app/admin/`
- **Torker Frontend**: `https://[tu-proyecto].up.railway.app/pages/torker/index.html`

## 🌐 **Otras Opciones de Hosting en Colombia**

### **Railway (Recomendado)**
- ✅ Fácil de usar
- ✅ PostgreSQL incluido
- ✅ Plan gratuito decente
- ✅ Despliegue rápido

### **Heroku**
```bash
# Crear app
heroku create torker-backend

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Configurar variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=tu-clave-secreta

# Desplegar
git push heroku main
```

### **DigitalOcean App Platform**
- Arrastrar y soltar para desplegar
- PostgreSQL managed
- CDN incluido

### **Vercel + Railway**
- **Frontend (Parche)**: Desplegar en Vercel
- **Backend (Torker)**: Desplegar en Railway
- Mejor separación de responsabilidades

## 🧪 Testing

### Registro de usuario
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@taller.com","first_name":"Juan","last_name":"Pérez","password":"123456"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@taller.com","password":"123456"}'
```

### Dashboard (con token)
```bash
curl -X GET http://localhost:8000/api/dashboard/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## 📁 Estructura del Proyecto

```
torker-backend/
├── torker_project/          # Configuración Django
│   ├── settings.py         # Configuración principal
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # WSGI
├── workshops/              # App principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas API
│   ├── serializers.py     # Serializers
│   ├── urls.py           # URLs de la app
│   └── admin.py          # Admin Django
├── .env                   # Variables de entorno
├── requirements.txt       # Dependencias
└── README.md             # Esta documentación
```

## 🔄 Próximos Pasos

1. **Conectar con frontend** (JavaScript del sitio web)
2. **Sistema de pagos** (Stripe/PayPal)
3. **Notificaciones** push/email
4. **Reportes** avanzados
5. **API externa** para integraciones

## 📞 Soporte

Para soporte técnico:
- Revisar logs: `railway logs`
- Documentación: Django REST Framework docs
- Issues: Crear en el repositorio

---

**Torker Backend** - API robusta y escalable para gestión de talleres 🏍️
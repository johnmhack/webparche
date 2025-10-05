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

## 🚀 Despliegue en Railway

### 1. Crear proyecto en Railway
```bash
railway login
railway init
```

### 2. Configurar PostgreSQL
```bash
railway add postgresql
```

### 3. Variables de entorno en Railway
```bash
railway variables set DEBUG=False
railway variables set SECRET_KEY=tu-clave-produccion
railway variables set DATABASE_URL=${DATABASE_URL}  # Automático
railway variables set ALLOWED_HOSTS=tu-dominio.com
```

### 4. Desplegar
```bash
railway up
```

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
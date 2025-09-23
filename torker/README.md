# Torker - Sistema de Gestión de Talleres

**Torker** es el módulo de gestión integral para talleres de motos, implementado como **subdominio independiente** de la plataforma **Parche**.

## 🏗️ Arquitectura Recomendada

### **🌐 Estructura de Dominios:**
- **`parche.com`** → Web principal (motociclistas)
- **`torker.parche.com`** → App para talleres (subdominio)

### **📁 Estructura de Archivos:**
```
web_parche/                    # parche.com
├── index.html                 # Página principal de Parche
├── style.css                  # Estilos de Parche
├── script.js                  # Funcionalidades de Parche
├── fotos/                     # Imágenes y recursos
└── torker/                    # torker.parche.com
    ├── index.html             # App de talleres
    ├── style.css              # Estilos de Torker
    ├── script.js              # Funcionalidades de Torker
    └── README.md              # Este archivo
```

## 🚀 Funcionalidades

### **Página Principal de Torker**
- **Hero Section** con descripción del sistema
- **Botones de Acción**: Iniciar Sesión y Registrarse
- **Navegación** de vuelta a Parche
- **Diseño idéntico** a Parche (colores, tipografía, estilos)

### **Sistema de Autenticación**
- **Login** para talleres existentes
- **Registro** para nuevos talleres
- **Persistencia** de sesión en localStorage
- **Validaciones** de formularios

### **Dashboard de Taller**
- **Estadísticas** en tiempo real
- **Módulos** principales:
  - 📅 Agenda y Citas
  - 🔧 Órdenes de Trabajo
  - 👥 Gestión de Clientes
  - 📦 Control de Inventario

## 🔗 Integración con Parche

### **Acceso desde Parche:**
- **Menú de navegación** → Enlace a sección Torker
- **Sección Torker** → Botón "Abrir Torker en Nueva Pestaña"
- **Dashboard de acceso rápido** → Botones directos para talleres

### **Experiencia del Usuario:**
1. **Usuario visita** `parche.com` (motociclista)
2. **Hace clic** en "Torker" (menú o sección)
3. **Se abre** `torker.parche.com` en **nueva pestaña**
4. **Puede** iniciar sesión o registrarse
5. **Accede** al dashboard completo del taller

## 🎨 Diseño

### **Identidad Visual:**
- **100% consistente** con Parche
- **Paleta de colores neón** idéntica
- **Tipografía Poppins** igual que Parche
- **Efectos visuales** y animaciones
- **Responsive design** mobile-first

### **Colores Principales:**
- **Neon Blue** (#00C2FF) - Color principal
- **Neon Green** (#25FF7A) - Color de acento
- **Neon Pink** (#FF2F77) - Color secundario
- **Dark Blue** (#1B2140) - Fondo principal

## 🔧 Tecnologías

- **HTML5** semántico
- **CSS3** con variables CSS y Grid/Flexbox
- **JavaScript** vanilla ES6+
- **LocalStorage** para persistencia de sesión
- **Boxicons** para iconografía
- **Responsive Design** mobile-first

## 🚀 Ventajas de esta Arquitectura

### **✅ Para Usuarios:**
- **Experiencia fluida** - Torker se abre en nueva pestaña
- **Navegación clara** - No se pierden en Parche
- **Acceso rápido** - Botones directos para talleres

### **✅ Para Desarrollo:**
- **Código separado** - Torker es independiente
- **Escalabilidad** - Se puede vender como SaaS separado
- **Mantenimiento** - Cada sistema se mantiene por separado
- **Seguridad** - Aislamiento de funcionalidades

### **✅ Para Negocio:**
- **Branding unificado** - Ambos bajo Parche
- **Flexibilidad** - Torker puede crecer independientemente
- **Monetización** - Posibilidad de vender Torker por separado

## 📱 Próximos Pasos

- [ ] **Configurar subdominio** `torker.parche.com`
- [ ] **Integración con backend** Django
- [ ] **Sistema de notificaciones** en tiempo real
- [ ] **Módulos avanzados** (reportes, facturación)
- [ ] **API REST** para comunicación con app móvil
- [ ] **Sistema de roles** y permisos
- [ ] **Deploy en servidor** separado

## 🌐 Configuración del Subdominio

### **DNS Records:**
```
torker.parche.com    A    [IP_DEL_SERVIDOR_TORKER]
torker.parche.com    CNAME parche.com
```

### **Servidor Web:**
- **Nginx/Apache** configurado para `torker.parche.com`
- **SSL Certificate** para el subdominio
- **Reverse proxy** si es necesario

## 📞 Soporte

Para soporte técnico o preguntas sobre Torker:
- Crear un issue en el repositorio de Parche
- Contactar al equipo de desarrollo
- Revisar la documentación de la API

---

**Torker** - Potenciando talleres de motos desde **Parche** 🏍️

*Arquitectura profesional y escalable para el futuro del negocio.*

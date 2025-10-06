# Parche - Plataforma para Motociclistas
# Test persistencia PostgreSQL - cambio pequeño

## 📁 Estructura del Proyecto

```
web_parche/
├── index.html              # Página principal de Parche
├── README.md               # Este archivo
├── robots.txt              # Configuración SEO para bots
├── sitemap.xml             # Mapa del sitio para motores de búsqueda
├── google-verification.html # Verificación Google Search Console
├── favicon.ico             # Icono del sitio
├── favicon.svg             # Icono SVG
├── .DS_Store               # Archivo sistema (ignorar)
├── .gitattributes          # Configuración Git
├── assets/                 # Recursos compartidos/globales
│   ├── css/
│   │   ├── main.css        # Estilos base/globales (antes style.css)
│   │   ├── components.css  # Estilos de componentes reutilizables
│   │   └── shared/         # Estilos compartidos opcionales
│   ├── js/
│   │   ├── main.js         # JS base/global (antes script.js)
│   │   ├── components.js   # JS de componentes reutilizables
│   │   └── shared/         # JS compartido opcional
│   └── images/             # Imágenes globales
│       ├── fotos/          # Fotos de Parche
│       ├── icons/          # Iconos generales
│       └── banners/        # Banners compartidos
├── pages/                  # Páginas/Apps adicionales
│   ├── torker/             # App Torker
│   │   ├── index.html      # Página principal de Torker
│   │   ├── assets/         # Assets específicos de Torker
│   │   │   ├── css/
│   │   │   │   └── torker.css # Estilos específicos de Torker
│   │   │   └── js/
│   │   │       └── torker.js # JS específico de Torker
│   │   └── components/     # Componentes específicos de Torker
│   └── revista/            # Sección Revista
│       ├── index.html      # Página principal de Revista
│       ├── assets/         # Assets específicos de Revista
│       │   ├── css/
│       │   │   └── revista.css # Estilos de Revista
│       │   ├── js/
│       │   │   └── revista.js # JS de Revista
│       │   └── images/     # Imágenes de Revista
│       └── components/     # Componentes de Revista
├── docs/                   # Documentación
│   ├── GUIA_SEO_PARCHE.md  # Guía SEO
│   └── PARCHE_EMPRESA.md   # Información corporativa
└── torker/                 # Archivos de despliegue Torker
    ├── DEPLOY.md
    ├── docker-compose.yml
    ├── nginx.conf
    └── README.md
```

## 🚀 Inicio Rápido

1. Abrir `index.html` en un navegador web (página principal de Parche)
2. Para Revista: navegar a `pages/revista/index.html`
3. Para Torker: navegar a `pages/torker/index.html`

## 🛠️ Tecnologías

- **HTML5** - Estructura semántica
- **CSS3** - Estilos con variables CSS
- **JavaScript ES6+** - Interactividad
- **Swiper.js** - Carrusel de testimonios
- **Boxicons** - Iconos

## 📱 Características

- Diseño responsive
- Optimizado para SEO
- Accesibilidad básica
- Animaciones CSS
- Formularios interactivos

## 🔧 Próximos Pasos

- Implementar backend real para Torker
- Reemplazar placeholders de Analytics y verificación
- Añadir validación de formularios
- Optimizar imágenes y performance
- Implementar PWA

## 📞 Contacto

Para soporte técnico o consultas sobre el proyecto.
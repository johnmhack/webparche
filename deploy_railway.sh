#!/bin/bash

# Script de despliegue para Railway - Torker Backend
# Uso: ./deploy_railway.sh

echo "🚀 Desplegando Torker Backend en Railway"
echo "========================================"

# Verificar si Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado"
    echo "Instálalo desde: https://docs.railway.app/develop/cli"
    exit 1
fi

# Verificar si estamos autenticados
if ! railway whoami &> /dev/null; then
    echo "❌ No estás autenticado en Railway"
    echo "Ejecuta: railway login"
    exit 1
fi

echo "✅ Railway CLI verificado"

# Crear proyecto
echo "📦 Creando proyecto en Railway..."
cd torker-backend
railway init torker-backend --yes

# Agregar PostgreSQL
echo "🐘 Agregando PostgreSQL..."
railway add postgresql

# Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
railway variables set DEBUG=False
railway variables set SECRET_KEY="$(openssl rand -hex 32)"
railway variables set DATABASE_URL="\${DATABASE_URL}"
railway variables set ALLOWED_HOSTS="\${RAILWAY_STATIC_URL}"

echo "🚀 Desplegando aplicación..."
railway up

echo ""
echo "🎉 ¡Despliegue completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Ve a https://railway.app/dashboard"
echo "2. Encuentra tu proyecto 'torker-backend'"
echo "3. Copia la URL del dominio (ej: https://torker-backend.up.railway.app)"
echo "4. Crea un superusuario:"
echo "   railway run python manage.py createsuperuser"
echo ""
echo "🔗 URLs importantes:"
echo "- API Base: [TU_DOMINIO]/api/"
echo "- Admin: [TU_DOMINIO]/admin/"
echo "- Torker Frontend: [TU_DOMINIO]/pages/torker/index.html"
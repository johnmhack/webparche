# 🚀 Guía de Deploy - Torker Subdominio

## 📋 Prerrequisitos

- **Servidor VPS** con Ubuntu 20.04+ o CentOS 8+
- **Dominio principal** configurado (parche.com)
- **Acceso SSH** al servidor
- **Permisos de root** o sudo

## 🌐 Configuración del Subdominio

### **1. DNS Records**

Agregar en tu proveedor de DNS:

```
torker.parche.com    A    [IP_DE_TU_SERVIDOR]
torker.parche.com    CNAME parche.com
```

### **2. Conectar al Servidor**

```bash
ssh root@[IP_DE_TU_SERVIDOR]
```

## 🛠️ Instalación del Servidor

### **1. Actualizar Sistema**

```bash
apt update && apt upgrade -y
```

### **2. Instalar Nginx**

```bash
apt install nginx -y
systemctl enable nginx
systemctl start nginx
```

### **3. Instalar Certbot (SSL)**

```bash
apt install certbot python3-certbot-nginx -y
```

### **4. Instalar Docker (Opcional)**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker
```

## 📁 Configuración de Archivos

### **1. Crear Directorio del Sitio**

```bash
mkdir -p /var/www/torker.parche.com
cd /var/www/torker.parche.com
```

### **2. Subir Archivos**

```bash
# Desde tu máquina local
scp -r torker/* root@[IP_SERVIDOR]:/var/www/torker.parche.com/
```

### **3. Configurar Nginx**

```bash
# Copiar configuración
cp /var/www/torker.parche.com/nginx.conf /etc/nginx/sites-available/torker.parche.com

# Crear enlace simbólico
ln -s /etc/nginx/sites-available/torker.parche.com /etc/nginx/sites-enabled/

# Verificar configuración
nginx -t

# Recargar Nginx
systemctl reload nginx
```

### **4. Configurar SSL**

```bash
certbot --nginx -d torker.parche.com
```

## 🐳 Deploy con Docker (Opcional)

### **1. Usar Docker Compose**

```bash
cd /var/www/torker.parche.com
docker-compose up -d
```

### **2. Verificar Contenedores**

```bash
docker ps
docker logs torker-frontend
```

## 🔧 Configuración de Firewall

### **1. UFW (Ubuntu)**

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### **2. iptables (CentOS)**

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## 📊 Monitoreo y Logs

### **1. Ver Logs de Nginx**

```bash
tail -f /var/log/nginx/torker.parche.com.access.log
tail -f /var/log/nginx/torker.parche.com.error.log
```

### **2. Ver Logs de Docker**

```bash
docker logs -f torker-frontend
```

### **3. Monitoreo de Recursos**

```bash
htop
df -h
free -h
```

## 🚨 Troubleshooting

### **Problema: SSL no funciona**
```bash
# Verificar certificados
certbot certificates

# Renovar manualmente
certbot renew --dry-run
```

### **Problema: Nginx no inicia**
```bash
# Verificar configuración
nginx -t

# Ver logs de error
journalctl -u nginx -f
```

### **Problema: Dominio no resuelve**
```bash
# Verificar DNS
nslookup torker.parche.com

# Verificar configuración de Nginx
nginx -T | grep server_name
```

## 🔄 Actualizaciones

### **1. Actualizar Frontend**

```bash
cd /var/www/torker.parche.com
git pull origin main
# o subir archivos manualmente
systemctl reload nginx
```

### **2. Actualizar Docker**

```bash
docker-compose pull
docker-compose up -d
```

## 📈 Escalabilidad

### **1. Load Balancer**

Para múltiples servidores, usar Nginx como load balancer:

```nginx
upstream torker_backend {
    server 192.168.1.10:80;
    server 192.168.1.11:80;
    server 192.168.1.12:80;
}
```

### **2. CDN**

Configurar Cloudflare o similar para:
- Cache global
- DDoS protection
- SSL automático

## 🔐 Seguridad

### **1. Headers de Seguridad**

Los headers ya están configurados en nginx.conf:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

### **2. Rate Limiting**

Agregar en nginx.conf si es necesario:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20 nodelay;
    # ... resto de configuración
}
```

## 📞 Soporte

- **Logs del servidor**: `/var/log/nginx/`
- **Configuración Nginx**: `/etc/nginx/sites-available/`
- **Archivos del sitio**: `/var/www/torker.parche.com/`

---

**¡Torker está listo para funcionar en torker.parche.com!** 🎉

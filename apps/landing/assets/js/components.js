// Componentes JavaScript reutilizables globales
// Funciones para notificaciones, validaciones, utilidades, etc.

// Función para mostrar notificaciones visuales
function showGlobalNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `global-notification global-notification-${type}`;

    // Iconos según tipo
    const icons = {
        success: 'bx-check-circle',
        error: 'bx-x-circle',
        warning: 'bx-error',
        info: 'bx-info-circle'
    };

    notification.innerHTML = `
        <div class="notification-content">
            <i class='bx ${icons[type] || icons.info}'></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    // Estilos inline para asegurar visibilidad
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 350px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    `;

    // Colores según tipo
    const colors = {
        success: 'linear-gradient(135deg, #22c55e, #16a34a)',
        error: 'linear-gradient(135deg, #ef4444, #dc2626)',
        warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
        info: 'linear-gradient(135deg, #0ea5e9, #0284c7)'
    };
    notification.style.background = colors[type] || colors.info;

    // Agregar al DOM
    document.body.appendChild(notification);

    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Función para validar emails
function validateEmail(email) {
    if (!email || typeof email !== 'string') return false;
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email.trim());
}

// Función para validar números de teléfono (Colombia)
function validatePhone(phone) {
    if (!phone || typeof phone !== 'string') return false;
    // Remover espacios, guiones, paréntesis
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    // Validar formato colombiano: +57 seguido de 10 dígitos, o 10 dígitos, o 7 dígitos
    const regex = /^(\+57)?[0-9]{7,10}$/;
    return regex.test(cleanPhone);
}

// Función para sanitizar inputs de texto
function sanitizeInput(input) {
    if (!input || typeof input !== 'string') return '';
    return input
        .trim()
        .replace(/[<>]/g, '') // Remover < >
        .substring(0, 500); // Limitar longitud
}

// Función para validar contraseña fuerte
function validatePassword(password) {
    if (!password || typeof password !== 'string') return { valid: false, message: 'Contraseña requerida' };
    if (password.length < 8) return { valid: false, message: 'Mínimo 8 caracteres' };
    if (!/[A-Z]/.test(password)) return { valid: false, message: 'Debe contener mayúscula' };
    if (!/[a-z]/.test(password)) return { valid: false, message: 'Debe contener minúscula' };
    if (!/[0-9]/.test(password)) return { valid: false, message: 'Debe contener número' };
    return { valid: true, message: 'Contraseña válida' };
}

// Función para mostrar/ocultar elementos con animación
function toggleElement(selector, show = null) {
    const element = document.querySelector(selector);
    if (!element) return;

    const isVisible = element.style.display !== 'none' && element.offsetWidth > 0;

    if (show === null) {
        show = !isVisible;
    }

    if (show) {
        element.style.display = '';
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        element.style.transition = 'all 0.3s ease';

        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        });
    } else {
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';
        element.style.transition = 'all 0.3s ease';

        setTimeout(() => {
            element.style.display = 'none';
        }, 300);
    }
}

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback para navegadores antiguos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        return new Promise((resolve, reject) => {
            if (document.execCommand('copy')) {
                resolve();
            } else {
                reject(new Error('Copy failed'));
            }
            document.body.removeChild(textArea);
        });
    }
}

// Función para formatear números como moneda (COP)
function formatCurrency(amount) {
    if (typeof amount !== 'number') return '$0';
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0
    }).format(amount);
}

// Función para debounce (limitar frecuencia de llamadas)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Función para throttle (limitar frecuencia de llamadas con ejecución inmediata)
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Función para detectar si el dispositivo es móvil
function isMobile() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Función para smooth scroll a elemento
function smoothScrollTo(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Exportar funciones globalmente (para uso en HTML)
window.showGlobalNotification = showGlobalNotification;
window.validateEmail = validateEmail;
window.validatePhone = validatePhone;
window.sanitizeInput = sanitizeInput;
window.validatePassword = validatePassword;
window.toggleElement = toggleElement;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.debounce = debounce;
window.throttle = throttle;
window.isMobile = isMobile;
window.smoothScrollTo = smoothScrollTo;
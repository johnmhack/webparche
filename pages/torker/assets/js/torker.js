// Torker - Sistema de Gestión de Talleres
// JavaScript para funcionalidad de login, registro y dashboard

// Estado de la aplicación
let currentUser = null;
let isAuthenticated = false;

// Elementos del DOM
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const dashboard = document.getElementById('dashboard');
const workshopNameDisplay = document.getElementById('workshopNameDisplay');

// Funciones para mostrar/ocultar modales
function showLogin() {
    loginModal.classList.remove('hidden');
    registerModal.classList.add('hidden');
    document.body.style.overflow = 'hidden'; // Prevenir scroll
}

function hideLogin() {
    loginModal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // Restaurar scroll
}

function showRegister() {
    registerModal.classList.remove('hidden');
    loginModal.classList.add('hidden');
    document.body.style.overflow = 'hidden'; // Prevenir scroll
}

function hideRegister() {
    registerModal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // Restaurar scroll
}

// Función para mostrar dashboard
function showDashboard() {
    dashboard.classList.remove('hidden');
    document.querySelector('.hero').classList.add('hidden');
    document.querySelector('.header').classList.add('hidden');
    
    // Animación de entrada del dashboard
    const dashboardElements = dashboard.querySelectorAll('.stat-card, .module-card');
    dashboardElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Función para ocultar dashboard
function hideDashboard() {
    dashboard.classList.add('hidden');
    document.querySelector('.hero').classList.remove('hidden');
    document.querySelector('.header').classList.remove('hidden');
}

// Función para manejar login
function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const email = formData.get('email');
    const password = formData.get('password');
    
    // Simulación de login (aquí iría la llamada real a la API)
    if (email && password) {
        // Simular autenticación exitosa
        currentUser = {
            email: email,
            workshopName: 'Taller Demo',
            role: 'owner'
        };
        
        isAuthenticated = true;
        
        // Mostrar dashboard
        showDashboard();
        
        // Actualizar nombre del taller en el dashboard
        workshopNameDisplay.textContent = currentUser.workshopName;
        
        // Ocultar modal de login
        hideLogin();
        
        // Guardar en localStorage
        localStorage.setItem('torker_user', JSON.stringify(currentUser));
        localStorage.setItem('torker_authenticated', 'true');
        
        // Mostrar mensaje de éxito
        showNotification('¡Bienvenido! Has iniciado sesión correctamente.', 'success');
        
        // Limpiar formulario
        event.target.reset();
    } else {
        showNotification('Por favor completa todos los campos.', 'error');
    }
}

// Función para manejar registro
function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const workshopName = formData.get('workshopName');
    const ownerName = formData.get('ownerName');
    const email = formData.get('email');
    const phone = formData.get('phone');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    // Validaciones básicas
    if (!workshopName || !ownerName || !email || !phone || !password || !confirmPassword) {
        showNotification('Por favor completa todos los campos.', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showNotification('Las contraseñas no coinciden.', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('La contraseña debe tener al menos 6 caracteres.', 'error');
        return;
    }
    
    // Simulación de registro exitoso
    currentUser = {
        email: email,
        workshopName: workshopName,
        ownerName: ownerName,
        phone: phone,
        role: 'owner'
    };
    
    isAuthenticated = true;
    
    // Mostrar dashboard
    showDashboard();
    
    // Actualizar nombre del taller en el dashboard
    workshopNameDisplay.textContent = currentUser.workshopName;
    
    // Ocultar modal de registro
    hideRegister();
    
    // Guardar en localStorage
    localStorage.setItem('torker_user', JSON.stringify(currentUser));
    localStorage.setItem('torker_authenticated', 'true');
    
    // Mostrar mensaje de éxito
    showNotification('¡Registro exitoso! Tu taller ha sido creado.', 'success');
    
    // Limpiar formulario
    event.target.reset();
}

// Función para logout
function logout() {
    currentUser = null;
    isAuthenticated = false;
    
    // Limpiar localStorage
    localStorage.removeItem('torker_user');
    localStorage.removeItem('torker_authenticated');
    
    // Ocultar dashboard y mostrar página principal
    hideDashboard();
    
    // Mostrar mensaje
    showNotification('Has cerrado sesión correctamente.', 'info');
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Crear contenido de la notificación con icono
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class='bx ${icon}' style="font-size: 1.2rem;"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Agregar estilos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 350px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    `;
    
    // Colores según tipo
    switch (type) {
        case 'success':
            notification.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
            break;
        case 'error':
            notification.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
            break;
        case 'warning':
            notification.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
            break;
        default:
            notification.style.background = 'linear-gradient(135deg, #0ea5e9, #0284c7)';
    }
    
    // Agregar al DOM
    document.body.appendChild(notification);
    
    // Remover después de 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Función para obtener icono según tipo de notificación
function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return 'bx-check-circle';
        case 'error':
            return 'bx-x-circle';
        case 'warning':
            return 'bx-error';
        default:
            return 'bx-info-circle';
    }
}

// Función para verificar autenticación al cargar la página
function checkAuthStatus() {
    const savedUser = localStorage.getItem('torker_user');
    const savedAuth = localStorage.getItem('torker_authenticated');
    
    if (savedUser && savedAuth === 'true') {
        currentUser = JSON.parse(savedUser);
        isAuthenticated = true;
        showDashboard();
        workshopNameDisplay.textContent = currentUser.workshopName;
    }
}

// Función para cerrar modales al hacer clic fuera
function closeModalsOnOutsideClick(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Función para agregar efectos hover a las tarjetas
function addCardEffects() {
    const cards = document.querySelectorAll('.stat-card, .module-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Verificar estado de autenticación
    checkAuthStatus();
    
    // Event listeners para cerrar modales
    loginModal.addEventListener('click', closeModalsOnOutsideClick);
    registerModal.addEventListener('click', closeModalsOnOutsideClick);
    
    // Cerrar modales con Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            hideLogin();
            hideRegister();
        }
    });
    
    // Agregar efectos a las tarjetas
    addCardEffects();
    
    // Agregar efecto de typing al título
    typeWriterEffect();
});

// Efecto de typing para el título
function typeWriterEffect() {
    const title = document.querySelector('.hero-title');
    if (!title) return;
    
    const text = title.textContent;
    title.textContent = '';
    title.style.borderRight = '2px solid var(--neon-green)';
    
    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < text.length) {
            title.textContent += text.charAt(i);
            i++;
        } else {
            clearInterval(typeInterval);
            title.style.borderRight = 'none';
        }
    }, 100);
}

// Funciones para los módulos del dashboard
function openModule(moduleName) {
    showNotification(`Módulo ${moduleName} en desarrollo. Próximamente disponible.`, 'info');
}

// Agregar event listeners a los botones de módulos
document.addEventListener('DOMContentLoaded', function() {
    const moduleButtons = document.querySelectorAll('.module-card .btn');
    moduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const moduleName = this.parentElement.querySelector('h3').textContent.replace(/[^\w\s]/g, '').trim();
            openModule(moduleName);
        });
    });
});

// Función para agregar efectos de partículas al fondo (opcional)
function addParticleEffect() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        opacity: 0.1;
    `;
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 2
        });
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fillStyle = 'var(--neon-blue)';
            ctx.fill();
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// Navbar auto-hide al hacer scroll
let lastScrollY = window.scrollY;
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
    if (!header) return;
    if (window.scrollY > lastScrollY && window.scrollY > 60) {
        // Scroll hacia abajo, ocultar header
        header.classList.add('navbar--hidden');
    } else {
        // Scroll hacia arriba, mostrar header
        header.classList.remove('navbar--hidden');
    }
    lastScrollY = window.scrollY;
});

// Funcionalidad del menú hamburguesa
function toggleMobileMenu() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');

        // Prevenir scroll del body cuando el menú está abierto
        if (navMenu.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'auto';
        }
    }
}

function closeMobileMenu() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

// Cerrar menú al hacer clic en un enlace
function setupMobileMenuLinks() {
    const navLinks = document.querySelectorAll('.nav-menu .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });
}

// Cerrar menú al hacer clic fuera
function setupMobileMenuOutsideClick() {
    document.addEventListener('click', function(event) {
        const navMenu = document.querySelector('.nav-menu');
        const navToggle = document.querySelector('.nav-toggle');

        if (navMenu && navMenu.classList.contains('active') &&
            !navMenu.contains(event.target) &&
            !navToggle.contains(event.target)) {
            closeMobileMenu();
        }
    });
}

// Iniciar funcionalidad del menú hamburguesa
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', toggleMobileMenu);
    }

    setupMobileMenuLinks();
    setupMobileMenuOutsideClick();

    // Comentar esta línea si no quieres el efecto de partículas
    // addParticleEffect();
});

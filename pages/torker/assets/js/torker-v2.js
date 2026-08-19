// Torker - Sistema de Gestión de Talleres
// JavaScript para funcionalidad de login, registro y dashboard

// Estado de la aplicación
let currentUser = null;
let isAuthenticated = false;
let accessToken = null;
let refreshToken = null;

// Configuración de la API (ver assets/js/torker-api-config.js)
const API_BASE_URL = window.TORKER_API_BASE || 'http://127.0.0.1:8000/api';

// Funciones helper para API
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    // Agregar token de autenticación si existe
    if (accessToken && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${accessToken}`;
    }

    try {
        const response = await fetch(url, config);

        // Si el token expiró, intentar refresh
        if (response.status === 401 && refreshToken) {
            const newTokens = await refreshAccessToken();
            if (newTokens) {
                config.headers.Authorization = `Bearer ${newTokens.access}`;
                return fetch(url, config);
            }
        }

        return response;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

async function refreshAccessToken() {
    if (isRefreshingToken) {
        // Si ya estamos refrescando, esperar un poco y retornar
        await new Promise(resolve => setTimeout(resolve, 100));
        return { access: accessToken };
    }

    isRefreshingToken = true;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            accessToken = data.access;
            localStorage.setItem('torker_access_token', accessToken);
            return data;
        } else {
            // Refresh token expiró, logout
            logout();
            return null;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        logout();
        return null;
    } finally {
        isRefreshingToken = false;
    }
}

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
    // Ocultar elementos de la página principal
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        heroSection.style.display = 'none'; // Forzar ocultamiento
    }

    dashboard.classList.remove('hidden');

    // Header se mantiene visible para navegación

    // Ocultar modales si están abiertos
    hideLogin();
    hideRegister();
    hideCreateInvoiceModal();

    // Ocultar sección de facturas si está abierta
    document.getElementById('invoicesSection').classList.add('hidden');

    // Actualizar datos del dashboard si tenemos información del usuario
    if (currentUser && currentUser.stats) {
        updateDashboardStats(currentUser.stats);
    }

    // Actualizar nombre del taller
    if (currentUser && currentUser.workshopName) {
        workshopNameDisplay.textContent = currentUser.workshopName;
    }

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

// Función para actualizar estadísticas del dashboard
function updateDashboardStats(stats) {
    // Actualizar estadísticas en las tarjetas
    const statCards = dashboard.querySelectorAll('.stat-card');

    statCards.forEach(card => {
        const statNumber = card.querySelector('.stat-number');
        const statTitle = card.querySelector('h3').textContent.toLowerCase();

        if (statTitle.includes('citas') && statNumber) {
            statNumber.textContent = stats.appointments || 0;
        } else if (statTitle.includes('órdenes') && statNumber) {
            statNumber.textContent = stats.work_orders || 0;
        } else if (statTitle.includes('clientes') && statNumber) {
            statNumber.textContent = stats.customers || 0;
        } else if (statTitle.includes('inventario') && statNumber) {
            statNumber.textContent = stats.parts || 0;
        }
    });
}

// Función para ocultar dashboard
function hideDashboard() {
    dashboard.classList.add('hidden');

    // Mostrar hero section nuevamente
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        heroSection.style.display = 'block';
    }

    // Header se mantiene visible
}

// Auth Supabase (misma cuenta Parche)
async function handleLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const email = formData.get('email');
    const password = formData.get('password');

    if (!email || !password) {
        showNotification('Por favor completa todos los campos.', 'error');
        return;
    }

    try {
        if (!supabaseConfigured()) {
            showNotification('Falta supabase-config.js — copia supabase-config.example.js', 'error');
            return;
        }
        await supabaseSignIn(email, password);
        hideLogin();
        event.target.reset();
        showNotification('¡Bienvenido! Sesión Parche/Torker iniciada.', 'success');
        window.location.href = '../dashboard/';
    } catch (error) {
        console.error('Login error:', error);
        showNotification(error.message || 'Error al iniciar sesión.', 'error');
    }
}

// Legacy Django login (respaldo)
async function handleLoginDjango(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const email = formData.get('email');
    const password = formData.get('password');

    if (!email || !password) {
        showNotification('Por favor completa todos los campos.', 'error');
        return;
    }

    const loginData = { email, password };

    try {
        const response = await apiRequest('/auth/login/', {
            method: 'POST',
            body: JSON.stringify(loginData)
        });

        if (response.ok) {
            const data = await response.json();

            accessToken = data.access;
            refreshToken = data.refresh;

            localStorage.setItem('torker_access_token', accessToken);
            localStorage.setItem('torker_refresh_token', refreshToken);

            const userDataSuccess = await loadUserData();

            if (userDataSuccess) {
                window.location.href = '../dashboard/';
                hideLogin();
                showNotification('¡Bienvenido! Has iniciado sesión correctamente.', 'success');
                event.target.reset();
            } else {
                showNotification('Error al cargar datos del usuario.', 'error');
            }

        } else {
            const errorData = await response.json();
            showNotification(errorData.detail || 'Error al iniciar sesión.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Error de conexión. Inténtalo de nuevo.', 'error');
    }
}

// Variable para controlar si ya estamos refrescando el token
let isRefreshingToken = false;

// Función para manejar registro
async function handleRegister(event) {
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

    // Separar nombre y apellido
    const nameParts = ownerName.trim().split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';

    try {
        const response = await apiRequest('/auth/register/', {
            method: 'POST',
            body: JSON.stringify({
                email,
                first_name: firstName,
                last_name: lastName,
                phone,
                password,
                workshopName
            })
        });

        if (response.ok) {
            const data = await response.json();

            // Guardar tokens (el registro podría devolver tokens automáticamente)
            if (data.access && data.refresh) {
                accessToken = data.access;
                refreshToken = data.refresh;
                localStorage.setItem('torker_access_token', accessToken);
                localStorage.setItem('torker_refresh_token', refreshToken);
            }

            // Cargar datos del usuario
            await loadUserData();

            // Redirigir al dashboard
            window.location.href = '../dashboard/';

            // Ocultar modal de registro
            hideRegister();

            // Mostrar mensaje de éxito
            showNotification('¡Registro exitoso! Tu taller ha sido creado.', 'success');

            // Limpiar formulario
            event.target.reset();

        } else {
            const errorData = await response.json();
            showNotification(errorData.message || 'Error al registrar el taller.', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showNotification('Error de conexión. Inténtalo de nuevo.', 'error');
    }
}

// Función para logout
function logout() {
    currentUser = null;
    isAuthenticated = false;
    accessToken = null;
    refreshToken = null;

    // Limpiar localStorage
    localStorage.removeItem('torker_user');
    localStorage.removeItem('torker_authenticated');
    localStorage.removeItem('torker_access_token');
    localStorage.removeItem('torker_refresh_token');

    // Ocultar todas las secciones y mostrar página principal
    hideDashboard();
    document.getElementById('invoicesSection').classList.add('hidden');

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

// Función para cargar datos del usuario y taller
async function loadUserData() {
    try {
        const response = await apiRequest('/dashboard/');

        if (response.ok) {
            const data = await response.json();
            currentUser = {
                id: data.workshop.owner,
                email: data.workshop.owner_email || '',
                workshopName: data.workshop.name,
                workshop: data.workshop,
                stats: data.stats
            };
            isAuthenticated = true;
            return true;
        } else {
            console.error('Error loading user data:', response.status, response.statusText);
            // Si es error 401, intentar refresh token
            if (response.status === 401) {
                const refreshSuccess = await refreshAccessToken();
                if (refreshSuccess) {
                    // Reintentar la carga de datos
                    return await loadUserData();
                }
            }
            return false;
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        return false;
    }
}

// Función para verificar autenticación al cargar la página
async function checkAuthStatus() {
    if (typeof getSupabaseAccessToken === 'function' && getSupabaseAccessToken()) {
        const ok = await loadSupabaseUserData();
        if (ok) {
            window.location.href = '../dashboard/';
            return;
        }
        supabaseSignOut();
    }

    const savedAccessToken = localStorage.getItem('torker_access_token');
    const savedRefreshToken = localStorage.getItem('torker_refresh_token');

    if (savedAccessToken && savedRefreshToken) {
        accessToken = savedAccessToken;
        refreshToken = savedRefreshToken;

        // Intentar cargar datos del usuario
        const success = await loadUserData();
        if (success) {
            // Usuario ya autenticado, redirigir a dashboard
            window.location.href = '../dashboard/';
        } else {
            // Tokens inválidos, limpiar
            logout();
        }
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
document.addEventListener('DOMContentLoaded', async function() {
    // Verificar estado de autenticación
    await checkAuthStatus();

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

    moduleButtons.forEach((button, index) => {
        button.addEventListener('click', function(event) {
            const moduleCard = this.closest('.module-card');
            const moduleTitle = moduleCard.querySelector('h3').textContent.trim();

            // Si el botón ya tiene onclick, no interferir
            if (this.hasAttribute('onclick')) {
                return;
            }

            // Verificar si es el módulo de Inventario
            if (moduleTitle.includes('Inventario')) {
                showInventory();
            } else {
                openModule(moduleTitle);
            }
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
        header.classList.add('header--hidden');
    } else {
        // Scroll hacia arriba, mostrar header
        header.classList.remove('header--hidden');
    }
    lastScrollY = window.scrollY;
});

// Funcionalidad del menú hamburguesa
function toggleMobileMenu() {
    const menuIcon = document.querySelector('.menu-icon');
    const navMenu = document.querySelector('.nav-menu');

    if (menuIcon && navMenu) {
        menuIcon.classList.toggle('active');
        navMenu.classList.toggle('active');

        // No prevenir scroll del body para menú desplegable
        // El menú desplegable no cubre toda la pantalla
    }
}

function closeMobileMenu() {
    const menuIcon = document.querySelector('.menu-icon');
    const navMenu = document.querySelector('.nav-menu');

    if (menuIcon && navMenu) {
        menuIcon.classList.remove('active');
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

// DESHABILITADO: Cerrar menú al hacer clic fuera (interfiere con menú principal)
function setupMobileMenuOutsideClick() {
    // DESHABILITADO PARA EVITAR CONFLICTOS
    // document.addEventListener('click', function(event) {
    //     const navMenu = document.querySelector('.nav-menu');
    //     const menuIcon = document.querySelector('.menu-icon');

    //     if (navMenu && navMenu.classList.contains('active') &&
    //         !navMenu.contains(event.target) &&
    //         !menuIcon.contains(event.target)) {
    //         menuIcon.classList.remove('active');
    //         navMenu.classList.remove('active');
    //         document.body.style.overflow = 'auto';
    //     }
    // });
}

// Iniciar funcionalidad del menú hamburguesa
document.addEventListener('DOMContentLoaded', function() {
    const menuIcon = document.querySelector('.menu-icon');
    if (menuIcon) {
        menuIcon.addEventListener('click', toggleMobileMenu);
    }

    setupMobileMenuLinks();
    setupMobileMenuOutsideClick();

    // Comentar esta línea si no quieres el efecto de partículas
    // addParticleEffect();
});

// ====================
// FUNCIONES DE FACTURACIÓN
// ====================

// Variables para facturación
let currentInvoices = [];

// Mostrar sección de facturas
async function showInvoices() {
    try {
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('invoicesSection').classList.remove('hidden');

        // Cargar datos de forma asíncrona y silenciosa
        await Promise.allSettled([
            loadInvoices(),
            loadCustomersForInvoice(),
            loadCompletedWorkOrders()
        ]);
    } catch (error) {
        console.error('Error al mostrar módulo de facturas:', error);
        // No mostrar notificación de error aquí para evitar popup
    }
}

// Ocultar sección de facturas y volver al dashboard
function showDashboard() {
    document.getElementById('invoicesSection').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
}

// Cargar lista de facturas
async function loadInvoices() {
    try {
        const response = await apiRequest('/invoices/');
        if (response.ok) {
            currentInvoices = await response.json();
            renderInvoices(currentInvoices);
        } else {
            console.error('Error loading invoices:', response.status, response.statusText);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando página...', 'warning');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                // Solo mostrar error si no es un error de red o conexión
                if (response.status >= 500) {
                    showNotification('Error al cargar facturas', 'error');
                }
            }
        }
    } catch (error) {
        console.error('Error loading invoices:', error);
        // No mostrar notificación de error de conexión al cargar inicialmente
        // Solo mostrar si es un error crítico
    }
}

// Renderizar facturas en la interfaz
function renderInvoices(invoices) {
    const container = document.getElementById('invoicesList');

    if (invoices.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--surface-variant);">
                <i class='bx bx-receipt' style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No hay facturas aún</p>
                <p>Crea tu primera factura haciendo clic en "Nueva Factura"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = invoices.map(invoice => `
        <div class="invoice-card">
            <div class="invoice-header">
                <div class="invoice-number">${invoice.invoice_number}</div>
                <div class="invoice-status ${invoice.payment_status}">${invoice.payment_status_display}</div>
            </div>
            <div class="invoice-info">
                <div class="invoice-info-item">
                    <div class="invoice-info-label">Cliente</div>
                    <div class="invoice-info-value">${invoice.customer_name}</div>
                </div>
                <div class="invoice-info-item">
                    <div class="invoice-info-label">Fecha</div>
                    <div class="invoice-info-value">${new Date(invoice.issue_date).toLocaleDateString('es-CO')}</div>
                </div>
                <div class="invoice-info-item">
                    <div class="invoice-info-label">Vencimiento</div>
                    <div class="invoice-info-value">${invoice.due_date ? new Date(invoice.due_date).toLocaleDateString('es-CO') : 'N/A'}</div>
                </div>
                <div class="invoice-info-item">
                    <div class="invoice-info-label">Total</div>
                    <div class="invoice-total">$${invoice.total.toLocaleString('es-CO')}</div>
                </div>
            </div>
            <div class="invoice-actions">
                <button class="btn btn-outline" onclick="downloadInvoicePDF(${invoice.id})">
                    <i class='bx bx-download'></i>
                    PDF
                </button>
                <button class="btn btn-primary" onclick="viewInvoiceDetails(${invoice.id})">
                    <i class='bx bx-show'></i>
                    Ver
                </button>
            </div>
        </div>
    `).join('');
}

// Filtrar facturas
function filterInvoices() {
    const statusFilter = document.getElementById('invoiceStatusFilter').value;
    const searchTerm = document.getElementById('invoiceSearch').value.toLowerCase();

    let filtered = currentInvoices;

    if (statusFilter) {
        filtered = filtered.filter(invoice => invoice.payment_status === statusFilter);
    }

    if (searchTerm) {
        filtered = filtered.filter(invoice =>
            invoice.invoice_number.toLowerCase().includes(searchTerm) ||
            invoice.customer_name.toLowerCase().includes(searchTerm)
        );
    }

    renderInvoices(filtered);
}

// Descargar PDF de factura
async function downloadInvoicePDF(invoiceId) {
    try {
        const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/download_pdf/`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `factura_${invoiceId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('PDF descargado exitosamente', 'success');
        } else {
            showNotification('Error al descargar PDF', 'error');
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Ver detalles de factura
function viewInvoiceDetails(invoiceId) {
    const invoice = currentInvoices.find(inv => inv.id === invoiceId);
    if (invoice) {
        // Por ahora solo mostrar notificación, después se puede implementar modal
        showNotification(`Factura ${invoice.invoice_number} - Total: $${invoice.total.toLocaleString('es-CO')}`, 'info');
    }
}

// Mostrar modal de crear factura
function showCreateInvoiceModal() {
    document.getElementById('createInvoiceModal').classList.remove('hidden');
}

// Ocultar modal de crear factura
function hideCreateInvoiceModal() {
    document.getElementById('createInvoiceModal').classList.add('hidden');
}

// Cargar clientes para el select de facturas
async function loadCustomersForInvoice() {
    try {
        const response = await apiRequest('/customers/');
        if (response.ok) {
            const customers = await response.json();
            const select = document.getElementById('invoiceCustomer');
            if (select) {
                select.innerHTML = '<option value="">Seleccionar cliente...</option>' +
                    customers.map(customer =>
                        `<option value="${customer.id}">${customer.first_name} ${customer.last_name}</option>`
                    ).join('');
            }
        }
    } catch (error) {
        console.error('Error loading customers:', error);
        // No mostrar notificación de error aquí
    }
}

// Cargar órdenes de trabajo completadas
async function loadCompletedWorkOrders() {
    try {
        const response = await apiRequest('/work-orders/');
        if (response.ok) {
            const workOrders = await response.json();
            const completedOrders = workOrders.filter(wo => wo.status === 'completed' && !wo.invoice);
            const select = document.getElementById('invoiceWorkOrder');
            if (select) {
                select.innerHTML = '<option value="">Sin orden de trabajo</option>' +
                    completedOrders.map(wo =>
                        `<option value="${wo.id}">OT-${wo.order_number} - ${wo.customer_name}</option>`
                    ).join('');
            }
        }
    } catch (error) {
        console.error('Error loading work orders:', error);
        // No mostrar notificación de error aquí
    }
}

// Manejar creación de factura
async function handleCreateInvoice(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const invoiceData = {
        customer: formData.get('customer'),
        work_order: formData.get('work_order') || null,
        due_date: formData.get('due_date') || null,
        payment_method: 'cash', // Por defecto
        notes: formData.get('notes') || ''
    };

    // Validar datos básicos
    if (!invoiceData.customer) {
        showNotification('Debe seleccionar un cliente', 'error');
        return;
    }

    try {
        let response;
        if (invoiceData.work_order) {
            // Crear factura desde orden de trabajo
            response = await apiRequest('/invoices/create_from_work_order/', {
                method: 'POST',
                body: JSON.stringify({
                    work_order_id: invoiceData.work_order,
                    payment_method: invoiceData.payment_method
                })
            });
        } else {
            // Crear factura manual (por ahora no implementado)
            showNotification('Creación manual de facturas próximamente', 'warning');
            return;
        }

        if (response.ok) {
            const invoice = await response.json();
            showNotification(`Factura ${invoice.invoice_number} creada exitosamente`, 'success');
            hideCreateInvoiceModal();
            event.target.reset();
            loadInvoices(); // Recargar lista
        } else {
            console.error('Error creating invoice:', response.status, response.statusText);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando página...', 'warning');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Error al crear factura', 'error');
            }
        }
    } catch (error) {
        console.error('Error creating invoice:', error);
        showNotification('Error de conexión al crear factura', 'error');
    }
// ====================
// FUNCIONES DE INVENTARIO
// ====================

// Variables para inventario
let currentParts = [];
let filteredParts = [];

// Mostrar sección de inventario
async function showInventory() {
    // Ocultar otras secciones
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('invoicesSection').classList.add('hidden');

    // Mostrar sección de inventario
    const inventorySection = document.getElementById('inventorySection');
    inventorySection.classList.remove('hidden');

    // Cargar datos de forma asíncrona y silenciosa
    await Promise.allSettled([
        loadParts()
    ]);

    showNotification('Módulo de Inventario activado', 'info');
}

// Ocultar sección de inventario y volver al dashboard
function showDashboard() {
    document.getElementById('inventorySection').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
}

// Cargar lista de repuestos
async function loadParts() {
    try {
        const response = await apiRequest('/spare-parts/');
        if (response.ok) {
            currentParts = await response.json();
            filteredParts = [...currentParts];
            renderParts(filteredParts);
            updateInventoryStats();
        } else {
            console.error('Error loading parts:', response.status, response.statusText);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando página...', 'warning');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                // Solo mostrar error si no es un error de red o conexión
                if (response.status >= 500) {
                    showNotification('Error al cargar repuestos', 'error');
                }
            }
        }
    } catch (error) {
        console.error('Error loading parts:', error);
        // No mostrar notificación de error de conexión al cargar inicialmente
        // Solo mostrar si es un error crítico
    }
}

// Actualizar estadísticas del inventario
function updateInventoryStats() {
    const totalParts = currentParts.length;
    const lowStockParts = currentParts.filter(part => part.is_low_stock).length;
    const totalValue = currentParts.reduce((sum, part) => sum + (part.stock_quantity * part.unit_cost), 0);
    const categories = new Set(currentParts.map(part => part.category)).size;

    document.getElementById('totalParts').textContent = totalParts;
    document.getElementById('lowStockParts').textContent = lowStockParts;
    document.getElementById('totalValue').textContent = `$${totalValue.toLocaleString('es-CO')}`;
    document.getElementById('totalCategories').textContent = categories;

    // Cambiar color del stock bajo si hay alertas
    const lowStockElement = document.getElementById('lowStockParts');
    if (lowStockParts > 0) {
        lowStockElement.style.color = 'var(--neon-pink)';
        lowStockElement.style.textShadow = '0 0 8px var(--neon-pink)';
    } else {
        lowStockElement.style.color = 'var(--neon-green)';
        lowStockElement.style.textShadow = '0 0 8px var(--neon-green)';
    }
}

// Renderizar repuestos en la interfaz
function renderParts(parts) {
    const container = document.getElementById('partsList');

    if (parts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--surface-variant);">
                <i class='bx bx-package' style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No se encontraron repuestos</p>
                <p>Agrega tu primer repuesto haciendo clic en "Agregar Repuesto"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = parts.map(part => {
        const stockStatus = getStockStatus(part);
        const profitMargin = part.profit_margin ? `${part.profit_margin.toFixed(1)}%` : 'N/A';

        return `
            <div class="part-card" data-id="${part.id}">
                <div class="part-header">
                    <div class="part-info">
                        <h3 class="part-name">${part.name}</h3>
                        <p class="part-code">${part.internal_code || part.part_number || 'Sin código'}</p>
                    </div>
                    <div class="part-status ${stockStatus.class}">
                        ${stockStatus.text}
                    </div>
                </div>

                <div class="part-details">
                    <div class="part-detail-item">
                        <span class="detail-label">Categoría:</span>
                        <span class="detail-value">${getCategoryDisplay(part.category)}</span>
                    </div>
                    <div class="part-detail-item">
                        <span class="detail-label">Marca:</span>
                        <span class="detail-value">${part.brand || 'N/A'}</span>
                    </div>
                    <div class="part-detail-item">
                        <span class="detail-label">Stock:</span>
                        <span class="detail-value ${part.is_low_stock ? 'low-stock' : ''}">${part.stock_quantity} unidades</span>
                    </div>
                    <div class="part-detail-item">
                        <span class="detail-label">Precio:</span>
                        <span class="detail-value">$${part.sale_price.toLocaleString('es-CO')}</span>
                    </div>
                    <div class="part-detail-item">
                        <span class="detail-label">Margen:</span>
                        <span class="detail-value">${profitMargin}</span>
                    </div>
                    <div class="part-detail-item">
                        <span class="detail-label">Ubicación:</span>
                        <span class="detail-value">${part.location || 'N/A'}</span>
                    </div>
                </div>

                <div class="part-description">
                    ${part.description || 'Sin descripción'}
                </div>

                <div class="part-actions">
                    <button class="btn btn-outline btn-sm" onclick="viewPartDetails(${part.id})">
                        <i class='bx bx-show'></i>
                        Ver
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="editPart(${part.id})">
                        <i class='bx bx-edit'></i>
                        Editar
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deletePart(${part.id})">
                        <i class='bx bx-trash'></i>
                        Eliminar
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Obtener estado del stock
function getStockStatus(part) {
    if (part.stock_quantity <= part.min_stock_level) {
        return { class: 'low-stock', text: 'Stock Bajo' };
    } else if (part.stock_quantity > part.max_stock_level) {
        return { class: 'over-stock', text: 'Sobre Stock' };
    } else {
        return { class: 'normal-stock', text: 'Stock Normal' };
    }
}

// Obtener nombre de categoría
function getCategoryDisplay(category) {
    const categories = {
        'motor': 'Motor',
        'transmision': 'Transmisión',
        'frenos': 'Frenos',
        'suspension': 'Suspensión',
        'electrico': 'Sistema Eléctrico',
        'carroceria': 'Carrocería',
        'accesorios': 'Accesorios',
        'lubricantes': 'Lubricantes',
        'filtros': 'Filtros',
        'neumaticos': 'Neumáticos',
        'other': 'Otro'
    };
    return categories[category] || category;
}

// Filtrar repuestos
function filterParts() {
    const searchTerm = document.getElementById('inventorySearch').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const stockFilter = document.getElementById('stockFilter').value;

    filteredParts = currentParts.filter(part => {
        // Filtro de búsqueda
        const matchesSearch = !searchTerm ||
            part.name.toLowerCase().includes(searchTerm) ||
            (part.internal_code && part.internal_code.toLowerCase().includes(searchTerm)) ||
            (part.part_number && part.part_number.toLowerCase().includes(searchTerm)) ||
            (part.brand && part.brand.toLowerCase().includes(searchTerm)) ||
            (part.description && part.description.toLowerCase().includes(searchTerm));

        // Filtro de categoría
        const matchesCategory = !categoryFilter || part.category === categoryFilter;

        // Filtro de stock
        let matchesStock = true;
        if (stockFilter) {
            if (stockFilter === 'low') {
                matchesStock = part.is_low_stock;
            } else if (stockFilter === 'normal') {
                matchesStock = !part.is_low_stock && part.stock_quantity <= part.max_stock_level;
            } else if (stockFilter === 'over') {
                matchesStock = part.stock_quantity > part.max_stock_level;
            }
        }

        return matchesSearch && matchesCategory && matchesStock;
    });

    sortParts();
}

// Ordenar repuestos
function sortParts() {
    const sortBy = document.getElementById('sortBy').value;

    filteredParts.sort((a, b) => {
        switch (sortBy) {
            case 'name':
                return a.name.localeCompare(b.name);
            case 'category':
                return a.category.localeCompare(b.category);
            case 'stock':
                return b.stock_quantity - a.stock_quantity;
            case 'price':
                return b.sale_price - a.sale_price;
            default:
                return 0;
        }
    });

    renderParts(filteredParts);
}

// Mostrar modal para agregar repuesto
function showAddPartModal() {
    document.getElementById('partModalTitle').innerHTML = "<i class='bx bx-plus'></i> Agregar Repuesto";
    document.getElementById('submitBtnText').textContent = "Guardar Repuesto";
    document.getElementById('partId').value = '';
    document.getElementById('partModal').classList.remove('hidden');
    document.querySelector('.part-form').reset();
}

// Mostrar modal para editar repuesto
function editPart(partId) {
    const part = currentParts.find(p => p.id === partId);
    if (!part) return;

    document.getElementById('partModalTitle').innerHTML = "<i class='bx bx-edit'></i> Editar Repuesto";
    document.getElementById('submitBtnText').textContent = "Actualizar Repuesto";
    document.getElementById('partId').value = part.id;

    // Llenar formulario con datos del repuesto
    document.getElementById('partName').value = part.name || '';
    document.getElementById('partNumber').value = part.part_number || '';
    document.getElementById('internalCode').value = part.internal_code || '';
    document.getElementById('brand').value = part.brand || '';
    document.getElementById('description').value = part.description || '';
    document.getElementById('category').value = part.category || '';
    document.getElementById('vehicleType').value = part.applicable_vehicle_types || 'motorcycle';
    document.getElementById('stockQuantity').value = part.stock_quantity || 0;
    document.getElementById('minStockLevel').value = part.min_stock_level || 5;
    document.getElementById('unitCost').value = part.unit_cost || 0;
    document.getElementById('salePrice').value = part.sale_price || 0;
    document.getElementById('wholesalePrice').value = part.wholesale_price || 0;
    document.getElementById('location').value = part.location || '';
    document.getElementById('supplier').value = part.supplier || '';
    document.getElementById('supplierCode').value = part.supplier_code || '';
    document.getElementById('warrantyMonths').value = part.warranty_months || 0;
    document.getElementById('weight').value = part.weight_kg || '';
    document.getElementById('dimensions').value = part.dimensions || '';
    document.getElementById('notes').value = part.notes || '';

    document.getElementById('partModal').classList.remove('hidden');
}

// Ocultar modal de repuesto
function hidePartModal() {
    document.getElementById('partModal').classList.add('hidden');
}

// Manejar envío del formulario de repuesto
async function handlePartSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const partId = formData.get('partId');

    const partData = {
        name: formData.get('name'),
        part_number: formData.get('part_number') || null,
        internal_code: formData.get('internal_code'),
        brand: formData.get('brand') || null,
        description: formData.get('description') || null,
        category: formData.get('category'),
        applicable_vehicle_types: formData.get('applicable_vehicle_types'),
        stock_quantity: parseInt(formData.get('stock_quantity')),
        min_stock_level: parseInt(formData.get('min_stock_level')) || 5,
        unit_cost: parseFloat(formData.get('unit_cost')),
        sale_price: parseFloat(formData.get('sale_price')),
        wholesale_price: formData.get('wholesale_price') ? parseFloat(formData.get('wholesale_price')) : null,
        location: formData.get('location') || null,
        supplier: formData.get('supplier') || null,
        supplier_code: formData.get('supplier_code') || null,
        warranty_months: parseInt(formData.get('warranty_months')) || 0,
        weight_kg: formData.get('weight_kg') ? parseFloat(formData.get('weight_kg')) : null,
        dimensions: formData.get('dimensions') || null,
        notes: formData.get('notes') || null
    };

    // Validaciones básicas
    if (!partData.name || !partData.internal_code || !partData.category) {
        showNotification('Por favor completa los campos obligatorios', 'error');
        return;
    }

    if (partData.unit_cost < 0 || partData.sale_price < 0) {
        showNotification('Los precios no pueden ser negativos', 'error');
        return;
    }

    if (partData.stock_quantity < 0) {
        showNotification('El stock no puede ser negativo', 'error');
        return;
    }

    try {
        let response;
        if (partId) {
            // Actualizar repuesto existente
            response = await apiRequest(`/spare-parts/${partId}/`, {
                method: 'PUT',
                body: JSON.stringify(partData)
            });
        } else {
            // Crear nuevo repuesto
            response = await apiRequest('/spare-parts/', {
                method: 'POST',
                body: JSON.stringify(partData)
            });
        }

        if (response.ok) {
            const part = await response.json();
            showNotification(
                partId ? 'Repuesto actualizado exitosamente' : 'Repuesto creado exitosamente',
                'success'
            );
            hidePartModal();
            event.target.reset();
            loadParts(); // Recargar lista
        } else {
            console.error('Error saving part:', response.status, response.statusText);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando página...', 'warning');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Error al guardar repuesto', 'error');
            }
        }
    } catch (error) {
        console.error('Error saving part:', error);
        showNotification('Error de conexión al guardar repuesto', 'error');
    }
}

// Ver detalles del repuesto
function viewPartDetails(partId) {
    const part = currentParts.find(p => p.id === partId);
    if (!part) return;

    // Por ahora mostrar notificación con información básica
    const details = `
        ${part.name}
        Código: ${part.internal_code || part.part_number || 'N/A'}
        Stock: ${part.stock_quantity} unidades
        Precio: $${part.sale_price.toLocaleString('es-CO')}
        Ubicación: ${part.location || 'N/A'}
    `;

    showNotification(details, 'info');
}

// Eliminar repuesto
async function deletePart(partId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este repuesto? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await apiRequest(`/spare-parts/${partId}/`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Repuesto eliminado exitosamente', 'success');
            loadParts(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al eliminar repuesto', 'error');
        }
    } catch (error) {
        console.error('Error deleting part:', error);
        showNotification('Error de conexión', 'error');
    }
}
}

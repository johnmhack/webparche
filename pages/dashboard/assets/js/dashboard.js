// Dashboard - Sistema de Gestión de Talleres
// JavaScript para funcionalidad del dashboard

// Estado de la aplicación
let currentUser = null;
let isAuthenticated = false;
let accessToken = null;
let refreshToken = null;

// Configuración de la API
const API_BASE_URL = 'https://webparche-production.up.railway.app/api';

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
    }
}

// Elementos del DOM
const dashboard = document.getElementById('dashboard');
const workshopNameDisplay = document.getElementById('workshopNameDisplay');

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

    // Redirigir a página principal de torker
    window.location.href = '../torker/';
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

            // Actualizar UI
            workshopNameDisplay.textContent = currentUser.workshopName;
            updateDashboardStats(currentUser.stats);

            return true;
        } else {
            console.error('Error loading user data');
            return false;
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        return false;
    }
}

// Función para verificar autenticación al cargar la página
async function checkAuthStatus() {
    const savedAccessToken = localStorage.getItem('torker_access_token');
    const savedRefreshToken = localStorage.getItem('torker_refresh_token');

    if (savedAccessToken && savedRefreshToken) {
        accessToken = savedAccessToken;
        refreshToken = savedRefreshToken;

        // Intentar cargar datos del usuario
        const success = await loadUserData();
        if (!success) {
            // Tokens inválidos, redirigir a login
            logout();
        }
    } else {
        // No hay tokens, redirigir a login
        logout();
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

    // Agregar efectos a las tarjetas
    addCardEffects();

    // Agregar event listeners a los botones de módulos
    const moduleButtons = document.querySelectorAll('.module-card .btn');
    moduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const moduleName = this.parentElement.querySelector('h3').textContent.replace(/[^\w\s]/g, '').trim();
            openModule(moduleName);
        });
    });
});

// Funciones para los módulos del dashboard
function openModule(moduleName) {
    showNotification(`Módulo ${moduleName} en desarrollo. Próximamente disponible.`, 'info');
}

// ====================
// FUNCIONES DE FACTURACIÓN
// ====================

// Variables para facturación
let currentInvoices = [];

// Mostrar sección de facturas
function showInvoices() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('invoicesSection').classList.remove('hidden');
    loadInvoices();
    loadCustomersForInvoice();
    loadCompletedWorkOrders();
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
            showNotification('Error al cargar facturas', 'error');
        }
    } catch (error) {
        console.error('Error loading invoices:', error);
        showNotification('Error de conexión', 'error');
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
            select.innerHTML = '<option value="">Seleccionar cliente...</option>' +
                customers.map(customer =>
                    `<option value="${customer.id}">${customer.first_name} ${customer.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading customers:', error);
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
            select.innerHTML = '<option value="">Sin orden de trabajo</option>' +
                completedOrders.map(wo =>
                    `<option value="${wo.id}">OT-${wo.order_number} - ${wo.customer_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading work orders:', error);
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
            const error = await response.json();
            showNotification(error.detail || 'Error al crear factura', 'error');
        }
    } catch (error) {
        console.error('Error creating invoice:', error);
        showNotification('Error de conexión', 'error');
    }
}
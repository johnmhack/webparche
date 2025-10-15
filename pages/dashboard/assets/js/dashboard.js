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
    console.log('🔍 Verificando autenticación en dashboard...');

    const savedAccessToken = localStorage.getItem('torker_access_token');
    const savedRefreshToken = localStorage.getItem('torker_refresh_token');

    console.log('📦 Tokens encontrados:', {
        access: !!savedAccessToken,
        refresh: !!savedRefreshToken
    });

    if (savedAccessToken && savedRefreshToken) {
        accessToken = savedAccessToken;
        refreshToken = savedRefreshToken;

        console.log('🔄 Intentando cargar datos del usuario...');
        // Intentar cargar datos del usuario
        const success = await loadUserData();
        if (!success) {
            console.log('❌ Tokens inválidos, redirigiendo a login...');
            // Tokens inválidos, redirigir a login
            logout();
        } else {
            console.log('✅ Usuario autenticado correctamente');
        }
    } else {
        console.log('❌ No hay tokens, redirigiendo a login...');
        // No hay tokens, redirigir a login
        logout();
    }
}

// Función para inicializar dashboard al cargar
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Dashboard DOM cargado, iniciando verificación de autenticación...');
    await checkAuthStatus();
});

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
// FUNCIONES DE FACTURACIÓN DIAN
// ====================

// Variables para facturación
let currentInvoices = [];

// Mostrar sección de facturas DIAN
function showInvoices() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('invoicesSection').classList.remove('hidden');
    loadInvoices();
    loadCustomersForInvoice();
    loadCompletedWorkOrders();
    showNotification('Módulo de Facturación Electrónica DIAN activado', 'info');
}

// Ocultar sección de facturas y volver al dashboard
function showDashboard() {
    // Ocultar todas las secciones
    document.getElementById('invoicesSection').classList.add('hidden');
    document.getElementById('customersSection').classList.add('hidden');

    // Mostrar dashboard
    document.getElementById('dashboard').classList.remove('hidden');

    // Scroll al inicio de la página
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Cargar lista de facturas DIAN
async function loadInvoices() {
    try {
        const response = await apiRequest('/electronic-invoices/');
        if (response.ok) {
            currentInvoices = await response.json();
            renderInvoices(currentInvoices);
        } else {
            showNotification('Error al cargar facturas electrónicas', 'error');
        }
    } catch (error) {
        console.error('Error loading electronic invoices:', error);
        showNotification('Error de conexión', 'error');
    }
}

// ====================
// FUNCIONES DE ÓRDENES DE TRABAJO
// ====================

// Variables para órdenes de trabajo
let currentWorkOrders = [];
let currentMechanics = [];

// Mostrar sección de órdenes de trabajo
function showWorkOrders() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('workOrdersSection').classList.remove('hidden');
    loadWorkOrders();
    loadMechanicsForFilter();
    showNotification('Módulo de Órdenes de Trabajo activado', 'info');
}

// Cargar lista de órdenes de trabajo
async function loadWorkOrders() {
    try {
        const response = await apiRequest('/work-orders/');
        if (response.ok) {
            currentWorkOrders = await response.json();
            renderWorkOrders(currentWorkOrders);
        } else {
            showNotification('Error al cargar órdenes de trabajo', 'error');
        }
    } catch (error) {
        console.error('Error loading work orders:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Renderizar órdenes de trabajo en la interfaz
function renderWorkOrders(workOrders) {
    const container = document.getElementById('workOrdersList');

    if (workOrders.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--surface-variant);">
                <i class='bx bx-clipboard' style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No hay órdenes de trabajo</p>
                <p>Crea tu primera orden de trabajo haciendo clic en "Nueva Orden de Trabajo"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = workOrders.map(workOrder => `
        <div class="work-order-card">
            <div class="work-order-header">
                <div class="work-order-number">OT-${workOrder.order_number}</div>
                <div class="work-order-status ${workOrder.status} ${workOrder.is_overdue ? 'overdue' : ''}">
                    ${getWorkOrderStatusDisplay(workOrder.status)}
                    ${workOrder.is_overdue ? ' (Atrasada)' : ''}
                </div>
            </div>
            <div class="work-order-info">
                <div class="work-order-info-item">
                    <div class="work-order-info-label">Cliente</div>
                    <div class="work-order-info-value">${workOrder.customer_name}</div>
                </div>
                <div class="work-order-info-item">
                    <div class="work-order-info-label">Vehículo</div>
                    <div class="work-order-info-value">${workOrder.vehicle_info}</div>
                </div>
                <div class="work-order-info-item">
                    <div class="work-order-info-label">Mecánico</div>
                    <div class="work-order-info-value">${workOrder.assigned_mechanic_name || 'Sin asignar'}</div>
                </div>
                <div class="work-order-info-item">
                    <div class="work-order-info-label">Progreso</div>
                    <div class="work-order-info-value">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${workOrder.progress_percentage}%"></div>
                        </div>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">${workOrder.progress_percentage}%</span>
                    </div>
                </div>
            </div>
            <div class="work-order-costs">
                <div class="work-order-cost-item">
                    <span class="cost-label">Estimado:</span>
                    <span class="cost-value">$${workOrder.estimated_cost?.toLocaleString('es-CO') || '0'}</span>
                </div>
                <div class="work-order-cost-item">
                    <span class="cost-label">Real:</span>
                    <span class="cost-value">$${workOrder.final_cost?.toLocaleString('es-CO') || '0'}</span>
                </div>
            </div>
            <div class="work-order-actions">
                <button class="btn btn-outline" onclick="viewWorkOrderDetails(${workOrder.id})">
                    <i class='bx bx-show'></i>
                    Ver
                </button>
                <button class="btn btn-secondary" onclick="editWorkOrder(${workOrder.id})">
                    <i class='bx bx-edit'></i>
                    Editar
                </button>
                <div class="status-actions">
                    ${getWorkOrderStatusActions(workOrder)}
                </div>
            </div>
        </div>
    `).join('');
}

// Función para obtener el display del estado de OT
function getWorkOrderStatusDisplay(status) {
    const statusMap = {
        'draft': 'Borrador',
        'pending': 'Pendiente',
        'approved': 'Aprobada',
        'in_progress': 'En Progreso',
        'quality_check': 'Control Calidad',
        'completed': 'Completada',
        'invoiced': 'Facturada',
        'cancelled': 'Cancelada'
    };
    return statusMap[status] || 'Desconocido';
}

// Función para obtener acciones de estado de OT
function getWorkOrderStatusActions(workOrder) {
    const actions = [];

    switch (workOrder.status) {
        case 'draft':
            actions.push(`<button class="btn btn-success" onclick="changeWorkOrderStatus(${workOrder.id}, 'approved')"><i class='bx bx-check'></i> Aprobar</button>`);
            break;
        case 'approved':
            actions.push(`<button class="btn btn-primary" onclick="changeWorkOrderStatus(${workOrder.id}, 'in_progress')"><i class='bx bx-play'></i> Iniciar</button>`);
            break;
        case 'in_progress':
            actions.push(`<button class="btn btn-warning" onclick="changeWorkOrderStatus(${workOrder.id}, 'quality_check')"><i class='bx bx-check-circle'></i> Control</button>`);
            actions.push(`<button class="btn btn-success" onclick="changeWorkOrderStatus(${workOrder.id}, 'completed')"><i class='bx bx-check-double'></i> Completar</button>`);
            break;
        case 'quality_check':
            actions.push(`<button class="btn btn-success" onclick="changeWorkOrderStatus(${workOrder.id}, 'completed')"><i class='bx bx-check-double'></i> Aprobar</button>`);
            actions.push(`<button class="btn btn-warning" onclick="changeWorkOrderStatus(${workOrder.id}, 'in_progress')"><i class='bx bx-undo'></i> Revisar</button>`);
            break;
        case 'completed':
            actions.push(`<button class="btn btn-primary" onclick="createInvoiceFromWorkOrder(${workOrder.id})"><i class='bx bx-receipt'></i> Facturar</button>`);
            break;
    }

    if (workOrder.status !== 'cancelled' && workOrder.status !== 'invoiced') {
        actions.push(`<button class="btn btn-danger" onclick="changeWorkOrderStatus(${workOrder.id}, 'cancelled')"><i class='bx bx-x'></i> Cancelar</button>`);
    }

    return actions.join('');
}

// Filtrar órdenes de trabajo
function filterWorkOrders() {
    const statusFilter = document.getElementById('workOrderStatusFilter').value;
    const searchTerm = document.getElementById('workOrderSearch').value.toLowerCase();
    const mechanicFilter = document.getElementById('workOrderMechanicFilter').value;

    let filtered = currentWorkOrders;

    if (statusFilter) {
        filtered = filtered.filter(wo => wo.status === statusFilter);
    }

    if (mechanicFilter) {
        filtered = filtered.filter(wo => wo.assigned_mechanic === parseInt(mechanicFilter));
    }

    if (searchTerm) {
        filtered = filtered.filter(wo =>
            wo.order_number.toString().includes(searchTerm) ||
            wo.customer_name.toLowerCase().includes(searchTerm) ||
            wo.vehicle_info.toLowerCase().includes(searchTerm)
        );
    }

    renderWorkOrders(filtered);
}

// Cargar mecánicos para el filtro
async function loadMechanicsForFilter() {
    try {
        const response = await apiRequest('/mechanics/');
        if (response.ok) {
            currentMechanics = await response.json();
            const select = document.getElementById('workOrderMechanicFilter');
            select.innerHTML = '<option value="">Todos</option>' +
                currentMechanics.map(mechanic =>
                    `<option value="${mechanic.id}">${mechanic.first_name} ${mechanic.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading mechanics:', error);
    }
}

// Mostrar modal para crear orden de trabajo
function showCreateWorkOrderModal() {
    document.getElementById('workOrderModalTitle').innerHTML = "<i class='bx bx-plus'></i> Nueva Orden de Trabajo";
    document.getElementById('workOrderSubmitText').textContent = 'Crear Orden de Trabajo';
    document.getElementById('workOrderModal').classList.remove('hidden');

    // Limpiar formulario
    document.querySelector('.work-order-form').reset();
    document.getElementById('workOrderId').value = '';

    // Cargar datos para los selects
    loadCustomersForWorkOrder();
    loadMechanicsForWorkOrder();
}

// Cargar clientes para el select de OT
async function loadCustomersForWorkOrder() {
    try {
        const response = await apiRequest('/customers/');
        if (response.ok) {
            const customers = await response.json();
            const select = document.getElementById('workOrderCustomer');
            select.innerHTML = '<option value="">Seleccionar cliente...</option>' +
                customers.map(customer =>
                    `<option value="${customer.id}">${customer.first_name} ${customer.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

// Cargar mecánicos para el select de OT
async function loadMechanicsForWorkOrder() {
    try {
        const response = await apiRequest('/mechanics/');
        if (response.ok) {
            const mechanics = await response.json();
            const select = document.getElementById('workOrderMechanic');
            select.innerHTML = '<option value="">Sin asignar</option>' +
                mechanics.map(mechanic =>
                    `<option value="${mechanic.id}">${mechanic.first_name} ${mechanic.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading mechanics:', error);
    }
}

// Cargar vehículos del cliente seleccionado
async function loadCustomerVehicles() {
    const customerId = document.getElementById('workOrderCustomer').value;
    if (!customerId) {
        document.getElementById('workOrderVehicle').innerHTML = '<option value="">Seleccionar vehículo...</option>';
        return;
    }

    try {
        const response = await apiRequest('/vehicles/');
        if (response.ok) {
            const vehicles = await response.json();
            const customerVehicles = vehicles.filter(v => v.customer === parseInt(customerId));
            const select = document.getElementById('workOrderVehicle');
            select.innerHTML = '<option value="">Seleccionar vehículo...</option>' +
                customerVehicles.map(vehicle =>
                    `<option value="${vehicle.id}">${vehicle.brand} ${vehicle.model} ${vehicle.year}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading vehicles:', error);
    }
}

// Ocultar modal de orden de trabajo
function hideWorkOrderModal() {
    document.getElementById('workOrderModal').classList.add('hidden');
}

// Manejar envío del formulario de orden de trabajo
async function handleWorkOrderSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const workOrderData = {
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        customer: formData.get('customer'),
        vehicle: formData.get('vehicle'),
        assigned_mechanic: formData.get('assigned_mechanic') || null,
        mileage_at_entry: formData.get('mileage_at_entry') || null,
        estimated_hours: formData.get('estimated_hours') || null,
        estimated_cost: formData.get('estimated_cost') || null,
        start_date: formData.get('start_date') || null,
        estimated_completion_date: formData.get('estimated_completion_date') || null,
        symptoms: formData.get('symptoms') || null,
        diagnosis: formData.get('diagnosis') || null,
        customer_notes: formData.get('customer_notes') || null,
        internal_notes: formData.get('internal_notes') || null
    };

    // Validar datos básicos
    if (!workOrderData.title || !workOrderData.customer || !workOrderData.vehicle) {
        showNotification('Título, cliente y vehículo son obligatorios', 'error');
        return;
    }

    try {
        const response = await apiRequest('/work-orders/', {
            method: 'POST',
            body: JSON.stringify(workOrderData)
        });

        if (response.ok) {
            const workOrder = await response.json();
            showNotification(`Orden de Trabajo OT-${workOrder.order_number} creada exitosamente`, 'success');

            hideWorkOrderModal();
            event.target.reset();
            loadWorkOrders(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al crear orden de trabajo', 'error');
        }
    } catch (error) {
        console.error('Error creating work order:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Cambiar estado de orden de trabajo
async function changeWorkOrderStatus(workOrderId, newStatus) {
    try {
        const response = await apiRequest(`/work-orders/${workOrderId}/change_status/`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(`Estado de OT actualizado: ${getWorkOrderStatusDisplay(newStatus)}`, 'success');
            loadWorkOrders(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al cambiar estado', 'error');
        }
    } catch (error) {
        console.error('Error changing work order status:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Ver detalles de orden de trabajo
function viewWorkOrderDetails(workOrderId) {
    const workOrder = currentWorkOrders.find(wo => wo.id === workOrderId);
    if (workOrder) {
        const details = `
            📋 Orden de Trabajo OT-${workOrder.order_number}
            Cliente: ${workOrder.customer_name}
            Vehículo: ${workOrder.vehicle_info}
            Mecánico: ${workOrder.assigned_mechanic_name || 'Sin asignar'}
            Estado: ${getWorkOrderStatusDisplay(workOrder.status)}
            Progreso: ${workOrder.progress_percentage}%
            Costo Estimado: $${workOrder.estimated_cost?.toLocaleString('es-CO') || '0'}
            Costo Real: $${workOrder.final_cost?.toLocaleString('es-CO') || '0'}
        `;
        showNotification(details, 'info');
    }
}

// Editar orden de trabajo
function editWorkOrder(workOrderId) {
    const workOrder = currentWorkOrders.find(wo => wo.id === workOrderId);
    if (!workOrder) return;

    // Por ahora mostrar mensaje, implementar edición completa después
    showNotification('Edición de órdenes de trabajo próximamente', 'info');
}

// Crear factura tradicional desde orden de trabajo
async function createInvoiceFromWorkOrder(workOrderId) {
    try {
        const response = await apiRequest('/invoices/create_from_work_order/', {
            method: 'POST',
            body: JSON.stringify({
                work_order_id: workOrderId,
                payment_method: 'cash'
            })
        });

        if (response.ok) {
            const invoice = await response.json();
            showNotification(`Factura ${invoice.invoice_number} creada desde OT-${workOrderId}`, 'success');
            loadWorkOrders(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al crear factura', 'error');
        }
    } catch (error) {
        console.error('Error creating invoice from work order:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Crear factura electrónica DIAN desde orden de trabajo
async function createElectronicInvoiceFromWorkOrder(workOrderId) {
    try {
        const response = await apiRequest('/electronic-invoices/create_from_work_order/', {
            method: 'POST',
            body: JSON.stringify({
                work_order_id: workOrderId,
                payment_method: 'cash'
            })
        });

        if (response.ok) {
            const invoice = await response.json();
            showNotification(`Factura Electrónica DIAN ${invoice.invoice_number} creada desde OT-${workOrderId}`, 'success');
            loadWorkOrders(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al crear factura electrónica', 'error');
        }
    } catch (error) {
        console.error('Error creating electronic invoice from work order:', error);
        showNotification('Error de conexión', 'error');
    }
}

// ====================
// FUNCIONES DE CLIENTES
// ====================

// Variables para clientes
let currentCustomers = [];
let editingCustomer = null;

// Mostrar sección de clientes
function showCustomers() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('customersSection').classList.remove('hidden');
    loadCustomers();
}

// Cargar lista de clientes
async function loadCustomers() {
    try {
        const response = await apiRequest('/customers/');
        if (response.ok) {
            currentCustomers = await response.json();
            renderCustomers(currentCustomers);
        } else {
            showNotification('Error al cargar clientes', 'error');
        }
    } catch (error) {
        console.error('Error loading customers:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Renderizar clientes en la interfaz
function renderCustomers(customers) {
    const container = document.getElementById('customersList');

    if (customers.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--surface-variant);">
                <i class='bx bx-group' style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No hay clientes registrados</p>
                <p>Crea tu primer cliente haciendo clic en "Nuevo Cliente"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = customers.map(customer => `
        <div class="customer-card">
            <div class="customer-header">
                <div class="customer-name">${customer.first_name} ${customer.last_name}</div>
                <div class="customer-status ${customer.is_active ? 'active' : 'inactive'}">
                    ${customer.is_active ? 'Activo' : 'Inactivo'}
                </div>
            </div>
            <div class="customer-info">
                <div class="customer-info-item">
                    <div class="customer-info-label">Documento</div>
                    <div class="customer-info-value">${customer.get_document_type_display} ${customer.document_number || 'N/A'}</div>
                </div>
                <div class="customer-info-item">
                    <div class="customer-info-label">Teléfono</div>
                    <div class="customer-info-value">${customer.phone || 'N/A'}</div>
                </div>
                <div class="customer-info-item">
                    <div class="customer-info-label">Email</div>
                    <div class="customer-info-value">${customer.email || 'N/A'}</div>
                </div>
                <div class="customer-info-item">
                    <div class="customer-info-label">Visitas</div>
                    <div class="customer-info-value">${customer.total_visits}</div>
                </div>
            </div>
            <div class="customer-address">
                <div class="customer-info-label">Dirección</div>
                <div class="customer-info-value">${customer.full_address || 'N/A'}</div>
            </div>
            <div class="customer-actions">
                <button class="btn btn-outline" onclick="viewCustomerDetails(${customer.id})">
                    <i class='bx bx-show'></i>
                    Ver
                </button>
                <button class="btn btn-secondary" onclick="editCustomer(${customer.id})">
                    <i class='bx bx-edit'></i>
                    Editar
                </button>
                <button class="btn ${customer.is_active ? 'btn-warning' : 'btn-success'}" onclick="toggleCustomerStatus(${customer.id})">
                    <i class='bx ${customer.is_active ? 'bx-pause' : 'bx-play'}'></i>
                    ${customer.is_active ? 'Desactivar' : 'Activar'}
                </button>
            </div>
        </div>
    `).join('');
}

// Filtrar clientes
function filterCustomers() {
    const searchTerm = document.getElementById('customerSearch').value.toLowerCase();
    const statusFilter = document.getElementById('customerStatusFilter').value;

    let filtered = currentCustomers;

    if (statusFilter !== '') {
        const isActive = statusFilter === 'true';
        filtered = filtered.filter(customer => customer.is_active === isActive);
    }

    if (searchTerm) {
        filtered = filtered.filter(customer =>
            customer.first_name.toLowerCase().includes(searchTerm) ||
            customer.last_name.toLowerCase().includes(searchTerm) ||
            customer.document_number?.toLowerCase().includes(searchTerm) ||
            customer.email?.toLowerCase().includes(searchTerm) ||
            customer.phone?.toLowerCase().includes(searchTerm)
        );
    }

    renderCustomers(filtered);
}

// Mostrar modal para crear cliente
function showCreateCustomerModal() {
    editingCustomer = null;
    document.getElementById('customerModalTitle').innerHTML = "<i class='bx bx-plus'></i> Nuevo Cliente";
    document.getElementById('customerSubmitText').textContent = 'Crear Cliente';
    document.getElementById('customerModal').classList.remove('hidden');

    // Limpiar formulario
    document.querySelector('.customer-form').reset();
    document.getElementById('customerId').value = '';
}

// Mostrar modal para editar cliente
function editCustomer(customerId) {
    const customer = currentCustomers.find(c => c.id === customerId);
    if (!customer) return;

    editingCustomer = customer;
    document.getElementById('customerModalTitle').innerHTML = "<i class='bx bx-edit'></i> Editar Cliente";
    document.getElementById('customerSubmitText').textContent = 'Actualizar Cliente';
    document.getElementById('customerModal').classList.remove('hidden');

    // Llenar formulario
    document.getElementById('customerId').value = customer.id;
    document.getElementById('firstName').value = customer.first_name;
    document.getElementById('lastName').value = customer.last_name;
    document.getElementById('documentType').value = customer.document_type;
    document.getElementById('documentNumber').value = customer.document_number || '';
    document.getElementById('phone').value = customer.phone || '';
    document.getElementById('email').value = customer.email || '';
    document.getElementById('address').value = customer.address || '';
    document.getElementById('city').value = customer.city || '';
    document.getElementById('department').value = customer.department || '';
    document.getElementById('customerNotes').value = customer.notes || '';
}

// Ocultar modal de cliente
function hideCustomerModal() {
    document.getElementById('customerModal').classList.add('hidden');
    editingCustomer = null;
}

// Manejar envío del formulario de cliente
async function handleCustomerSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const customerData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        document_type: formData.get('document_type'),
        document_number: formData.get('document_number') || null,
        phone: formData.get('phone') || null,
        email: formData.get('email') || null,
        address: formData.get('address') || null,
        city: formData.get('city') || null,
        department: formData.get('department') || null,
        notes: formData.get('notes') || null
    };

    // Validar datos básicos
    if (!customerData.first_name || !customerData.last_name) {
        showNotification('Nombre y apellido son obligatorios', 'error');
        return;
    }

    try {
        let response;
        if (editingCustomer) {
            // Actualizar cliente existente
            response = await apiRequest(`/customers/${editingCustomer.id}/`, {
                method: 'PUT',
                body: JSON.stringify(customerData)
            });
        } else {
            // Crear nuevo cliente
            response = await apiRequest('/customers/', {
                method: 'POST',
                body: JSON.stringify(customerData)
            });
        }

        if (response.ok) {
            const customer = await response.json();
            const message = editingCustomer ?
                `Cliente ${customer.first_name} ${customer.last_name} actualizado` :
                `Cliente ${customer.first_name} ${customer.last_name} creado`;
            showNotification(message, 'success');

            hideCustomerModal();
            event.target.reset();
            loadCustomers(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al guardar cliente', 'error');
        }
    } catch (error) {
        console.error('Error saving customer:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Ver detalles del cliente
function viewCustomerDetails(customerId) {
    const customer = currentCustomers.find(c => c.id === customerId);
    if (!customer) return;

    // Por ahora mostrar información básica, después se puede implementar modal detallado
    const details = `
        ${customer.first_name} ${customer.last_name}
        Documento: ${customer.get_document_type_display} ${customer.document_number || 'N/A'}
        Teléfono: ${customer.phone || 'N/A'}
        Email: ${customer.email || 'N/A'}
        Dirección: ${customer.full_address || 'N/A'}
        Visitas: ${customer.total_visits}
        Gasto total: $${customer.total_spent.toLocaleString('es-CO')}
    `;
    showNotification(details, 'info');
}

// Cambiar estado del cliente (activar/desactivar)
async function toggleCustomerStatus(customerId) {
    const customer = currentCustomers.find(c => c.id === customerId);
    if (!customer) return;

    const newStatus = !customer.is_active;
    const action = newStatus ? 'activar' : 'desactivar';

    try {
        const response = await apiRequest(`/customers/${customerId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ is_active: newStatus })
        });

        if (response.ok) {
            customer.is_active = newStatus;
            showNotification(`Cliente ${action}do exitosamente`, 'success');
            renderCustomers(currentCustomers); // Re-renderizar con el estado actualizado
        } else {
            showNotification(`Error al ${action} cliente`, 'error');
        }
    } catch (error) {
        console.error('Error toggling customer status:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Renderizar facturas DIAN en la interfaz
function renderInvoices(invoices) {
    const container = document.getElementById('invoicesList');

    if (invoices.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--surface-variant);">
                <i class='bx bx-receipt' style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No hay facturas electrónicas aún</p>
                <p>Crea tu primera factura DIAN haciendo clic en "Nueva Factura Electrónica"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = invoices.map(invoice => `
        <div class="invoice-card">
            <div class="invoice-header">
                <div class="invoice-number">${invoice.invoice_number}</div>
                <div class="invoice-status ${invoice.dian_status || 'draft'}">${getDianStatusDisplay(invoice.dian_status)}</div>
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
                    <div class="invoice-info-label">CUDE</div>
                    <div class="invoice-info-value" style="font-family: monospace; font-size: 0.8rem;">
                        ${invoice.cude ? invoice.cude.substring(0, 20) + '...' : 'Pendiente'}
                    </div>
                </div>
                <div class="invoice-info-item">
                    <div class="invoice-info-label">Total</div>
                    <div class="invoice-total">$${invoice.total.toLocaleString('es-CO')}</div>
                </div>
            </div>
            <div class="invoice-actions">
                <button class="btn btn-outline" onclick="downloadInvoiceXML(${invoice.id})">
                    <i class='bx bx-file'></i>
                    XML
                </button>
                <button class="btn btn-outline" onclick="downloadInvoicePDF(${invoice.id})">
                    <i class='bx bx-download'></i>
                    PDF
                </button>
                <button class="btn btn-primary" onclick="viewInvoiceDetails(${invoice.id})">
                    <i class='bx bx-show'></i>
                    Ver
                </button>
                ${invoice.dian_status === 'draft' ? `
                    <button class="btn btn-success" onclick="sendToDian(${invoice.id})">
                        <i class='bx bx-send'></i>
                        Enviar DIAN
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Función para obtener el display del estado DIAN
function getDianStatusDisplay(status) {
    const statusMap = {
        'draft': 'Borrador',
        'sent': 'Enviado',
        'processing': 'Procesando',
        'processed': 'Aprobado',
        'send_failed': 'Error Envío',
        'rejected': 'Rechazado'
    };
    return statusMap[status] || 'Desconocido';
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

// Ver detalles de factura DIAN
function viewInvoiceDetails(invoiceId) {
    const invoice = currentInvoices.find(inv => inv.id === invoiceId);
    if (invoice) {
        const details = `
            📄 Factura Electrónica DIAN
            Número: ${invoice.invoice_number}
            Cliente: ${invoice.customer_name}
            Fecha: ${new Date(invoice.issue_date).toLocaleDateString('es-CO')}
            Total: $${invoice.total.toLocaleString('es-CO')}
            Estado DIAN: ${getDianStatusDisplay(invoice.dian_status)}
            ${invoice.cude ? `CUDE: ${invoice.cude}` : 'CUDE: Pendiente de generación'}
        `;
        showNotification(details, 'info');
    }
}

// Descargar XML de factura DIAN
async function downloadInvoiceXML(invoiceId) {
    try {
        const response = await fetch(`${API_BASE_URL}/electronic-invoices/${invoiceId}/download_xml/`, {
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
            a.download = `factura_dian_${invoiceId}.xml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('XML DIAN descargado exitosamente', 'success');
        } else {
            showNotification('Error al descargar XML DIAN', 'error');
        }
    } catch (error) {
        console.error('Error downloading XML:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Enviar factura a DIAN
async function sendToDian(invoiceId) {
    try {
        showNotification('Enviando factura a DIAN...', 'info');

        const response = await apiRequest(`/electronic-invoices/${invoiceId}/send_to_dian/`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showNotification(`Factura enviada exitosamente. CUFE: ${result.cufe}`, 'success');
                loadInvoices(); // Recargar lista
            } else {
                showNotification(`Error al enviar: ${result.error}`, 'error');
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al enviar factura a DIAN', 'error');
        }
    } catch (error) {
        console.error('Error sending to DIAN:', error);
        showNotification('Error de conexión con DIAN', 'error');
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

// Manejar creación de factura DIAN
async function handleCreateInvoice(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const invoiceData = {
        customer: formData.get('customer'),
        work_order: formData.get('work_order') || null,
        due_date: formData.get('due_date') || null,
        payment_method: formData.get('payment_method') || 'cash',
        notes: formData.get('notes') || ''
    };

    // Validar datos básicos
    if (!invoiceData.customer) {
        showNotification('Debe seleccionar un cliente', 'error');
        return;
    }

    try {
        // Cambiar texto del botón mientras procesa
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Creando Factura DIAN...';
        submitBtn.disabled = true;

        let response;
        if (invoiceData.work_order) {
            // Crear factura electrónica desde orden de trabajo
            response = await apiRequest('/electronic-invoices/create_from_work_order/', {
                method: 'POST',
                body: JSON.stringify({
                    work_order_id: invoiceData.work_order,
                    payment_method: invoiceData.payment_method,
                    notes: invoiceData.notes
                })
            });
        } else {
            // Crear factura manual (por ahora no implementado)
            showNotification('Creación manual de facturas electrónicas próximamente', 'warning');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            return;
        }

        if (response.ok) {
            const invoice = await response.json();
            showNotification(`Factura Electrónica DIAN ${invoice.invoice_number} creada exitosamente`, 'success');

            // Mostrar información adicional sobre el proceso DIAN
            setTimeout(() => {
                showNotification(
                    `XML generado y validado. ${invoice.cude ? 'CUDE generado: ' + invoice.cude.substring(0, 20) + '...' : 'Listo para envío a DIAN'}`, 'info'
                );
            }, 1000);

            hideCreateInvoiceModal();
            event.target.reset();
            loadInvoices(); // Recargar lista
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al crear factura electrónica', 'error');
        }
    } catch (error) {
        console.error('Error creating electronic invoice:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        // Restaurar botón
        const submitBtn = event.target.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<i class="bx bx-save"></i> Crear Factura Electrónica';
        submitBtn.disabled = false;
    }
}
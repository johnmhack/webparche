// Dashboard - Sistema de Gestión de Talleres
// JavaScript para funcionalidad del dashboard

console.log('🚀 Dashboard JavaScript cargado correctamente');

// Estado de la aplicación
let currentUser = null;
let isAuthenticated = false;
let accessToken = null;
let refreshToken = null;

// Configuración de la API
const API_BASE_URL = 'https://webparche-production.up.railway.app/api';

// Estado para controlar reintentos de autenticación
let isRefreshingToken = false;
let refreshPromise = null;

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
        let response = await fetch(url, config);

        // Si el token expiró, intentar refresh (solo una vez por sesión)
        if (response.status === 401 && refreshToken && !isRefreshingToken) {
            console.log('🔄 Token expirado, intentando refresh...');

            isRefreshingToken = true;

            // Si ya hay un refresh en proceso, esperar
            if (!refreshPromise) {
                refreshPromise = refreshAccessToken();
            }

            const newTokens = await refreshPromise;

            if (newTokens) {
                console.log('✅ Token refrescado exitosamente');
                config.headers.Authorization = `Bearer ${newTokens.access}`;

                // Reintentar la petición original
                response = await fetch(url, config);
                console.log('🔄 Reintento de petición completado');
            } else {
                console.log('❌ Falló refresh de token, redirigiendo a login');
                logout();
                return response; // Retornar respuesta original con error
            }

            // Limpiar estado de refresh
            isRefreshingToken = false;
            refreshPromise = null;
        }

        return response;
    } catch (error) {
        console.error('API Request Error:', error);
        // Solo mostrar error de conexión si no es un problema de autenticación
        if (!isRefreshingToken) {
            showNotification('Error de conexión con el servidor', 'error');
        }
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

// Función para inicializar dashboard al cargar
document.addEventListener('DOMContentLoaded', async function() {
    await checkAuthStatus();
});

// ====================
// FUNCIONES DE AGENDA
// ====================

// Variables para agenda
let currentAppointments = [];
let currentServiceTypes = [];
let currentCalendarDate = new Date();
let calendarView = 'month'; // 'month', 'week', 'day'

// Mostrar sección de agenda
async function showAgenda() {
    console.log('🎯 Dashboard - Función showAgenda ejecutada - Abriendo módulo Agenda');

    try {
        // Ocultar otras secciones
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('invoicesSection').classList.add('hidden');
        document.getElementById('customersSection').classList.add('hidden');
        document.getElementById('inventorySection').classList.add('hidden');
        document.getElementById('workOrdersSection').classList.add('hidden');

        // Mostrar sección de agenda
        const agendaSection = document.getElementById('agendaSection');
        console.log('🔍 Dashboard - Verificando elemento agendaSection:', agendaSection);

        if (agendaSection) {
            agendaSection.classList.remove('hidden');
            console.log('📅 Dashboard - Sección de agenda mostrada, cargando datos...');

            // Cargar datos de forma asíncrona y silenciosa
            await Promise.allSettled([
                loadServiceTypes(),
                loadAppointments()
            ]);

            console.log('📅 Dashboard - Datos cargados, renderizando calendario...');
            renderCalendar();

            console.log('📅 Dashboard - Calendario renderizado, mostrando notificación...');
            showNotification('Módulo de Agenda activado', 'info');
            console.log('✅ Dashboard - Notificación de Agenda mostrada exitosamente');
        } else {
            console.error('❌ Dashboard - Elemento agendaSection no encontrado');
            showNotification('Error: Sección de agenda no encontrada', 'error');
        }
    } catch (error) {
        console.error('❌ Dashboard - Error en showAgenda():', error);
        showNotification('Error al abrir módulo de Agenda', 'error');
    }
}

// Cargar tipos de servicios
async function loadServiceTypes() {
    try {
        const response = await apiRequest('/service-types/');
        if (response.ok) {
            currentServiceTypes = await response.json();
        } else {
            console.error('Error loading service types:', response.status, response.statusText);
            // No mostrar notificación de error al cargar inicialmente
        }
    } catch (error) {
        console.error('Error loading service types:', error);
        // No mostrar notificación de error de conexión al cargar inicialmente
    }
}

// Cargar citas
async function loadAppointments() {
    try {
        console.log('📅 Dashboard - Iniciando carga de citas...');
        const response = await apiRequest('/appointments/');
        if (response.ok) {
            const data = await response.json();
            console.log('📅 Dashboard - Citas cargadas:', data);

            // Asegurar que sea un array
            currentAppointments = Array.isArray(data) ? data : [];
            console.log('📅 Dashboard - currentAppointments establecido como array:', currentAppointments.length, 'elementos');

            renderTodayAppointments();
        } else if (response.status !== 401) { // No mostrar error para 401 (se maneja automáticamente)
            console.error('Error loading appointments:', response.status, response.statusText);
            // Inicializar como array vacío en caso de error
            currentAppointments = [];
        }
    } catch (error) {
        console.error('Error loading appointments:', error);
        // Inicializar como array vacío en caso de error
        currentAppointments = [];
        // Error de conexión ya se maneja en apiRequest, no mostrar popup al cargar inicialmente
    }
}

// Renderizar calendario
function renderCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthYear = document.getElementById('currentMonthYear');

    if (calendarView === 'month') {
        renderMonthView(calendarGrid, currentMonthYear);
    } else if (calendarView === 'week') {
        renderWeekView(calendarGrid, currentMonthYear);
    } else if (calendarView === 'day') {
        renderDayView(calendarGrid, currentMonthYear);
    }
}

// Renderizar vista mensual
function renderMonthView(container, titleElement) {
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();

    titleElement.textContent = `${getMonthName(month)} ${year}`;

    // Obtener primer día del mes y último día
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay()); // Comenzar desde el domingo anterior

    const endDate = new Date(lastDay);
    endDate.setDate(endDate.getDate() + (6 - lastDay.getDay())); // Terminar el sábado siguiente

    let html = `
        <div class="calendar-header-days">
            <div class="calendar-day-header">Dom</div>
            <div class="calendar-day-header">Lun</div>
            <div class="calendar-day-header">Mar</div>
            <div class="calendar-day-header">Mié</div>
            <div class="calendar-day-header">Jue</div>
            <div class="calendar-day-header">Vie</div>
            <div class="calendar-day-header">Sáb</div>
        </div>
        <div class="calendar-body">
    `;

    let currentDate = new Date(startDate);

    while (currentDate <= endDate) {
        const weekStart = currentDate.getDay() === 0;
        if (weekStart) {
            html += '<div class="calendar-week">';
        }

        const isCurrentMonth = currentDate.getMonth() === month;
        const isToday = isSameDate(currentDate, new Date());
        const dayAppointments = getAppointmentsForDate(currentDate);

        html += `
            <div class="calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}" onclick="selectDate('${currentDate.toISOString().split('T')[0]}')">
                <div class="calendar-day-number">${currentDate.getDate()}</div>
                <div class="calendar-day-appointments">
                    ${dayAppointments.slice(0, 3).map(apt => `
                        <div class="calendar-appointment ${apt.status}" style="background-color: ${apt.service_type?.color || '#3b82f6'}">
                            <span class="appointment-time">${formatTime(apt.start_time)}</span>
                            <span class="appointment-title">${apt.customer_full_name.split(' ')[0]}</span>
                        </div>
                    `).join('')}
                    ${dayAppointments.length > 3 ? `<div class="calendar-more">+${dayAppointments.length - 3} más</div>` : ''}
                </div>
            </div>
        `;

        const weekEnd = currentDate.getDay() === 6;
        if (weekEnd) {
            html += '</div>';
        }

        currentDate.setDate(currentDate.getDate() + 1);
    }

    html += '</div></div>';
    container.innerHTML = html;
}

// Funciones auxiliares para calendario
function getMonthName(month) {
    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    return months[month];
}

function isSameDate(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
}

function getAppointmentsForDate(date) {
    const dateStr = date.toISOString().split('T')[0];
    return Array.isArray(currentAppointments) ? currentAppointments.filter(apt => apt.appointment_date === dateStr) : [];
}

function formatTime(timeStr) {
    return timeStr.substring(0, 5); // HH:MM
}

// Renderizar vista semanal (simplificada)
function renderWeekView(container, titleElement) {
    // Implementación simplificada - mostrar solo mensaje por ahora
    container.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-secondary);">Vista semanal próximamente</div>';
    titleElement.textContent = 'Vista Semanal';
}

// Renderizar vista diaria (simplificada)
function renderDayView(container, titleElement) {
    // Implementación simplificada - mostrar solo mensaje por ahora
    container.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-secondary);">Vista diaria próximamente</div>';
    titleElement.textContent = 'Vista Diaria';
}

// Cambiar vista del calendario
function setCalendarView(view) {
    calendarView = view;
    renderCalendar();

    // Actualizar botones
    document.querySelectorAll('.calendar-view-toggle button').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-sm');
    });

    event.target.classList.add('btn-primary');
    event.target.classList.remove('btn-sm');
}

// Navegación del calendario
function previousMonth() {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
    renderCalendar();
}

function nextMonth() {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
    renderCalendar();
    showNotification('Módulo de Agenda activado', 'info');
}

// Seleccionar fecha en el calendario
function selectDate(dateStr) {
    // Por ahora solo mostrar notificación
    const date = new Date(dateStr);
    const appointments = getAppointmentsForDate(date);

    if (appointments.length > 0) {
        const aptList = appointments.map(apt =>
            `${formatTime(apt.start_time)} - ${apt.customer_full_name} (${apt.service_type?.name || apt.custom_service_description})`
        ).join('\n');
        showNotification(`Citas para ${date.toLocaleDateString('es-CO')}:\n${aptList}`, 'info');
    } else {
        showNotification(`No hay citas programadas para ${date.toLocaleDateString('es-CO')}`, 'info');
    }
}

// Renderizar citas de hoy
function renderTodayAppointments() {
    console.log('📅 Dashboard - Renderizando citas de hoy, currentAppointments:', currentAppointments);
    const today = new Date().toISOString().split('T')[0];
    const todayAppointments = Array.isArray(currentAppointments) ? currentAppointments.filter(apt => apt.appointment_date === today) : [];
    console.log('📅 Dashboard - Citas de hoy encontradas:', todayAppointments.length);

    const container = document.getElementById('todayAppointmentsList');

    if (todayAppointments.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class='bx bx-calendar-x' style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>No hay citas programadas para hoy</p>
            </div>
        `;
        return;
    }

    container.innerHTML = todayAppointments.map(appointment => `
        <div class="appointment-card ${appointment.status}" onclick="viewAppointmentDetails(${appointment.id})">
            <div class="appointment-header">
                <div class="appointment-time">${formatTime(appointment.start_time)} - ${formatTime(appointment.end_time)}</div>
                <div class="appointment-status ${appointment.status}">${getAppointmentStatusDisplay(appointment.status)}</div>
            </div>
            <div class="appointment-info">
                <div class="appointment-customer">${appointment.customer_full_name}</div>
                <div class="appointment-service">${appointment.service_type?.name || appointment.custom_service_description}</div>
                <div class="appointment-vehicle">${appointment.vehicle_info}</div>
            </div>
            <div class="appointment-actions">
                <button class="btn btn-outline btn-sm" onclick="editAppointment(${appointment.id}); event.stopPropagation();">
                    <i class='bx bx-edit'></i>
                    Editar
                </button>
                <button class="btn btn-danger btn-sm" onclick="cancelAppointment(${appointment.id}); event.stopPropagation();">
                    <i class='bx bx-x'></i>
                    Cancelar
                </button>
            </div>
        </div>
    `).join('');
}

// Obtener display del estado de cita
function getAppointmentStatusDisplay(status) {
    const statusMap = {
        'scheduled': 'Programada',
        'confirmed': 'Confirmada',
        'in_progress': 'En Progreso',
        'completed': 'Completada',
        'no_show': 'No Asistió',
        'cancelled': 'Cancelada'
    };
    return statusMap[status] || 'Desconocido';
}

// Mostrar modal para crear cita
function showCreateAppointmentModal() {
    document.getElementById('appointmentModalTitle').innerHTML = "<i class='bx bx-plus'></i> Nueva Cita";
    document.getElementById('appointmentSubmitText').textContent = 'Programar Cita';
    document.getElementById('appointmentModal').classList.remove('hidden');

    // Limpiar formulario
    document.querySelector('.appointment-form').reset();
    document.getElementById('appointmentId').value = '';

    // Cargar datos para los selects
    loadCustomersForAppointment();
    loadServiceTypesForAppointment();
    loadMechanicsForAppointment();

    // Establecer fecha por defecto a hoy
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('appointmentDate').value = today;
}

// Cargar clientes para citas
async function loadCustomersForAppointment() {
    try {
        const response = await apiRequest('/customers/');
        if (response.ok) {
            const customers = await response.json();
            const select = document.getElementById('appointmentCustomer');
            select.innerHTML = '<option value="">Seleccionar cliente...</option>' +
                customers.map(customer =>
                    `<option value="${customer.id}">${customer.first_name} ${customer.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading customers for appointment:', error);
    }
}

// Cargar tipos de servicio para citas
function loadServiceTypesForAppointment() {
    const select = document.getElementById('appointmentServiceType');
    select.innerHTML = '<option value="">Seleccionar servicio...</option>' +
        currentServiceTypes.map(service =>
            `<option value="${service.id}">${service.name} (${service.estimated_duration} min)</option>`
        ).join('');
}

// Cargar mecánicos para citas
async function loadMechanicsForAppointment() {
    try {
        const response = await apiRequest('/mechanics/');
        if (response.ok) {
            const mechanics = await response.json();
            const select = document.getElementById('appointmentMechanic');
            select.innerHTML = '<option value="">Sin asignar</option>' +
                mechanics.map(mechanic =>
                    `<option value="${mechanic.id}">${mechanic.first_name} ${mechanic.last_name}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading mechanics for appointment:', error);
    }
}

// Cargar vehículos del cliente seleccionado
async function loadCustomerVehiclesForAppointment() {
    const customerId = document.getElementById('appointmentCustomer').value;
    if (!customerId) {
        document.getElementById('appointmentVehicle').innerHTML = '<option value="">Seleccionar vehículo...</option>';
        return;
    }

    try {
        const response = await apiRequest('/vehicles/');
        if (response.ok) {
            const vehicles = await response.json();
            const customerVehicles = vehicles.filter(v => v.customer === parseInt(customerId));
            const select = document.getElementById('appointmentVehicle');
            select.innerHTML = '<option value="">Seleccionar vehículo...</option>' +
                customerVehicles.map(vehicle =>
                    `<option value="${vehicle.id}">${vehicle.brand} ${vehicle.model} ${vehicle.year}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading vehicles for appointment:', error);
    }
}

// Calcular hora de fin automáticamente
function calculateEndTime() {
    const startTime = document.getElementById('appointmentStartTime').value;
    const duration = parseInt(document.getElementById('appointmentDuration').value) || 60;

    if (startTime) {
        const [hours, minutes] = startTime.split(':').map(Number);
        const startMinutes = hours * 60 + minutes;
        const endMinutes = startMinutes + duration;

        const endHours = Math.floor(endMinutes / 60);
        const endMins = endMinutes % 60;

        const endTimeStr = `${endHours.toString().padStart(2, '0')}:${endMins.toString().padStart(2, '0')}`;
        document.getElementById('appointmentEndTime').value = endTimeStr;
    }
}

// Actualizar duración cuando se selecciona tipo de servicio
function updateAppointmentDuration() {
    const serviceTypeId = document.getElementById('appointmentServiceType').value;
    const serviceType = currentServiceTypes.find(st => st.id === parseInt(serviceTypeId));

    if (serviceType) {
        document.getElementById('appointmentDuration').value = serviceType.estimated_duration;
        calculateEndTime();
    }
}

// Ocultar modal de cita
function hideAppointmentModal() {
    document.getElementById('appointmentModal').classList.add('hidden');
}

// Manejar envío del formulario de cita
async function handleAppointmentSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const appointmentData = {
        customer: formData.get('customer'),
        vehicle: formData.get('vehicle') || null,
        service_type: formData.get('service_type') || null,
        custom_service_description: formData.get('custom_service_description') || null,
        appointment_date: formData.get('appointment_date'),
        start_time: formData.get('start_time'),
        duration_minutes: parseInt(formData.get('duration_minutes')) || 60,
        assigned_mechanic: formData.get('assigned_mechanic') || null,
        priority: formData.get('priority') || 'normal',
        estimated_cost: parseFloat(formData.get('estimated_cost')) || 0,
        contact_phone: formData.get('contact_phone') || null,
        contact_email: formData.get('contact_email') || null,
        notes: formData.get('notes') || null,
        customer_notes: formData.get('customer_notes') || null
    };

    // Validar datos básicos
    if (!appointmentData.customer || !appointmentData.appointment_date || !appointmentData.start_time) {
        showNotification('Cliente, fecha y hora de inicio son obligatorios', 'error');
        return;
    }

    if (!appointmentData.service_type && !appointmentData.custom_service_description) {
        showNotification('Debe seleccionar un tipo de servicio o proporcionar una descripción', 'error');
        return;
    }

    try {
        const response = await apiRequest('/appointments/', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });

        if (response.ok) {
            const appointment = await response.json();
            showNotification(`Cita programada exitosamente para ${appointment.customer_full_name}`, 'success');

            hideAppointmentModal();
            event.target.reset();
            loadAppointments(); // Recargar lista
            renderCalendar(); // Actualizar calendario
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al programar cita', 'error');
        }
    } catch (error) {
        console.error('Error creating appointment:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Ver detalles de cita
function viewAppointmentDetails(appointmentId) {
    const appointment = currentAppointments.find(apt => apt.id === appointmentId);
    if (!appointment) return;

    const details = `
        📅 Cita - ${appointment.customer_full_name}
        Servicio: ${appointment.service_type?.name || appointment.custom_service_description}
        Fecha: ${new Date(appointment.appointment_date).toLocaleDateString('es-CO')}
        Hora: ${formatTime(appointment.start_time)} - ${formatTime(appointment.end_time)}
        Mecánico: ${appointment.assigned_mechanic_name || 'Sin asignar'}
        Estado: ${getAppointmentStatusDisplay(appointment.status)}
        ${appointment.vehicle_info ? `Vehículo: ${appointment.vehicle_info}` : ''}
        ${appointment.estimated_cost ? `Costo estimado: $${appointment.estimated_cost.toLocaleString('es-CO')}` : ''}
    `;
    showNotification(details, 'info');
}

// Editar cita
function editAppointment(appointmentId) {
    const appointment = currentAppointments.find(apt => apt.id === appointmentId);
    if (!appointment) return;

    // Por ahora mostrar mensaje, implementar edición completa después
    showNotification('Edición de citas próximamente', 'info');
}

// Cancelar cita
async function cancelAppointment(appointmentId) {
    if (!confirm('¿Estás seguro de que deseas cancelar esta cita?')) {
        return;
    }

    try {
        const response = await apiRequest(`/appointments/${appointmentId}/cancel/`, {
            method: 'POST',
            body: JSON.stringify({ notes: 'Cancelada por usuario' })
        });

        if (response.ok) {
            showNotification('Cita cancelada exitosamente', 'success');
            loadAppointments(); // Recargar lista
            renderCalendar(); // Actualizar calendario
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Error al cancelar cita', 'error');
        }
    } catch (error) {
        console.error('Error cancelling appointment:', error);
        showNotification('Error de conexión', 'error');
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
                const moduleCard = this.closest('.module-card');
                const moduleTitle = moduleCard.querySelector('h3').textContent.trim();

                console.log('🖱️ Dashboard - Botón clickeado:', moduleTitle);

                // Si el botón ya tiene onclick, no interferir
                if (this.hasAttribute('onclick')) {
                    console.log('✅ Dashboard - Botón con onclick directo, ejecutando acción directa');
                    return;
                }

                // Verificar módulos disponibles
                if (moduleTitle.includes('Inventario')) {
                    console.log('🎯 Dashboard - Detectado módulo Inventario, ejecutando showInventory()');
                    showInventory();
                } else if (moduleTitle.includes('Agenda')) {
                    console.log('📅 Dashboard - Detectado módulo Agenda, ejecutando showAgenda()');
                    showAgenda();
                } else {
                    console.log('⚠️ Dashboard - Módulo en desarrollo:', moduleTitle);
                    openModule(moduleTitle);
                }
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

        showNotification('Módulo de Facturación Electrónica DIAN activado', 'info');
    } catch (error) {
        console.error('Error al mostrar módulo de facturas:', error);
        // No mostrar notificación de error aquí para evitar popup
    }
}

// Ocultar sección de facturas y volver al dashboard
function showDashboard() {
    // Ocultar todas las secciones
    document.getElementById('invoicesSection').classList.add('hidden');
    document.getElementById('customersSection').classList.add('hidden');
    document.getElementById('inventorySection').classList.add('hidden');
    document.getElementById('workOrdersSection').classList.add('hidden');
    document.getElementById('agendaSection').classList.add('hidden');

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
            console.error('Error loading electronic invoices:', response.status, response.statusText);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando página...', 'warning');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                // Solo mostrar error si no es un error de red o conexión
                if (response.status >= 500) {
                    showNotification('Error al cargar facturas electrónicas', 'error');
                }
            }
        }
    } catch (error) {
        console.error('Error loading electronic invoices:', error);
        // No mostrar notificación de error de conexión al cargar inicialmente
        // Solo mostrar si es un error crítico
    }
}

// ====================
// FUNCIONES DE INVENTARIO
// ====================

// Variables para inventario
let currentParts = [];
let filteredParts = [];

// Mostrar sección de inventario
async function showInventory() {
    console.log('🎯 Dashboard - Función showInventory ejecutada - Abriendo módulo Inventario');

    // Ocultar otras secciones
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('inventorySection').classList.add('hidden');
    document.getElementById('invoicesSection').classList.add('hidden');
    document.getElementById('customersSection').classList.add('hidden');
    document.getElementById('workOrdersSection').classList.add('hidden');
    document.getElementById('agendaSection').classList.add('hidden');

    // Mostrar sección de inventario
    const inventorySection = document.getElementById('inventorySection');
    if (inventorySection) {
        inventorySection.classList.remove('hidden');
        console.log('📦 Dashboard - Sección de inventario mostrada, cargando partes...');

        // Cargar datos de forma asíncrona y silenciosa
        await Promise.allSettled([
            loadParts()
        ]);

        showNotification('Módulo de Inventario activado', 'info');
    } else {
        console.error('❌ Dashboard - Elemento inventorySection no encontrado');
        showNotification('Error: Sección de inventario no encontrada', 'error');
    }
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
        } else if (response.status !== 401) { // No mostrar error para 401 (se maneja automáticamente)
            console.error('Error loading parts:', response.status, response.statusText);
            // No mostrar notificación de error al cargar inicialmente
        }
    } catch (error) {
        console.error('Error loading parts:', error);
        // Error de conexión ya se maneja en apiRequest, no mostrar popup al cargar inicialmente
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
            const error = await response.json();
            showNotification(error.detail || 'Error al guardar repuesto', 'error');
        }
    } catch (error) {
        console.error('Error saving part:', error);
        showNotification('Error de conexión', 'error');
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

// ====================
// FUNCIONES DE ÓRDENES DE TRABAJO
// ====================

// Variables para órdenes de trabajo
let currentWorkOrders = [];
let currentMechanics = [];

// Mostrar sección de órdenes de trabajo
async function showWorkOrders() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('workOrdersSection').classList.remove('hidden');

    // Cargar datos de forma asíncrona y silenciosa
    await Promise.allSettled([
        loadWorkOrders(),
        loadMechanicsForFilter()
    ]);

    showNotification('Módulo de Órdenes de Trabajo activado', 'info');
}

// Cargar lista de órdenes de trabajo
async function loadWorkOrders() {
    try {
        const response = await apiRequest('/work-orders/');
        if (response.ok) {
            currentWorkOrders = await response.json();
            renderWorkOrders(currentWorkOrders);
        } else if (response.status !== 401) { // No mostrar error para 401 (se maneja automáticamente)
            console.error('Error loading work orders:', response.status, response.statusText);
            // No mostrar notificación de error al cargar inicialmente
        }
    } catch (error) {
        console.error('Error loading work orders:', error);
        // Error de conexión ya se maneja en apiRequest, no mostrar popup al cargar inicialmente
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
            if (select) {
                select.innerHTML = '<option value="">Todos</option>' +
                    currentMechanics.map(mechanic =>
                        `<option value="${mechanic.id}">${mechanic.first_name} ${mechanic.last_name}</option>`
                    ).join('');
            }
        }
    } catch (error) {
        console.error('Error loading mechanics:', error);
        // No mostrar notificación de error al cargar inicialmente
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
async function showCustomers() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('customersSection').classList.remove('hidden');

    // Cargar datos de forma asíncrona y silenciosa
    await Promise.allSettled([
        loadCustomers()
    ]);

    showNotification('Módulo de Clientes activado', 'info');
}

// Cargar lista de clientes
async function loadCustomers() {
    try {
        const response = await apiRequest('/customers/');
        if (response.ok) {
            currentCustomers = await response.json();
            renderCustomers(currentCustomers);
        } else if (response.status !== 401) { // No mostrar error para 401 (se maneja automáticamente)
            console.error('Error loading customers:', response.status, response.statusText);
            // No mostrar notificación de error al cargar inicialmente
        }
    } catch (error) {
        console.error('Error loading customers:', error);
        // Error de conexión ya se maneja en apiRequest, no mostrar popup al cargar inicialmente
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
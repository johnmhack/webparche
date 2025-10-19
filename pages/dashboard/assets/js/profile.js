/**
 * Gestión del Perfil del Taller y Configuración DIAN
 */

// Función auxiliar para ocultar todas las secciones
function hideAllSections() {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('invoicesSection').classList.add('hidden');
    document.getElementById('customersSection').classList.add('hidden');
    document.getElementById('inventorySection').classList.add('hidden');
    document.getElementById('workOrdersSection').classList.add('hidden');
    document.getElementById('agendaSection').classList.add('hidden');
    
    // Ocultar perfil si existe
    const profileSection = document.getElementById('profileSection');
    if (profileSection) {
        profileSection.classList.add('hidden');
    }
}

// Mostrar sección de perfil
function showProfile() {
    console.log('🎯 showProfile() - Iniciando...');
    
    hideAllSections();
    console.log('✅ Secciones ocultadas');
    
    const profileSection = document.getElementById('profileSection');
    console.log('📋 profileSection encontrado:', profileSection);
    
    if (profileSection) {
        profileSection.classList.remove('hidden');
        console.log('✅ Clase hidden removida de profileSection');
        console.log('📊 Classes actuales:', profileSection.className);
        console.log('👁️ Display style:', window.getComputedStyle(profileSection).display);
        console.log('📏 Visibility:', window.getComputedStyle(profileSection).visibility);
        console.log('📐 Position:', window.getComputedStyle(profileSection).position);
        console.log('🎨 Z-index:', window.getComputedStyle(profileSection).zIndex);
        
        // Obtener posición del elemento
        const rect = profileSection.getBoundingClientRect();
        console.log('📍 Posición en viewport:', {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            visible: rect.top < window.innerHeight && rect.bottom > 0
        });
        
        // Scroll al elemento
        console.log('🔄 Haciendo scroll al profileSection...');
        profileSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        console.log('📦 Contenido HTML (primeros 500 chars):', profileSection.innerHTML.substring(0, 500));
    } else {
        console.error('❌ profileSection NO encontrado en el DOM');
        return;
    }
    
    loadWorkshopProfile();
    checkDianConfigurationStatus();
    
    console.log('✅ showProfile() - Completado');
}

// Mostrar tab específico del perfil
function showProfileTab(tabName) {
    // Ocultar todos los tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar tab seleccionado
    document.getElementById(`${tabName}Tab`).classList.add('active');
    event.target.classList.add('active');
}

// Cargar datos del perfil del taller
async function loadWorkshopProfile() {
    try {
        // Verificar que haya token
        if (!accessToken) {
            console.error('No hay token de acceso');
            showNotification('Sesión expirada. Recargando...', 'warning');
            setTimeout(() => window.location.reload(), 1000);
            return;
        }
        
        // Usar apiRequest del dashboard.js que maneja autenticación
        const response = await apiRequest('/workshops/');
        
        if (!response.ok) {
            console.error('Error en respuesta:', response.status);
            if (response.status === 401) {
                showNotification('Sesión expirada. Recargando...', 'warning');
                setTimeout(() => window.location.reload(), 1000);
                return;
            }
            throw new Error('Error cargando perfil');
        }
        
        const data = await response.json();
        console.log('Workshops recibidos:', data);
        
        // La API retorna un objeto paginado: {count, next, previous, results}
        const workshops = data.results || data;
        
        if (!workshops || workshops.length === 0) {
            throw new Error('No se encontró taller para este usuario');
        }
        
        const workshop = workshops[0]; // El usuario solo tiene un taller
        console.log('Workshop seleccionado:', workshop);
        
        if (!workshop || !workshop.name) {
            throw new Error('Datos del taller incompletos');
        }
        
        // Llenar formulario de datos básicos
        document.getElementById('workshopName').value = workshop.name || '';
        document.getElementById('workshopLegalName').value = workshop.legal_name || '';
        document.getElementById('workshopNit').value = workshop.nit || '';
        document.getElementById('workshopPhone').value = workshop.phone || '';
        document.getElementById('workshopEmail').value = workshop.email || '';
        document.getElementById('workshopAddress').value = workshop.address || '';
        document.getElementById('workshopCity').value = workshop.city || '';
        document.getElementById('workshopDepartment').value = workshop.department || '';
        
        // Llenar formulario DIAN
        document.getElementById('taxRegime').value = workshop.tax_regime || 'comun';
        document.getElementById('organizationType').value = workshop.organization_type || '1';
        document.getElementById('defaultTaxRate').value = workshop.default_tax_rate || '19';
        
        // Marcar responsabilidades fiscales
        if (workshop.tax_responsibilities && Array.isArray(workshop.tax_responsibilities)) {
            workshop.tax_responsibilities.forEach(resp => {
                const checkbox = document.querySelector(`input[value="${resp}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        // Guardar ID del workshop
        window.currentWorkshopId = workshop.id;
        
        // Cargar resoluciones
        loadResolutions();
        
    } catch (error) {
        console.error('Error cargando perfil:', error);
        showNotification('Error cargando perfil del taller', 'error');
    }
}

// Verificar estado de configuración DIAN
async function checkDianConfigurationStatus() {
    // Esperar a que se cargue el workshop ID
    if (!window.currentWorkshopId) {
        console.log('Esperando workshop ID...');
        return;
    }
    
    try {
        // Usar apiRequest del dashboard.js
        const response = await apiRequest(`/workshops/${window.currentWorkshopId}/dian_configuration_status/`);
        
        if (!response.ok) throw new Error('Error verificando configuración');
        
        const status = await response.json();
        
        // Mostrar indicador de estado
        const indicator = document.getElementById('dianStatusIndicator');
        
        if (status.is_complete) {
            indicator.innerHTML = `
                <div style="background: rgba(34, 197, 94, 0.1); border: 2px solid #22c55e; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <i class='bx bx-check-circle' style="font-size: 2.5rem; color: #22c55e;"></i>
                        <div>
                            <h3 style="color: #22c55e; margin: 0;">Configuración DIAN Completa</h3>
                            <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary);">
                                Tu taller está listo para generar facturas electrónicas válidas ante la DIAN
                            </p>
                        </div>
                    </div>
                </div>
            `;
        } else {
            indicator.innerHTML = `
                <div style="background: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; border-radius: 12px; padding: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <i class='bx bx-error-circle' style="font-size: 2.5rem; color: #ef4444;"></i>
                        <div style="flex: 1;">
                            <h3 style="color: #ef4444; margin: 0;">Configuración DIAN Incompleta</h3>
                            <p style="margin: 0.5rem 0; color: var(--text-secondary);">
                                Completa los siguientes campos para habilitar la facturación electrónica:
                            </p>
                            <ul style="margin: 0.5rem 0; padding-left: 1.5rem; color: var(--text-primary);">
                                ${status.missing_fields.map(field => `<li>${field}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Mostrar warnings si existen
        if (status.warnings && status.warnings.length > 0) {
            const warningsHtml = `
                <div style="background: rgba(245, 158, 11, 0.1); border: 2px solid #f59e0b; border-radius: 12px; padding: 1rem; margin-top: 1rem;">
                    <h4 style="color: #f59e0b; margin: 0 0 0.5rem 0;">⚠️ Advertencias</h4>
                    <ul style="margin: 0; padding-left: 1.5rem;">
                        ${status.warnings.map(warning => `<li>${warning}</li>`).join('')}
                    </ul>
                </div>
            `;
            indicator.innerHTML += warningsHtml;
        }
        
    } catch (error) {
        console.error('Error verificando configuración DIAN:', error);
    }
}

// Guardar datos básicos del taller
async function handleSaveBasicData(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await apiRequest(`/workshops/${window.currentWorkshopId}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Error guardando datos');
        
        showNotification('Datos básicos guardados exitosamente', 'success');
        checkDianConfigurationStatus();
        
    } catch (error) {
        console.error('Error guardando datos básicos:', error);
        showNotification('Error guardando datos básicos', 'error');
    }
}

// Guardar configuración DIAN
async function handleSaveDianConfig(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    // Obtener responsabilidades fiscales marcadas
    const responsibilities = [];
    document.querySelectorAll('input[name="tax_responsibilities"]:checked').forEach(checkbox => {
        responsibilities.push(checkbox.value);
    });
    data.tax_responsibilities = responsibilities;
    
    try {
        const response = await apiRequest(`/workshops/${window.currentWorkshopId}/`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Error guardando configuración DIAN');
        
        showNotification('Configuración DIAN guardada exitosamente', 'success');
        checkDianConfigurationStatus();
        
    } catch (error) {
        console.error('Error guardando configuración DIAN:', error);
        showNotification('Error guardando configuración DIAN', 'error');
    }
}

// Guardar resolución DIAN
async function saveResolution() {
    const resolutionData = {
        resolution_number: document.getElementById('resolutionNumber').value,
        prefix: document.getElementById('resolutionPrefix').value,
        resolution_date: document.getElementById('resolutionDate').value,
        expires_date: document.getElementById('resolutionExpires').value,
        from_number: parseInt(document.getElementById('resolutionFrom').value),
        to_number: parseInt(document.getElementById('resolutionTo').value),
        document_type: 'invoice',
        is_active: true
    };
    
    // Validar campos
    if (!resolutionData.resolution_number || !resolutionData.prefix || 
        !resolutionData.resolution_date || !resolutionData.expires_date ||
        !resolutionData.from_number || !resolutionData.to_number) {
        showNotification('Complete todos los campos de la resolución', 'error');
        return;
    }
    
    try {
        const response = await apiRequest('/dian-resolutions/', {
            method: 'POST',
            body: JSON.stringify(resolutionData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error guardando resolución');
        }
        
        showNotification('Resolución DIAN guardada exitosamente', 'success');
        
        // Limpiar formulario
        document.getElementById('resolutionNumber').value = '';
        document.getElementById('resolutionPrefix').value = '';
        document.getElementById('resolutionDate').value = '';
        document.getElementById('resolutionExpires').value = '';
        document.getElementById('resolutionFrom').value = '';
        document.getElementById('resolutionTo').value = '';
        
        // Recargar lista de resoluciones
        loadResolutions();
        checkDianConfigurationStatus();
        
    } catch (error) {
        console.error('Error guardando resolución:', error);
        showNotification(error.message, 'error');
    }
}

// Cargar lista de resoluciones
async function loadResolutions() {
    try {
        const response = await apiRequest('/dian-resolutions/');
        
        if (!response.ok) {
            console.warn('No se pudieron cargar resoluciones:', response.status);
            const container = document.getElementById('resolutionsList');
            if (container) {
                container.innerHTML = '<p style="color: var(--text-secondary);">No hay resoluciones registradas</p>';
            }
            return;
        }
        
        const resolutions = await response.json();
        const container = document.getElementById('resolutionsList');
        
        if (!container) {
            console.warn('Contenedor de resoluciones no encontrado');
            return;
        }
        
        if (resolutions.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary);">No hay resoluciones registradas</p>';
            return;
        }
        
        container.innerHTML = resolutions.map(res => `
            <div style="background: rgba(0, 194, 255, 0.05); border: 1px solid rgba(0, 194, 255, 0.2); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h5 style="margin: 0 0 0.5rem 0; color: var(--neon-blue);">
                            ${res.prefix} - ${res.resolution_number}
                        </h5>
                        <p style="margin: 0; font-size: 0.9rem; color: var(--text-secondary);">
                            Rango: ${res.from_number} - ${res.to_number} | 
                            Actual: ${res.current_number} | 
                            Disponibles: ${res.available_numbers}
                        </p>
                        <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: var(--text-secondary);">
                            Vigencia: ${res.resolution_date} - ${res.expires_date}
                        </p>
                        <div style="margin-top: 0.5rem;">
                            <span style="padding: 0.25rem 0.75rem; background: ${res.status === 'ok' ? '#22c55e' : res.status === 'warning' ? '#f59e0b' : '#ef4444'}; color: white; border-radius: 12px; font-size: 0.85rem;">
                                ${res.status === 'ok' ? '✓ Activa' : res.status === 'warning' ? '⚠ Alerta' : '✗ Crítica'}
                            </span>
                            <span style="margin-left: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                                Uso: ${res.usage_percentage.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline" onclick="toggleResolutionStatus('${res.id}', ${!res.is_active})">
                        ${res.is_active ? 'Desactivar' : 'Activar'}
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error cargando resoluciones:', error);
    }
}

// Activar/Desactivar resolución
async function toggleResolutionStatus(resolutionId, activate) {
    try {
        const response = await apiRequest(`/dian-resolutions/${resolutionId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ is_active: activate })
        });
        
        if (!response.ok) throw new Error('Error actualizando resolución');
        
        showNotification(`Resolución ${activate ? 'activada' : 'desactivada'} exitosamente`, 'success');
        loadResolutions();
        checkDianConfigurationStatus();
        
    } catch (error) {
        console.error('Error actualizando resolución:', error);
        showNotification('Error actualizando resolución', 'error');
    }
}

// Función auxiliar para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
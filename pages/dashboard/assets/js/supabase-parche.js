// MVP Parche ↔ Torker vía Supabase (temporal: UUID manual hasta Auth Supabase)

const PARCHE_UUID_KEY = 'torker_propietario_id';
let parcheTaller = null;
let parcheMotoEncontrada = null;

function getPropietarioId() {
  return (localStorage.getItem(PARCHE_UUID_KEY) || '').trim();
}

function hideParcheSection() {
  document.getElementById('parcheSection')?.classList.add('hidden');
}

function hideAllForParche() {
  [
    'dashboard',
    'invoicesSection',
    'customersSection',
    'inventorySection',
    'workOrdersSection',
    'agendaSection',
    'profileSection',
  ].forEach((id) => document.getElementById(id)?.classList.add('hidden'));
}

async function supabaseApi(endpoint, options = {}) {
  const token = typeof getSupabaseAccessToken === 'function' ? getSupabaseAccessToken() : '';
  const propietarioId = getPropietarioId();

  if (!token && !propietarioId) {
    throw new Error('Inicia sesión con tu cuenta Parche');
  }

  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const uid = typeof getSupabasePropietarioId === 'function' ? getSupabasePropietarioId() : propietarioId;
  if (uid) headers['X-Propietario-Id'] = uid;
  if (token) headers.Authorization = `Bearer ${token}`;
  else if (propietarioId) headers['X-Propietario-Id'] = propietarioId;

  const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || data.detail || `Error ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

function guardarParcheUuid() {
  const input = document.getElementById('parchePropietarioId');
  const val = input?.value.trim();
  if (!val) {
    showNotification('Pega tu UUID de Supabase', 'warning');
    return;
  }
  localStorage.setItem(PARCHE_UUID_KEY, val);
  showNotification('UUID guardado', 'success');
  initParcheModule();
}

async function initParcheModule() {
  const token = typeof getSupabaseAccessToken === 'function' ? getSupabaseAccessToken() : '';
  const uuidBox = document.getElementById('parcheUuidBox');
  if (uuidBox) uuidBox.style.display = token ? 'none' : 'block';

  const uuid = token ? getSupabasePropietarioId() : getPropietarioId();
  const input = document.getElementById('parchePropietarioId');
  if (input && uuid) input.value = uuid;

  const status = document.getElementById('parcheTallerStatus');
  if (!uuid) {
    if (status) status.textContent = 'Pega tu UUID de Supabase para vincular el taller con Parche.';
    return;
  }

  try {
    parcheTaller = await supabaseApi('/supabase/taller/');
    if (status) status.textContent = `Taller vinculado: ${parcheTaller.nombre}`;
  } catch {
    parcheTaller = null;
    if (status) status.textContent = 'Sin taller en Supabase. Créalo con el botón de abajo.';
  }

  await cargarOrdenesParche();
}

async function crearTallerParche() {
  const nombre = document.getElementById('parcheTallerNombre')?.value.trim();
  if (!nombre) {
    showNotification('Nombre del taller requerido', 'warning');
    return;
  }
  try {
    parcheTaller = await supabaseApi('/supabase/taller/', {
      method: 'POST',
      body: JSON.stringify({
        nombre,
        direccion: document.getElementById('parcheTallerDireccion')?.value.trim() || 'Por definir',
        ciudad: document.getElementById('parcheTallerCiudad')?.value.trim() || 'Bogota',
        telefono: document.getElementById('parcheTallerTelefono')?.value.trim() || null,
      }),
    });
    showNotification('Taller creado en Supabase', 'success');
    initParcheModule();
  } catch (e) {
    if (String(e.message).includes('ya tiene un taller')) {
      parcheTaller = (await supabaseApi('/supabase/taller/'));
      initParcheModule();
      return;
    }
    showNotification(e.message, 'error');
  }
}

async function buscarMotoParche() {
  const placa = document.getElementById('parchePlaca')?.value.trim();
  if (!placa) {
    showNotification('Escribe una placa', 'warning');
    return;
  }
  try {
    parcheMotoEncontrada = await supabaseApi(`/supabase/motos/buscar/?placa=${encodeURIComponent(placa)}`);
    const box = document.getElementById('parcheMotoResult');
    if (box) {
      box.classList.remove('hidden');
      box.innerHTML = `
        <strong>Moto encontrada</strong><br>
        ${parcheMotoEncontrada.marca} ${parcheMotoEncontrada.modelo} · Placa ${parcheMotoEncontrada.placa}<br>
        Km: ${parcheMotoEncontrada.kilometraje_actual ?? '—'}
      `;
    }
  } catch (e) {
    parcheMotoEncontrada = null;
    document.getElementById('parcheMotoResult')?.classList.add('hidden');
    showNotification(e.message, 'error');
  }
}

async function crearOrdenParche() {
  if (!parcheTaller?.id) {
    showNotification('Primero vincula o crea tu taller en Supabase', 'warning');
    return;
  }
  const placa = document.getElementById('parchePlaca')?.value.trim();
  if (!placa) {
    showNotification('Busca una moto por placa', 'warning');
    return;
  }
  try {
    await supabaseApi('/supabase/ordenes/', {
      method: 'POST',
      body: JSON.stringify({
        taller_id: parcheTaller.id,
        placa,
        mecanico_nombre: document.getElementById('parcheMecanico')?.value.trim() || 'Mecánico',
        servicios: [{ nombre: document.getElementById('parcheServicio')?.value.trim() || 'Servicio general' }],
        notas: document.getElementById('parcheNotas')?.value.trim() || null,
      }),
    });
    showNotification('Orden creada en Supabase', 'success');
    await cargarOrdenesParche();
  } catch (e) {
    showNotification(e.message, 'error');
  }
}

async function cargarOrdenesParche() {
  const list = document.getElementById('parcheOrdenesList');
  if (!list || !parcheTaller?.id) {
    if (list) list.innerHTML = '<p class="parche-hint">Sin taller vinculado.</p>';
    return;
  }
  try {
    const ordenes = await supabaseApi(`/supabase/ordenes/?taller_id=${parcheTaller.id}`);
    if (!ordenes.length) {
      list.innerHTML = '<p class="parche-hint">No hay órdenes aún.</p>';
      return;
    }
    list.innerHTML = ordenes
      .map(
        (o) => `
      <div class="parche-orden-card">
        <div><strong>${o.servicios?.[0]?.nombre || 'Servicio'}</strong> · ${o.estado}</div>
        <div class="parche-hint">${new Date(o.created_at).toLocaleString('es-CO')}</div>
        ${
          o.estado === 'pendiente'
            ? `<button class="btn btn-primary btn-sm" onclick="cerrarOrdenParche('${o.id}')">Cerrar → historial Parche</button>`
            : '<span class="parche-ok">✓ En historial Parche</span>'
        }
      </div>`
      )
      .join('');
  } catch (e) {
    list.innerHTML = `<p class="parche-hint">${e.message}</p>`;
  }
}

async function cerrarOrdenParche(ordenId) {
  const costo = prompt('Costo total (COP):', '85000');
  if (costo === null) return;
  const km = prompt('Kilometraje:', '15000');
  if (km === null) return;
  const servicio = prompt('Tipo de servicio:', 'Cambio de aceite');
  if (servicio === null) return;

  try {
    await supabaseApi(`/supabase/ordenes/${ordenId}/cerrar/`, {
      method: 'POST',
      body: JSON.stringify({
        tipo_servicio: servicio,
        costo_total: Number(costo),
        kilometraje: Number(km),
      }),
    });
    showNotification('Orden cerrada · visible en app Parche', 'success');
    await cargarOrdenesParche();
  } catch (e) {
    showNotification(e.message, 'error');
  }
}

async function showParche() {
  hideAllForParche();
  document.getElementById('parcheSection')?.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  await initParcheModule();
  showNotification('Módulo Parche activado', 'info');
}

document.addEventListener('DOMContentLoaded', () => {
  const origShowDashboard = window.showDashboard;
  if (typeof origShowDashboard === 'function') {
    window.showDashboard = function () {
      origShowDashboard();
      hideParcheSection();
    };
  }
});

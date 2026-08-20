// Auth Supabase — misma cuenta que Parche

const SB_TOKEN_KEY = 'torker_supabase_access_token';
const SB_REFRESH_KEY = 'torker_supabase_refresh_token';
const SB_USER_KEY = 'torker_supabase_user';

function supabaseConfigured() {
  return Boolean(window.SUPABASE_URL && window.SUPABASE_ANON_KEY);
}

function getSupabaseAccessToken() {
  return localStorage.getItem(SB_TOKEN_KEY) || '';
}

function getSupabasePropietarioId() {
  const raw = localStorage.getItem(SB_USER_KEY);
  if (!raw) return '';
  try {
    return JSON.parse(raw).id || '';
  } catch {
    return '';
  }
}

async function supabaseAuthFetch(path, options = {}) {
  if (!supabaseConfigured()) {
    throw new Error('Falta assets/js/supabase-config.js (copia supabase-config.example.js)');
  }
  const url = `${window.SUPABASE_URL.replace(/\/rest\/v1\/?$/, '').replace(/\/$/, '')}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      apikey: window.SUPABASE_ANON_KEY,
      ...(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.msg || data.error_description || data.message || 'Error de autenticación');
  }
  return data;
}

function saveSupabaseSession(data) {
  localStorage.setItem(SB_TOKEN_KEY, data.access_token);
  localStorage.setItem(SB_REFRESH_KEY, data.refresh_token);
  localStorage.setItem(SB_USER_KEY, JSON.stringify(data.user || {}));
  if (data.user?.id) {
    localStorage.setItem('torker_propietario_id', data.user.id);
  }
  window.TORKER_USE_SUPABASE = true;
}

async function supabaseSignIn(email, password) {
  const data = await supabaseAuthFetch('/auth/v1/token?grant_type=password', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  saveSupabaseSession(data);
  return data;
}

async function supabaseRefreshSession() {
  const refresh = localStorage.getItem(SB_REFRESH_KEY);
  if (!refresh) return null;
  try {
    const data = await supabaseAuthFetch('/auth/v1/token?grant_type=refresh_token', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refresh }),
    });
    saveSupabaseSession(data);
    return data;
  } catch {
    return null;
  }
}

function supabaseSignOut() {
  localStorage.removeItem(SB_TOKEN_KEY);
  localStorage.removeItem(SB_REFRESH_KEY);
  localStorage.removeItem(SB_USER_KEY);
  localStorage.removeItem('torker_propietario_id');
  window.TORKER_USE_SUPABASE = false;
}

function useSupabaseErp() {
  if (window.TORKER_USE_SUPABASE) return true;
  const token = getSupabaseAccessToken();
  const uid = getSupabasePropietarioId();
  return !!(token || uid);
}

async function supabaseApi(endpoint, options = {}) {
  const base = window.TORKER_API_BASE || 'http://127.0.0.1:8000/api';
  const token = getSupabaseAccessToken();
  const propietarioId = getSupabasePropietarioId() || localStorage.getItem('torker_propietario_id') || '';

  if (!token && !propietarioId) {
    throw new Error('Inicia sesión con tu cuenta Parche');
  }

  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (propietarioId) headers['X-Propietario-Id'] = propietarioId;
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${base}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || data.detail || `Error ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

let parcheTallerCache = null;

async function ensureParcheTaller() {
  if (parcheTallerCache?.id) return parcheTallerCache;
  try {
    parcheTallerCache = await supabaseApi('/supabase/taller/');
  } catch {
    parcheTallerCache = null;
  }
  return parcheTallerCache;
}

function setParcheTallerCache(taller) {
  parcheTallerCache = taller;
}

async function loadSupabaseUserData() {
  const token = getSupabaseAccessToken();
  const propietarioId = getSupabasePropietarioId();
  if (!token && !propietarioId) return false;

  try {
    const headers = {};
    if (propietarioId) headers['X-Propietario-Id'] = propietarioId;
    if (token) headers.Authorization = `Bearer ${token}`;

    const base = window.TORKER_API_BASE || 'http://127.0.0.1:8000/api';
    let res = await fetch(`${base}/supabase/taller/`, { headers });

    if (res.status === 401 && token) {
      const refreshed = await supabaseRefreshSession();
      if (!refreshed) return false;
      headers.Authorization = `Bearer ${getSupabaseAccessToken()}`;
      res = await fetch(`${base}/supabase/taller/`, { headers });
    }

    const el = document.getElementById('workshopNameDisplay');
    if (res.ok) {
      const taller = await res.json();
      setParcheTallerCache(taller);
      if (el) el.textContent = taller.nombre;
    } else if (res.status === 404 && el) {
      el.textContent = 'Mi Taller (Parche)';
    }
    window.TORKER_USE_SUPABASE = true;
    return true;
  } catch {
    return false;
  }
}

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
}

async function loadSupabaseUserData() {
  const token = getSupabaseAccessToken();
  if (!token) return false;

  try {
    let res = await fetch(`${API_BASE_URL}/supabase/taller/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.status === 401) {
      const refreshed = await supabaseRefreshSession();
      if (!refreshed) return false;
      res = await fetch(`${API_BASE_URL}/supabase/taller/`, {
        headers: { Authorization: `Bearer ${getSupabaseAccessToken()}` },
      });
    }

    const el = document.getElementById('workshopNameDisplay');
    if (res.ok) {
      const taller = await res.json();
      if (el) el.textContent = taller.nombre;
    } else if (res.status === 404 && el) {
      el.textContent = 'Mi Taller (Parche)';
    }
    return true;
  } catch {
    return false;
  }
}

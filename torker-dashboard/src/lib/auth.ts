const TOKEN_KEY = 'torker_supabase_access_token';
const REFRESH_KEY = 'torker_supabase_refresh_token';
const USER_KEY = 'torker_supabase_user';

export function getAccessToken(): string {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_KEY) || '';
}

export function getPropietarioId(): string {
  const raw = localStorage.getItem(USER_KEY);
  if (raw) {
    try {
      return JSON.parse(raw).id || '';
    } catch {
      /* ignore */
    }
  }
  return localStorage.getItem('torker_propietario_id') || '';
}

export function getUserEmail(): string {
  const raw = localStorage.getItem(USER_KEY);
  if (raw) {
    try {
      return JSON.parse(raw).email || '';
    } catch {
      /* ignore */
    }
  }
  return '';
}

export function isAuthenticated(): boolean {
  return !!(getAccessToken() || getPropietarioId());
}

export function saveSession(data: {
  access_token: string;
  refresh_token: string;
  user?: { id: string; email?: string };
}) {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_KEY, data.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}));
  if (data.user?.id) {
    localStorage.setItem('torker_propietario_id', data.user.id);
  }
}

export function signOut() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem('torker_propietario_id');
}

export const LOGIN_PATH = '/pages/dashboard/app/login';

export function redirectToLogin() {
  window.location.href = LOGIN_PATH;
}

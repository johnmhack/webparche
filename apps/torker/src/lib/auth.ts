import { refreshSession } from './supabaseAuth';

const TOKEN_KEY = 'torker_supabase_access_token';
const REFRESH_KEY = 'torker_supabase_refresh_token';
const USER_KEY = 'torker_supabase_user';

let refreshInFlight: Promise<boolean> | null = null;

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
  return !!(getAccessToken() || getRefreshToken() || getPropietarioId());
}

export function saveSession(data: {
  access_token: string;
  refresh_token: string;
  user?: { id?: string; email?: string };
}) {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_KEY, data.refresh_token);
  if (data.user && (data.user.id || data.user.email)) {
    const prev = (() => {
      try {
        return JSON.parse(localStorage.getItem(USER_KEY) || '{}') as {
          id?: string;
          email?: string;
        };
      } catch {
        return {};
      }
    })();
    const merged = {
      id: data.user.id || prev.id || '',
      email: data.user.email || prev.email || '',
    };
    localStorage.setItem(USER_KEY, JSON.stringify(merged));
    if (merged.id) {
      localStorage.setItem('torker_propietario_id', merged.id);
    }
  }
}

export function signOut() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem('torker_propietario_id');
}

export const LOGIN_PATH = '/torker/login';

export function redirectToLogin() {
  window.location.href = LOGIN_PATH;
}

/** true si el JWT ya venció o vence en menos de `skewSec` segundos */
export function isAccessTokenExpired(skewSec = 60): boolean {
  const token = getAccessToken();
  if (!token) return true;
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (!payload?.exp) return true;
    return Date.now() / 1000 >= Number(payload.exp) - skewSec;
  } catch {
    return true;
  }
}

/**
 * Renueva el access_token con el refresh_token si hace falta.
 * Evita el estado “logueado pero sin taller” al recargar la página.
 */
export async function ensureValidSession(): Promise<boolean> {
  if (!isAccessTokenExpired()) return true;

  const refresh = getRefreshToken();
  if (!refresh) {
    if (!getAccessToken()) signOut();
    return !!getAccessToken();
  }

  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const session = await refreshSession(refresh);
      const prevUser = (() => {
        try {
          return JSON.parse(localStorage.getItem(USER_KEY) || '{}') as {
            id?: string;
            email?: string;
          };
        } catch {
          return {};
        }
      })();
      saveSession({
        access_token: session.access_token,
        refresh_token: session.refresh_token || refresh,
        user: session.user?.id ? session.user : prevUser,
      });
      return true;
    } catch {
      signOut();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

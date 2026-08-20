import { getSupabaseAnonKey, getSupabaseUrl, supabaseConfigured } from './supabaseEnv';

export { supabaseConfigured };

async function authFetch(path: string, options: RequestInit = {}) {
  if (!supabaseConfigured()) {
    throw new Error(
      'Falta VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY (archivo .env o variables de Netlify)',
    );
  }
  const res = await fetch(`${getSupabaseUrl()}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      apikey: getSupabaseAnonKey(),
      ...(options.headers as Record<string, string>),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      (data as { msg?: string; error_description?: string; message?: string }).msg ||
      (data as { error_description?: string }).error_description ||
      (data as { message?: string }).message ||
      'Error de autenticación';
    throw new Error(msg);
  }
  return data;
}

export interface SupabaseSession {
  access_token: string;
  refresh_token: string;
  user?: { id: string; email?: string };
}

export async function signInWithPassword(
  email: string,
  password: string,
): Promise<SupabaseSession> {
  return authFetch('/auth/v1/token?grant_type=password', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function refreshSession(refreshToken: string): Promise<SupabaseSession> {
  return authFetch('/auth/v1/token?grant_type=refresh_token', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

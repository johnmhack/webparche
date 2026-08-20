declare global {
  interface Window {
    SUPABASE_URL?: string;
    SUPABASE_ANON_KEY?: string;
  }
}

export {};

function baseUrl(): string {
  const raw = window.SUPABASE_URL || '';
  return raw.replace(/\/rest\/v1\/?$/, '').replace(/\/$/, '');
}

export function supabaseConfigured(): boolean {
  return Boolean(window.SUPABASE_URL && window.SUPABASE_ANON_KEY);
}

async function authFetch(path: string, options: RequestInit = {}) {
  if (!supabaseConfigured()) {
    throw new Error(
      'Falta supabase-runtime.js — en Netlify revisa SUPABASE_URL / SUPABASE_ANON_KEY y redeploy',
    );
  }
  const res = await fetch(`${baseUrl()}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      apikey: window.SUPABASE_ANON_KEY!,
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

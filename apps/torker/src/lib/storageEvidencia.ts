import { ensureValidSession, getAccessToken } from './auth';
import { getSupabaseAnonKey, getSupabaseUrl, supabaseConfigured } from './supabaseEnv';

/** Sube una foto de evidencia al bucket público evidencias-taller. */
export async function uploadEvidencia(
  tallerId: string,
  ordenId: string,
  file: File,
): Promise<string> {
  await ensureValidSession();
  const token = getAccessToken();
  if (!token || !supabaseConfigured()) {
    throw new Error('Sesión no válida');
  }

  const ext = (file.name.split('.').pop() || 'jpg').toLowerCase().replace(/[^a-z0-9]/g, '') || 'jpg';
  const path = `${tallerId}/${ordenId}/${crypto.randomUUID()}.${ext}`;
  const url = `${getSupabaseUrl()}/storage/v1/object/evidencias-taller/${path}`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      apikey: getSupabaseAnonKey(),
      'Content-Type': file.type || 'image/jpeg',
      'x-upsert': 'true',
    },
    body: file,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg =
      (data as { message?: string; error?: string }).message ||
      (data as { error?: string }).error ||
      `Error al subir foto (${res.status})`;
    throw new Error(msg);
  }

  return `${getSupabaseUrl()}/storage/v1/object/public/evidencias-taller/${path}`;
}

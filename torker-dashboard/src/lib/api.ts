import { API_BASE } from './types';
import { getAccessToken, getPropietarioId } from './auth';
import { supabaseApi } from './supabaseData';

declare global {
  interface Window {
    TORKER_API_BASE?: string;
  }
}

/** En Netlify no hay Django: usamos Supabase directo. En local (:8000 / Vite) usamos /api. */
export function shouldUseDirectSupabase(): boolean {
  if (typeof window === 'undefined') return false;
  if (window.TORKER_API_BASE) return false;
  if (import.meta.env.DEV) return false;
  const { hostname, port } = window.location;
  if ((hostname === 'localhost' || hostname === '127.0.0.1') && port === '8000') {
    return false;
  }
  return true;
}

function apiBase(): string {
  if (window.TORKER_API_BASE) return window.TORKER_API_BASE.replace(/\/$/, '');
  return API_BASE;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const propietarioId = getPropietarioId();

  if (!token && !propietarioId) {
    throw new Error('Inicia sesión con tu cuenta Parche');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (propietarioId) headers['X-Propietario-Id'] = propietarioId;
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${apiBase()}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.error || data.detail || `Error ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data as T;
}

export const api = {
  getTaller: () =>
    shouldUseDirectSupabase()
      ? supabaseApi.getTaller()
      : request<import('./types').Taller>('/supabase/taller/'),

  getClientes: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.getClientes(tallerId)
      : request<import('./types').Cliente[]>(`/supabase/clientes/?taller_id=${tallerId}`),

  createCliente: (tallerId: string, body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.createCliente(tallerId, body as Record<string, unknown>)
      : request<import('./types').Cliente>(`/supabase/clientes/?taller_id=${tallerId}`, {
          method: 'POST',
          body: JSON.stringify(body),
        }),

  updateCliente: (id: string, body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.updateCliente(id, body as Record<string, unknown>)
      : request<import('./types').Cliente>(`/supabase/clientes/${id}/`, {
          method: 'PATCH',
          body: JSON.stringify(body),
        }),

  getTiposServicio: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.getTiposServicio(tallerId)
      : request<import('./types').TipoServicio[]>(`/supabase/tipos-servicio/?taller_id=${tallerId}`),

  sembrarTiposServicio: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.sembrarTiposServicio(tallerId)
      : request<import('./types').TipoServicio[]>('/supabase/tipos-servicio/sembrar/', {
          method: 'POST',
          body: JSON.stringify({ taller_id: tallerId }),
        }),

  getCitas: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.getCitas(tallerId)
      : request<import('./types').Cita[]>(`/supabase/citas/?taller_id=${tallerId}`),

  createCita: (body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.createCita(body as Record<string, unknown>)
      : request<import('./types').Cita>('/supabase/citas/', {
          method: 'POST',
          body: JSON.stringify(body),
        }),

  cancelarCita: (id: string, tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.cancelarCita(id, tallerId)
      : request<import('./types').Cita>(`/supabase/citas/${id}/cancelar/`, {
          method: 'POST',
          body: JSON.stringify({ taller_id: tallerId, notes: 'Cancelada por usuario' }),
        }),

  buscarMoto: (placa: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.buscarMoto(placa)
      : request<import('./types').Moto>(`/supabase/motos/buscar/?placa=${encodeURIComponent(placa)}`),

  getOrdenes: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.getOrdenes(tallerId)
      : request<import('./types').Orden[]>(`/supabase/ordenes/?taller_id=${tallerId}`),

  createOrden: (body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.createOrden(body as Record<string, unknown>)
      : request('/supabase/ordenes/', { method: 'POST', body: JSON.stringify(body) }),

  cerrarOrden: (id: string, body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.cerrarOrden(id, body as Record<string, unknown>)
      : request(`/supabase/ordenes/${id}/cerrar/`, { method: 'POST', body: JSON.stringify(body) }),

  getRepuestos: (tallerId: string) =>
    shouldUseDirectSupabase()
      ? supabaseApi.getRepuestos(tallerId)
      : request<import('./types').Repuesto[]>(`/supabase/repuestos/?taller_id=${tallerId}`),

  createRepuesto: (tallerId: string, body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.createRepuesto(tallerId, body as Record<string, unknown>)
      : request<import('./types').Repuesto>(`/supabase/repuestos/?taller_id=${tallerId}`, {
          method: 'POST',
          body: JSON.stringify(body),
        }),

  updateRepuesto: (id: string, body: object) =>
    shouldUseDirectSupabase()
      ? supabaseApi.updateRepuesto(id, body as Record<string, unknown>)
      : request<import('./types').Repuesto>(`/supabase/repuestos/${id}/`, {
          method: 'PATCH',
          body: JSON.stringify(body),
        }),
};

let tallerCache: import('./types').Taller | null = null;

export async function ensureTaller() {
  if (tallerCache?.id) return tallerCache;
  tallerCache = await api.getTaller();
  return tallerCache;
}

export function clearTallerCache() {
  tallerCache = null;
}

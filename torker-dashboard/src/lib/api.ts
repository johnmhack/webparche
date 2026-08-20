import { API_BASE } from './types';
import { getAccessToken, getPropietarioId } from './auth';

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

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.error || data.detail || `Error ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data as T;
}

export const api = {
  getTaller: () => request<import('./types').Taller>('/supabase/taller/'),

  getClientes: (tallerId: string) =>
    request<import('./types').Cliente[]>(`/supabase/clientes/?taller_id=${tallerId}`),

  createCliente: (tallerId: string, body: object) =>
    request<import('./types').Cliente>(`/supabase/clientes/?taller_id=${tallerId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  updateCliente: (id: string, body: object) =>
    request<import('./types').Cliente>(`/supabase/clientes/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  getTiposServicio: (tallerId: string) =>
    request<import('./types').TipoServicio[]>(`/supabase/tipos-servicio/?taller_id=${tallerId}`),

  sembrarTiposServicio: (tallerId: string) =>
    request<import('./types').TipoServicio[]>('/supabase/tipos-servicio/sembrar/', {
      method: 'POST',
      body: JSON.stringify({ taller_id: tallerId }),
    }),

  getCitas: (tallerId: string) =>
    request<import('./types').Cita[]>(`/supabase/citas/?taller_id=${tallerId}`),

  createCita: (body: object) =>
    request<import('./types').Cita>('/supabase/citas/', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  cancelarCita: (id: string, tallerId: string) =>
    request<import('./types').Cita>(`/supabase/citas/${id}/cancelar/`, {
      method: 'POST',
      body: JSON.stringify({ taller_id: tallerId, notes: 'Cancelada por usuario' }),
    }),

  buscarMoto: (placa: string) =>
    request<import('./types').Moto>(`/supabase/motos/buscar/?placa=${encodeURIComponent(placa)}`),

  getOrdenes: (tallerId: string) =>
    request<import('./types').Orden[]>(`/supabase/ordenes/?taller_id=${tallerId}`),

  createOrden: (body: object) =>
    request('/supabase/ordenes/', { method: 'POST', body: JSON.stringify(body) }),

  cerrarOrden: (id: string, body: object) =>
    request(`/supabase/ordenes/${id}/cerrar/`, { method: 'POST', body: JSON.stringify(body) }),
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

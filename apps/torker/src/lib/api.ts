import { getAccessToken, getPropietarioId } from './auth';
import { supabaseApi } from './supabaseData';
import { supabaseConfigured } from './supabaseAuth';

/**
 * Torker usa solo Supabase (sin Django).
 * Django queda congelado / legacy.
 */
function assertReady() {
  if (!supabaseConfigured()) {
    throw new Error(
      'Falta supabase-runtime.js — ejecuta: python scripts/gen-supabase-config.py',
    );
  }
  if (!getAccessToken() && !getPropietarioId()) {
    throw new Error('Inicia sesión con tu cuenta Parche');
  }
}

export const api = {
  getTaller: () => {
    assertReady();
    return supabaseApi.getTaller();
  },

  updateTaller: (
    id: string,
    body: Partial<{
      nombre: string;
      direccion: string | null;
      ciudad: string | null;
      telefono: string | null;
      email: string | null;
      nit: string | null;
      horario: string | null;
      descripcion: string | null;
      contrato_aceptado_at: string | null;
      contrato_version: string | null;
    }>,
  ) => {
    assertReady();
    return supabaseApi.updateTaller(id, body);
  },

  getMecanicos: (tallerId: string, soloActivos = true) => {
    assertReady();
    return supabaseApi.getMecanicos(tallerId, soloActivos);
  },

  createMecanico: (
    tallerId: string,
    body: { nombre: string; telefono?: string | null; especialidad?: string | null },
  ) => {
    assertReady();
    return supabaseApi.createMecanico(tallerId, body);
  },

  updateMecanico: (
    id: string,
    body: Partial<{
      nombre: string;
      telefono: string | null;
      especialidad: string | null;
      activo: boolean;
    }>,
  ) => {
    assertReady();
    return supabaseApi.updateMecanico(id, body);
  },

  deleteMecanico: (id: string) => {
    assertReady();
    return supabaseApi.deleteMecanico(id);
  },

  getClientes: (tallerId: string) => {
    assertReady();
    return supabaseApi.getClientes(tallerId);
  },

  createCliente: (tallerId: string, body: object) => {
    assertReady();
    return supabaseApi.createCliente(tallerId, body as Record<string, unknown>);
  },

  updateCliente: (id: string, body: object) => {
    assertReady();
    return supabaseApi.updateCliente(id, body as Record<string, unknown>);
  },

  getTiposServicio: (tallerId: string, soloActivos = true) => {
    assertReady();
    return supabaseApi.getTiposServicio(tallerId, soloActivos);
  },

  sembrarTiposServicio: (tallerId: string) => {
    assertReady();
    return supabaseApi.sembrarTiposServicio(tallerId);
  },

  createTipoServicio: (
    tallerId: string,
    body: {
      name: string;
      description?: string;
      category?: string;
      estimated_duration?: number;
      base_price?: number;
      color?: string;
    },
  ) => {
    assertReady();
    return supabaseApi.createTipoServicio(tallerId, body);
  },

  updateTipoServicio: (
    id: string,
    body: Partial<{
      name: string;
      description: string;
      category: string;
      estimated_duration: number;
      base_price: number;
      color: string;
      is_active: boolean;
    }>,
  ) => {
    assertReady();
    return supabaseApi.updateTipoServicio(id, body);
  },

  getCitas: (tallerId: string) => {
    assertReady();
    return supabaseApi.getCitas(tallerId);
  },

  createCita: (body: object) => {
    assertReady();
    return supabaseApi.createCita(body as Record<string, unknown>);
  },

  cancelarCita: (id: string, tallerId: string) => {
    assertReady();
    return supabaseApi.cancelarCita(id, tallerId);
  },

  buscarMoto: (query: string, tallerId?: string) => {
    assertReady();
    return supabaseApi.buscarMoto(query, tallerId);
  },

  getHistorialMoto: (motoId: string, tallerId: string) => {
    assertReady();
    return supabaseApi.getHistorialMoto(motoId, tallerId);
  },

  getHistorialMotero: (moteroId: string, tallerId: string) => {
    assertReady();
    return supabaseApi.getHistorialMotero(moteroId, tallerId);
  },

  getOrdenes: (tallerId: string) => {
    assertReady();
    return supabaseApi.getOrdenes(tallerId);
  },

  getOrdenItems: (ordenId: string) => {
    assertReady();
    return supabaseApi.getOrdenItems(ordenId);
  },

  createOrden: (body: object) => {
    assertReady();
    return supabaseApi.createOrden(body as Record<string, unknown>);
  },

  addOrdenItem: (
    ordenId: string,
    body: { repuesto_id?: string | null; nombre: string; cantidad: number; precio_unitario: number },
  ) => {
    assertReady();
    return supabaseApi.addOrdenItem(ordenId, body);
  },

  removeOrdenItem: (itemId: string) => {
    assertReady();
    return supabaseApi.removeOrdenItem(itemId);
  },

  cerrarOrden: (id: string, body: object) => {
    assertReady();
    return supabaseApi.cerrarOrden(id, body as Record<string, unknown>);
  },

  getRepuestos: (tallerId: string) => {
    assertReady();
    return supabaseApi.getRepuestos(tallerId);
  },

  createRepuesto: (tallerId: string, body: object) => {
    assertReady();
    return supabaseApi.createRepuesto(tallerId, body as Record<string, unknown>);
  },

  updateRepuesto: (id: string, body: object) => {
    assertReady();
    return supabaseApi.updateRepuesto(id, body as Record<string, unknown>);
  },
};

let tallerCache: import('./types').Taller | null = null;

export async function ensureTaller() {
  if (tallerCache?.id) return tallerCache;
  try {
    tallerCache = await api.getTaller();
    return tallerCache;
  } catch (e) {
    // Si el token expiró, forzar mensaje claro
    const msg = e instanceof Error ? e.message : 'No se pudo cargar el taller';
    throw new Error(msg);
  }
}

export function clearTallerCache() {
  tallerCache = null;
}

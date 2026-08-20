/**
 * Acceso directo a Supabase REST (Netlify / producción sin Django).
 * En local con Django (:8000 o Vite proxy) se usa api.ts → /api.
 */
import { getAccessToken, getPropietarioId } from './auth';
import type { Cita, Cliente, Moto, Orden, Repuesto, Taller, TipoServicio } from './types';

const DOC_LABELS: Record<string, string> = {
  cc: 'Cédula de Ciudadanía',
  ce: 'Cédula de Extranjería',
  nit: 'NIT',
  ti: 'Tarjeta de Identidad',
  pasaporte: 'Pasaporte',
  other: 'Otro',
};

const CATEGORY_LABELS: Record<string, string> = {
  motor: 'Motor',
  transmision: 'Transmisión',
  frenos: 'Frenos',
  suspension: 'Suspensión',
  electrico: 'Sistema Eléctrico',
  carroceria: 'Carrocería',
  accesorios: 'Accesorios',
  lubricantes: 'Lubricantes',
  filtros: 'Filtros',
  neumaticos: 'Neumáticos',
  other: 'Otro',
};

function baseUrl(): string {
  return (window.SUPABASE_URL || '').replace(/\/rest\/v1\/?$/, '').replace(/\/$/, '');
}

async function rest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  if (!token) throw new Error('Inicia sesión con tu cuenta Parche');
  if (!window.SUPABASE_URL || !window.SUPABASE_ANON_KEY) {
    throw new Error('Falta configuración Supabase');
  }

  const res = await fetch(`${baseUrl()}/rest/v1/${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      apikey: window.SUPABASE_ANON_KEY,
      Authorization: `Bearer ${token}`,
      Prefer: options.method && options.method !== 'GET' ? 'return=representation' : 'return=representation',
      ...(options.headers as Record<string, string>),
    },
  });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      (data as { message?: string; error?: string; hint?: string }).message ||
      (data as { error?: string }).error ||
      `Error Supabase ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data as T;
}

async function rpc<T>(fn: string, body: object): Promise<T> {
  const token = getAccessToken();
  if (!token) throw new Error('Inicia sesión con tu cuenta Parche');
  const res = await fetch(`${baseUrl()}/rest/v1/rpc/${fn}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: window.SUPABASE_ANON_KEY!,
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = (data as { message?: string }).message || `Error RPC ${res.status}`;
    throw new Error(msg);
  }
  return data as T;
}

function serializarCliente(row: Record<string, unknown>): Cliente {
  const tipo = String(row.tipo_documento || 'cc');
  const parts = [row.direccion, row.ciudad, row.departamento].filter(Boolean);
  return {
    id: String(row.id),
    first_name: String(row.nombre || ''),
    last_name: String(row.apellido || ''),
    phone: (row.telefono as string) || null,
    email: (row.email as string) || null,
    document_type: tipo,
    document_number: (row.numero_documento as string) || null,
    address: (row.direccion as string) || null,
    city: (row.ciudad as string) || null,
    department: (row.departamento as string) || null,
    is_active: row.activo !== false,
    total_visits: Number(row.total_visitas || 0),
    total_spent: Number(row.total_gastado || 0),
    notes: (row.notas as string) || null,
    full_address: parts.length ? parts.join(', ') : null,
    get_document_type_display: DOC_LABELS[tipo] || tipo,
  };
}

function serializarRepuesto(row: Record<string, unknown>): Repuesto {
  const stock = Number(row.stock_cantidad || 0);
  const min = Number(row.stock_minimo || 5);
  const max = Number(row.stock_maximo || 50);
  const categoria = String(row.categoria || 'other');
  const costo = Number(row.costo_unitario || 0);
  let stock_status: Repuesto['stock_status'] = 'normal';
  if (stock <= min) stock_status = 'low';
  else if (stock >= max) stock_status = 'over';

  return {
    id: String(row.id),
    name: String(row.nombre || ''),
    description: (row.descripcion as string) || null,
    part_number: (row.numero_parte as string) || null,
    internal_code: (row.codigo_interno as string) || null,
    category: categoria,
    category_display: CATEGORY_LABELS[categoria] || categoria,
    brand: (row.marca as string) || null,
    stock_quantity: stock,
    min_stock_level: min,
    max_stock_level: max,
    unit_cost: costo,
    sale_price: Number(row.precio_venta || 0),
    location: (row.ubicacion as string) || null,
    supplier: (row.proveedor as string) || null,
    is_active: row.activo !== false,
    stock_status,
    inventory_value: stock * costo,
  };
}

function serializarTipo(row: Record<string, unknown>): TipoServicio {
  return {
    id: String(row.id),
    name: String(row.nombre || ''),
    estimated_duration: Number(row.duracion_estimada_min || 60),
    color: String(row.color || '#3b82f6'),
  };
}

function serializarCita(
  row: Record<string, unknown>,
  clientes: Record<string, Record<string, unknown>>,
  tipos: Record<string, Record<string, unknown>>,
): Cita {
  const cliente = clientes[String(row.cliente_id)] || {};
  const tipo = tipos[String(row.tipo_servicio_id || '')] || null;
  const nombre = `${cliente.nombre || ''} ${cliente.apellido || ''}`.trim();
  let hi = String(row.hora_inicio || '09:00').slice(0, 8);
  let hf = String(row.hora_fin || '10:00').slice(0, 8);
  if (hi.length === 5) hi += ':00';
  if (hf.length === 5) hf += ':00';

  return {
    id: String(row.id),
    customer: String(row.cliente_id),
    appointment_date: String(row.fecha_cita),
    start_time: hi,
    end_time: hf,
    duration_minutes: Number(row.duracion_minutos || 60),
    status: String(row.estado || 'scheduled'),
    priority: String(row.prioridad || 'normal'),
    estimated_cost: Number(row.costo_estimado || 0),
    custom_service_description: (row.descripcion_servicio_custom as string) || null,
    customer_full_name: nombre || 'Cliente',
    assigned_mechanic_name: (row.mecanico_nombre as string) || null,
    service_type: tipo ? serializarTipo(tipo) : null,
  };
}

export const supabaseApi = {
  async getTaller(): Promise<Taller> {
    const pid = getPropietarioId();
    const rows = await rest<Record<string, unknown>[]>(
      `talleres?propietario_id=eq.${pid}&select=*&limit=1`,
    );
    if (!rows?.[0]) throw new Error('Taller no encontrado');
    const t = rows[0];
    return {
      id: String(t.id),
      nombre: String(t.nombre || ''),
      direccion: t.direccion as string | undefined,
      ciudad: t.ciudad as string | undefined,
    };
  },

  async getClientes(tallerId: string): Promise<Cliente[]> {
    const rows = await rest<Record<string, unknown>[]>(
      `clientes_taller?taller_id=eq.${tallerId}&select=*&order=nombre.asc`,
    );
    return (rows || []).map(serializarCliente);
  },

  async createCliente(tallerId: string, body: Record<string, unknown>): Promise<Cliente> {
    const payload = {
      taller_id: tallerId,
      nombre: body.first_name,
      apellido: body.last_name || '',
      telefono: body.phone || null,
      email: body.email || null,
      tipo_documento: body.document_type || 'cc',
      numero_documento: body.document_number || null,
      direccion: body.address || null,
      ciudad: body.city || null,
      departamento: body.department || null,
      notas: body.notes || null,
      activo: true,
    };
    const rows = await rest<Record<string, unknown>[]>('clientes_taller', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return serializarCliente(Array.isArray(rows) ? rows[0] : rows);
  },

  async updateCliente(id: string, body: Record<string, unknown>): Promise<Cliente> {
    const map: Record<string, string> = {
      first_name: 'nombre',
      last_name: 'apellido',
      phone: 'telefono',
      email: 'email',
      document_type: 'tipo_documento',
      document_number: 'numero_documento',
      address: 'direccion',
      city: 'ciudad',
      department: 'departamento',
      notes: 'notas',
      is_active: 'activo',
    };
    const payload: Record<string, unknown> = { updated_at: new Date().toISOString() };
    for (const [k, db] of Object.entries(map)) {
      if (k in body && body[k] !== undefined) payload[db] = body[k];
    }
    const tallerId = body.taller_id;
    const q = tallerId
      ? `clientes_taller?id=eq.${id}&taller_id=eq.${tallerId}`
      : `clientes_taller?id=eq.${id}`;
    const rows = await rest<Record<string, unknown>[]>(q, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return serializarCliente(Array.isArray(rows) ? rows[0] : rows);
  },

  async getTiposServicio(tallerId: string): Promise<TipoServicio[]> {
    const rows = await rest<Record<string, unknown>[]>(
      `tipos_servicio_taller?taller_id=eq.${tallerId}&activo=eq.true&select=*&order=nombre.asc`,
    );
    return (rows || []).map(serializarTipo);
  },

  async sembrarTiposServicio(tallerId: string): Promise<TipoServicio[]> {
    const existing = await rest<Record<string, unknown>[]>(
      `tipos_servicio_taller?taller_id=eq.${tallerId}&select=id&limit=1`,
    );
    if (!existing?.length) {
      await rest('tipos_servicio_taller', {
        method: 'POST',
        body: JSON.stringify([
          {
            taller_id: tallerId,
            nombre: 'Mantenimiento general',
            categoria: 'maintenance',
            color: '#3b82f6',
            duracion_estimada_min: 60,
          },
          {
            taller_id: tallerId,
            nombre: 'Reparación',
            categoria: 'repair',
            color: '#ef4444',
            duracion_estimada_min: 120,
          },
          {
            taller_id: tallerId,
            nombre: 'Diagnóstico',
            categoria: 'diagnostic',
            color: '#f59e0b',
            duracion_estimada_min: 45,
          },
        ]),
      });
    }
    return supabaseApi.getTiposServicio(tallerId);
  },

  async getCitas(tallerId: string): Promise<Cita[]> {
    const [citas, clientes, tipos] = await Promise.all([
      rest<Record<string, unknown>[]>(
        `citas_taller?taller_id=eq.${tallerId}&select=*&order=fecha_cita.asc`,
      ),
      rest<Record<string, unknown>[]>(`clientes_taller?taller_id=eq.${tallerId}&select=*`),
      rest<Record<string, unknown>[]>(`tipos_servicio_taller?taller_id=eq.${tallerId}&select=*`),
    ]);
    const cmap = Object.fromEntries((clientes || []).map((c) => [String(c.id), c]));
    const tmap = Object.fromEntries((tipos || []).map((t) => [String(t.id), t]));
    return (citas || []).map((c) => serializarCita(c, cmap, tmap));
  },

  async createCita(body: Record<string, unknown>): Promise<Cita> {
    const tallerId = String(body.taller_id);
    const duracion = Number(body.duration_minutes || 60);
    let horaInicio = String(body.start_time || '09:00');
    if (horaInicio.length === 5) horaInicio += ':00';
    const [h, m] = horaInicio.split(':').map(Number);
    const finDate = new Date(2000, 0, 1, h, m + duracion);
    const horaFin = `${String(finDate.getHours()).padStart(2, '0')}:${String(finDate.getMinutes()).padStart(2, '0')}:00`;

    const payload = {
      taller_id: tallerId,
      cliente_id: body.customer,
      moto_id: body.vehicle || body.moto_id || null,
      tipo_servicio_id: body.service_type || null,
      descripcion_servicio_custom: body.custom_service_description || null,
      fecha_cita: body.appointment_date,
      hora_inicio: horaInicio,
      hora_fin: horaFin,
      duracion_minutos: duracion,
      estado: 'scheduled',
      prioridad: body.priority || 'normal',
      costo_estimado: body.estimated_cost || 0,
      mecanico_nombre: body.assigned_mechanic || body.mecanico_nombre || null,
      telefono_contacto: body.contact_phone || null,
      email_contacto: body.contact_email || null,
      notas_internas: body.notes || null,
      notas_cliente: body.customer_notes || null,
    };
    const rows = await rest<Record<string, unknown>[]>('citas_taller', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    const row = Array.isArray(rows) ? rows[0] : rows;
    const list = await supabaseApi.getCitas(tallerId);
    return list.find((c) => c.id === String(row.id)) || serializarCita(row, {}, {});
  },

  async cancelarCita(id: string, tallerId: string): Promise<Cita> {
    await rest(`citas_taller?id=eq.${id}&taller_id=eq.${tallerId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        estado: 'cancelled',
        notas_internas: 'Cancelada por usuario',
        updated_at: new Date().toISOString(),
      }),
    });
    const list = await supabaseApi.getCitas(tallerId);
    const found = list.find((c) => c.id === id);
    if (!found) throw new Error('Cita no encontrada');
    return found;
  },

  async buscarMoto(placa: string): Promise<Moto> {
    const row = await rpc<Record<string, unknown> | null>('buscar_moto_por_placa', {
      p_placa: placa.trim().toUpperCase(),
    });
    if (!row || row === null) throw new Error('Moto no encontrada');
    return {
      id: String(row.id),
      placa: String(row.placa),
      marca: String(row.marca || ''),
      modelo: String(row.modelo || ''),
      kilometraje_actual: row.kilometraje_actual != null ? Number(row.kilometraje_actual) : undefined,
    };
  },

  async getOrdenes(tallerId: string): Promise<Orden[]> {
    const rows = await rest<Record<string, unknown>[]>(
      `ordenes_trabajo?taller_id=eq.${tallerId}&select=*&order=created_at.desc`,
    );
    const ordenes = rows || [];
    if (!ordenes.length) return [];

    const ids = ordenes.map((r) => r.id).join(',');
    const items = await rest<Record<string, unknown>[]>(
      `orden_items?orden_id=in.(${ids})&select=*&order=created_at.asc`,
    ).catch(() => [] as Record<string, unknown>[]);

    const byOrden: Record<string, Orden['items']> = {};
    for (const it of items || []) {
      const oid = String(it.orden_id);
      if (!byOrden[oid]) byOrden[oid] = [];
      byOrden[oid]!.push({
        id: String(it.id),
        orden_id: oid,
        repuesto_id: (it.repuesto_id as string) || null,
        nombre: String(it.nombre || ''),
        cantidad: Number(it.cantidad || 1),
        precio_unitario: Number(it.precio_unitario || 0),
      });
    }

    return ordenes.map((r) => ({
      id: String(r.id),
      estado: String(r.estado || ''),
      servicios: r.servicios as Orden['servicios'],
      created_at: String(r.created_at || ''),
      mecanico_nombre: (r.mecanico_nombre as string) || null,
      costo_total: r.costo_total != null ? Number(r.costo_total) : null,
      moto_id: (r.moto_id as string) || null,
      notas: (r.notas as string) || null,
      items: byOrden[String(r.id)] || [],
    }));
  },

  async createOrden(body: Record<string, unknown>) {
    let motoId = body.moto_id;
    let moteroId = body.motero_id;
    if (!motoId && body.placa) {
      const moto = await supabaseApi.buscarMoto(String(body.placa));
      motoId = moto.id;
    }
    const payload = {
      taller_id: body.taller_id,
      moto_id: motoId,
      motero_id: moteroId || null,
      mecanico_nombre: body.mecanico_nombre || null,
      servicios: body.servicios || [],
      estado: body.estado || 'pendiente',
      costo_total: body.costo_total || null,
      notas: body.notas || null,
      fecha_entrada: body.fecha_entrada || new Date().toISOString(),
    };
    const rows = await rest<Record<string, unknown>[]>('ordenes_trabajo', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    const row = Array.isArray(rows) ? rows[0] : rows;
    return {
      id: String(row.id),
      estado: String(row.estado || 'pendiente'),
      servicios: row.servicios as Orden['servicios'],
      created_at: String(row.created_at || ''),
      items: [],
    } satisfies Orden;
  },

  async addOrdenItem(ordenId: string, body: {
    repuesto_id?: string | null;
    nombre: string;
    cantidad: number;
    precio_unitario: number;
  }) {
    const rows = await rest<Record<string, unknown>[]>('orden_items', {
      method: 'POST',
      body: JSON.stringify({
        orden_id: ordenId,
        repuesto_id: body.repuesto_id || null,
        nombre: body.nombre,
        cantidad: body.cantidad,
        precio_unitario: body.precio_unitario,
      }),
    });
    const it = Array.isArray(rows) ? rows[0] : rows;
    return {
      id: String(it.id),
      orden_id: ordenId,
      repuesto_id: (it.repuesto_id as string) || null,
      nombre: String(it.nombre),
      cantidad: Number(it.cantidad),
      precio_unitario: Number(it.precio_unitario),
    };
  },

  async removeOrdenItem(itemId: string) {
    await rest(`orden_items?id=eq.${itemId}`, { method: 'DELETE' });
  },

  async cerrarOrden(id: string, body: Record<string, unknown>) {
    return rpc('cerrar_orden_con_stock', {
      p_orden_id: id,
      p_costo: body.costo_total ?? null,
      p_kilometraje: body.kilometraje ?? null,
      p_tipo_servicio: body.tipo_servicio ?? null,
      p_descripcion: body.descripcion ?? null,
    });
  },

  async getRepuestos(tallerId: string): Promise<Repuesto[]> {
    const rows = await rest<Record<string, unknown>[]>(
      `repuestos_taller?taller_id=eq.${tallerId}&activo=eq.true&select=*&order=nombre.asc`,
    );
    return (rows || []).map(serializarRepuesto);
  },

  async createRepuesto(tallerId: string, body: Record<string, unknown>): Promise<Repuesto> {
    const payload = {
      taller_id: tallerId,
      nombre: body.name,
      descripcion: body.description || null,
      numero_parte: body.part_number || null,
      codigo_interno: body.internal_code || null,
      categoria: body.category || 'other',
      marca: body.brand || null,
      stock_cantidad: Number(body.stock_quantity || 0),
      stock_minimo: Number(body.min_stock_level || 5),
      stock_maximo: Number(body.max_stock_level || 50),
      costo_unitario: body.unit_cost || 0,
      precio_venta: body.sale_price || 0,
      ubicacion: body.location || null,
      proveedor: body.supplier || null,
      activo: true,
    };
    const rows = await rest<Record<string, unknown>[]>('repuestos_taller', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return serializarRepuesto(Array.isArray(rows) ? rows[0] : rows);
  },

  async updateRepuesto(id: string, body: Record<string, unknown>): Promise<Repuesto> {
    const map: Record<string, string> = {
      name: 'nombre',
      description: 'descripcion',
      part_number: 'numero_parte',
      internal_code: 'codigo_interno',
      category: 'categoria',
      brand: 'marca',
      stock_quantity: 'stock_cantidad',
      min_stock_level: 'stock_minimo',
      max_stock_level: 'stock_maximo',
      unit_cost: 'costo_unitario',
      sale_price: 'precio_venta',
      location: 'ubicacion',
      supplier: 'proveedor',
      is_active: 'activo',
    };
    const payload: Record<string, unknown> = { updated_at: new Date().toISOString() };
    for (const [k, db] of Object.entries(map)) {
      if (k in body && body[k] !== undefined) payload[db] = body[k];
    }
    const tallerId = body.taller_id;
    const q = tallerId
      ? `repuestos_taller?id=eq.${id}&taller_id=eq.${tallerId}`
      : `repuestos_taller?id=eq.${id}`;
    const rows = await rest<Record<string, unknown>[]>(q, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return serializarRepuesto(Array.isArray(rows) ? rows[0] : rows);
  },
};

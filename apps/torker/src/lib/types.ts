export interface Taller {
  id: string;
  nombre: string;
  direccion?: string;
  ciudad?: string;
}

export interface Cliente {
  id: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  email?: string | null;
  document_type: string;
  document_number?: string | null;
  address?: string | null;
  city?: string | null;
  department?: string | null;
  is_active: boolean;
  total_visits: number;
  total_spent: number;
  notes?: string | null;
  full_address?: string | null;
  get_document_type_display: string;
  motero_id?: string | null;
}

export interface TipoServicio {
  id: string;
  name: string;
  description?: string | null;
  category: string;
  estimated_duration: number;
  base_price: number;
  color: string;
  is_active: boolean;
}

export interface Cita {
  id: string;
  customer: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  status: string;
  priority: string;
  estimated_cost: number;
  custom_service_description?: string | null;
  customer_full_name: string;
  assigned_mechanic_name?: string | null;
  service_type?: TipoServicio | null;
}

export interface Moto {
  id: string;
  placa: string;
  codigo_parche?: string | null;
  marca: string;
  modelo: string;
  anio?: number | null;
  color?: string | null;
  kilometraje_actual?: number;
  dueno_id?: string;
  dueno_nombre?: string | null;
  dueno_telefono?: string | null;
  dueno_ciudad?: string | null;
  dueno_email?: string | null;
  es_cliente?: boolean;
  cliente_id?: string | null;
  cliente_nombre?: string | null;
  cliente_apellido?: string | null;
  cliente_telefono?: string | null;
  cliente_email?: string | null;
  cliente_direccion?: string | null;
  cliente_ciudad?: string | null;
}

export interface RegistroHistorialMoto {
  id: string;
  moto_id: string;
  tipo_servicio: string;
  descripcion?: string | null;
  kilometraje?: number | null;
  costo?: number | null;
  fecha: string;
  origen: 'taller' | 'propietario';
  taller_id?: string | null;
  taller_nombre?: string | null;
  mecanico_nombre?: string | null;
  verificado?: boolean;
  placa?: string | null;
  marca?: string | null;
  modelo?: string | null;
  fotos_urls?: string[];
}

export interface OrdenItem {
  id: string;
  orden_id: string;
  repuesto_id?: string | null;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
}

export interface Orden {
  id: string;
  estado: string;
  servicios?: { nombre: string }[];
  created_at: string;
  mecanico_nombre?: string | null;
  costo_total?: number | null;
  moto_id?: string | null;
  notas?: string | null;
  items?: OrdenItem[];
}

export interface Repuesto {
  id: string;
  name: string;
  description?: string | null;
  part_number?: string | null;
  internal_code?: string | null;
  category: string;
  category_display: string;
  brand?: string | null;
  stock_quantity: number;
  min_stock_level: number;
  max_stock_level: number;
  unit_cost: number;
  sale_price: number;
  location?: string | null;
  supplier?: string | null;
  is_active: boolean;
  stock_status: 'low' | 'normal' | 'over';
  inventory_value: number;
}

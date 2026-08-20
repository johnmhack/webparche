export const API_BASE =
  import.meta.env.DEV
    ? '/api'
    : `${window.location.origin}/api`;

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
}

export interface TipoServicio {
  id: string;
  name: string;
  estimated_duration: number;
  color: string;
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
  marca: string;
  modelo: string;
  kilometraje_actual?: number;
}

export interface Orden {
  id: string;
  estado: string;
  servicios?: { nombre: string }[];
  created_at: string;
}

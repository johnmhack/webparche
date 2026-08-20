-- Torker: clientes y citas (ejecutar en Supabase → SQL Editor)
-- Requiere tabla talleres existente

CREATE TABLE IF NOT EXISTS clientes_taller (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  taller_id UUID NOT NULL REFERENCES talleres(id) ON DELETE CASCADE,
  motero_id UUID,
  nombre TEXT NOT NULL,
  apellido TEXT NOT NULL DEFAULT '',
  telefono TEXT,
  email TEXT,
  tipo_documento TEXT NOT NULL DEFAULT 'cc',
  numero_documento TEXT,
  direccion TEXT,
  ciudad TEXT,
  departamento TEXT,
  total_visitas INT NOT NULL DEFAULT 0,
  total_gastado NUMERIC(12,2) NOT NULL DEFAULT 0,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  notas TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clientes_taller_taller ON clientes_taller(taller_id);

CREATE TABLE IF NOT EXISTS tipos_servicio_taller (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  taller_id UUID NOT NULL REFERENCES talleres(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  categoria TEXT NOT NULL DEFAULT 'maintenance',
  duracion_estimada_min INT NOT NULL DEFAULT 60,
  precio_base NUMERIC(10,2) NOT NULL DEFAULT 0,
  color TEXT NOT NULL DEFAULT '#3b82f6',
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (taller_id, nombre)
);

CREATE TABLE IF NOT EXISTS citas_taller (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  taller_id UUID NOT NULL REFERENCES talleres(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes_taller(id) ON DELETE CASCADE,
  moto_id UUID REFERENCES motos(id),
  tipo_servicio_id UUID REFERENCES tipos_servicio_taller(id),
  descripcion_servicio_custom TEXT,
  fecha_cita DATE NOT NULL,
  hora_inicio TIME NOT NULL,
  hora_fin TIME NOT NULL,
  duracion_minutos INT NOT NULL DEFAULT 60,
  estado TEXT NOT NULL DEFAULT 'scheduled',
  prioridad TEXT NOT NULL DEFAULT 'normal',
  costo_estimado NUMERIC(10,2) NOT NULL DEFAULT 0,
  mecanico_nombre TEXT,
  telefono_contacto TEXT,
  email_contacto TEXT,
  notas_internas TEXT,
  notas_cliente TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_citas_taller_fecha ON citas_taller(taller_id, fecha_cita);

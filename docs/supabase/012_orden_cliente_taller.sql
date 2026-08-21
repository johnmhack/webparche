-- Órdenes también para clientes del taller (sin moto Parche).
-- Ejecutar en Supabase SQL Editor.

ALTER TABLE ordenes_trabajo
  ADD COLUMN IF NOT EXISTS cliente_id UUID REFERENCES clientes_taller(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_ordenes_cliente
  ON ordenes_trabajo(cliente_id)
  WHERE cliente_id IS NOT NULL;

COMMENT ON COLUMN ordenes_trabajo.cliente_id IS
  'Cliente CRM del taller (puede no tener cuenta Parche). moto_id/motero_id opcionales.';

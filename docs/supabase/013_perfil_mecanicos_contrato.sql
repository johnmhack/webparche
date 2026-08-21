-- Perfil del taller, mecánicos y aceptación de contrato Parche.
-- Ejecutar en Supabase SQL Editor.

-- Perfil establecimiento
ALTER TABLE talleres
  ADD COLUMN IF NOT EXISTS telefono text,
  ADD COLUMN IF NOT EXISTS email text,
  ADD COLUMN IF NOT EXISTS nit text,
  ADD COLUMN IF NOT EXISTS horario text,
  ADD COLUMN IF NOT EXISTS descripcion text,
  ADD COLUMN IF NOT EXISTS contrato_aceptado_at timestamptz,
  ADD COLUMN IF NOT EXISTS contrato_version text;

COMMENT ON COLUMN talleres.contrato_aceptado_at IS
  'Fecha en que el taller confirmó haber leído el contrato de servicio Parche/Torker.';
COMMENT ON COLUMN talleres.contrato_version IS
  'Versión del contrato aceptado (ej. 2026-03).';

-- Mecánicos del taller (asignables a órdenes)
CREATE TABLE IF NOT EXISTS mecanicos_taller (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  taller_id UUID NOT NULL REFERENCES talleres(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  telefono TEXT,
  especialidad TEXT,
  activo BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mecanicos_taller
  ON mecanicos_taller(taller_id)
  WHERE activo = true;

ALTER TABLE mecanicos_taller ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_mecanicos_all ON mecanicos_taller;
CREATE POLICY torker_mecanicos_all ON mecanicos_taller
  FOR ALL TO authenticated
  USING (taller_id IN (SELECT public.mis_taller_ids()))
  WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));

GRANT SELECT, INSERT, UPDATE, DELETE ON mecanicos_taller TO authenticated;

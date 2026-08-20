-- Fix RLS: propietario_id a veces es text y auth.uid() es uuid
-- Ejecutar en Supabase → SQL Editor

CREATE OR REPLACE FUNCTION public.mis_taller_ids()
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id
  FROM talleres
  WHERE propietario_id::text = auth.uid()::text;
$$;

DROP POLICY IF EXISTS torker_talleres_select ON talleres;
CREATE POLICY torker_talleres_select ON talleres
  FOR SELECT TO authenticated
  USING (propietario_id::text = auth.uid()::text);

DROP POLICY IF EXISTS torker_talleres_insert ON talleres;
CREATE POLICY torker_talleres_insert ON talleres
  FOR INSERT TO authenticated
  WITH CHECK (propietario_id::text = auth.uid()::text);

DROP POLICY IF EXISTS torker_talleres_update ON talleres;
CREATE POLICY torker_talleres_update ON talleres
  FOR UPDATE TO authenticated
  USING (propietario_id::text = auth.uid()::text)
  WITH CHECK (propietario_id::text = auth.uid()::text);

-- Prueba rápida (debe devolver filas si tu sesión es la del taller):
-- SELECT auth.uid(), (SELECT array_agg(id) FROM mis_taller_ids());
-- SELECT * FROM repuestos_taller;
-- SELECT * FROM ordenes_trabajo;

-- Código Parche por moto: el taller busca por placa O por este código (QR).
-- Ejecutar en Supabase SQL Editor.

ALTER TABLE motos
  ADD COLUMN IF NOT EXISTS codigo_parche TEXT;

-- Backfill motos existentes (8 hex chars en mayúsculas)
UPDATE motos
SET codigo_parche = upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 8))
WHERE codigo_parche IS NULL OR trim(codigo_parche) = '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_motos_codigo_parche
  ON motos (codigo_parche)
  WHERE codigo_parche IS NOT NULL AND codigo_parche <> '';

-- Búsqueda unificada: placa o código Parche
CREATE OR REPLACE FUNCTION public.buscar_moto_parche(p_query text)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT COALESCE(
    (
      SELECT json_build_object(
        'id', m.id,
        'dueno_id', m.dueno_id,
        'placa', m.placa,
        'codigo_parche', m.codigo_parche,
        'marca', m.marca,
        'modelo', m.modelo,
        'kilometraje_actual', m.kilometraje_actual,
        'activa', m.activa
      )
      FROM motos m
      WHERE m.activa = true
        AND (
          m.placa = upper(trim(p_query))
          OR upper(trim(m.codigo_parche)) = upper(trim(p_query))
        )
      LIMIT 1
    ),
    'null'::json
  );
$$;

REVOKE ALL ON FUNCTION public.buscar_moto_parche(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.buscar_moto_parche(text) TO authenticated;

-- Mantener compatibilidad con clientes que aún llaman por placa
CREATE OR REPLACE FUNCTION public.buscar_moto_por_placa(p_placa text)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT public.buscar_moto_parche(p_placa);
$$;

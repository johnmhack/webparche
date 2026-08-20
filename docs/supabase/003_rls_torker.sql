-- Permisos Torker: el taller (usuario autenticado) solo ve/edita su data.
-- Ejecutar en Supabase → SQL Editor
-- Necesario para que clientes/inventario funcionen desde Netlify (sin Django).

CREATE OR REPLACE FUNCTION public.mis_taller_ids()
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id FROM talleres WHERE propietario_id = auth.uid();
$$;

REVOKE ALL ON FUNCTION public.mis_taller_ids() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.mis_taller_ids() TO authenticated;

-- talleres
ALTER TABLE talleres ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_talleres_select ON talleres;
CREATE POLICY torker_talleres_select ON talleres
  FOR SELECT TO authenticated
  USING (propietario_id = auth.uid());

DROP POLICY IF EXISTS torker_talleres_insert ON talleres;
CREATE POLICY torker_talleres_insert ON talleres
  FOR INSERT TO authenticated
  WITH CHECK (propietario_id = auth.uid());

DROP POLICY IF EXISTS torker_talleres_update ON talleres;
CREATE POLICY torker_talleres_update ON talleres
  FOR UPDATE TO authenticated
  USING (propietario_id = auth.uid())
  WITH CHECK (propietario_id = auth.uid());

-- clientes_taller
ALTER TABLE clientes_taller ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_clientes_all ON clientes_taller;
CREATE POLICY torker_clientes_all ON clientes_taller
  FOR ALL TO authenticated
  USING (taller_id IN (SELECT public.mis_taller_ids()))
  WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));

-- tipos_servicio_taller
ALTER TABLE tipos_servicio_taller ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_tipos_all ON tipos_servicio_taller;
CREATE POLICY torker_tipos_all ON tipos_servicio_taller
  FOR ALL TO authenticated
  USING (taller_id IN (SELECT public.mis_taller_ids()))
  WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));

-- citas_taller
ALTER TABLE citas_taller ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_citas_all ON citas_taller;
CREATE POLICY torker_citas_all ON citas_taller
  FOR ALL TO authenticated
  USING (taller_id IN (SELECT public.mis_taller_ids()))
  WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));

-- repuestos_taller
ALTER TABLE repuestos_taller ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_repuestos_all ON repuestos_taller;
CREATE POLICY torker_repuestos_all ON repuestos_taller
  FOR ALL TO authenticated
  USING (taller_id IN (SELECT public.mis_taller_ids()))
  WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));

-- ordenes_trabajo (si la tabla existe)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ordenes_trabajo') THEN
    ALTER TABLE ordenes_trabajo ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS torker_ordenes_all ON ordenes_trabajo;
    CREATE POLICY torker_ordenes_all ON ordenes_trabajo
      FOR ALL TO authenticated
      USING (taller_id IN (SELECT public.mis_taller_ids()))
      WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));
  END IF;
END $$;

-- Buscar moto por placa (lectura limitada para talleres autenticados)
CREATE OR REPLACE FUNCTION public.buscar_moto_por_placa(p_placa text)
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
        'marca', m.marca,
        'modelo', m.modelo,
        'kilometraje_actual', m.kilometraje_actual,
        'activa', m.activa
      )
      FROM motos m
      WHERE m.placa = upper(trim(p_placa))
        AND m.activa = true
      LIMIT 1
    ),
    'null'::json
  );
$$;

REVOKE ALL ON FUNCTION public.buscar_moto_por_placa(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.buscar_moto_por_placa(text) TO authenticated;

-- Historial de la moto (si la tabla existe)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'historial_moto') THEN
    ALTER TABLE historial_moto ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS torker_historial_insert ON historial_moto;
    CREATE POLICY torker_historial_insert ON historial_moto
      FOR INSERT TO authenticated
      WITH CHECK (taller_id IN (SELECT public.mis_taller_ids()));
    DROP POLICY IF EXISTS torker_historial_select ON historial_moto;
    CREATE POLICY torker_historial_select ON historial_moto
      FOR SELECT TO authenticated
      USING (taller_id IN (SELECT public.mis_taller_ids()));
  END IF;
END $$;

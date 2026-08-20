-- Items de orden + cerrar descontando inventario
-- Ejecutar en Supabase → SQL Editor

CREATE TABLE IF NOT EXISTS orden_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  orden_id UUID NOT NULL REFERENCES ordenes_trabajo(id) ON DELETE CASCADE,
  repuesto_id UUID REFERENCES repuestos_taller(id) ON DELETE SET NULL,
  nombre TEXT NOT NULL,
  cantidad INT NOT NULL DEFAULT 1 CHECK (cantidad > 0),
  precio_unitario NUMERIC(10,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orden_items_orden ON orden_items(orden_id);

ALTER TABLE orden_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS torker_orden_items_all ON orden_items;
CREATE POLICY torker_orden_items_all ON orden_items
  FOR ALL TO authenticated
  USING (
    orden_id IN (
      SELECT o.id FROM ordenes_trabajo o
      WHERE o.taller_id IN (SELECT public.mis_taller_ids())
    )
  )
  WITH CHECK (
    orden_id IN (
      SELECT o.id FROM ordenes_trabajo o
      WHERE o.taller_id IN (SELECT public.mis_taller_ids())
    )
  );

CREATE OR REPLACE FUNCTION public.cerrar_orden_con_stock(
  p_orden_id uuid,
  p_costo numeric DEFAULT NULL,
  p_kilometraje int DEFAULT NULL,
  p_tipo_servicio text DEFAULT NULL,
  p_descripcion text DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_orden ordenes_trabajo%ROWTYPE;
  v_item RECORD;
  v_costo numeric;
  v_tipo text;
  v_hist json;
BEGIN
  SELECT * INTO v_orden FROM ordenes_trabajo WHERE id = p_orden_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Orden no encontrada';
  END IF;

  IF v_orden.taller_id NOT IN (SELECT public.mis_taller_ids()) THEN
    RAISE EXCEPTION 'Sin permiso sobre esta orden';
  END IF;

  IF v_orden.estado = 'completado' THEN
    RAISE EXCEPTION 'La orden ya está cerrada';
  END IF;

  FOR v_item IN
    SELECT * FROM orden_items WHERE orden_id = p_orden_id AND repuesto_id IS NOT NULL
  LOOP
    UPDATE repuestos_taller
    SET
      stock_cantidad = stock_cantidad - v_item.cantidad,
      updated_at = now()
    WHERE id = v_item.repuesto_id
      AND taller_id = v_orden.taller_id
      AND stock_cantidad >= v_item.cantidad;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'Stock insuficiente para: %', v_item.nombre;
    END IF;
  END LOOP;

  SELECT COALESCE(
    p_costo,
    (SELECT SUM(cantidad * precio_unitario) FROM orden_items WHERE orden_id = p_orden_id),
    v_orden.costo_total,
    0
  ) INTO v_costo;

  v_tipo := COALESCE(
    p_tipo_servicio,
    (v_orden.servicios->0->>'nombre'),
    'Servicio general'
  );

  IF v_orden.moto_id IS NOT NULL THEN
    INSERT INTO historial_moto (
      moto_id, taller_id, mecanico_nombre, tipo_servicio, descripcion,
      kilometraje, costo, fecha, verificado
    ) VALUES (
      v_orden.moto_id,
      v_orden.taller_id,
      v_orden.mecanico_nombre,
      v_tipo,
      COALESCE(p_descripcion, v_orden.notas),
      p_kilometraje,
      v_costo,
      CURRENT_DATE,
      true
    )
    RETURNING to_json(historial_moto.*) INTO v_hist;
  END IF;

  UPDATE ordenes_trabajo
  SET
    estado = 'completado',
    costo_total = v_costo,
    fecha_salida = now(),
    updated_at = now()
  WHERE id = p_orden_id;

  RETURN json_build_object(
    'orden', (SELECT to_json(o.*) FROM ordenes_trabajo o WHERE o.id = p_orden_id),
    'historial', v_hist
  );
END;
$$;

REVOKE ALL ON FUNCTION public.cerrar_orden_con_stock(uuid, numeric, int, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.cerrar_orden_con_stock(uuid, numeric, int, text, text) TO authenticated;

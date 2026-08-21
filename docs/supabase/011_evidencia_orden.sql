-- Evidencia al cerrar orden: descripción del mecánico + fotos.
-- Órdenes completadas quedan bloqueadas (solo soporte Parche puede corregir vía ticket / service role).
-- Ejecutar en Supabase SQL Editor.

-- 1) Columnas de evidencia
ALTER TABLE historial_moto
  ADD COLUMN IF NOT EXISTS notas_mecanico TEXT,
  ADD COLUMN IF NOT EXISTS fotos_urls TEXT[] NOT NULL DEFAULT '{}';

ALTER TABLE ordenes_trabajo
  ADD COLUMN IF NOT EXISTS notas_cierre TEXT,
  ADD COLUMN IF NOT EXISTS fotos_evidencia TEXT[] NOT NULL DEFAULT '{}';

-- 2) Bloquear edición de órdenes ya cerradas
CREATE OR REPLACE FUNCTION public.bloquea_edicion_orden_cerrada()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF OLD.estado = 'completado' THEN
    RAISE EXCEPTION
      'Orden cerrada: no se puede editar. Si hay un error, contacta soporte Parche.';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_bloquea_orden_cerrada ON ordenes_trabajo;
CREATE TRIGGER trg_bloquea_orden_cerrada
  BEFORE UPDATE ON ordenes_trabajo
  FOR EACH ROW
  EXECUTE PROCEDURE public.bloquea_edicion_orden_cerrada();

-- También bloquear agregar/quitar ítems si la orden ya cerró
CREATE OR REPLACE FUNCTION public.bloquea_items_orden_cerrada()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  v_estado text;
  v_orden_id uuid;
BEGIN
  v_orden_id := COALESCE(NEW.orden_id, OLD.orden_id);
  SELECT estado INTO v_estado FROM ordenes_trabajo WHERE id = v_orden_id;
  IF v_estado = 'completado' THEN
    RAISE EXCEPTION
      'Orden cerrada: no se pueden modificar ítems. Contacta soporte Parche.';
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_bloquea_items_orden_cerrada ON orden_items;
CREATE TRIGGER trg_bloquea_items_orden_cerrada
  BEFORE INSERT OR UPDATE OR DELETE ON orden_items
  FOR EACH ROW
  EXECUTE PROCEDURE public.bloquea_items_orden_cerrada();

-- 3) No permitir UPDATE de historial verificado por talleres (RLS sin policy UPDATE)
-- Si existiera alguna policy de update, la quitamos:
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'historial_moto') THEN
    DROP POLICY IF EXISTS torker_historial_update ON historial_moto;
    DROP POLICY IF EXISTS torker_historial_delete ON historial_moto;
  END IF;
END $$;

-- 4) Cerrar orden con evidencia (reemplaza la firma anterior)
DROP FUNCTION IF EXISTS public.cerrar_orden_con_stock(uuid, numeric, int, text, text);

CREATE OR REPLACE FUNCTION public.cerrar_orden_con_stock(
  p_orden_id uuid,
  p_costo numeric DEFAULT NULL,
  p_kilometraje int DEFAULT NULL,
  p_tipo_servicio text DEFAULT NULL,
  p_descripcion text DEFAULT NULL,
  p_fotos text[] DEFAULT NULL
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
  v_fotos text[];
  v_desc text;
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

  v_desc := NULLIF(trim(COALESCE(p_descripcion, v_orden.notas, '')), '');
  v_fotos := COALESCE(p_fotos, '{}'::text[]);

  IF v_orden.moto_id IS NOT NULL THEN
    INSERT INTO historial_moto (
      moto_id, taller_id, mecanico_nombre, tipo_servicio, descripcion,
      notas_mecanico, fotos_urls, kilometraje, costo, fecha, verificado
    ) VALUES (
      v_orden.moto_id,
      v_orden.taller_id,
      v_orden.mecanico_nombre,
      v_tipo,
      v_desc,
      v_desc,
      v_fotos,
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
    notas_cierre = v_desc,
    fotos_evidencia = v_fotos,
    fecha_salida = now(),
    updated_at = now()
  WHERE id = p_orden_id;

  RETURN json_build_object(
    'orden', (SELECT to_json(o.*) FROM ordenes_trabajo o WHERE o.id = p_orden_id),
    'historial', v_hist
  );
END;
$$;

REVOKE ALL ON FUNCTION public.cerrar_orden_con_stock(uuid, numeric, int, text, text, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.cerrar_orden_con_stock(uuid, numeric, int, text, text, text[]) TO authenticated;

-- 5) Actualizar RPCs de historial para devolver evidencia
CREATE OR REPLACE FUNCTION public.historial_moto_para_taller(p_moto_id uuid, p_taller_id uuid)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_dueno uuid;
  v_es_cliente boolean;
BEGIN
  IF p_taller_id NOT IN (SELECT public.mis_taller_ids()) THEN
    RAISE EXCEPTION 'Taller no autorizado';
  END IF;

  SELECT m.dueno_id INTO v_dueno
  FROM motos m
  WHERE m.id = p_moto_id AND m.activa = true;

  IF v_dueno IS NULL THEN
    RAISE EXCEPTION 'Moto no encontrada';
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM clientes_taller c
    WHERE c.taller_id = p_taller_id AND c.motero_id = v_dueno
      AND c.activo IS DISTINCT FROM false
  ) INTO v_es_cliente;

  IF NOT v_es_cliente THEN
    RAISE EXCEPTION 'El motero no es cliente de este taller';
  END IF;

  RETURN COALESCE(
    (
      SELECT json_agg(row_to_json(x))
      FROM (
        SELECT
          h.id::text AS id,
          h.moto_id::text AS moto_id,
          h.tipo_servicio,
          COALESCE(h.notas_mecanico, h.descripcion) AS descripcion,
          h.kilometraje,
          h.costo,
          h.fecha::text AS fecha,
          'taller'::text AS origen,
          h.taller_id::text AS taller_id,
          t.nombre AS taller_nombre,
          h.mecanico_nombre,
          COALESCE(h.verificado, true) AS verificado,
          COALESCE(h.fotos_urls, '{}'::text[]) AS fotos_urls
        FROM historial_moto h
        LEFT JOIN talleres t ON t.id = h.taller_id
        WHERE h.moto_id = p_moto_id

        UNION ALL

        SELECT
          hp.id::text,
          hp.moto_id::text,
          hp.tipo_servicio,
          hp.contenido,
          hp.kilometraje,
          hp.costo,
          hp.fecha::text,
          'propietario'::text,
          NULL::text,
          NULL::text,
          NULL::text,
          false,
          '{}'::text[]
        FROM historial_propietario hp
        WHERE hp.moto_id = p_moto_id
      ) x
    ),
    '[]'::json
  );
END;
$$;

CREATE OR REPLACE FUNCTION public.historial_motero_para_taller(p_motero_id uuid, p_taller_id uuid)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_es_cliente boolean;
BEGIN
  IF p_taller_id NOT IN (SELECT public.mis_taller_ids()) THEN
    RAISE EXCEPTION 'Taller no autorizado';
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM clientes_taller c
    WHERE c.taller_id = p_taller_id AND c.motero_id = p_motero_id
      AND c.activo IS DISTINCT FROM false
  ) INTO v_es_cliente;

  IF NOT v_es_cliente THEN
    RAISE EXCEPTION 'El motero no es cliente de este taller';
  END IF;

  RETURN COALESCE(
    (
      SELECT json_agg(row_to_json(x))
      FROM (
        SELECT
          h.id::text AS id,
          h.moto_id::text AS moto_id,
          m.placa,
          m.marca,
          m.modelo,
          h.tipo_servicio,
          COALESCE(h.notas_mecanico, h.descripcion) AS descripcion,
          h.kilometraje,
          h.costo,
          h.fecha::text AS fecha,
          'taller'::text AS origen,
          h.taller_id::text AS taller_id,
          t.nombre AS taller_nombre,
          h.mecanico_nombre,
          COALESCE(h.verificado, true) AS verificado,
          COALESCE(h.fotos_urls, '{}'::text[]) AS fotos_urls
        FROM historial_moto h
        JOIN motos m ON m.id = h.moto_id
        LEFT JOIN talleres t ON t.id = h.taller_id
        WHERE m.dueno_id = p_motero_id

        UNION ALL

        SELECT
          hp.id::text,
          hp.moto_id::text,
          m2.placa,
          m2.marca,
          m2.modelo,
          hp.tipo_servicio,
          hp.contenido,
          hp.kilometraje,
          hp.costo,
          hp.fecha::text,
          'propietario'::text,
          NULL::text,
          NULL::text,
          NULL::text,
          false,
          '{}'::text[]
        FROM historial_propietario hp
        JOIN motos m2 ON m2.id = hp.moto_id
        WHERE m2.dueno_id = p_motero_id
      ) x
    ),
    '[]'::json
  );
END;
$$;

-- 6) Bucket de evidencias (Storage)
INSERT INTO storage.buckets (id, name, public)
VALUES ('evidencias-taller', 'evidencias-taller', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS evidencias_upload ON storage.objects;
CREATE POLICY evidencias_upload ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'evidencias-taller');

DROP POLICY IF EXISTS evidencias_read ON storage.objects;
CREATE POLICY evidencias_read ON storage.objects
  FOR SELECT TO authenticated
  USING (bucket_id = 'evidencias-taller');

DROP POLICY IF EXISTS evidencias_public_read ON storage.objects;
CREATE POLICY evidencias_public_read ON storage.objects
  FOR SELECT TO public
  USING (bucket_id = 'evidencias-taller');

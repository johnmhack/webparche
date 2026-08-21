-- Historial de todas las motos de un motero (cliente vinculado).
-- Ejecutar en Supabase SQL Editor (después de 009).

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
    SELECT 1
    FROM clientes_taller c
    WHERE c.taller_id = p_taller_id
      AND c.motero_id = p_motero_id
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
          h.descripcion,
          h.kilometraje,
          h.costo,
          h.fecha::text AS fecha,
          'taller'::text AS origen,
          h.taller_id::text AS taller_id,
          t.nombre AS taller_nombre,
          h.mecanico_nombre,
          COALESCE(h.verificado, true) AS verificado
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
          hp.contenido AS descripcion,
          hp.kilometraje,
          hp.costo,
          hp.fecha::text,
          'propietario'::text,
          NULL::text,
          NULL::text,
          NULL::text,
          false
        FROM historial_propietario hp
        JOIN motos m2 ON m2.id = hp.moto_id
        WHERE m2.dueno_id = p_motero_id
      ) x
    ),
    '[]'::json
  );
END;
$$;

REVOKE ALL ON FUNCTION public.historial_motero_para_taller(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.historial_motero_para_taller(uuid, uuid) TO authenticated;

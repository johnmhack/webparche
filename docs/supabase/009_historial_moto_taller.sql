-- Historial completo de una moto para el taller, solo si el dueño ya es cliente.
-- Incluye servicios verificados (cualquier taller) + registros del propietario.
-- Ejecutar en Supabase SQL Editor.

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
  -- El taller debe ser del usuario autenticado
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
    SELECT 1
    FROM clientes_taller c
    WHERE c.taller_id = p_taller_id
      AND c.motero_id = v_dueno
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
        LEFT JOIN talleres t ON t.id = h.taller_id
        WHERE h.moto_id = p_moto_id

        UNION ALL

        SELECT
          hp.id::text,
          hp.moto_id::text,
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
        WHERE hp.moto_id = p_moto_id
      ) x
    ),
    '[]'::json
  );
END;
$$;

REVOKE ALL ON FUNCTION public.historial_moto_para_taller(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.historial_moto_para_taller(uuid, uuid) TO authenticated;

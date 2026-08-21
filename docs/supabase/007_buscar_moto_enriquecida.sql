-- Enriquecer búsqueda de moto: datos del motero + si ya es cliente del taller.
-- Ejecutar en Supabase SQL Editor (después de 006).

CREATE OR REPLACE FUNCTION public.buscar_moto_parche(p_query text, p_taller_id uuid DEFAULT NULL)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, auth
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
        'anio', m.anio,
        'color', m.color,
        'kilometraje_actual', m.kilometraje_actual,
        'activa', m.activa,
        'dueno_nombre', p.nombre,
        'dueno_telefono', p.telefono,
        'dueno_ciudad', p.ciudad,
        'dueno_email', u.email,
        'es_cliente', (ct.id IS NOT NULL),
        'cliente_id', ct.id,
        'cliente_nombre', ct.nombre,
        'cliente_apellido', ct.apellido,
        'cliente_telefono', ct.telefono,
        'cliente_email', ct.email,
        'cliente_direccion', ct.direccion,
        'cliente_ciudad', ct.ciudad
      )
      FROM motos m
      LEFT JOIN perfiles p ON p.id = m.dueno_id
      LEFT JOIN auth.users u ON u.id = m.dueno_id
      LEFT JOIN LATERAL (
        SELECT c.*
        FROM clientes_taller c
        WHERE p_taller_id IS NOT NULL
          AND c.taller_id = p_taller_id
          AND c.motero_id = m.dueno_id
        ORDER BY c.created_at DESC
        LIMIT 1
      ) ct ON true
      WHERE m.activa = true
        AND (
          m.placa = upper(trim(p_query))
          OR upper(trim(COALESCE(m.codigo_parche, ''))) = upper(trim(p_query))
        )
      LIMIT 1
    ),
    'null'::json
  );
$$;

REVOKE ALL ON FUNCTION public.buscar_moto_parche(text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.buscar_moto_parche(text, uuid) TO authenticated;

-- Compat: llamada con un solo argumento (placa/código)
CREATE OR REPLACE FUNCTION public.buscar_moto_parche(p_query text)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, auth
AS $$
  SELECT public.buscar_moto_parche(p_query, NULL::uuid);
$$;

REVOKE ALL ON FUNCTION public.buscar_moto_parche(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.buscar_moto_parche(text) TO authenticated;

CREATE OR REPLACE FUNCTION public.buscar_moto_por_placa(p_placa text)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, auth
AS $$
  SELECT public.buscar_moto_parche(p_placa, NULL::uuid);
$$;

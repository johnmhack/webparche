CREATE TABLE IF NOT EXISTS repuestos_taller (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  taller_id UUID NOT NULL REFERENCES talleres(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  numero_parte TEXT,
  codigo_interno TEXT,
  categoria TEXT NOT NULL DEFAULT 'other',
  marca TEXT,
  stock_cantidad INT NOT NULL DEFAULT 0,
  stock_minimo INT NOT NULL DEFAULT 5,
  stock_maximo INT NOT NULL DEFAULT 50,
  costo_unitario NUMERIC(10,2) NOT NULL DEFAULT 0,
  precio_venta NUMERIC(10,2) NOT NULL DEFAULT 0,
  ubicacion TEXT,
  proveedor TEXT,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_repuestos_taller ON repuestos_taller(taller_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_repuestos_codigo_interno
  ON repuestos_taller(taller_id, codigo_interno)
  WHERE codigo_interno IS NOT NULL AND codigo_interno <> '';

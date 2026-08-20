from __future__ import annotations

from datetime import datetime, timezone

from .client import get_supabase
from .services import SupabaseError, _first_row, _error, obtener_taller_por_propietario

CATEGORY_LABELS = {
    'motor': 'Motor',
    'transmision': 'Transmisión',
    'frenos': 'Frenos',
    'suspension': 'Suspensión',
    'electrico': 'Sistema Eléctrico',
    'carroceria': 'Carrocería',
    'accesorios': 'Accesorios',
    'lubricantes': 'Lubricantes',
    'filtros': 'Filtros',
    'neumaticos': 'Neumáticos',
    'other': 'Otro',
}


def _verificar_taller(taller_id: str, propietario_id: str) -> dict:
    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != taller_id:
        raise SupabaseError('No tienes permiso sobre este taller')
    return taller


def _serializar_repuesto(row: dict) -> dict:
    stock = int(row.get('stock_cantidad') or 0)
    min_stock = int(row.get('stock_minimo') or 5)
    max_stock = int(row.get('stock_maximo') or 50)
    categoria = row.get('categoria') or 'other'
    costo = float(row.get('costo_unitario') or 0)
    precio = float(row.get('precio_venta') or 0)

    if stock <= min_stock:
        stock_status = 'low'
    elif stock >= max_stock:
        stock_status = 'over'
    else:
        stock_status = 'normal'

    return {
        'id': row['id'],
        'name': row.get('nombre', ''),
        'description': row.get('descripcion'),
        'part_number': row.get('numero_parte'),
        'internal_code': row.get('codigo_interno'),
        'category': categoria,
        'category_display': CATEGORY_LABELS.get(categoria, categoria),
        'brand': row.get('marca'),
        'stock_quantity': stock,
        'min_stock_level': min_stock,
        'max_stock_level': max_stock,
        'unit_cost': costo,
        'sale_price': precio,
        'location': row.get('ubicacion'),
        'supplier': row.get('proveedor'),
        'is_active': row.get('activo', True),
        'stock_status': stock_status,
        'inventory_value': stock * costo,
    }


def listar_repuestos(taller_id: str, propietario_id: str) -> list[dict]:
    _verificar_taller(taller_id, propietario_id)
    sb = get_supabase()
    resp = (
        sb.table('repuestos_taller')
        .select('*')
        .eq('taller_id', taller_id)
        .eq('activo', True)
        .order('nombre')
        .execute()
    )
    _error(resp)
    return [_serializar_repuesto(r) for r in (resp.data or [])]


def crear_repuesto(taller_id: str, propietario_id: str, datos: dict) -> dict:
    _verificar_taller(taller_id, propietario_id)
    payload = {
        'taller_id': taller_id,
        'nombre': datos['name'],
        'descripcion': datos.get('description'),
        'numero_parte': datos.get('part_number'),
        'codigo_interno': datos.get('internal_code'),
        'categoria': datos.get('category') or 'other',
        'marca': datos.get('brand'),
        'stock_cantidad': int(datos.get('stock_quantity') or 0),
        'stock_minimo': int(datos.get('min_stock_level') or 5),
        'stock_maximo': int(datos.get('max_stock_level') or 50),
        'costo_unitario': datos.get('unit_cost') or 0,
        'precio_venta': datos.get('sale_price') or 0,
        'ubicacion': datos.get('location'),
        'proveedor': datos.get('supplier'),
        'activo': True,
    }
    sb = get_supabase()
    resp = sb.table('repuestos_taller').insert(payload).execute()
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('No se pudo crear el repuesto')
    return _serializar_repuesto(row)


def actualizar_repuesto(repuesto_id: str, taller_id: str, propietario_id: str, datos: dict) -> dict:
    _verificar_taller(taller_id, propietario_id)
    permitidos = {
        'name': 'nombre',
        'description': 'descripcion',
        'part_number': 'numero_parte',
        'internal_code': 'codigo_interno',
        'category': 'categoria',
        'brand': 'marca',
        'stock_quantity': 'stock_cantidad',
        'min_stock_level': 'stock_minimo',
        'max_stock_level': 'stock_maximo',
        'unit_cost': 'costo_unitario',
        'sale_price': 'precio_venta',
        'location': 'ubicacion',
        'supplier': 'proveedor',
        'is_active': 'activo',
    }
    payload = {db: datos[k] for k, db in permitidos.items() if k in datos and datos[k] is not None}
    payload['updated_at'] = datetime.now(timezone.utc).isoformat()
    sb = get_supabase()
    resp = (
        sb.table('repuestos_taller')
        .update(payload)
        .eq('id', repuesto_id)
        .eq('taller_id', taller_id)
        .execute()
    )
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('Repuesto no encontrado')
    return _serializar_repuesto(row)

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from .client import get_supabase


class SupabaseError(Exception):
    def __init__(self, mensaje: str, detalle: Any = None):
        super().__init__(mensaje)
        self.detalle = detalle


def _error(resp) -> None:
    if getattr(resp, 'data', None) is None and getattr(resp, 'error', None):
        raise SupabaseError('Error en Supabase', resp.error)


def _first_row(resp) -> dict | None:
    data = resp.data
    if not data:
        return None
    if isinstance(data, list):
        return data[0]
    return data


def crear_taller(propietario_id: str, datos: dict) -> dict:
    sb = get_supabase()
    payload = {
        'propietario_id': propietario_id,
        'nombre': datos['nombre'],
        'direccion': datos.get('direccion') or 'Por definir',
        'descripcion': datos.get('descripcion'),
        'ciudad': datos.get('ciudad'),
        'telefono': datos.get('telefono'),
        'whatsapp': datos.get('whatsapp'),
        'email': datos.get('email'),
        'latitud': datos.get('latitud'),
        'longitud': datos.get('longitud'),
        'categorias': datos.get('categorias') or ['mecánica'],
        'plan': datos.get('plan') or 'basico',
        'activo': True,
        'verificado': False,
    }
    resp = sb.table('talleres').insert(payload).execute()
    _error(resp)
    taller = _first_row(resp)
    if not taller:
        raise SupabaseError('No se pudo crear el taller')
    return taller


def obtener_taller_por_propietario(propietario_id: str) -> dict | None:
    sb = get_supabase()
    resp = (
        sb.table('talleres')
        .select('*')
        .eq('propietario_id', propietario_id)
        .limit(1)
        .execute()
    )
    _error(resp)
    if not resp.data:
        return None
    return resp.data[0]


def actualizar_taller(taller_id: str, propietario_id: str, datos: dict) -> dict:
    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != taller_id:
        raise SupabaseError('No tienes permiso sobre este taller')

    permitidos = {
        'nombre', 'descripcion', 'direccion', 'ciudad', 'telefono', 'whatsapp',
        'email', 'latitud', 'longitud', 'categorias', 'foto_url', 'activo',
    }
    payload = {k: v for k, v in datos.items() if k in permitidos and v is not None}
    payload['updated_at'] = datetime.now(timezone.utc).isoformat()

    sb = get_supabase()
    resp = sb.table('talleres').update(payload).eq('id', taller_id).execute()
    _error(resp)
    taller = _first_row(resp)
    if not taller:
        raise SupabaseError('No se pudo actualizar el taller')
    return taller


def buscar_moto_por_placa(placa: str) -> dict | None:
    sb = get_supabase()
    placa_limpia = placa.strip().upper()
    resp = (
        sb.table('motos')
        .select('id, dueno_id, placa, marca, modelo, anio, kilometraje_actual, activa')
        .eq('placa', placa_limpia)
        .eq('activa', True)
        .limit(1)
        .execute()
    )
    _error(resp)
    if not resp.data:
        return None
    return resp.data[0]


def crear_orden_trabajo(taller_id: str, propietario_id: str, datos: dict) -> dict:
    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != taller_id:
        raise SupabaseError('No tienes permiso sobre este taller')

    moto_id = datos.get('moto_id')
    motero_id = datos.get('motero_id')

    if not moto_id and datos.get('placa'):
        moto = buscar_moto_por_placa(datos['placa'])
        if not moto:
            raise SupabaseError(f'No hay moto activa con placa {datos["placa"]}')
        moto_id = moto['id']
        motero_id = moto.get('dueno_id')

    if not moto_id:
        raise SupabaseError('Indica moto_id o placa de la moto')

    payload = {
        'taller_id': taller_id,
        'moto_id': moto_id,
        'motero_id': motero_id,
        'mecanico_nombre': datos.get('mecanico_nombre'),
        'servicios': datos.get('servicios') or [],
        'estado': datos.get('estado') or 'pendiente',
        'costo_total': datos.get('costo_total'),
        'notas': datos.get('notas'),
        'fecha_entrada': datos.get('fecha_entrada') or datetime.now(timezone.utc).isoformat(),
    }

    sb = get_supabase()
    resp = sb.table('ordenes_trabajo').insert(payload).execute()
    _error(resp)
    orden = _first_row(resp)
    if not orden:
        raise SupabaseError('No se pudo crear la orden')
    return orden


def listar_ordenes_taller(taller_id: str, propietario_id: str) -> list[dict]:
    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != taller_id:
        raise SupabaseError('No tienes permiso sobre este taller')

    sb = get_supabase()
    resp = (
        sb.table('ordenes_trabajo')
        .select('*')
        .eq('taller_id', taller_id)
        .order('created_at', desc=True)
        .execute()
    )
    _error(resp)
    return resp.data or []


def cerrar_orden_y_registrar_historial(
    orden_id: str,
    propietario_id: str,
    datos: dict,
) -> dict:
    sb = get_supabase()
    orden_resp = sb.table('ordenes_trabajo').select('*').eq('id', orden_id).single().execute()
    _error(orden_resp)
    orden = orden_resp.data
    if not orden:
        raise SupabaseError('Orden no encontrada')

    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != orden['taller_id']:
        raise SupabaseError('No tienes permiso sobre esta orden')

    if not orden.get('moto_id'):
        raise SupabaseError('La orden no tiene moto vinculada')

    tipo_servicio = datos.get('tipo_servicio')
    if not tipo_servicio:
        servicios = orden.get('servicios') or []
        tipo_servicio = servicios[0].get('nombre') if servicios else 'Servicio general'

    fecha = datos.get('fecha') or date.today().isoformat()
    costo = datos.get('costo_total', orden.get('costo_total'))

    historial_payload = {
        'moto_id': orden['moto_id'],
        'taller_id': orden['taller_id'],
        'mecanico_nombre': datos.get('mecanico_nombre') or orden.get('mecanico_nombre'),
        'tipo_servicio': tipo_servicio,
        'descripcion': datos.get('descripcion') or orden.get('notas'),
        'kilometraje': datos.get('kilometraje'),
        'costo': costo,
        'fecha': fecha,
        'verificado': True,
    }

    hist_resp = sb.table('historial_moto').insert(historial_payload).execute()
    _error(hist_resp)
    historial = _first_row(hist_resp)
    if not historial:
        raise SupabaseError('No se pudo registrar el historial')

    orden_resp = (
        sb.table('ordenes_trabajo')
        .update({
            'estado': 'completado',
            'fecha_salida': datetime.now(timezone.utc).isoformat(),
            'costo_total': costo,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })
        .eq('id', orden_id)
        .execute()
    )
    _error(orden_resp)
    orden_actualizada = _first_row(orden_resp)
    if not orden_actualizada:
        raise SupabaseError('No se pudo cerrar la orden')

    return {
        'orden': orden_actualizada,
        'historial_moto': historial,
    }

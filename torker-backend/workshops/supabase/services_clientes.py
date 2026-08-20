from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .client import get_supabase
from .services import SupabaseError, _first_row, _error, obtener_taller_por_propietario

DOC_LABELS = {
    'cc': 'Cédula de Ciudadanía',
    'ce': 'Cédula de Extranjería',
    'nit': 'NIT',
    'ti': 'Tarjeta de Identidad',
    'pasaporte': 'Pasaporte',
    'other': 'Otro',
}


def _verificar_taller(taller_id: str, propietario_id: str) -> dict:
    taller = obtener_taller_por_propietario(propietario_id)
    if not taller or taller['id'] != taller_id:
        raise SupabaseError('No tienes permiso sobre este taller')
    return taller


def _serializar_cliente(row: dict) -> dict:
    parts = [row.get('direccion'), row.get('ciudad'), row.get('departamento')]
    full_address = ', '.join(p for p in parts if p) or None
    tipo = row.get('tipo_documento') or 'cc'
    return {
        'id': row['id'],
        'first_name': row.get('nombre', ''),
        'last_name': row.get('apellido', ''),
        'phone': row.get('telefono'),
        'email': row.get('email'),
        'document_type': tipo,
        'document_number': row.get('numero_documento'),
        'address': row.get('direccion'),
        'city': row.get('ciudad'),
        'department': row.get('departamento'),
        'is_active': row.get('activo', True),
        'total_visits': row.get('total_visitas') or 0,
        'total_spent': float(row.get('total_gastado') or 0),
        'notes': row.get('notas'),
        'full_address': full_address,
        'get_document_type_display': DOC_LABELS.get(tipo, tipo),
    }


def listar_clientes(taller_id: str, propietario_id: str) -> list[dict]:
    _verificar_taller(taller_id, propietario_id)
    sb = get_supabase()
    resp = (
        sb.table('clientes_taller')
        .select('*')
        .eq('taller_id', taller_id)
        .order('nombre')
        .execute()
    )
    _error(resp)
    return [_serializar_cliente(r) for r in (resp.data or [])]


def crear_cliente(taller_id: str, propietario_id: str, datos: dict) -> dict:
    _verificar_taller(taller_id, propietario_id)
    payload = {
        'taller_id': taller_id,
        'nombre': datos['first_name'],
        'apellido': datos.get('last_name') or '',
        'telefono': datos.get('phone'),
        'email': datos.get('email'),
        'tipo_documento': datos.get('document_type') or 'cc',
        'numero_documento': datos.get('document_number'),
        'direccion': datos.get('address'),
        'ciudad': datos.get('city'),
        'departamento': datos.get('department'),
        'notas': datos.get('notes'),
        'activo': True,
    }
    sb = get_supabase()
    resp = sb.table('clientes_taller').insert(payload).execute()
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('No se pudo crear el cliente')
    return _serializar_cliente(row)


def actualizar_cliente(cliente_id: str, taller_id: str, propietario_id: str, datos: dict) -> dict:
    _verificar_taller(taller_id, propietario_id)
    permitidos = {
        'first_name': 'nombre',
        'last_name': 'apellido',
        'phone': 'telefono',
        'email': 'email',
        'document_type': 'tipo_documento',
        'document_number': 'numero_documento',
        'address': 'direccion',
        'city': 'ciudad',
        'department': 'departamento',
        'notes': 'notas',
        'is_active': 'activo',
    }
    payload = {db: datos[k] for k, db in permitidos.items() if k in datos and datos[k] is not None}
    payload['updated_at'] = datetime.now(timezone.utc).isoformat()
    sb = get_supabase()
    resp = sb.table('clientes_taller').update(payload).eq('id', cliente_id).eq('taller_id', taller_id).execute()
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('Cliente no encontrado')
    return _serializar_cliente(row)


def _calcular_hora_fin(hora_inicio: str, duracion_min: int) -> str:
    fmt = '%H:%M:%S' if len(hora_inicio) > 5 else '%H:%M'
    t = datetime.strptime(hora_inicio[:8], fmt)
    fin = t + timedelta(minutes=duracion_min)
    return fin.strftime('%H:%M:%S')


def _serializar_tipo_servicio(row: dict) -> dict:
    return {
        'id': row['id'],
        'name': row['nombre'],
        'description': row.get('descripcion'),
        'category': row.get('categoria'),
        'estimated_duration': row.get('duracion_estimada_min') or 60,
        'base_price': float(row.get('precio_base') or 0),
        'color': row.get('color') or '#3b82f6',
        'is_active': row.get('activo', True),
    }


def listar_tipos_servicio(taller_id: str, propietario_id: str) -> list[dict]:
    _verificar_taller(taller_id, propietario_id)
    sb = get_supabase()
    resp = (
        sb.table('tipos_servicio_taller')
        .select('*')
        .eq('taller_id', taller_id)
        .eq('activo', True)
        .order('nombre')
        .execute()
    )
    _error(resp)
    return [_serializar_tipo_servicio(r) for r in (resp.data or [])]


def _cargar_clientes_map(taller_id: str) -> dict[str, dict]:
    sb = get_supabase()
    resp = sb.table('clientes_taller').select('*').eq('taller_id', taller_id).execute()
    _error(resp)
    return {r['id']: r for r in (resp.data or [])}


def _cargar_tipos_map(taller_id: str) -> dict[str, dict]:
    sb = get_supabase()
    resp = sb.table('tipos_servicio_taller').select('*').eq('taller_id', taller_id).execute()
    _error(resp)
    return {r['id']: r for r in (resp.data or [])}


def _serializar_cita(row: dict, clientes: dict[str, dict], tipos: dict[str, dict]) -> dict:
    cliente = clientes.get(row['cliente_id'], {})
    tipo = tipos.get(row.get('tipo_servicio_id') or '', {})
    nombre = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}".strip()
    hi = str(row.get('hora_inicio', '09:00'))[:5]
    hf = str(row.get('hora_fin', '10:00'))[:5]
    if len(hi) == 5:
        hi = hi + ':00'
    if len(hf) == 5:
        hf = hf + ':00'
    svc = _serializar_tipo_servicio(tipo) if tipo else None
    return {
        'id': row['id'],
        'customer': row['cliente_id'],
        'appointment_date': row['fecha_cita'],
        'start_time': hi,
        'end_time': hf,
        'duration_minutes': row.get('duracion_minutos') or 60,
        'status': row.get('estado') or 'scheduled',
        'priority': row.get('prioridad') or 'normal',
        'estimated_cost': float(row.get('costo_estimado') or 0),
        'custom_service_description': row.get('descripcion_servicio_custom'),
        'customer_full_name': nombre or 'Cliente',
        'assigned_mechanic_name': row.get('mecanico_nombre'),
        'vehicle_info': None,
        'service_type': svc,
        'contact_phone': row.get('telefono_contacto'),
        'contact_email': row.get('email_contacto'),
        'notes': row.get('notas_internas'),
        'customer_notes': row.get('notas_cliente'),
    }


def listar_citas(taller_id: str, propietario_id: str) -> list[dict]:
    _verificar_taller(taller_id, propietario_id)
    sb = get_supabase()
    resp = (
        sb.table('citas_taller')
        .select('*')
        .eq('taller_id', taller_id)
        .order('fecha_cita')
        .execute()
    )
    _error(resp)
    clientes = _cargar_clientes_map(taller_id)
    tipos = _cargar_tipos_map(taller_id)
    return [_serializar_cita(r, clientes, tipos) for r in (resp.data or [])]


def crear_cita(taller_id: str, propietario_id: str, datos: dict) -> dict:
    _verificar_taller(taller_id, propietario_id)
    duracion = int(datos.get('duration_minutes') or 60)
    hora_inicio = datos['start_time']
    if len(hora_inicio) == 5:
        hora_inicio = hora_inicio + ':00'
    payload = {
        'taller_id': taller_id,
        'cliente_id': datos['customer'],
        'moto_id': datos.get('vehicle') or datos.get('moto_id'),
        'tipo_servicio_id': datos.get('service_type') or None,
        'descripcion_servicio_custom': datos.get('custom_service_description'),
        'fecha_cita': datos['appointment_date'],
        'hora_inicio': hora_inicio,
        'hora_fin': _calcular_hora_fin(hora_inicio, duracion),
        'duracion_minutos': duracion,
        'estado': 'scheduled',
        'prioridad': datos.get('priority') or 'normal',
        'costo_estimado': datos.get('estimated_cost') or 0,
        'mecanico_nombre': datos.get('assigned_mechanic') or datos.get('mecanico_nombre'),
        'telefono_contacto': datos.get('contact_phone'),
        'email_contacto': datos.get('contact_email'),
        'notas_internas': datos.get('notes'),
        'notas_cliente': datos.get('customer_notes'),
    }
    sb = get_supabase()
    resp = sb.table('citas_taller').insert(payload).execute()
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('No se pudo crear la cita')
    clientes = _cargar_clientes_map(taller_id)
    tipos = _cargar_tipos_map(taller_id)
    return _serializar_cita(row, clientes, tipos)


def cancelar_cita(cita_id: str, taller_id: str, propietario_id: str, notas: str | None = None) -> dict:
    _verificar_taller(taller_id, propietario_id)
    payload: dict[str, Any] = {
        'estado': 'cancelled',
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    if notas:
        payload['notas_internas'] = notas
    sb = get_supabase()
    resp = (
        sb.table('citas_taller')
        .update(payload)
        .eq('id', cita_id)
        .eq('taller_id', taller_id)
        .execute()
    )
    _error(resp)
    row = _first_row(resp)
    if not row:
        raise SupabaseError('Cita no encontrada')
    clientes = _cargar_clientes_map(taller_id)
    tipos = _cargar_tipos_map(taller_id)
    return _serializar_cita(row, clientes, tipos)


def sembrar_tipos_servicio_default(taller_id: str, propietario_id: str) -> None:
    _verificar_taller(taller_id, propietario_id)
    sb = get_supabase()
    existente = sb.table('tipos_servicio_taller').select('id').eq('taller_id', taller_id).limit(1).execute()
    if existente.data:
        return
    defaults = [
        {'nombre': 'Mantenimiento general', 'categoria': 'maintenance', 'color': '#3b82f6', 'duracion_estimada_min': 60},
        {'nombre': 'Reparación', 'categoria': 'repair', 'color': '#ef4444', 'duracion_estimada_min': 120},
        {'nombre': 'Diagnóstico', 'categoria': 'diagnostic', 'color': '#f59e0b', 'duracion_estimada_min': 45},
    ]
    for d in defaults:
        d['taller_id'] = taller_id
    sb.table('tipos_servicio_taller').insert(defaults).execute()

import {
  Bike,
  Loader2,
  Search,
  CheckCircle2,
  UserPlus,
  Mail,
  Phone,
  MapPin,
  User,
  ClipboardList,
  ScanLine,
} from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { FotosHistorial } from '../components/FotosHistorial';
import { QrScannerModal } from '../components/QrScannerModal';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { Moto, Orden, RegistroHistorialMoto } from '../lib/types';
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function splitNombre(full: string | null | undefined) {
  const parts = (full || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return { first: 'Cliente', last: 'Parche' };
  if (parts.length === 1) return { first: parts[0], last: '' };
  return { first: parts[0], last: parts.slice(1).join(' ') };
}

function formatMoney(n: number | null | undefined) {
  if (n == null) return null;
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(n);
}

export function ParchePage() {
  const { taller } = useApp();
  const [query, setQuery] = useState('');
  const [moto, setMoto] = useState<Moto | null>(null);
  const [historial, setHistorial] = useState<RegistroHistorialMoto[]>([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [ordenes, setOrdenes] = useState<Orden[]>([]);
  const [loading, setLoading] = useState(false);
  const [agregandoCliente, setAgregandoCliente] = useState(false);
  const [servicio, setServicio] = useState('Cambio de aceite');
  const [mecanico, setMecanico] = useState('Mecánico');
  const [buscando, setBuscando] = useState(false);
  const [scannerOpen, setScannerOpen] = useState(false);
  const [busquedaError, setBusquedaError] = useState('');

  const loadOrdenes = async () => {
    if (!taller?.id) return;
    setOrdenes(await api.getOrdenes(taller.id));
  };

  const loadHistorial = async (motoId: string, esCliente: boolean) => {
    if (!taller?.id || !esCliente) {
      setHistorial([]);
      return;
    }
    setCargandoHistorial(true);
    try {
      const rows = await api.getHistorialMoto(motoId, taller.id);
      setHistorial(
        [...rows].sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime()),
      );
    } catch {
      setHistorial([]);
    } finally {
      setCargandoHistorial(false);
    }
  };

  useEffect(() => {
    loadOrdenes();
  }, [taller?.id]);

  const buscarCodigo = useCallback(
    async (codigo: string) => {
      const code = codigo.trim().toUpperCase();
      if (!code || !taller?.id) return;
      setQuery(code);
      setBuscando(true);
      setHistorial([]);
      setBusquedaError('');
      setScannerOpen(false);
      try {
        const found = await api.buscarMoto(code, taller.id);
        setMoto(found);
        await loadHistorial(found.id, Boolean(found.es_cliente));
      } catch (err) {
        setMoto(null);
        setHistorial([]);
        setBusquedaError(
          err instanceof Error
            ? `Código ${code}: ${err.message}`
            : `No se encontró moto con código ${code}`,
        );
      } finally {
        setBuscando(false);
      }
    },
    [taller?.id],
  );

  const buscar = async () => {
    await buscarCodigo(query);
  };

  const crearOrden = async () => {
    if (!taller?.id || !moto) return;
    setLoading(true);
    try {
      await api.createOrden({
        taller_id: taller.id,
        moto_id: moto.id,
        motero_id: moto.dueno_id || null,
        placa: moto.placa,
        mecanico_nombre: mecanico,
        servicios: [{ nombre: servicio }],
      });
      await loadOrdenes();
    } finally {
      setLoading(false);
    }
  };

  const agregarComoCliente = async () => {
    if (!taller?.id || !moto?.dueno_id) return;
    setAgregandoCliente(true);
    try {
      const { first, last } = splitNombre(moto.dueno_nombre);
      await api.createCliente(taller.id, {
        first_name: moto.cliente_nombre || first,
        last_name: moto.cliente_apellido || last,
        phone: moto.dueno_telefono || null,
        email: moto.dueno_email || null,
        city: moto.dueno_ciudad || null,
        address: null,
        motero_id: moto.dueno_id,
        notes: `Vinculado desde Parche · placa ${moto.placa}`,
      });
      const refreshed = await api.buscarMoto(query.trim() || moto.codigo_parche || '', taller.id);
      setMoto(refreshed);
      await loadHistorial(refreshed.id, Boolean(refreshed.es_cliente));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'No se pudo agregar el cliente');
    } finally {
      setAgregandoCliente(false);
    }
  };

  const nombreMostrar =
    moto?.es_cliente && (moto.cliente_nombre || moto.cliente_apellido)
      ? `${moto.cliente_nombre || ''} ${moto.cliente_apellido || ''}`.trim()
      : moto?.dueno_nombre || 'Motero Parche';

  const emailMostrar = moto?.es_cliente
    ? moto.cliente_email || moto.dueno_email
    : moto?.dueno_email;
  const telefonoMostrar = moto?.es_cliente
    ? moto.cliente_telefono || moto.dueno_telefono
    : moto?.dueno_telefono;
  const ciudadMostrar = moto?.es_cliente
    ? moto.cliente_ciudad || moto.dueno_ciudad
    : moto?.dueno_ciudad;
  const direccionMostrar = moto?.es_cliente ? moto.cliente_direccion : null;

  return (
    <div>
      <PageHeader
        title="Parche · Motos"
        description="Busca con el código Parche (QR del motero), crea la orden y gestiona repuestos en Órdenes"
      />

      <div className="glass-card mb-6 p-6">
        <h3 className="mb-4 font-semibold text-white">Buscar moto por código Parche</h3>
        <p className="mb-3 text-xs text-slate-500">
          Solo el código o QR que muestra el motero en la app (no se busca por placa)
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              className="input-field pl-10 uppercase"
              placeholder="Código Parche (ej. A7K2M9)"
              value={query}
              onChange={(e) => setQuery(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && buscar()}
            />
          </div>
          <button
            type="button"
            className="btn-secondary inline-flex items-center justify-center gap-2"
            onClick={() => setScannerOpen(true)}
            disabled={buscando}
          >
            <ScanLine className="h-4 w-4" />
            Escanear QR
          </button>
          <button type="button" className="btn-primary" onClick={buscar} disabled={buscando}>
            {buscando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buscar'}
          </button>
        </div>

        {busquedaError && (
          <p className="mt-3 rounded-lg bg-pink-500/10 px-3 py-2 text-sm text-pink-400">
            {busquedaError}
          </p>
        )}

        <QrScannerModal
          open={scannerOpen}
          onClose={() => setScannerOpen(false)}
          onScan={buscarCodigo}
        />

        {moto && (
          <div
            className={`mt-4 rounded-xl border p-4 ${
              moto.es_cliente
                ? 'border-emerald-400/35 bg-emerald-400/5'
                : 'border-amber-400/35 bg-amber-400/5'
            }`}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <Bike className={`h-8 w-8 ${moto.es_cliente ? 'text-emerald-400' : 'text-amber-400'}`} />
                <div>
                  <p className="font-semibold text-white">
                    {moto.marca} {moto.modelo}
                    {moto.anio ? ` · ${moto.anio}` : ''}
                  </p>
                  <p className="text-sm text-slate-400">
                    Placa {moto.placa}
                    {moto.codigo_parche ? ` · Código ${moto.codigo_parche}` : ''}
                    {moto.color ? ` · ${moto.color}` : ''}
                    {' · '}
                    {moto.kilometraje_actual ?? '—'} km
                  </p>
                </div>
              </div>
              <Badge variant={moto.es_cliente ? 'success' : 'warning'}>
                {moto.es_cliente ? 'Cliente del taller' : 'Aún no es cliente'}
              </Badge>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="flex items-start gap-2 text-sm">
                <User className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Nombre</p>
                  <p className="text-slate-200">{nombreMostrar}</p>
                </div>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <Mail className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Correo</p>
                  <p className="text-slate-200">{emailMostrar || 'Sin registrar'}</p>
                </div>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <Phone className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Teléfono</p>
                  <p className="text-slate-200">{telefonoMostrar || 'Sin registrar'}</p>
                </div>
              </div>
              <div className="flex items-start gap-2 text-sm">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    {direccionMostrar ? 'Dirección' : 'Ciudad'}
                  </p>
                  <p className="text-slate-200">
                    {direccionMostrar
                      ? `${direccionMostrar}${ciudadMostrar ? `, ${ciudadMostrar}` : ''}`
                      : ciudadMostrar || 'Sin registrar'}
                  </p>
                </div>
              </div>
            </div>

            {!moto.es_cliente && moto.dueno_id && (
              <button
                type="button"
                className="btn-secondary mt-4 inline-flex items-center gap-2"
                onClick={agregarComoCliente}
                disabled={agregandoCliente}
              >
                {agregandoCliente ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <UserPlus className="h-4 w-4" />
                )}
                Agregar como cliente del taller
              </button>
            )}

            {moto.es_cliente ? (
              <div className="mt-5 border-t border-white/10 pt-4">
                <div className="mb-3 flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-cyan-400" />
                  <h4 className="text-sm font-semibold text-white">Historial clínico completo</h4>
                </div>
                <p className="mb-3 text-xs text-slate-500">
                  Servicios verificados de cualquier taller + registros del dueño
                </p>
                {cargandoHistorial ? (
                  <div className="flex justify-center py-6">
                    <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
                  </div>
                ) : historial.length === 0 ? (
                  <p className="text-sm text-slate-500">Sin registros de historial aún</p>
                ) : (
                  <ul className="max-h-80 space-y-2 overflow-y-auto pr-1">
                    {historial.map((h) => (
                      <li
                        key={`${h.origen}-${h.id}`}
                        className="rounded-lg border border-white/10 bg-slate-950/40 px-3 py-2.5"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <p className="font-medium text-white">{h.tipo_servicio}</p>
                            {h.descripcion && (
                              <p className="mt-0.5 line-clamp-2 text-xs text-slate-400">{h.descripcion}</p>
                            )}
                            <p className="mt-1 text-xs text-slate-500">
                              {h.fecha}
                              {h.origen === 'taller' && h.taller_nombre
                                ? ` · ${h.taller_nombre}`
                                : ''}
                              {h.kilometraje != null
                                ? ` · ${h.kilometraje.toLocaleString('es-CO')} km`
                                : ''}
                              {formatMoney(h.costo) ? ` · ${formatMoney(h.costo)}` : ''}
                            </p>
                            {h.fotos_urls && h.fotos_urls.length > 0 && (
                              <FotosHistorial urls={h.fotos_urls} />
                            )}
                          </div>
                          <Badge variant={h.origen === 'taller' ? 'success' : 'default'}>
                            {h.origen === 'taller' ? 'Verificado' : 'Dueño'}
                          </Badge>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="mt-4 text-xs text-amber-200/80">
                Agrega al motero como cliente para ver el historial completo de la moto.
              </p>
            )}
          </div>
        )}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="label-field">Servicio</label>
            <input
              className="input-field"
              value={servicio}
              onChange={(e) => setServicio(e.target.value)}
            />
          </div>
          <div>
            <label className="label-field">Mecánico</label>
            <input
              className="input-field"
              value={mecanico}
              onChange={(e) => setMecanico(e.target.value)}
            />
          </div>
        </div>
        <button
          type="button"
          className="btn-primary mt-4"
          onClick={crearOrden}
          disabled={loading || !moto}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear orden de trabajo'}
        </button>
      </div>

      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Órdenes recientes
        </h3>
        <Link to="/ordenes" className="text-sm font-medium text-cyan-400 hover:underline">
          Ir a Órdenes →
        </Link>
      </div>
      {ordenes.length === 0 ? (
        <EmptyState icon={Bike} title="Sin órdenes" description="Busca una moto y crea la primera orden" />
      ) : (
        <div className="space-y-3">
          {ordenes.map((o) => (
            <div key={o.id} className="glass-card flex items-center justify-between gap-3 p-4">
              <div>
                <p className="font-medium text-white">{o.servicios?.[0]?.nombre || 'Servicio'}</p>
                <p className="text-xs text-slate-500">
                  {new Date(o.created_at).toLocaleString('es-CO')}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={o.estado === 'completado' ? 'success' : 'warning'}>{o.estado}</Badge>
                {o.estado === 'pendiente' ? (
                  <Link to="/ordenes" className="btn-primary text-xs">
                    Agregar repuestos / Cerrar
                  </Link>
                ) : (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

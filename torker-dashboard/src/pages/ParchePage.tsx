import { useEffect, useState } from 'react';
import { Bike, Loader2, Search, CheckCircle2 } from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { Moto, Orden } from '../lib/types';

export function ParchePage() {
  const { taller } = useApp();
  const [placa, setPlaca] = useState('');
  const [moto, setMoto] = useState<Moto | null>(null);
  const [ordenes, setOrdenes] = useState<Orden[]>([]);
  const [loading, setLoading] = useState(false);
  const [servicio, setServicio] = useState('Cambio de aceite');
  const [mecanico, setMecanico] = useState('Mecánico');
  const [buscando, setBuscando] = useState(false);

  const loadOrdenes = async () => {
    if (!taller?.id) return;
    setOrdenes(await api.getOrdenes(taller.id));
  };

  useEffect(() => {
    loadOrdenes();
  }, [taller?.id]);

  const buscar = async () => {
    if (!placa.trim()) return;
    setBuscando(true);
    try {
      setMoto(await api.buscarMoto(placa.trim()));
    } catch {
      setMoto(null);
      alert('Moto no encontrada');
    } finally {
      setBuscando(false);
    }
  };

  const crearOrden = async () => {
    if (!taller?.id || !placa.trim()) return;
    setLoading(true);
    try {
      await api.createOrden({
        taller_id: taller.id,
        placa: placa.trim(),
        mecanico_nombre: mecanico,
        servicios: [{ nombre: servicio }],
      });
      await loadOrdenes();
    } finally {
      setLoading(false);
    }
  };

  const cerrarOrden = async (id: string) => {
    const costo = prompt('Costo total (COP):', '85000');
    if (costo === null) return;
    const km = prompt('Kilometraje:', '15000');
    if (km === null) return;
    await api.cerrarOrden(id, {
      tipo_servicio: servicio,
      costo_total: Number(costo),
      kilometraje: Number(km),
    });
    await loadOrdenes();
  };

  return (
    <div>
      <PageHeader
        title="Parche · Motos"
        description="Busca motos del ecosistema Parche y registra servicios en el historial clínico"
      />

      <div className="glass-card mb-6 p-6">
        <h3 className="mb-4 font-semibold text-white">Buscar moto por placa</h3>
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              className="input-field pl-10 uppercase"
              placeholder="Ej: HTNEJ"
              value={placa}
              onChange={(e) => setPlaca(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && buscar()}
            />
          </div>
          <button type="button" className="btn-primary" onClick={buscar} disabled={buscando}>
            {buscando ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buscar'}
          </button>
        </div>

        {moto && (
          <div className="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4">
            <div className="flex items-center gap-3">
              <Bike className="h-8 w-8 text-emerald-400" />
              <div>
                <p className="font-semibold text-white">{moto.marca} {moto.modelo}</p>
                <p className="text-sm text-slate-400">Placa {moto.placa} · {moto.kilometraje_actual ?? '—'} km</p>
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="label-field">Servicio</label>
            <input className="input-field" value={servicio} onChange={(e) => setServicio(e.target.value)} />
          </div>
          <div>
            <label className="label-field">Mecánico</label>
            <input className="input-field" value={mecanico} onChange={(e) => setMecanico(e.target.value)} />
          </div>
        </div>
        <button type="button" className="btn-primary mt-4" onClick={crearOrden} disabled={loading || !placa.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear orden de trabajo'}
        </button>
      </div>

      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">Órdenes recientes</h3>
      {ordenes.length === 0 ? (
        <EmptyState icon={Bike} title="Sin órdenes" description="Busca una moto y crea la primera orden" />
      ) : (
        <div className="space-y-3">
          {ordenes.map((o) => (
            <div key={o.id} className="glass-card flex items-center justify-between p-4">
              <div>
                <p className="font-medium text-white">{o.servicios?.[0]?.nombre || 'Servicio'}</p>
                <p className="text-xs text-slate-500">{new Date(o.created_at).toLocaleString('es-CO')}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={o.estado === 'completado' ? 'success' : 'warning'}>{o.estado}</Badge>
                {o.estado === 'pendiente' ? (
                  <button type="button" className="btn-primary text-xs" onClick={() => cerrarOrden(o.id)}>
                    Cerrar → Parche
                  </button>
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

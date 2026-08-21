import { useEffect, useState } from 'react';
import { ClipboardList, Loader2, Plus, Trash2, Camera } from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import { uploadEvidencia } from '../lib/storageEvidencia';
import type { Orden, Repuesto } from '../lib/types';

function money(n: number) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(n);
}

const MAX_FOTOS = 5;

export function OrdenesPage() {
  const { taller, loading: tallerLoading } = useApp();
  const [ordenes, setOrdenes] = useState<Orden[]>([]);
  const [repuestos, setRepuestos] = useState<Repuesto[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Orden | null>(null);
  const [repuestoId, setRepuestoId] = useState('');
  const [cantidad, setCantidad] = useState('1');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [cerrarOpen, setCerrarOpen] = useState(false);
  const [costo, setCosto] = useState('');
  const [km, setKm] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [fotosFiles, setFotosFiles] = useState<File[]>([]);
  const [fotosPreview, setFotosPreview] = useState<string[]>([]);

  const load = async () => {
    if (!taller?.id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const ords = await api.getOrdenes(taller.id);
      setOrdenes(ords);
      setSelected((prev) => {
        if (!prev) return null;
        const found = ords.find((o) => o.id === prev.id);
        if (!found || found.estado !== 'pendiente') return null;
        return { ...found, items: prev.items || [] };
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar órdenes');
      setOrdenes([]);
    } finally {
      setLoading(false);
    }
    try {
      setRepuestos(await api.getRepuestos(taller.id));
    } catch {
      /* ignore */
    }
  };

  const selectOrden = async (o: Orden) => {
    setSelected({ ...o, items: [] });
    setError('');
    const items = await api.getOrdenItems(o.id);
    setSelected({ ...o, items });
  };

  useEffect(() => {
    if (tallerLoading) return;
    load();
  }, [taller?.id, tallerLoading]);

  useEffect(() => {
    return () => {
      fotosPreview.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [fotosPreview]);

  const refreshSelectedItems = async (ordenId: string) => {
    const items = await api.getOrdenItems(ordenId);
    setSelected((prev) => (prev && prev.id === ordenId ? { ...prev, items } : prev));
  };

  const addItem = async () => {
    if (!selected || !repuestoId) return;
    const rep = repuestos.find((r) => r.id === repuestoId);
    if (!rep) return;
    setSaving(true);
    setError('');
    try {
      await api.addOrdenItem(selected.id, {
        repuesto_id: rep.id,
        nombre: rep.name,
        cantidad: Number(cantidad) || 1,
        precio_unitario: rep.sale_price,
      });
      setRepuestoId('');
      setCantidad('1');
      await refreshSelectedItems(selected.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al agregar');
    } finally {
      setSaving(false);
    }
  };

  const removeItem = async (itemId: string) => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.removeOrdenItem(itemId);
      await refreshSelectedItems(selected.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al quitar');
    } finally {
      setSaving(false);
    }
  };

  const openCerrar = () => {
    if (!selected) return;
    const itemsTotal = (selected.items || []).reduce(
      (s, i) => s + i.cantidad * i.precio_unitario,
      0,
    );
    setCosto(String(itemsTotal || 0));
    setKm('');
    setDescripcion('');
    setFotosFiles([]);
    setFotosPreview([]);
    setCerrarOpen(true);
  };

  const onPickFotos = (files: FileList | null) => {
    if (!files) return;
    const next = [...fotosFiles, ...Array.from(files)].slice(0, MAX_FOTOS);
    fotosPreview.forEach((u) => URL.revokeObjectURL(u));
    setFotosFiles(next);
    setFotosPreview(next.map((f) => URL.createObjectURL(f)));
  };

  const removeFoto = (idx: number) => {
    URL.revokeObjectURL(fotosPreview[idx]);
    setFotosFiles((prev) => prev.filter((_, i) => i !== idx));
    setFotosPreview((prev) => prev.filter((_, i) => i !== idx));
  };

  const confirmarCerrar = async () => {
    if (!selected || !taller?.id) return;
    if (!descripcion.trim()) {
      setError('La descripción del mecánico es obligatoria');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const urls: string[] = [];
      for (const file of fotosFiles) {
        urls.push(await uploadEvidencia(taller.id, selected.id, file));
      }
      await api.cerrarOrden(selected.id, {
        costo_total: Number(costo) || 0,
        kilometraje: km ? Number(km) : null,
        tipo_servicio: selected.servicios?.[0]?.nombre,
        descripcion: descripcion.trim(),
        fotos: urls,
      });
      setCerrarOpen(false);
      setSelected(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cerrar');
    } finally {
      setSaving(false);
    }
  };

  const pendientes = ordenes.filter((o) => o.estado === 'pendiente');
  const cerradas = ordenes.filter((o) => o.estado !== 'pendiente');

  return (
    <div>
      <PageHeader
        title="Órdenes de trabajo"
        description="Agrega repuestos y cierra con evidencia (descripción + fotos). Luego queda bloqueada."
      />

      {error && !cerrarOpen && <p className="mb-4 text-sm text-pink-400">{error}</p>}

      {tallerLoading || loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        </div>
      ) : ordenes.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="Sin órdenes"
          description="Crea una desde Parche · Motos con el código Parche."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Pendientes
            </h3>
            {pendientes.length === 0 && (
              <p className="text-sm text-slate-500">No hay órdenes abiertas</p>
            )}
            {pendientes.map((o) => (
              <button
                key={o.id}
                type="button"
                onClick={() => selectOrden(o)}
                className={`glass-card w-full p-4 text-left transition ${
                  selected?.id === o.id ? 'border-cyan-400/50' : 'hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium text-white">
                    {o.servicios?.[0]?.nombre || 'Servicio'}
                  </p>
                  <Badge variant="warning">{o.estado}</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {o.mecanico_nombre || '—'} · {new Date(o.created_at).toLocaleString('es-CO')}
                </p>
              </button>
            ))}

            <h3 className="pt-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Cerradas (solo lectura)
            </h3>
            {cerradas.slice(0, 8).map((o) => (
              <div key={o.id} className="glass-card p-4 opacity-80">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white">{o.servicios?.[0]?.nombre || 'Servicio'}</p>
                  <Badge variant="success">completado</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {o.costo_total != null ? money(o.costo_total) : '—'} ·{' '}
                  {new Date(o.created_at).toLocaleString('es-CO')}
                </p>
              </div>
            ))}
          </div>

          <div className="glass-card p-6">
            {!selected ? (
              <p className="text-sm text-slate-400">Selecciona una orden pendiente</p>
            ) : (
              <>
                <h3 className="text-lg font-semibold text-white">
                  {selected.servicios?.[0]?.nombre || 'Orden'}
                </h3>
                <p className="text-sm text-slate-400">{selected.mecanico_nombre}</p>

                <div className="mt-4 space-y-2">
                  {(selected.items || []).map((it) => (
                    <div
                      key={it.id}
                      className="flex items-center justify-between rounded-xl border border-parche-border bg-slate-900/50 px-3 py-2"
                    >
                      <div>
                        <p className="text-sm text-white">{it.nombre}</p>
                        <p className="text-xs text-slate-500">
                          x{it.cantidad} · {money(it.precio_unitario)}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeItem(it.id)}
                        className="rounded-lg p-2 text-slate-500 hover:text-pink-400"
                        disabled={saving}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  {!selected.items?.length && (
                    <p className="text-sm text-slate-500">Sin repuestos aún</p>
                  )}
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
                  <select
                    className="input-field"
                    value={repuestoId}
                    onChange={(e) => setRepuestoId(e.target.value)}
                  >
                    <option value="">Agregar del inventario…</option>
                    {repuestos.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name} (stock {r.stock_quantity})
                      </option>
                    ))}
                  </select>
                  <input
                    className="input-field w-20"
                    type="number"
                    min="1"
                    value={cantidad}
                    onChange={(e) => setCantidad(e.target.value)}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={addItem}
                    disabled={saving || !repuestoId}
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>

                <p className="mt-3 text-sm text-slate-400">
                  Subtotal ítems:{' '}
                  <span className="font-medium text-white">
                    {money(
                      (selected.items || []).reduce(
                        (s, i) => s + i.cantidad * i.precio_unitario,
                        0,
                      ),
                    )}
                  </span>
                </p>

                <button
                  type="button"
                  className="btn-primary mt-6 w-full"
                  onClick={openCerrar}
                  disabled={saving}
                >
                  Cerrar orden con evidencia
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {cerrarOpen && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !saving && setCerrarOpen(false)}
          />
          <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-parche-border bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white">Cerrar orden</h2>
            <p className="mt-1 text-xs text-slate-500">
              Al cerrar, el historial queda verificado y no editable. Si hay error, ticket a soporte
              Parche.
            </p>

            <div className="mt-5 space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="label-field">Costo total (COP)</label>
                  <input
                    className="input-field"
                    type="number"
                    min={0}
                    value={costo}
                    onChange={(e) => setCosto(e.target.value)}
                  />
                </div>
                <div>
                  <label className="label-field">Kilometraje</label>
                  <input
                    className="input-field"
                    type="number"
                    min={0}
                    value={km}
                    onChange={(e) => setKm(e.target.value)}
                    placeholder="Opcional"
                  />
                </div>
              </div>

              <div>
                <label className="label-field">Descripción del mecánico *</label>
                <textarea
                  className="input-field min-h-[100px]"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  placeholder="Qué se hizo, hallazgos, recomendaciones…"
                  required
                />
              </div>

              <div>
                <label className="label-field">Fotos de evidencia (máx. {MAX_FOTOS})</label>
                <div className="mt-1 flex flex-wrap gap-2">
                  <label className="btn-secondary inline-flex cursor-pointer items-center gap-2">
                    <Camera className="h-4 w-4" />
                    Galería
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={(e) => onPickFotos(e.target.files)}
                    />
                  </label>
                  <label className="btn-secondary inline-flex cursor-pointer items-center gap-2">
                    <Camera className="h-4 w-4" />
                    Cámara
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                      onChange={(e) => onPickFotos(e.target.files)}
                    />
                  </label>
                </div>
                {fotosPreview.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {fotosPreview.map((src, i) => (
                      <div key={src} className="relative">
                        <img
                          src={src}
                          alt=""
                          className="h-20 w-20 rounded-lg object-cover border border-white/10"
                        />
                        <button
                          type="button"
                          onClick={() => removeFoto(i)}
                          className="absolute -right-1 -top-1 rounded-full bg-slate-900 px-1.5 text-xs text-pink-400"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {error && <p className="text-sm text-pink-400">{error}</p>}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  className="btn-secondary flex-1"
                  disabled={saving}
                  onClick={() => setCerrarOpen(false)}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn-primary flex-1"
                  disabled={saving}
                  onClick={confirmarCerrar}
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Confirmar cierre'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

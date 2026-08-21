import { useCallback, useEffect, useState } from 'react';
import { Loader2, Plus, Pencil, Wrench } from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { TipoServicio } from '../lib/types';

const COLORES = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b'];

const emptyForm = {
  name: '',
  description: '',
  color: '#3b82f6',
  is_active: true,
};

export function ServiciosPage() {
  const { taller } = useApp();
  const [items, setItems] = useState<TipoServicio[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TipoServicio | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!taller?.id) return;
    setLoading(true);
    try {
      let list = await api.getTiposServicio(taller.id, false);
      if (list.length === 0) {
        await api.sembrarTiposServicio(taller.id);
        list = await api.getTiposServicio(taller.id, false);
      }
      setItems(list);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [taller?.id]);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setModalOpen(true);
  };

  const openEdit = (t: TipoServicio) => {
    setEditing(t);
    setForm({
      name: t.name,
      description: t.description || '',
      color: t.color || '#3b82f6',
      is_active: t.is_active,
    });
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taller?.id || !form.name.trim()) {
      setError('El nombre es obligatorio');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        color: form.color,
      };
      if (editing) {
        await api.updateTipoServicio(editing.id, { ...payload, is_active: form.is_active });
      } else {
        await api.createTipoServicio(taller.id, payload);
      }
      setModalOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Servicios"
        description="Etiquetas para la agenda (sin tiempo fijo: lo defines en cada cita)"
        action={
          <button type="button" className="btn-primary" onClick={openCreate}>
            <Plus className="h-4 w-4" /> Nuevo servicio
          </button>
        }
      />

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={Wrench}
          title="Sin servicios"
          description="Crea etiquetas simples: mantenimiento, reparación, diagnóstico…"
          action={
            <button type="button" className="btn-primary" onClick={openCreate}>
              <Plus className="h-4 w-4" /> Crear primero
            </button>
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Servicio</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {items.map((t) => (
                <tr key={t.id} className="hover:bg-white/[0.02]">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <span
                        className="h-3 w-3 shrink-0 rounded-full"
                        style={{ backgroundColor: t.color }}
                      />
                      <div>
                        <p className="font-medium text-white">{t.name}</p>
                        {t.description && (
                          <p className="line-clamp-1 text-xs text-slate-500">{t.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={t.is_active ? 'success' : 'default'}>
                      {t.is_active ? 'Activo' : 'Inactivo'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => openEdit(t)}
                      className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-parche-border bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white">
              {editing ? 'Editar servicio' : 'Nuevo servicio'}
            </h2>
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="label-field">Nombre *</label>
                <input
                  className="input-field"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Cambio de aceite"
                />
              </div>
              <div>
                <label className="label-field">Descripción</label>
                <textarea
                  className="input-field"
                  rows={2}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Opcional"
                />
              </div>
              <div>
                <label className="label-field">Color en agenda</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {COLORES.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setForm({ ...form, color: c })}
                      className={`h-8 w-8 rounded-full border-2 transition ${
                        form.color === c ? 'scale-110 border-white' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>
              {editing && (
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                    className="rounded border-white/20"
                  />
                  Activo (aparece al agendar citas)
                </label>
              )}
              {error && <p className="text-sm text-pink-400">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" className="btn-secondary flex-1" onClick={() => setModalOpen(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  {editing ? 'Guardar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

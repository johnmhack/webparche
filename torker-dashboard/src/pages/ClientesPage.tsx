import { useEffect, useState } from 'react';
import { Loader2, Plus, Search, UserPlus } from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { Cliente } from '../lib/types';

const DOC_TYPES = [
  { value: 'cc', label: 'Cédula de Ciudadanía' },
  { value: 'ce', label: 'Cédula de Extranjería' },
  { value: 'nit', label: 'NIT' },
  { value: 'ti', label: 'Tarjeta de Identidad' },
  { value: 'pasaporte', label: 'Pasaporte' },
];

const emptyForm = {
  first_name: '',
  last_name: '',
  document_type: 'cc',
  document_number: '',
  phone: '',
  email: '',
  address: '',
  city: '',
  department: '',
  notes: '',
};

export function ClientesPage() {
  const { taller } = useApp();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Cliente | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!taller?.id) return;
    setLoading(true);
    try {
      setClientes(await api.getClientes(taller.id));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [taller?.id]);

  const filtered = clientes.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.first_name.toLowerCase().includes(q) ||
      c.last_name.toLowerCase().includes(q) ||
      c.phone?.includes(q) ||
      c.email?.toLowerCase().includes(q) ||
      c.document_number?.includes(q)
    );
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setModalOpen(true);
  };

  const openEdit = (c: Cliente) => {
    setEditing(c);
    setForm({
      first_name: c.first_name,
      last_name: c.last_name,
      document_type: c.document_type,
      document_number: c.document_number || '',
      phone: c.phone || '',
      email: c.email || '',
      address: c.address || '',
      city: c.city || '',
      department: c.department || '',
      notes: c.notes || '',
    });
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taller?.id) return;
    setSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        document_number: form.document_number || null,
        phone: form.phone || null,
        email: form.email || null,
        address: form.address || null,
        city: form.city || null,
        department: form.department || null,
        notes: form.notes || null,
      };
      if (editing) {
        await api.updateCliente(editing.id, { ...payload, taller_id: taller.id });
      } else {
        await api.createCliente(taller.id, payload);
      }
      setModalOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (c: Cliente) => {
    if (!taller?.id) return;
    await api.updateCliente(c.id, { is_active: !c.is_active, taller_id: taller.id });
    await load();
  };

  return (
    <div>
      <PageHeader
        title="Clientes"
        description="Gestiona la base de clientes de tu taller"
        action={
          <button type="button" className="btn-primary" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Nuevo cliente
          </button>
        }
      />

      <div className="relative mb-6">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <input
          className="input-field pl-10"
          placeholder="Buscar por nombre, teléfono, email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={UserPlus}
          title="Sin clientes"
          description="Crea tu primer cliente para empezar"
          action={
            <button type="button" className="btn-primary" onClick={openCreate}>
              <Plus className="h-4 w-4" />
              Crear cliente
            </button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((c) => (
            <div key={c.id} className="glass-card p-5">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-white">
                    {c.first_name} {c.last_name}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {c.get_document_type_display} {c.document_number || '—'}
                  </p>
                </div>
                <Badge variant={c.is_active ? 'success' : 'danger'}>
                  {c.is_active ? 'Activo' : 'Inactivo'}
                </Badge>
              </div>
              <dl className="space-y-1.5 text-sm">
                {c.phone && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Teléfono</dt>
                    <dd>{c.phone}</dd>
                  </div>
                )}
                {c.email && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Email</dt>
                    <dd className="truncate pl-4">{c.email}</dd>
                  </div>
                )}
              </dl>
              <div className="mt-4 flex gap-2 border-t border-parche-border pt-4">
                <button type="button" className="btn-secondary flex-1 text-xs" onClick={() => openEdit(c)}>
                  Editar
                </button>
                <button type="button" className="btn-ghost text-xs" onClick={() => toggleActive(c)}>
                  {c.is_active ? 'Desactivar' : 'Activar'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-parche-border bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white">
              {editing ? 'Editar cliente' : 'Nuevo cliente'}
            </h2>
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label-field">Nombre *</label>
                  <input className="input-field" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                </div>
                <div>
                  <label className="label-field">Apellido *</label>
                  <input className="input-field" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label-field">Tipo documento</label>
                  <select className="input-field" value={form.document_type} onChange={(e) => setForm({ ...form, document_type: e.target.value })}>
                    {DOC_TYPES.map((d) => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label-field">Número</label>
                  <input className="input-field" value={form.document_number} onChange={(e) => setForm({ ...form, document_number: e.target.value })} />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label-field">Teléfono</label>
                  <input className="input-field" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                </div>
                <div>
                  <label className="label-field">Email</label>
                  <input type="email" className="input-field" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </div>
              </div>
              {error && <p className="text-sm text-pink-400">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" className="btn-secondary flex-1" onClick={() => setModalOpen(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : editing ? 'Guardar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

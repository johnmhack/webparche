import { useEffect, useMemo, useState } from 'react';
import { Loader2, Package, Plus, Search } from 'lucide-react';
import { PageHeader, EmptyState, Badge, StatCard } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { Repuesto } from '../lib/types';

const CATEGORIES = [
  { value: 'motor', label: 'Motor' },
  { value: 'transmision', label: 'Transmisión' },
  { value: 'frenos', label: 'Frenos' },
  { value: 'suspension', label: 'Suspensión' },
  { value: 'electrico', label: 'Sistema Eléctrico' },
  { value: 'carroceria', label: 'Carrocería' },
  { value: 'accesorios', label: 'Accesorios' },
  { value: 'lubricantes', label: 'Lubricantes' },
  { value: 'filtros', label: 'Filtros' },
  { value: 'neumaticos', label: 'Neumáticos' },
  { value: 'other', label: 'Otro' },
];

const emptyForm = {
  name: '',
  description: '',
  part_number: '',
  internal_code: '',
  category: 'other',
  brand: '',
  stock_quantity: '0',
  min_stock_level: '5',
  max_stock_level: '50',
  unit_cost: '0',
  sale_price: '0',
  location: '',
  supplier: '',
};

function formatMoney(value: number) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value);
}

function stockBadge(status: Repuesto['stock_status']) {
  if (status === 'low') return <Badge variant="danger">Stock bajo</Badge>;
  if (status === 'over') return <Badge variant="warning">Sobre stock</Badge>;
  return <Badge variant="success">Normal</Badge>;
}

export function InventarioPage() {
  const { taller } = useApp();
  const [repuestos, setRepuestos] = useState<Repuesto[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Repuesto | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!taller?.id) return;
    setLoading(true);
    try {
      setRepuestos(await api.getRepuestos(taller.id));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [taller?.id]);

  const stats = useMemo(() => {
    const categories = new Set(repuestos.map((r) => r.category));
    const lowStock = repuestos.filter((r) => r.stock_status === 'low').length;
    const totalValue = repuestos.reduce((sum, r) => sum + r.inventory_value, 0);
    return {
      total: repuestos.length,
      lowStock,
      totalValue,
      categories: categories.size,
    };
  }, [repuestos]);

  const filtered = repuestos.filter((r) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      r.name.toLowerCase().includes(q) ||
      r.part_number?.toLowerCase().includes(q) ||
      r.internal_code?.toLowerCase().includes(q) ||
      r.brand?.toLowerCase().includes(q);
    const matchesCategory = !categoryFilter || r.category === categoryFilter;
    const matchesStock = !stockFilter || r.stock_status === stockFilter;
    return matchesSearch && matchesCategory && matchesStock;
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setModalOpen(true);
  };

  const openEdit = (r: Repuesto) => {
    setEditing(r);
    setForm({
      name: r.name,
      description: r.description || '',
      part_number: r.part_number || '',
      internal_code: r.internal_code || '',
      category: r.category,
      brand: r.brand || '',
      stock_quantity: String(r.stock_quantity),
      min_stock_level: String(r.min_stock_level),
      max_stock_level: String(r.max_stock_level),
      unit_cost: String(r.unit_cost),
      sale_price: String(r.sale_price),
      location: r.location || '',
      supplier: r.supplier || '',
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
        name: form.name.trim(),
        description: form.description || null,
        part_number: form.part_number || null,
        internal_code: form.internal_code || null,
        category: form.category,
        brand: form.brand || null,
        stock_quantity: Number(form.stock_quantity) || 0,
        min_stock_level: Number(form.min_stock_level) || 5,
        max_stock_level: Number(form.max_stock_level) || 50,
        unit_cost: Number(form.unit_cost) || 0,
        sale_price: Number(form.sale_price) || 0,
        location: form.location || null,
        supplier: form.supplier || null,
      };
      if (editing) {
        await api.updateRepuesto(editing.id, { ...payload, taller_id: taller.id });
      } else {
        await api.createRepuesto(taller.id, payload);
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
        title="Inventario"
        description="Repuestos y stock del taller"
        action={
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:brightness-105"
          >
            <Plus className="h-4 w-4" />
            Agregar repuesto
          </button>
        }
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total repuestos" value={stats.total} icon={Package} accent="cyan" />
        <StatCard label="Stock bajo" value={stats.lowStock} icon={Package} accent="pink" />
        <StatCard label="Valor inventario" value={formatMoney(stats.totalValue)} icon={Package} accent="green" />
        <StatCard label="Categorías" value={stats.categories} icon={Package} accent="cyan" />
      </div>

      <div className="glass-card mb-6 grid gap-4 p-4 md:grid-cols-3">
        <div className="relative md:col-span-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="search"
            placeholder="Nombre, código, marca..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-parche-border bg-slate-900/60 py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2.5 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
        >
          <option value="">Todas las categorías</option>
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <select
          value={stockFilter}
          onChange={(e) => setStockFilter(e.target.value)}
          className="rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2.5 text-sm text-white focus:border-cyan-400/50 focus:outline-none"
        >
          <option value="">Todo el stock</option>
          <option value="low">Stock bajo</option>
          <option value="normal">Stock normal</option>
          <option value="over">Sobre stock</option>
        </select>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Package}
          title="Sin repuestos"
          description="Agrega el primer repuesto para empezar a controlar el inventario."
          action={
            <button
              type="button"
              onClick={openCreate}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-400/15 px-4 py-2 text-sm font-semibold text-cyan-300"
            >
              <Plus className="h-4 w-4" />
              Agregar repuesto
            </button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => openEdit(r)}
              className="glass-card p-5 text-left transition hover:border-cyan-400/30"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-white">{r.name}</h3>
                  <p className="mt-0.5 text-xs text-slate-500">{r.category_display}</p>
                </div>
                {stockBadge(r.stock_status)}
              </div>
              <div className="space-y-1 text-sm text-slate-400">
                {r.internal_code && <p>Código: {r.internal_code}</p>}
                {r.brand && <p>Marca: {r.brand}</p>}
                <p>
                  Stock: <span className="font-medium text-white">{r.stock_quantity}</span>
                </p>
                <p>Precio venta: {formatMoney(r.sale_price)}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <form
            onSubmit={handleSubmit}
            className="glass-card max-h-[90vh] w-full max-w-lg overflow-y-auto p-6"
          >
            <h2 className="text-xl font-bold text-white">
              {editing ? 'Editar repuesto' : 'Nuevo repuesto'}
            </h2>
            {error && <p className="mt-3 text-sm text-pink-400">{error}</p>}

            <div className="mt-5 space-y-4">
              <label className="block text-sm">
                <span className="text-slate-400">Nombre *</span>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="text-slate-400">Código interno</span>
                  <input
                    value={form.internal_code}
                    onChange={(e) => setForm({ ...form, internal_code: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Número de parte</span>
                  <input
                    value={form.part_number}
                    onChange={(e) => setForm({ ...form, part_number: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="text-slate-400">Categoría</span>
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Marca</span>
                  <input
                    value={form.brand}
                    onChange={(e) => setForm({ ...form, brand: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <label className="block text-sm">
                  <span className="text-slate-400">Stock</span>
                  <input
                    type="number"
                    min="0"
                    value={form.stock_quantity}
                    onChange={(e) => setForm({ ...form, stock_quantity: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Mínimo</span>
                  <input
                    type="number"
                    min="0"
                    value={form.min_stock_level}
                    onChange={(e) => setForm({ ...form, min_stock_level: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Máximo</span>
                  <input
                    type="number"
                    min="0"
                    value={form.max_stock_level}
                    onChange={(e) => setForm({ ...form, max_stock_level: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="text-slate-400">Costo unitario</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.unit_cost}
                    onChange={(e) => setForm({ ...form, unit_cost: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Precio venta</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.sale_price}
                    onChange={(e) => setForm({ ...form, sale_price: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="text-slate-400">Ubicación</span>
                  <input
                    value={form.location}
                    onChange={(e) => setForm({ ...form, location: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
                <label className="block text-sm">
                  <span className="text-slate-400">Proveedor</span>
                  <input
                    value={form.supplier}
                    onChange={(e) => setForm({ ...form, supplier: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-parche-border bg-slate-900/60 px-3 py-2 text-white"
                  />
                </label>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-xl px-4 py-2 text-sm text-slate-400 hover:text-white"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-60"
              >
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                Guardar
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

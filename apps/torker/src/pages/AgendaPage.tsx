import { useEffect, useMemo, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  Plus,
  Calendar as CalendarIcon,
  X,
} from 'lucide-react';
import { PageHeader, Badge } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import type { Cita, Cliente } from '../lib/types';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const DIAS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

const STATUS_LABEL: Record<string, string> = {
  scheduled: 'Programada',
  confirmed: 'Confirmada',
  cancelled: 'Cancelada',
  completed: 'Completada',
};

function formatTime(t: string) {
  return t.substring(0, 5);
}

function dateKey(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function AgendaPage() {
  const { taller } = useApp();
  const [citas, setCitas] = useState<Cita[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(() => new Date());
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    customer: '',
    custom_service_description: '',
    appointment_date: dateKey(new Date()),
    start_time: '09:00',
    duration_minutes: 60,
  });

  const load = async () => {
    if (!taller?.id) return;
    setLoading(true);
    try {
      const [c, cl] = await Promise.all([
        api.getCitas(taller.id),
        api.getClientes(taller.id),
      ]);
      setCitas(c);
      setClientes(cl);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [taller?.id]);

  const calendarDays = useMemo(() => {
    const year = month.getFullYear();
    const m = month.getMonth();
    const first = new Date(year, m, 1);
    const start = new Date(first);
    start.setDate(start.getDate() - first.getDay());
    const days: Date[] = [];
    for (let i = 0; i < 42; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      days.push(d);
    }
    return days;
  }, [month]);

  const citasPorFecha = useMemo(() => {
    const map: Record<string, Cita[]> = {};
    citas.forEach((c) => {
      if (!map[c.appointment_date]) map[c.appointment_date] = [];
      map[c.appointment_date].push(c);
    });
    return map;
  }, [citas]);

  const citasHoy = citas.filter(
    (c) => c.appointment_date === dateKey(new Date()) && c.status !== 'cancelled',
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taller?.id) return;
    setSaving(true);
    try {
      await api.createCita({
        ...form,
        taller_id: taller.id,
        service_type: null,
        custom_service_description: form.custom_service_description || null,
      });
      setModalOpen(false);
      await load();
    } finally {
      setSaving(false);
    }
  };

  const cancelar = async (id: string) => {
    if (!taller?.id || !confirm('¿Cancelar esta cita?')) return;
    await api.cancelarCita(id, taller.id);
    await load();
  };

  return (
    <div>
      <PageHeader
        title="Agenda"
        description="Calendario de citas del taller"
        action={
          <button type="button" className="btn-primary" onClick={() => setModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Nueva cita
          </button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
        <div className="glass-card p-5">
          <div className="mb-5 flex items-center justify-between">
            <button type="button" className="btn-ghost" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1))}>
              <ChevronLeft className="h-5 w-5" />
            </button>
            <h2 className="text-lg font-semibold text-white">
              {MESES[month.getMonth()]} {month.getFullYear()}
            </h2>
            <button type="button" className="btn-ghost" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1))}>
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
            </div>
          ) : (
            <>
              <div className="mb-2 grid grid-cols-7 gap-1">
                {DIAS.map((d) => (
                  <div key={d} className="py-2 text-center text-xs font-semibold uppercase text-slate-500">
                    {d}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((d) => {
                  const key = dateKey(d);
                  const inMonth = d.getMonth() === month.getMonth();
                  const isToday = key === dateKey(new Date());
                  const dayCitas = citasPorFecha[key] || [];
                  return (
                    <div
                      key={key}
                      className={`min-h-[88px] rounded-xl border p-1.5 transition ${
                        inMonth ? 'border-parche-border bg-slate-900/40' : 'border-transparent bg-slate-900/20 opacity-40'
                      } ${isToday ? 'ring-1 ring-cyan-400/50' : ''}`}
                    >
                      <span className={`text-xs font-semibold ${isToday ? 'text-cyan-300' : 'text-slate-400'}`}>
                        {d.getDate()}
                      </span>
                      <div className="mt-1 space-y-0.5">
                        {dayCitas.slice(0, 2).map((c) => (
                          <div
                            key={c.id}
                            className="truncate rounded px-1 py-0.5 text-[10px] font-medium text-white"
                            style={{ backgroundColor: c.service_type?.color || '#3b82f6' }}
                          >
                            {formatTime(c.start_time)} {c.customer_full_name.split(' ')[0]}
                          </div>
                        ))}
                        {dayCitas.length > 2 && (
                          <span className="text-[10px] text-cyan-400">+{dayCitas.length - 2}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        <div className="glass-card p-5">
          <h3 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <CalendarIcon className="h-4 w-4 text-cyan-400" />
            Citas de hoy
          </h3>
          {citasHoy.length === 0 ? (
            <p className="text-sm text-slate-500">No hay citas para hoy</p>
          ) : (
            <div className="space-y-3">
              {citasHoy.map((c) => (
                <div key={c.id} className="rounded-xl border border-parche-border bg-slate-900/50 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-white">{c.customer_full_name}</p>
                      <p className="text-xs text-slate-400">
                        {formatTime(c.start_time)} – {formatTime(c.end_time)}
                      </p>
                      <p className="mt-1 text-sm text-slate-300">
                        {c.custom_service_description || c.service_type?.name || 'Cita'}
                      </p>
                    </div>
                    <Badge variant={c.status === 'cancelled' ? 'danger' : 'success'}>
                      {STATUS_LABEL[c.status] || c.status}
                    </Badge>
                  </div>
                  {c.status !== 'cancelled' && (
                    <button type="button" className="btn-ghost mt-2 text-xs text-pink-400" onClick={() => cancelar(c.id)}>
                      <X className="h-3 w-3" />
                      Cancelar
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative w-full max-w-md rounded-2xl border border-parche-border bg-slate-900 p-6">
            <h2 className="text-xl font-bold text-white">Nueva cita</h2>
            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div>
                <label className="label-field">Cliente *</label>
                <select className="input-field" required value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })}>
                  <option value="">Seleccionar…</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label-field">Motivo *</label>
                <input
                  className="input-field"
                  required
                  placeholder="Ej. revisión, cambio de aceite…"
                  value={form.custom_service_description}
                  onChange={(e) =>
                    setForm({ ...form, custom_service_description: e.target.value })
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label-field">Fecha *</label>
                  <input type="date" className="input-field" required value={form.appointment_date} onChange={(e) => setForm({ ...form, appointment_date: e.target.value })} />
                </div>
                <div>
                  <label className="label-field">Hora *</label>
                  <input type="time" className="input-field" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-3">
                <button type="button" className="btn-secondary flex-1" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="btn-primary flex-1" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Programar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

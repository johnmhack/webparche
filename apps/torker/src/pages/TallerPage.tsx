import { useEffect, useState } from 'react';
import {
  Building2,
  Download,
  Loader2,
  Pencil,
  Plus,
  Printer,
  Trash2,
  UserCog,
  FileText,
} from 'lucide-react';
import { PageHeader, EmptyState, Badge } from '../components/ui';
import { ContratoParcheContenido } from '../components/ContratoParcheContenido';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';
import { CONTRATO_PARCHE_VERSION } from '../lib/contrato';
import type { Mecanico } from '../lib/types';

type Tab = 'perfil' | 'mecanicos' | 'contrato';

const PDF_URL = import.meta.env.VITE_CONTRATO_PARCHE_URL as string | undefined;

const emptyMecForm = { nombre: '', telefono: '', especialidad: '' };

export function TallerPage() {
  const { taller, loading: tallerLoading, refreshTaller } = useApp();
  const [tab, setTab] = useState<Tab>('perfil');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');

  const [form, setForm] = useState({
    nombre: '',
    direccion: '',
    ciudad: '',
    telefono: '',
    email: '',
    nit: '',
    horario: '',
    descripcion: '',
  });

  const [mecanicos, setMecanicos] = useState<Mecanico[]>([]);
  const [cargandoMec, setCargandoMec] = useState(false);
  const [mecForm, setMecForm] = useState(emptyMecForm);
  const [mecOpen, setMecOpen] = useState(false);
  const [editingMec, setEditingMec] = useState<Mecanico | null>(null);

  useEffect(() => {
    if (!taller) return;
    setForm({
      nombre: taller.nombre || '',
      direccion: taller.direccion || '',
      ciudad: taller.ciudad || '',
      telefono: taller.telefono || '',
      email: taller.email || '',
      nit: taller.nit || '',
      horario: taller.horario || '',
      descripcion: taller.descripcion || '',
    });
  }, [taller?.id, taller?.nombre, taller?.contrato_aceptado_at]);

  const loadMecanicos = async () => {
    if (!taller?.id) return;
    setCargandoMec(true);
    try {
      setMecanicos(await api.getMecanicos(taller.id, false));
    } catch {
      setMecanicos([]);
    } finally {
      setCargandoMec(false);
    }
  };

  useEffect(() => {
    if (tab === 'mecanicos') loadMecanicos();
  }, [tab, taller?.id]);

  const guardarPerfil = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taller?.id || !form.nombre.trim()) {
      setError('El nombre del establecimiento es obligatorio');
      return;
    }
    setSaving(true);
    setError('');
    setOkMsg('');
    try {
      await api.updateTaller(taller.id, {
        nombre: form.nombre.trim(),
        direccion: form.direccion.trim() || null,
        ciudad: form.ciudad.trim() || null,
        telefono: form.telefono.trim() || null,
        email: form.email.trim() || null,
        nit: form.nit.trim() || null,
        horario: form.horario.trim() || null,
        descripcion: form.descripcion.trim() || null,
      });
      await refreshTaller();
      setOkMsg('Perfil guardado');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar');
    } finally {
      setSaving(false);
    }
  };

  const aceptarContrato = async () => {
    if (!taller?.id) return;
    setSaving(true);
    setError('');
    try {
      await api.updateTaller(taller.id, {
        contrato_aceptado_at: new Date().toISOString(),
        contrato_version: CONTRATO_PARCHE_VERSION,
      });
      await refreshTaller();
      setOkMsg('Contrato aceptado');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la aceptación');
    } finally {
      setSaving(false);
    }
  };

  const openNuevoMecanico = () => {
    setEditingMec(null);
    setMecForm(emptyMecForm);
    setError('');
    setMecOpen(true);
  };

  const openEditarMecanico = (m: Mecanico) => {
    setEditingMec(m);
    setMecForm({
      nombre: m.nombre,
      telefono: m.telefono || '',
      especialidad: m.especialidad || '',
    });
    setError('');
    setMecOpen(true);
  };

  const cerrarModalMec = () => {
    setMecOpen(false);
    setEditingMec(null);
    setMecForm(emptyMecForm);
  };

  const guardarMecanico = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taller?.id || !mecForm.nombre.trim()) return;
    setSaving(true);
    setError('');
    try {
      if (editingMec) {
        await api.updateMecanico(editingMec.id, {
          nombre: mecForm.nombre,
          telefono: mecForm.telefono || null,
          especialidad: mecForm.especialidad || null,
        });
      } else {
        await api.createMecanico(taller.id, {
          nombre: mecForm.nombre,
          telefono: mecForm.telefono || null,
          especialidad: mecForm.especialidad || null,
        });
      }
      cerrarModalMec();
      await loadMecanicos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el mecánico');
    } finally {
      setSaving(false);
    }
  };

  const eliminarMecanico = async (m: Mecanico) => {
    if (!confirm(`¿Eliminar a ${m.nombre}?`)) return;
    setSaving(true);
    setError('');
    try {
      await api.deleteMecanico(m.id);
      await loadMecanicos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar');
    } finally {
      setSaving(false);
    }
  };

  const toggleMecanico = async (m: Mecanico) => {
    setSaving(true);
    try {
      await api.updateMecanico(m.id, { activo: !m.activo });
      await loadMecanicos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar');
    } finally {
      setSaving(false);
    }
  };

  const imprimirContrato = () => {
    window.print();
  };

  const contratoAlDia =
    Boolean(taller?.contrato_aceptado_at) &&
    taller?.contrato_version === CONTRATO_PARCHE_VERSION;

  if (tallerLoading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: typeof Building2 }[] = [
    { id: 'perfil', label: 'Perfil', icon: Building2 },
    { id: 'mecanicos', label: 'Mecánicos', icon: UserCog },
    { id: 'contrato', label: 'Contrato', icon: FileText },
  ];

  return (
    <div>
      <PageHeader
        title="Mi taller"
        description="Perfil del establecimiento, mecánicos y contrato con Parche"
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setError('');
              setOkMsg('');
              setTab(id);
            }}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
              tab === id
                ? 'bg-cyan-400/15 text-cyan-300'
                : 'bg-slate-800/50 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-pink-400">{error}</p>}
      {okMsg && <p className="mb-4 text-sm text-emerald-400">{okMsg}</p>}

      {tab === 'perfil' && (
        <form onSubmit={guardarPerfil} className="glass-card max-w-2xl space-y-4 p-6">
          <div>
            <label className="label-field">Nombre del establecimiento *</label>
            <input
              className="input-field"
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label-field">NIT / documento</label>
              <input
                className="input-field"
                value={form.nit}
                onChange={(e) => setForm({ ...form, nit: e.target.value })}
              />
            </div>
            <div>
              <label className="label-field">Teléfono</label>
              <input
                className="input-field"
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label-field">Email</label>
              <input
                type="email"
                className="input-field"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div>
              <label className="label-field">Ciudad</label>
              <input
                className="input-field"
                value={form.ciudad}
                onChange={(e) => setForm({ ...form, ciudad: e.target.value })}
              />
            </div>
          </div>
          <div>
            <label className="label-field">Dirección</label>
            <input
              className="input-field"
              value={form.direccion}
              onChange={(e) => setForm({ ...form, direccion: e.target.value })}
            />
          </div>
          <div>
            <label className="label-field">Horario</label>
            <input
              className="input-field"
              placeholder="Ej. Lun–Sáb 8:00–18:00"
              value={form.horario}
              onChange={(e) => setForm({ ...form, horario: e.target.value })}
            />
          </div>
          <div>
            <label className="label-field">Descripción breve</label>
            <textarea
              className="input-field min-h-[88px]"
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
            />
          </div>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Guardar perfil'}
          </button>
        </form>
      )}

      {tab === 'mecanicos' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button type="button" className="btn-primary" onClick={openNuevoMecanico}>
              <Plus className="h-4 w-4" /> Agregar mecánico
            </button>
          </div>
          {cargandoMec ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-7 w-7 animate-spin text-cyan-400" />
            </div>
          ) : mecanicos.length === 0 ? (
            <EmptyState
              icon={UserCog}
              title="Sin mecánicos"
              description="Agrégalos para asignarlos al crear órdenes"
            />
          ) : (
            <ul className="space-y-2">
              {mecanicos.map((m) => (
                <li
                  key={m.id}
                  className="glass-card flex flex-wrap items-center justify-between gap-3 p-4"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium text-white">{m.nombre}</p>
                      <Badge variant={m.activo ? 'success' : 'danger'}>
                        {m.activo ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {[m.especialidad, m.telefono].filter(Boolean).join(' · ') || 'Sin detalle'}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn-secondary text-xs"
                      disabled={saving}
                      onClick={() => openEditarMecanico(m)}
                    >
                      <Pencil className="h-3.5 w-3.5" /> Editar
                    </button>
                    <button
                      type="button"
                      className="btn-secondary text-xs"
                      disabled={saving}
                      onClick={() => toggleMecanico(m)}
                    >
                      {m.activo ? 'Desactivar' : 'Activar'}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary text-xs text-pink-300 hover:border-pink-400/40"
                      disabled={saving}
                      onClick={() => eliminarMecanico(m)}
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Eliminar
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {tab === 'contrato' && (
        <div className="space-y-4">
          <div className="glass-card flex flex-wrap items-center justify-between gap-3 p-4 print:hidden">
            <div>
              {contratoAlDia ? (
                <p className="text-sm text-emerald-400">
                  Contrato aceptado (v{taller?.contrato_version}) ·{' '}
                  {taller?.contrato_aceptado_at
                    ? new Date(taller.contrato_aceptado_at).toLocaleString('es-CO')
                    : ''}
                </p>
              ) : (
                <p className="text-sm text-amber-300">
                  Debes revisar y aceptar la versión vigente ({CONTRATO_PARCHE_VERSION})
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" onClick={imprimirContrato}>
                <Printer className="h-4 w-4" /> Imprimir / PDF
              </button>
              {PDF_URL && (
                <a
                  href={PDF_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary inline-flex items-center gap-2"
                >
                  <Download className="h-4 w-4" /> Descargar PDF
                </a>
              )}
              {!contratoAlDia && (
                <button
                  type="button"
                  className="btn-primary"
                  disabled={saving}
                  onClick={aceptarContrato}
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Acepto el contrato'}
                </button>
              )}
            </div>
          </div>

          <div
            id="contrato-parche-print"
            className="glass-card p-6 print:border-0 print:bg-white print:p-8 print:text-black"
          >
            <ContratoParcheContenido tallerNombre={taller?.nombre} />
          </div>
        </div>
      )}

      {mecOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 print:hidden">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !saving && cerrarModalMec()}
          />
          <div className="relative w-full max-w-md rounded-2xl border border-parche-border bg-slate-900 p-6">
            <h2 className="text-xl font-bold text-white">
              {editingMec ? 'Editar mecánico' : 'Nuevo mecánico'}
            </h2>
            <form onSubmit={guardarMecanico} className="mt-5 space-y-4">
              <div>
                <label className="label-field">Nombre *</label>
                <input
                  className="input-field"
                  required
                  value={mecForm.nombre}
                  onChange={(e) => setMecForm({ ...mecForm, nombre: e.target.value })}
                />
              </div>
              <div>
                <label className="label-field">Teléfono</label>
                <input
                  className="input-field"
                  value={mecForm.telefono}
                  onChange={(e) => setMecForm({ ...mecForm, telefono: e.target.value })}
                />
              </div>
              <div>
                <label className="label-field">Especialidad</label>
                <input
                  className="input-field"
                  placeholder="Ej. motor, electricidad…"
                  value={mecForm.especialidad}
                  onChange={(e) => setMecForm({ ...mecForm, especialidad: e.target.value })}
                />
              </div>
              {error && <p className="text-sm text-pink-400">{error}</p>}
              <div className="flex gap-3">
                <button
                  type="button"
                  className="btn-secondary flex-1"
                  disabled={saving}
                  onClick={cerrarModalMec}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

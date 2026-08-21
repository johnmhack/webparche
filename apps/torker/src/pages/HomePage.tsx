import { Link } from 'react-router-dom';
import { Calendar, Users, Bike, Package, ClipboardList, ArrowRight, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PageHeader, StatCard } from '../components/ui';
import { useApp } from '../context/AppContext';
import { api } from '../lib/api';

export function HomePage() {
  const { taller, loading: tallerLoading } = useApp();
  const [stats, setStats] = useState({ clientes: 0, citasHoy: 0, ordenes: 0 });

  useEffect(() => {
    if (!taller?.id) return;
    const today = new Date().toISOString().split('T')[0];
    Promise.all([
      api.getClientes(taller.id),
      api.getCitas(taller.id),
      api.getOrdenes(taller.id),
    ]).then(([clientes, citas, ordenes]) => {
      setStats({
        clientes: clientes.length,
        citasHoy: citas.filter((c) => c.appointment_date === today && c.status !== 'cancelled').length,
        ordenes: ordenes.filter((o) => o.estado === 'pendiente').length,
      });
    }).catch(() => {});
  }, [taller?.id]);

  if (tallerLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  const modules = [
    {
      to: '/clientes',
      icon: Users,
      title: 'Clientes',
      desc: 'Registra y gestiona clientes del taller',
      color: 'text-emerald-400',
    },
    {
      to: '/agenda',
      icon: Calendar,
      title: 'Agenda',
      desc: 'Programa citas y visualiza el calendario',
      color: 'text-cyan-400',
    },
    {
      to: '/inventario',
      icon: Package,
      title: 'Inventario',
      desc: 'Controla repuestos, stock y precios',
      color: 'text-amber-400',
    },
    {
      to: '/ordenes',
      icon: ClipboardList,
      title: 'Órdenes',
      desc: 'Órdenes de trabajo, repuestos y cierre',
      color: 'text-violet-400',
    },
    {
      to: '/parche',
      icon: Bike,
      title: 'Parche · Motos',
      desc: 'Busca por código/QR e historial de clientes',
      color: 'text-pink-400',
    },
  ];

  return (
    <div>
      <PageHeader
        title={taller?.nombre || 'Mi Taller'}
        description="Panel de gestión conectado al ecosistema Parche"
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <StatCard label="Clientes" value={stats.clientes} icon={Users} accent="green" />
        <StatCard label="Citas hoy" value={stats.citasHoy} icon={Calendar} accent="cyan" />
        <StatCard label="Órdenes activas" value={stats.ordenes} icon={Bike} accent="pink" />
      </div>

      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">Módulos</h2>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {modules.map(({ to, icon: Icon, title, desc, color }) => (
          <Link
            key={to}
            to={to}
            className="glass-card group flex flex-col p-6 transition hover:border-cyan-400/30 hover:shadow-glow"
          >
            <Icon className={`mb-4 h-8 w-8 ${color}`} />
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="mt-1 flex-1 text-sm text-slate-400">{desc}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-cyan-400 opacity-0 transition group-hover:opacity-100">
              Abrir <ArrowRight className="h-4 w-4" />
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

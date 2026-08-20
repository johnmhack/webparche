import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Calendar,
  Home,
  LogOut,
  Menu,
  Users,
  Wrench,
  Bike,
  Package,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { signOut as clearAuth } from '../lib/auth';
import { useApp } from '../context/AppContext';

const nav = [
  { to: '/', icon: Home, label: 'Inicio' },
  { to: '/clientes', icon: Users, label: 'Clientes' },
  { to: '/agenda', icon: Calendar, label: 'Agenda' },
  { to: '/inventario', icon: Package, label: 'Inventario' },
  { to: '/parche', icon: Bike, label: 'Parche · Motos' },
];

export function Layout() {
  const { taller, loading } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleSignOut = () => {
    clearAuth();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar desktop */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-parche-border bg-slate-950/80 lg:flex">
        <div className="flex items-center gap-2 border-b border-parche-border px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400">
            <Wrench className="h-5 w-5 text-slate-950" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Torker</p>
            <p className="text-xs text-slate-500">by Parche</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-cyan-400/10 text-cyan-300'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-parche-border p-4">
          <p className="truncate text-sm font-medium text-slate-200">
            {loading ? 'Cargando…' : taller?.nombre || 'Sin taller'}
          </p>
          <button type="button" onClick={handleSignOut} className="btn-ghost mt-2 w-full justify-start px-0">
            <LogOut className="h-4 w-4" />
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Mobile header */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-parche-border bg-slate-950/90 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-cyan-400" />
            <span className="font-semibold">Torker</span>
          </div>
          <button type="button" className="btn-ghost" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </button>
        </header>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
            <aside className="absolute left-0 top-0 flex h-full w-72 flex-col bg-slate-950 shadow-2xl">
              <div className="flex items-center justify-between border-b border-parche-border p-4">
                <span className="font-bold">Menú</span>
                <button type="button" className="btn-ghost" onClick={() => setMobileOpen(false)}>
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav className="flex-1 space-y-1 p-3">
                {nav.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${
                        isActive ? 'bg-cyan-400/10 text-cyan-300' : 'text-slate-400'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </NavLink>
                ))}
              </nav>
            </aside>
          </div>
        )}

        <main className="flex-1 overflow-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

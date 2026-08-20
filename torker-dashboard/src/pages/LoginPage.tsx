import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Mail, Lock, Wrench, ArrowRight } from 'lucide-react';
import { saveSession } from '../lib/auth';
import { signInWithPassword, supabaseConfigured } from '../lib/supabaseAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const session = await signInWithPassword(email.trim(), password);
      saveSession(session);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Panel izquierdo — branding */}
      <div className="relative hidden w-1/2 overflow-hidden lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950" />
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-emerald-500/15 blur-3xl" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-400">
            <Wrench className="h-6 w-6 text-slate-950" />
          </div>
          <div>
            <p className="text-xl font-bold text-white">Torker</p>
            <p className="text-sm text-slate-400">Gestión de talleres · Parche</p>
          </div>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="text-4xl font-bold leading-tight text-white">
            Tu taller, conectado al ecosistema Parche
          </h1>
          <p className="mt-4 text-lg text-slate-400">
            Clientes, citas, motos e historial clínico de la moto — todo en un solo panel.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-slate-300">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Cuenta propia para tu taller
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
              Historial clínico de la moto, visible para tus clientes
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-pink-400" />
              Información protegida y siempre al día
            </li>
          </ul>
        </div>

        <p className="relative z-10 text-xs text-slate-600">© Parche · Torker 2026</p>
      </div>

      {/* Panel derecho — formulario */}
      <div className="flex w-full flex-col justify-center px-6 py-12 lg:w-1/2 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400">
              <Wrench className="h-5 w-5 text-slate-950" />
            </div>
            <span className="text-xl font-bold text-white">Torker</span>
          </div>

          <h2 className="text-2xl font-bold text-white">Iniciar sesión</h2>
          <p className="mt-2 text-sm text-slate-400">
            Ingresa con la cuenta de tu taller
          </p>

          {!supabaseConfigured() && (
            <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              Falta configuración del sistema. Contacta al administrador.
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label className="label-field" htmlFor="email">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="email"
                  type="email"
                  className="input-field pl-10"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="label-field" htmlFor="password">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="password"
                  type="password"
                  className="input-field pl-10"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <p className="rounded-xl border border-pink-500/30 bg-pink-500/10 px-4 py-3 text-sm text-pink-300">
                {error}
              </p>
            )}

            <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <>
                  Entrar al dashboard
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-500">
            ¿Eres motociclista? Descarga{' '}
            <a href="/index.html" className="text-cyan-400 hover:underline">
              Parche
            </a>{' '}
            para gestionar tus motos.
          </p>
        </div>
      </div>
    </div>
  );
}

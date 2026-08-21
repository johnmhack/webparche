import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { ensureValidSession, redirectToLogin, signOut } from '../lib/auth';
import { ensureTaller, clearTallerCache } from '../lib/api';
import type { Taller } from '../lib/types';

interface AppContextValue {
  taller: Taller | null;
  loading: boolean;
  refreshTaller: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [taller, setTaller] = useState<Taller | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshTaller = async () => {
    clearTallerCache();
    const ok = await ensureValidSession();
    if (!ok) {
      setTaller(null);
      return;
    }
    try {
      const t = await ensureTaller();
      setTaller(t);
    } catch {
      setTaller(null);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const ok = await ensureValidSession();
        if (!ok) {
          signOut();
          redirectToLogin();
          return;
        }
        await refreshTaller();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <AppContext.Provider value={{ taller, loading, refreshTaller }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}

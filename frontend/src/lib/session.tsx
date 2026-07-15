import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, type CV, type User } from './api';

const STORAGE_KEY = 'acia_user';

type SessionState = {
  user: User | null;
  latestCv: CV | null;
  loading: boolean;
  error: string | null;
  ensureUser: (email: string, fullName?: string, targetRole?: string) => Promise<User>;
  setLatestCv: (cv: CV | null) => void;
  refreshCvFromDashboard: () => Promise<void>;
  logout: () => void;
};

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  });
  const [latestCv, setLatestCv] = useState<CV | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const persist = (u: User) => {
    setUser(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
  };

  const refreshCvFromDashboard = useCallback(async () => {
    if (!user) return;
    try {
      const dash = await api.getDashboard(user.id);
      setLatestCv(dash.latest_cv ?? null);
      if (dash.user) persist(dash.user);
    } catch {
      /* ignore */
    }
  }, [user]);

  useEffect(() => {
    if (user) void refreshCvFromDashboard();
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const ensureUser = useCallback(
    async (email: string, fullName?: string, targetRole?: string) => {
      setLoading(true);
      setError(null);
      try {
        const u = await api.createUser(email, fullName, targetRole);
        persist(u);
        return u;
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Failed to create user';
        setError(msg);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    setUser(null);
    setLatestCv(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({
      user,
      latestCv,
      loading,
      error,
      ensureUser,
      setLatestCv,
      refreshCvFromDashboard,
      logout,
    }),
    [user, latestCv, loading, error, ensureUser, refreshCvFromDashboard, logout],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}

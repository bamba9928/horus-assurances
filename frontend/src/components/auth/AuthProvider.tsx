"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from "@/lib/api";
import type { AuthUser } from "@/types/api";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setUser(null);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    const profile = await fetchCurrentUser();
    setUser(profile);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const profile = await loginRequest(username, password);
    setUser(profile);
  }, []);

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        const profile = await fetchCurrentUser();
        if (mounted) {
          setUser(profile);
        }
      } catch {
        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshProfile }),
    [loading, login, logout, refreshProfile, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}

"use client";

// Auth state for the app: token + user profile in localStorage-backed state.
// `useAuth` exposes login/register/logout plus a `user` and `loading` flag.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import * as api from "@/lib/api";
import type { LoginPayload, RegisterPayload, User } from "@/lib/types";

const USER_KEY = "shramiksathi.user";

type UserUpdatePayload = Partial<
  Pick<User, "gender" | "date_of_birth" | "ethnicity" | "education_level" | "language">
>;

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateUser: (payload: UserUpdatePayload) => Promise<User>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    const stored = window.localStorage.getItem(USER_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        // fall through to a fresh fetch
      }
    }
    api
      .fetchMe()
      .then((u) => {
        setUser(u);
        window.localStorage.setItem(USER_KEY, JSON.stringify(u));
      })
      .catch(() => {
        api.setToken(null);
        window.localStorage.removeItem(USER_KEY);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const res = await api.login(payload);
    setUser(res.user);
    window.localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    return res.user;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const res = await api.register(payload);
    setUser(res.user);
    window.localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    return res.user;
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    window.localStorage.removeItem(USER_KEY);
  }, []);

  const refreshUser = useCallback(async () => {
    const u = await api.fetchMe();
    setUser(u);
    window.localStorage.setItem(USER_KEY, JSON.stringify(u));
  }, []);

  const updateUser = useCallback(async (payload: UserUpdatePayload) => {
    const u = await api.updateMe(payload);
    setUser(u);
    window.localStorage.setItem(USER_KEY, JSON.stringify(u));
    return u;
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser, updateUser }),
    [user, loading, login, register, logout, refreshUser, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

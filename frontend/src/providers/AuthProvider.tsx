import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { apiFetch, type User } from "../lib/api";
import { db } from "../lib/db";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  refresh: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  setup: (username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
};

type LoginResponse = {
  ok: boolean;
  user: User;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const AUTH_CACHE_KEY = "auth:last_user";

async function cacheUser(user: User | null) {
  if (!user) {
    await db.settings_cache.delete(AUTH_CACHE_KEY);
    return;
  }
  await db.settings_cache.put({
    key: AUTH_CACHE_KEY,
    value: user,
    updated_at: new Date().toISOString()
  });
}

async function readCachedUser() {
  const cached = await db.settings_cache.get(AUTH_CACHE_KEY);
  if (!cached || typeof cached.value !== "object" || cached.value === null) {
    return null;
  }
  const value = cached.value as Partial<User>;
  if (typeof value.id !== "string" || typeof value.username !== "string") {
    return null;
  }
  return {
    id: value.id,
    username: value.username,
    display_name: typeof value.display_name === "string" ? value.display_name : null
  } satisfies User;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  const refresh = useCallback(async () => {
    try {
      const nextUser = await apiFetch<User>("/auth/me");
      await cacheUser(nextUser);
      setUser(nextUser);
      setStatus("authenticated");
    } catch {
      if (!navigator.onLine) {
        const cachedUser = await readCachedUser();
        if (cachedUser) {
          setUser(cachedUser);
          setStatus("authenticated");
          return;
        }
      }
      await cacheUser(null);
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (username: string, password: string) => {
    const response = await apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    await cacheUser(response.user);
    setUser(response.user);
    setStatus("authenticated");
  }, []);

  const setup = useCallback(async (username: string, password: string, displayName?: string) => {
    const response = await apiFetch<LoginResponse>("/auth/setup", {
      method: "POST",
      body: JSON.stringify({
        username,
        password,
        display_name: displayName
      })
    });
    await cacheUser(response.user);
    setUser(response.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    await apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" });
    await cacheUser(null);
    setUser(null);
    setStatus("anonymous");
  }, []);

  const value = useMemo(
    () => ({ status, user, refresh, login, setup, logout }),
    [status, user, refresh, login, setup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}

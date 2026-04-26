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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  const refresh = useCallback(async () => {
    try {
      const nextUser = await apiFetch<User>("/auth/me");
      setUser(nextUser);
      setStatus("authenticated");
    } catch {
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
    setUser(response.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    await apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" });
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

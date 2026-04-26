import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { flushSyncQueue, type SyncFlushResult } from "../lib/sync";
import { useOffline } from "./OfflineProvider";

type SyncState = "synced" | "syncing" | "pending" | "offline" | "error";

type SyncContextValue = {
  state: SyncState;
  flush: () => Promise<void>;
};

const SyncContext = createContext<SyncContextValue | null>(null);

function stateFromResult(result: SyncFlushResult): SyncState {
  if (result.failed > 0) {
    return "error";
  }
  if (result.pending > 0) {
    return "pending";
  }
  return "synced";
}

export function SyncProvider({ children }: { children: ReactNode }) {
  const { online } = useOffline();
  const [state, setState] = useState<SyncState>(online ? "synced" : "offline");

  const flush = useCallback(async () => {
    if (!online) {
      setState("offline");
      return;
    }
    setState("syncing");
    try {
      const result = await flushSyncQueue();
      setState(stateFromResult(result));
    } catch {
      setState("error");
    }
  }, [online]);

  useEffect(() => {
    if (!online) {
      setState("offline");
      return;
    }
    void flush();
    const interval = window.setInterval(() => void flush(), 60_000);
    return () => window.clearInterval(interval);
  }, [online, flush]);

  const value = useMemo(() => ({ state, flush }), [state, flush]);
  return <SyncContext.Provider value={value}>{children}</SyncContext.Provider>;
}

export function useSyncState() {
  const value = useContext(SyncContext);
  if (!value) {
    throw new Error("useSyncState must be used inside SyncProvider");
  }
  return value;
}

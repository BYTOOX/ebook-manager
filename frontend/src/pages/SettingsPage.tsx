import {
  Activity,
  AlertCircle,
  Check,
  Database,
  HardDrive,
  Loader2,
  LogOut,
  Moon,
  RefreshCw,
  Settings2,
  Trash2,
  Upload,
  Wifi
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, scanIncoming, type ImportJobsResponse, type ScanResponse } from "../lib/api";
import { db, type OfflineBook } from "../lib/db";
import { removeOfflineBook } from "../lib/offline";
import { useAuth } from "../providers/AuthProvider";
import { useOffline } from "../providers/OfflineProvider";
import { useSyncState } from "../providers/SyncProvider";
import { useUiStore, type AppTheme } from "../stores/ui";

const themes: AppTheme[] = ["system", "black_gold", "dark", "light"];

type LocalStats = {
  offlineCount: number;
  offlineBytes: number;
  offlineBooks: OfflineBook[];
  progressCount: number;
  bookmarkCount: number;
  queuePending: number;
  queueFailed: number;
  storageUsed?: number;
  storageQuota?: number;
};

function formatBytes(size?: number) {
  if (!size) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

async function readLocalStats(): Promise<LocalStats> {
  const [offlineBooks, progressCount, bookmarks, queue, storage] = await Promise.all([
    db.offline_books.toArray(),
    db.reading_progress.count(),
    db.bookmarks.toArray(),
    db.sync_queue.toArray(),
    navigator.storage?.estimate
      ? navigator.storage.estimate()
      : Promise.resolve({} as StorageEstimate)
  ]);
  const offlineBytes = offlineBooks.reduce(
    (total, book) => total + (book.epub_blob?.size ?? 0) + (book.cover_blob?.size ?? 0),
    0
  );
  return {
    offlineCount: offlineBooks.filter((book) => book.epub_blob).length,
    offlineBytes,
    offlineBooks: offlineBooks.filter((book) => book.epub_blob),
    progressCount,
    bookmarkCount: bookmarks.filter((bookmark) => !bookmark.deleted).length,
    queuePending: queue.filter((event) => event.status === "pending" || event.status === "syncing").length,
    queueFailed: queue.filter((event) => event.status === "failed").length,
    storageUsed: storage.usage,
    storageQuota: storage.quota
  };
}

export function SettingsPage() {
  const { logout } = useAuth();
  const theme = useUiStore((state) => state.theme);
  const setTheme = useUiStore((state) => state.setTheme);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Aurelia</p>
          <h1>Settings</h1>
        </div>
      </header>

      <section className="settings-section">
        <h2>Apparence</h2>
        <div className="theme-grid">
          {themes.map((item) => (
            <button key={item} className={theme === item ? "active" : ""} onClick={() => setTheme(item)}>
              <Moon size={17} aria-hidden="true" />
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="settings-section">
        <h2>Gestion</h2>
        <Link className="settings-link" to="/import">
          <Upload size={19} aria-hidden="true" />
          Import EPUB
        </Link>
        <Link className="settings-link" to="/settings/advanced">
          <Settings2 size={19} aria-hidden="true" />
          Avance
        </Link>
      </section>

      <button className="secondary-action wide" onClick={() => void logout()}>
        <LogOut size={18} aria-hidden="true" />
        Logout
      </button>
    </main>
  );
}

export function AdvancedSettingsPage() {
  const queryClient = useQueryClient();
  const { online } = useOffline();
  const { state: syncState, flush } = useSyncState();
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [scanBusy, setScanBusy] = useState(false);
  const [localBusy, setLocalBusy] = useState(false);
  const [localMessage, setLocalMessage] = useState<string | null>(null);

  const health = useQuery({
    queryKey: ["advanced", "health"],
    queryFn: () => apiFetch<{ status: string; app: string }>("/health"),
    refetchInterval: 30_000
  });

  const jobs = useQuery({
    queryKey: ["advanced", "import-jobs"],
    queryFn: () => apiFetch<ImportJobsResponse>("/import-jobs?limit=6"),
    refetchInterval: 45_000
  });

  const localStats = useQuery({
    queryKey: ["advanced", "local-stats"],
    queryFn: readLocalStats,
    refetchInterval: 20_000
  });

  useEffect(() => {
    const refresh = () => void queryClient.invalidateQueries({ queryKey: ["advanced", "local-stats"] });
    window.addEventListener("online", refresh);
    window.addEventListener("offline", refresh);
    return () => {
      window.removeEventListener("online", refresh);
      window.removeEventListener("offline", refresh);
    };
  }, [queryClient]);

  async function handleScan() {
    setScanBusy(true);
    setScanResult(null);
    try {
      const result = await scanIncoming();
      setScanResult(result);
      await queryClient.invalidateQueries({ queryKey: ["advanced", "import-jobs"] });
    } finally {
      setScanBusy(false);
    }
  }

  async function handleFlush() {
    await flush();
    await queryClient.invalidateQueries({ queryKey: ["advanced", "local-stats"] });
  }

  async function handlePurgeLocalCache() {
    setLocalBusy(true);
    setLocalMessage(null);
    try {
      await db.offline_books.clear();
      setLocalMessage("Cache EPUB offline purge. Progression et sync conservees.");
      await queryClient.invalidateQueries({ queryKey: ["advanced", "local-stats"] });
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    } finally {
      setLocalBusy(false);
    }
  }

  async function handleRemoveOfflineBook(bookId: string) {
    setLocalBusy(true);
    setLocalMessage(null);
    try {
      await removeOfflineBook(bookId);
      setLocalMessage("Livre retire du cache offline");
      await queryClient.invalidateQueries({ queryKey: ["advanced", "local-stats"] });
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    } finally {
      setLocalBusy(false);
    }
  }

  const stats = localStats.data;

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Gestion</p>
          <h1>Avance</h1>
        </div>
      </header>

      <div className="maintenance-grid">
        <section className="settings-section">
          <div className="metadata-heading">
            <Activity size={18} aria-hidden="true" />
            <h2>Sante</h2>
          </div>
          <div className="stat-grid">
            <div>
              <span>API</span>
              <strong>{health.data?.status ?? (health.isError ? "error" : "...")}</strong>
            </div>
            <div>
              <span>Reseau</span>
              <strong>{online ? "online" : "offline"}</strong>
            </div>
            <div>
              <span>Sync</span>
              <strong>{syncState}</strong>
            </div>
          </div>
          <button className="secondary-action wide" onClick={() => void handleFlush()}>
            <Wifi size={18} aria-hidden="true" />
            Sync maintenant
          </button>
        </section>

        <section className="settings-section">
          <div className="metadata-heading">
            <Database size={18} aria-hidden="true" />
            <h2>IndexedDB</h2>
          </div>
          <div className="stat-grid">
            <div>
              <span>EPUB offline</span>
              <strong>{stats?.offlineCount ?? 0}</strong>
            </div>
            <div>
              <span>Taille offline</span>
              <strong>{formatBytes(stats?.offlineBytes)}</strong>
            </div>
            <div>
              <span>Stockage</span>
              <strong>{formatBytes(stats?.storageUsed)}</strong>
            </div>
            <div>
              <span>Quota</span>
              <strong>{formatBytes(stats?.storageQuota)}</strong>
            </div>
          </div>
          <div className="stat-grid">
            <div>
              <span>Progressions</span>
              <strong>{stats?.progressCount ?? 0}</strong>
            </div>
            <div>
              <span>Bookmarks</span>
              <strong>{stats?.bookmarkCount ?? 0}</strong>
            </div>
            <div>
              <span>Queue</span>
              <strong>{stats?.queuePending ?? 0}</strong>
            </div>
            <div>
              <span>Failed</span>
              <strong>{stats?.queueFailed ?? 0}</strong>
            </div>
          </div>
          <button className="secondary-action wide" onClick={() => void handlePurgeLocalCache()} disabled={localBusy}>
            {localBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Trash2 size={18} aria-hidden="true" />}
            Purger EPUB offline
          </button>
          <div className="maintenance-list">
            {(stats?.offlineBooks ?? []).map((book) => (
              <div key={book.book_id} className="maintenance-row success">
                <div>
                  <strong>{book.title}</strong>
                  <span>{formatBytes(book.file_size)}</span>
                </div>
                <p>
                  <span>{book.authors[0] ?? "Auteur inconnu"}</span>
                  <button
                    className="icon-button compact-icon"
                    aria-label={`Retirer ${book.title} du cache offline`}
                    onClick={() => void handleRemoveOfflineBook(book.book_id)}
                    disabled={localBusy}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </p>
              </div>
            ))}
            {!localStats.isLoading && (stats?.offlineBooks.length ?? 0) === 0 && (
              <p className="muted-line">Aucun EPUB offline.</p>
            )}
          </div>
          {localMessage && (
            <p className="notice success">
              <Check size={16} aria-hidden="true" />
              {localMessage}
            </p>
          )}
        </section>

        <section className="settings-section">
          <div className="metadata-heading">
            <HardDrive size={18} aria-hidden="true" />
            <h2>Import</h2>
          </div>
          <button className="primary-action wide" onClick={() => void handleScan()} disabled={scanBusy}>
            {scanBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <RefreshCw size={18} aria-hidden="true" />}
            Scanner incoming
          </button>
          {scanResult && (
            <div className="stat-grid">
              <div>
                <span>Scannes</span>
                <strong>{scanResult.scanned}</strong>
              </div>
              <div>
                <span>Importes</span>
                <strong>{scanResult.imported}</strong>
              </div>
              <div>
                <span>Warnings</span>
                <strong>{scanResult.warnings}</strong>
              </div>
              <div>
                <span>Failed</span>
                <strong>{scanResult.failed}</strong>
              </div>
            </div>
          )}
          <div className="maintenance-list">
            {(jobs.data?.items ?? []).map((job) => (
              <div key={job.id} className={`maintenance-row ${job.status}`}>
                <div>
                  <strong>{job.filename ?? job.file_path ?? "EPUB"}</strong>
                  <span>{job.status}</span>
                </div>
                {job.error_message && (
                  <p>
                    <AlertCircle size={14} aria-hidden="true" />
                    {job.error_message}
                  </p>
                )}
              </div>
            ))}
            {!jobs.isLoading && (jobs.data?.items.length ?? 0) === 0 && (
              <p className="muted-line">Aucun import.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

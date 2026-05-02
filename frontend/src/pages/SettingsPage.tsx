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
  Shield,
  Sparkles,
  Trash2,
  Upload,
  Wifi
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  apiFetch,
  autoApplyBookMetadata,
  getAppSettings,
  getSystemSettings,
  listPendingMetadataBooks,
  updateAppSettings,
  type AppSettingsValues,
  type ImportBatchListResponse,
  type MetadataLibraryAutoApplyItem,
  type MetadataLibraryAutoApplyResponse,
  type MetadataPendingBook,
} from "../lib/api";
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

type MetadataProgress = {
  index: number;
  total: number;
  book: MetadataPendingBook;
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

function metadataRowClass(status: MetadataLibraryAutoApplyItem["status"]) {
  if (status === "applied") {
    return "maintenance-row success";
  }
  if (status === "needs_review") {
    return "maintenance-row warning";
  }
  if (status === "error") {
    return "maintenance-row failed";
  }
  return "maintenance-row";
}

function formatScore(score: number | null) {
  return score === null ? "" : `${Math.round(score * 100)}%`;
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
        <Link className="settings-link" to="/admin/library">
          <Shield size={19} aria-hidden="true" />
          Admin bibliotheque
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
  const [settingsDraft, setSettingsDraft] = useState<Partial<AppSettingsValues>>({});
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [settingsMessage, setSettingsMessage] = useState<string | null>(null);
  const [metadataResult, setMetadataResult] = useState<MetadataLibraryAutoApplyResponse | null>(null);
  const [metadataBusy, setMetadataBusy] = useState(false);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [metadataProgress, setMetadataProgress] = useState<MetadataProgress | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localMessage, setLocalMessage] = useState<string | null>(null);

  const health = useQuery({
    queryKey: ["advanced", "health"],
    queryFn: () => apiFetch<{ status: string; app: string }>("/health"),
    refetchInterval: 30_000
  });

  const jobs = useQuery({
    queryKey: ["advanced", "import-jobs"],
    queryFn: () => apiFetch<ImportBatchListResponse>("/jobs?limit=6"),
    refetchInterval: 45_000
  });

  const appSettings = useQuery({
    queryKey: ["settings", "app"],
    queryFn: getAppSettings
  });

  const systemSettings = useQuery({
    queryKey: ["settings", "system"],
    queryFn: getSystemSettings
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

  useEffect(() => {
    if (appSettings.data?.values) {
      setSettingsDraft(appSettings.data.values);
    }
  }, [appSettings.data?.values]);

  async function handleSaveSettings() {
    setSettingsBusy(true);
    setSettingsMessage(null);
    try {
      await updateAppSettings(settingsDraft);
      setSettingsMessage("Settings sauvegardes.");
      await queryClient.invalidateQueries({ queryKey: ["settings", "app"] });
    } finally {
      setSettingsBusy(false);
    }
  }

  async function handleLibraryMetadataAuto() {
    setMetadataBusy(true);
    setMetadataResult(null);
    setMetadataError(null);
    setMetadataProgress(null);
    try {
      const pending = await listPendingMetadataBooks();
      const summary: MetadataLibraryAutoApplyResponse = {
        scanned: pending.items.length,
        applied: 0,
        needs_review: 0,
        no_match: 0,
        skipped: Math.max(pending.total - pending.items.length, 0),
        errors: 0,
        items: []
      };
      setMetadataResult(summary);

      for (const [index, book] of pending.items.entries()) {
        setMetadataProgress({ index: index + 1, total: pending.total, book });
        try {
          const result = await autoApplyBookMetadata(book.id, {});
          const item: MetadataLibraryAutoApplyItem = {
            book_id: book.id,
            title: result.book?.title ?? book.title,
            status: result.status,
            message: result.message,
            candidate_title: result.candidate?.title ?? null,
            candidate_provider_id: result.candidate?.provider_item_id ?? null,
            score: result.candidate?.score ?? null,
            applied_fields: result.applied_fields
          };
          if (result.status === "applied") {
            summary.applied += 1;
          } else if (result.status === "needs_review") {
            summary.needs_review += 1;
          } else {
            summary.no_match += 1;
          }
          summary.items = [item, ...summary.items].slice(0, 12);
          setMetadataResult({ ...summary });
        } catch (error) {
          const item: MetadataLibraryAutoApplyItem = {
            book_id: book.id,
            title: book.title,
            status: "error",
            message: error instanceof Error ? error.message : "Erreur inconnue",
            candidate_title: null,
            candidate_provider_id: null,
            score: null,
            applied_fields: []
          };
          summary.errors += 1;
          summary.items = [item, ...summary.items].slice(0, 12);
          setMetadataResult({ ...summary });
        }
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["books"] }),
        queryClient.invalidateQueries({ queryKey: ["organization", "tags"] })
      ]);
    } catch (error) {
      setMetadataError(error instanceof Error ? error.message : "Enrichissement impossible");
    } finally {
      setMetadataProgress(null);
      setMetadataBusy(false);
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
  const system = systemSettings.data;

  function updateDraft<K extends keyof AppSettingsValues>(key: K, value: AppSettingsValues[K]) {
    setSettingsDraft((current) => ({ ...current, [key]: value }));
  }

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
            <h2>Settings serveur</h2>
          </div>
          <div className="settings-grid">
            <label>
              <span>Upload max MB</span>
              <input
                type="number"
                value={settingsDraft.max_upload_size_mb ?? ""}
                onChange={(event) => updateDraft("max_upload_size_mb", Number(event.target.value))}
              />
            </label>
            <label>
              <span>Fichiers par batch</span>
              <input
                type="number"
                value={settingsDraft.import_max_files_per_batch ?? ""}
                onChange={(event) => updateDraft("import_max_files_per_batch", Number(event.target.value))}
              />
            </label>
            <label>
              <span>Worker</span>
              <input
                type="number"
                value={settingsDraft.import_worker_concurrency ?? ""}
                onChange={(event) => updateDraft("import_worker_concurrency", Number(event.target.value))}
              />
            </label>
            <label>
              <span>Corbeille h</span>
              <input
                type="number"
                value={settingsDraft.trash_retention_hours ?? ""}
                onChange={(event) => updateDraft("trash_retention_hours", Number(event.target.value))}
              />
            </label>
          </div>
          <div className="settings-toggle-grid">
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={Boolean(settingsDraft.metadata_googlebooks_enabled)}
                onChange={(event) => updateDraft("metadata_googlebooks_enabled", event.target.checked)}
              />
              <span>Google Books</span>
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={Boolean(settingsDraft.metadata_openlibrary_enabled)}
                onChange={(event) => updateDraft("metadata_openlibrary_enabled", event.target.checked)}
              />
              <span>Open Library</span>
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={Boolean(settingsDraft.metadata_auto_enrich_on_import)}
                onChange={(event) => updateDraft("metadata_auto_enrich_on_import", event.target.checked)}
              />
              <span>Auto metadata import</span>
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={Boolean(settingsDraft.trash_auto_purge_enabled)}
                onChange={(event) => updateDraft("trash_auto_purge_enabled", event.target.checked)}
              />
              <span>Purge auto</span>
            </label>
          </div>
          <button className="primary-action wide" onClick={() => void handleSaveSettings()} disabled={settingsBusy}>
            {settingsBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <RefreshCw size={18} aria-hidden="true" />}
            Sauver settings
          </button>
          {settingsMessage && (
            <p className="notice success">
              <Check size={16} aria-hidden="true" />
              {settingsMessage}
            </p>
          )}
          <div className="stat-grid">
            <div>
              <span>ENV</span>
              <strong>{system?.app_env ?? "..."}</strong>
            </div>
            <div>
              <span>Setup token</span>
              <strong>{system?.setup_token_configured ? "oui" : "non"}</strong>
            </div>
            <div>
              <span>DB</span>
              <strong>{system?.database_url_configured ? "config" : "missing"}</strong>
            </div>
            <div>
              <span>Secret</span>
              <strong>{system?.secret_key_configured ? "config" : "default"}</strong>
            </div>
          </div>
        </section>

        <section className="settings-section">
          <div className="metadata-heading">
            <HardDrive size={18} aria-hidden="true" />
            <h2>File import</h2>
          </div>
          <div className="maintenance-list">
            {(jobs.data?.items ?? []).map((job) => (
              <div key={job.id} className={`maintenance-row ${job.status}`}>
                <div>
                  <strong>{job.message ?? "Import EPUB"}</strong>
                  <span>{job.status} - {Math.round(job.progress_percent)}%</span>
                </div>
                <p>
                  <span>{job.processed_items}/{job.total_items}</span>
                  <span>{job.success_count} ok, {job.warning_count} warning, {job.failed_count} failed</span>
                </p>
              </div>
            ))}
            {!jobs.isLoading && (jobs.data?.items.length ?? 0) === 0 && (
              <p className="muted-line">Aucun import.</p>
            )}
          </div>
        </section>

        <section className="settings-section">
          <div className="metadata-heading">
            <Sparkles size={18} aria-hidden="true" />
            <h2>Metadonnees</h2>
          </div>
          <button
            className="primary-action wide"
            onClick={() => void handleLibraryMetadataAuto()}
            disabled={metadataBusy}
          >
            {metadataBusy ? (
              <Loader2 className="spin" size={18} aria-hidden="true" />
            ) : (
              <Sparkles size={18} aria-hidden="true" />
            )}
            Enrichir toute la bibliotheque
          </button>
          {metadataBusy && (
            <p className="notice pending">
              <Loader2 className="spin" size={16} aria-hidden="true" />
              {metadataProgress
                ? `Livre ${metadataProgress.index}/${metadataProgress.total} - ${metadataProgress.book.title}`
                : "Preparation de la liste des livres..."}
            </p>
          )}
          {metadataResult && (
            <div className="stat-grid">
              <div>
                <span>Scannes</span>
                <strong>{metadataResult.scanned}</strong>
              </div>
              <div>
                <span>Appliques</span>
                <strong>{metadataResult.applied}</strong>
              </div>
              <div>
                <span>A verifier</span>
                <strong>{metadataResult.needs_review}</strong>
              </div>
              <div>
                <span>Sans match</span>
                <strong>{metadataResult.no_match}</strong>
              </div>
              <div>
                <span>Erreurs</span>
                <strong>{metadataResult.errors}</strong>
              </div>
            </div>
          )}
          {metadataError && (
            <p className="notice error">
              <AlertCircle size={16} aria-hidden="true" />
              {metadataError}
            </p>
          )}
          {metadataResult && metadataResult.items.length > 0 && (
            <div className="maintenance-list">
              {metadataResult.items.slice(0, 8).map((item) => (
                <div key={item.book_id} className={metadataRowClass(item.status)}>
                  <div>
                    <strong>{item.title}</strong>
                    <span>{item.status}</span>
                  </div>
                  <p>
                    {item.candidate_title ? (
                      <>
                        <span>{item.candidate_title}</span>
                        <span>{formatScore(item.score)}</span>
                      </>
                    ) : (
                      <span>{item.message}</span>
                    )}
                    {item.status !== "applied" && (
                      <Link className="metadata-review-link" to={`/books/${item.book_id}`}>
                        Revoir
                      </Link>
                    )}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

import {
  ArrowLeft,
  Bookmark,
  BookmarkPlus,
  Check,
  ChevronLeft,
  ChevronRight,
  Columns2,
  ListTree,
  Loader2,
  Settings,
  Trash2,
  X
} from "lucide-react";
import type { Book, Location as EpubLocation, NavItem, Rendition } from "epubjs";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  apiBlob,
  apiFetch,
  getReadingSettings,
  listBookBookmarks,
  updateReadingSettings,
  type BookmarkItem,
  type BookDetail,
  type ReadingProgress,
  type ReadingSettings as ServerReadingSettings,
  type ReadingSettingsUpdate
} from "../lib/api";
import { db, type LocalBookmark, type LocalReadingProgress } from "../lib/db";
import { getOfflineBookDetail } from "../lib/offline";
import { enqueueSyncEvent } from "../lib/sync";
import { useSyncState } from "../providers/SyncProvider";

type ReaderMode = "paged" | "scroll";

type ReaderSettings = {
  mode: ReaderMode;
  fontSize: number;
  lineHeight: number;
  margin: number;
  fontFamily: string;
};

type CachedReaderSettings = Partial<ReaderSettings> & {
  dirty?: boolean;
  local_updated_at?: string;
  server_updated_at?: string;
};

type TocEntry = NavItem & {
  depth: number;
};

type ReaderPosition = {
  cfi: string;
  progressPercent: number;
  chapterLabel?: string;
  chapterHref?: string;
  locationJson: Record<string, unknown>;
};

const DEVICE_ID = "android-pwa";
const SETTINGS_KEY = "reader_settings";
const DEFAULT_SETTINGS: ReaderSettings = {
  mode: "paged",
  fontSize: 108,
  lineHeight: 1.7,
  margin: 24,
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
};

const fontOptions = [
  {
    label: "System",
    value: DEFAULT_SETTINGS.fontFamily
  },
  {
    label: "Serif",
    value: 'Georgia, "Times New Roman", serif'
  },
  {
    label: "Focus",
    value: '"Atkinson Hyperlegible", Inter, ui-sans-serif, system-ui, sans-serif'
  }
];

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function readerSettingsFromCache(value: unknown): { settings: ReaderSettings; dirty: boolean } | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const cached = value as CachedReaderSettings;
  return {
    settings: {
      mode: cached.mode === "scroll" ? "scroll" : "paged",
      fontSize: clamp(Number(cached.fontSize) || DEFAULT_SETTINGS.fontSize, 86, 146),
      lineHeight: clamp(Number(cached.lineHeight) || DEFAULT_SETTINGS.lineHeight, 1.35, 2.2),
      margin: clamp(Number(cached.margin) || DEFAULT_SETTINGS.margin, 8, 56),
      fontFamily: typeof cached.fontFamily === "string" ? cached.fontFamily : DEFAULT_SETTINGS.fontFamily
    },
    dirty: Boolean(cached.dirty)
  };
}

async function cacheReaderSettings(settings: ReaderSettings, dirty: boolean, updatedAt = new Date().toISOString()) {
  await db.settings_cache.put({
    key: SETTINGS_KEY,
    value: {
      ...settings,
      dirty,
      local_updated_at: updatedAt,
      server_updated_at: dirty ? undefined : updatedAt
    },
    updated_at: updatedAt
  });
}

function serverToReaderSettings(settings: ServerReadingSettings): ReaderSettings {
  const fontSize = Math.round((settings.font_size / 18) * DEFAULT_SETTINGS.fontSize);
  return {
    mode: settings.reading_mode === "scroll" ? "scroll" : "paged",
    fontSize: clamp(fontSize, 86, 146),
    lineHeight: clamp(Number(settings.line_height) || DEFAULT_SETTINGS.lineHeight, 1.35, 2.2),
    margin: clamp(settings.margin_size, 8, 56),
    fontFamily: settings.font_family || DEFAULT_SETTINGS.fontFamily
  };
}

function readerToServerSettings(settings: ReaderSettings): ReadingSettingsUpdate {
  return {
    reader_theme: "black_gold",
    font_family: settings.fontFamily,
    font_size: clamp(Math.round((settings.fontSize / DEFAULT_SETTINGS.fontSize) * 18), 12, 36),
    line_height: Number(settings.lineHeight.toFixed(2)),
    margin_size: settings.margin,
    reading_mode: settings.mode
  };
}

function flattenToc(items: NavItem[], depth = 0): TocEntry[] {
  return items.flatMap((item) => [
    { ...item, depth },
    ...flattenToc(item.subitems ?? [], depth + 1)
  ]);
}

function normalizeHref(href?: string) {
  return ((href ?? "").split("#")[0] ?? "").replace(/^\.\//, "");
}

function findChapter(toc: TocEntry[], href?: string) {
  const normalized = normalizeHref(href);
  return toc.find((entry) => normalizeHref(entry.href) === normalized);
}

function percentFromDecimal(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const percent = value <= 1 ? value * 100 : value;
  return Math.round(Math.max(0, Math.min(100, percent)) * 10) / 10;
}

function progressPercentFor(book: Book, cfi: string, displayedPercentage?: number) {
  if (typeof displayedPercentage === "number") {
    return percentFromDecimal(displayedPercentage);
  }
  try {
    return percentFromDecimal(book.locations.percentageFromCfi(cfi));
  } catch {
    return 0;
  }
}

function hasProgress(progress: ReadingProgress | null) {
  return Boolean(progress?.cfi || progress?.progress_percent);
}

function localToProgress(progress: LocalReadingProgress): ReadingProgress {
  return {
    cfi: progress.cfi ?? null,
    progress_percent: progress.progress_percent ?? null,
    chapter_label: progress.chapter_label ?? null,
    chapter_href: progress.chapter_href ?? null,
    location_json:
      progress.location_json && typeof progress.location_json === "object"
        ? (progress.location_json as Record<string, unknown>)
        : null,
    device_id: DEVICE_ID,
    updated_at: progress.updated_at
  };
}

async function getInitialProgress(bookId: string) {
  const [local, server] = await Promise.all([
    db.reading_progress.get(bookId),
    apiFetch<ReadingProgress>(`/books/${bookId}/progress`).catch(() => null)
  ]);
  const localProgress = local ? localToProgress(local) : null;
  const localTime = localProgress?.updated_at ? Date.parse(localProgress.updated_at) : 0;
  const serverTime = server?.updated_at ? Date.parse(server.updated_at) : 0;

  if (hasProgress(localProgress) && localTime >= serverTime) {
    return localProgress;
  }

  if (hasProgress(server)) {
    await db.reading_progress.put({
      book_id: bookId,
      cfi: server?.cfi ?? undefined,
      progress_percent: server?.progress_percent ?? undefined,
      chapter_label: server?.chapter_label ?? undefined,
      chapter_href: server?.chapter_href ?? undefined,
      location_json: server?.location_json ?? undefined,
      updated_at: server?.updated_at ?? new Date().toISOString(),
      dirty: false
    });
    return server;
  }

  return localProgress;
}

async function loadEpubBlob(bookId: string) {
  const offlineBook = await db.offline_books.get(bookId);
  if (offlineBook?.epub_blob) {
    return { blob: offlineBook.epub_blob, source: "offline" as const };
  }
  if (!navigator.onLine) {
    throw new Error("EPUB non telecharge. Reconnecte le reseau pour l'ouvrir ou telecharge-le offline depuis sa fiche.");
  }
  try {
    return { blob: await apiBlob(`/books/${bookId}/file`), source: "network" as const };
  } catch (caught) {
    if (!navigator.onLine) {
      throw new Error("EPUB non telecharge. Reconnecte le reseau pour l'ouvrir ou telecharge-le offline depuis sa fiche.");
    }
    throw caught;
  }
}

function buildReaderTheme(settings: ReaderSettings) {
  return {
    body: {
      background: "#030303 !important",
      color: "#f5f1e8 !important",
      "font-family": `${settings.fontFamily} !important`,
      "line-height": `${settings.lineHeight} !important`,
      "padding-left": `${settings.margin}px !important`,
      "padding-right": `${settings.margin}px !important`
    },
    "p, li": {
      "font-size": "1em !important",
      "line-height": `${settings.lineHeight} !important`
    },
    "h1, h2, h3, h4": {
      color: "#ffd966 !important",
      "letter-spacing": "0 !important"
    },
    a: {
      color: "#f5c542 !important"
    },
    "::selection": {
      background: "rgba(245, 197, 66, 0.3) !important"
    }
  };
}

function applyReaderTheme(rendition: Rendition, settings: ReaderSettings) {
  rendition.themes.register("aurelia", buildReaderTheme(settings));
  rendition.themes.select("aurelia");
  rendition.themes.font(settings.fontFamily);
  rendition.themes.fontSize(`${settings.fontSize}%`);
  rendition.themes.override("line-height", String(settings.lineHeight), true);
}

function destroyRendition(rendition: Rendition | null) {
  try {
    rendition?.destroy();
  } catch {
    // epub.js can throw during React StrictMode cleanup while a rendition is still booting.
  }
}

function destroyBook(book: Book | null) {
  try {
    book?.destroy();
  } catch {
    // epub.js can throw during React StrictMode cleanup while a book is still booting.
  }
}

function scheduleDestroyRendition(rendition: Rendition | null) {
  window.setTimeout(() => destroyRendition(rendition), 4000);
}

function scheduleDestroyBook(book: Book | null) {
  window.setTimeout(() => destroyBook(book), 4000);
}

async function persistReaderPosition(bookId: string, position: ReaderPosition) {
  const now = new Date().toISOString();
  await db.reading_progress.put({
    book_id: bookId,
    cfi: position.cfi,
    progress_percent: position.progressPercent,
    chapter_label: position.chapterLabel,
    chapter_href: position.chapterHref,
    location_json: position.locationJson,
    updated_at: now,
    dirty: true
  });
  await enqueueSyncEvent({
    event_id: crypto.randomUUID(),
    type: "progress.updated",
    payload: {
      book_id: bookId,
      cfi: position.cfi,
      progress_percent: position.progressPercent,
      chapter_label: position.chapterLabel,
      chapter_href: position.chapterHref,
      location_json: position.locationJson,
      device_id: DEVICE_ID,
      client_updated_at: now
    },
    created_at: now,
    retry_count: 0,
    status: "pending"
  });
}

function timeValue(value?: string | null) {
  return value ? Date.parse(value) || 0 : 0;
}

function serverBookmarkToLocal(bookmark: BookmarkItem): LocalBookmark {
  return {
    id: bookmark.id,
    book_id: bookmark.book_id,
    cfi: bookmark.cfi,
    progress_percent: bookmark.progress_percent ?? undefined,
    chapter_label: bookmark.chapter_label ?? undefined,
    excerpt: bookmark.excerpt ?? undefined,
    note: bookmark.note ?? undefined,
    created_at: bookmark.created_at,
    updated_at: bookmark.updated_at,
    dirty: false,
    deleted: Boolean(bookmark.deleted_at)
  };
}

function sortBookmarks(bookmarks: LocalBookmark[]) {
  return [...bookmarks].sort((left, right) => {
    const leftProgress = left.progress_percent ?? Number.POSITIVE_INFINITY;
    const rightProgress = right.progress_percent ?? Number.POSITIVE_INFINITY;
    if (leftProgress !== rightProgress) {
      return leftProgress - rightProgress;
    }
    return timeValue(left.created_at) - timeValue(right.created_at);
  });
}

async function refreshReaderBookmarks(bookId: string) {
  if (navigator.onLine) {
    const serverBookmarks = await listBookBookmarks(bookId).catch(() => null);
    if (serverBookmarks) {
      await Promise.all(
        serverBookmarks.items.map(async (bookmark) => {
          const local = await db.bookmarks.get(bookmark.id);
          if (local?.dirty && timeValue(local.updated_at) > timeValue(bookmark.updated_at)) {
            return;
          }
          await db.bookmarks.put(serverBookmarkToLocal(bookmark));
        })
      );
    }
  }
  const localBookmarks = await db.bookmarks.where("book_id").equals(bookId).toArray();
  return sortBookmarks(localBookmarks.filter((bookmark) => !bookmark.deleted));
}

export function ReaderPage() {
  const { bookId } = useParams();
  const { flush } = useSyncState();
  const viewerRef = useRef<HTMLDivElement | null>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const bookRef = useRef<Book | null>(null);
  const flushRef = useRef(flush);
  const saveTimerRef = useRef<number | null>(null);
  const settingsSaveTimerRef = useRef<number | null>(null);
  const skipNextSettingsSaveRef = useRef(true);
  const latestPositionRef = useRef<ReaderPosition | null>(null);
  const lastSavedCfiRef = useRef<string | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<ReaderSettings>(DEFAULT_SETTINGS);
  const [settingsReady, setSettingsReady] = useState(false);
  const [toc, setToc] = useState<TocEntry[]>([]);
  const [bookmarks, setBookmarks] = useState<LocalBookmark[]>([]);
  const [position, setPosition] = useState<ReaderPosition | null>(null);
  const [source, setSource] = useState<"network" | "offline">("network");
  const [showToc, setShowToc] = useState(false);
  const [showBookmarks, setShowBookmarks] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const { data: book } = useQuery({
    queryKey: ["book", bookId, "reader"],
    queryFn: async () => {
      if (!bookId) {
        throw new Error("Livre introuvable");
      }
      try {
        return await apiFetch<BookDetail>(`/books/${bookId}`);
      } catch (caught) {
        const offlineBook = await getOfflineBookDetail(bookId);
        if (offlineBook) {
          return offlineBook;
        }
        throw caught;
      }
    },
    enabled: Boolean(bookId)
  });

  const progressLabel = useMemo(() => {
    const value = position?.progressPercent ?? book?.progress_percent ?? 0;
    return `${Math.round(value)}%`;
  }, [book?.progress_percent, position?.progressPercent]);

  useEffect(() => {
    flushRef.current = flush;
  }, [flush]);

  useEffect(() => {
    if (!bookId) {
      return;
    }
    let alive = true;
    const refresh = () => {
      void refreshReaderBookmarks(bookId).then((items) => {
        if (alive) {
          setBookmarks(items);
        }
      });
    };
    refresh();
    window.addEventListener("online", refresh);
    return () => {
      alive = false;
      window.removeEventListener("online", refresh);
    };
  }, [bookId]);

  useEffect(() => {
    let alive = true;
    async function hydrateSettings() {
      let nextSettings = DEFAULT_SETTINGS;
      let settingsDirty = false;
      const cached = await db.settings_cache.get(SETTINGS_KEY);
      const cachedSettings = readerSettingsFromCache(cached?.value);
      if (cachedSettings) {
        nextSettings = cachedSettings.settings;
        settingsDirty = cachedSettings.dirty;
      }

      if (navigator.onLine) {
        if (settingsDirty) {
          const pushedSettings = await updateReadingSettings(readerToServerSettings(nextSettings)).catch(() => null);
          if (pushedSettings) {
            nextSettings = serverToReaderSettings(pushedSettings);
            settingsDirty = false;
            await cacheReaderSettings(nextSettings, false, pushedSettings.updated_at);
          }
        } else {
          const serverSettings = await getReadingSettings().catch(() => null);
          if (serverSettings) {
            nextSettings = serverToReaderSettings(serverSettings);
            await cacheReaderSettings(nextSettings, false, serverSettings.updated_at);
          }
        }
      }

      if (!alive) {
        return;
      }
      skipNextSettingsSaveRef.current = true;
      setSettings(nextSettings);
      setSettingsReady(true);
    }

    void hydrateSettings().catch(() => {
      if (alive) {
        setSettingsReady(true);
      }
    });

    return () => {
      alive = false;
      if (settingsSaveTimerRef.current) {
        window.clearTimeout(settingsSaveTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!settingsReady) {
      return;
    }
    const syncCurrentSettings = () => {
      if (!navigator.onLine) {
        return;
      }
      void updateReadingSettings(readerToServerSettings(settings))
        .then((serverSettings) => cacheReaderSettings(serverToReaderSettings(serverSettings), false, serverSettings.updated_at))
        .catch(() => undefined);
    };
    window.addEventListener("online", syncCurrentSettings);
    return () => window.removeEventListener("online", syncCurrentSettings);
  }, [settings, settingsReady]);

  useEffect(() => {
    if (!settingsReady) {
      return;
    }
    const updatedAt = new Date().toISOString();
    void cacheReaderSettings(settings, !navigator.onLine, updatedAt);
    if (renditionRef.current) {
      applyReaderTheme(renditionRef.current, settings);
    }
    if (skipNextSettingsSaveRef.current) {
      skipNextSettingsSaveRef.current = false;
      return;
    }
    if (!navigator.onLine) {
      return;
    }
    if (settingsSaveTimerRef.current) {
      window.clearTimeout(settingsSaveTimerRef.current);
    }
    settingsSaveTimerRef.current = window.setTimeout(() => {
      void updateReadingSettings(readerToServerSettings(settings))
        .then((serverSettings) => cacheReaderSettings(serverToReaderSettings(serverSettings), false, serverSettings.updated_at))
        .catch(() => cacheReaderSettings(settings, true));
    }, 800);
    return () => {
      if (settingsSaveTimerRef.current) {
        window.clearTimeout(settingsSaveTimerRef.current);
      }
    };
  }, [settings, settingsReady]);

  useEffect(() => {
    if (!bookId || !viewerRef.current || !settingsReady) {
      return;
    }

    const currentBookId = bookId;
    let cancelled = false;
    let activeBook: Book | null = null;
    let activeRendition: Rendition | null = null;
    const viewer = viewerRef.current;
    setStatus("loading");
    setError(null);
    setToc([]);
    setPosition(null);
    latestPositionRef.current = null;
    lastSavedCfiRef.current = null;
    viewer.replaceChildren();

    const scheduleSave = (nextPosition: ReaderPosition) => {
      latestPositionRef.current = nextPosition;
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
      saveTimerRef.current = window.setTimeout(() => {
        const pendingPosition = latestPositionRef.current;
        if (!pendingPosition || pendingPosition.cfi === lastSavedCfiRef.current) {
          return;
        }
        lastSavedCfiRef.current = pendingPosition.cfi;
        void persistReaderPosition(currentBookId, pendingPosition).then(() => {
          if (navigator.onLine) {
            void flushRef.current();
          }
        });
      }, 900);
    };

    async function setupReader() {
      try {
        const [initialProgress, epubFile] = await Promise.all([
          getInitialProgress(currentBookId),
          loadEpubBlob(currentBookId)
        ]);
        if (cancelled) {
          return;
        }

        setSource(epubFile.source);
        const buffer = await epubFile.blob.arrayBuffer();
        if (cancelled) {
          return;
        }

        const { default: ePub } = await import("epubjs");
        const nextBook = ePub(buffer);
        activeBook = nextBook;
        bookRef.current = nextBook;
        await nextBook.ready;

        const nextToc = flattenToc(
          await nextBook.loaded.navigation.then((navigation) => navigation.toc).catch(() => [])
        );
        if (cancelled) {
          if (bookRef.current === nextBook) {
            bookRef.current = null;
          }
          scheduleDestroyBook(nextBook);
          return;
        }
        setToc(nextToc);

        const rendition = nextBook.renderTo(viewer, {
          width: "100%",
          height: "100%",
          flow: settings.mode === "scroll" ? "scrolled-doc" : "paginated",
          manager: settings.mode === "scroll" ? "continuous" : "default",
          spread: "none"
        });
        activeRendition = rendition;
        renditionRef.current = rendition;
        applyReaderTheme(rendition, settings);
        rendition.on("relocated", (location: EpubLocation) => {
          const start = location.start;
          const cfi = start.cfi;
          const chapter = findChapter(nextToc, start.href);
          const progressPercent = progressPercentFor(nextBook, cfi, start.percentage);
          const nextPosition: ReaderPosition = {
            cfi,
            progressPercent,
            chapterLabel: chapter?.label,
            chapterHref: start.href,
            locationJson: {
              at_start: location.atStart,
              at_end: location.atEnd,
              displayed_page: start.displayed?.page,
              displayed_total: start.displayed?.total,
              href: start.href,
              index: start.index,
              location: start.location
            }
          };
          setPosition(nextPosition);
          scheduleSave(nextPosition);
        });

        try {
          await rendition.display(initialProgress?.cfi ?? undefined);
        } catch {
          await rendition.display();
        }
        if (!cancelled) {
          setStatus("ready");
          void nextBook.locations
            .generate(1500)
            .then(() =>
              !cancelled && renditionRef.current === rendition
                ? rendition.reportLocation()
                : undefined
            )
            .catch(() => undefined);
        }
      } catch (readerError) {
        if (!cancelled) {
          setStatus("error");
          setError(readerError instanceof Error ? readerError.message : "Lecture impossible");
        }
      }
    }

    void setupReader();

    return () => {
      cancelled = true;
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
      const pendingPosition = latestPositionRef.current;
      if (pendingPosition && pendingPosition.cfi !== lastSavedCfiRef.current) {
        void persistReaderPosition(currentBookId, pendingPosition);
      }
      if (renditionRef.current === activeRendition) {
        renditionRef.current = null;
      }
      if (bookRef.current === activeBook) {
        bookRef.current = null;
      }
      viewer.replaceChildren();
      scheduleDestroyRendition(activeRendition);
      scheduleDestroyBook(activeBook);
    };
  }, [bookId, settings.mode, settingsReady]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!bookId || !document.hidden || !latestPositionRef.current) {
        return;
      }
      void persistReaderPosition(bookId, latestPositionRef.current).then(() => {
        if (navigator.onLine) {
          void flushRef.current();
        }
      });
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [bookId]);

  async function goPrevious() {
    await renditionRef.current?.prev();
  }

  async function goNext() {
    await renditionRef.current?.next();
  }

  async function displayTocItem(item: TocEntry) {
    await renditionRef.current?.display(item.href);
    setShowToc(false);
  }

  async function displayBookmark(bookmark: LocalBookmark) {
    await renditionRef.current?.display(bookmark.cfi);
    setShowBookmarks(false);
  }

  async function addBookmark() {
    if (!bookId || !latestPositionRef.current) {
      return;
    }
    const bookmarkId = crypto.randomUUID();
    const now = new Date().toISOString();
    const bookmark = {
      id: bookmarkId,
      book_id: bookId,
      cfi: latestPositionRef.current.cfi,
      progress_percent: latestPositionRef.current.progressPercent,
      chapter_label: latestPositionRef.current.chapterLabel,
      created_at: now,
      updated_at: now,
      dirty: true,
      deleted: false
    };
    await db.bookmarks.put(bookmark);
    await enqueueSyncEvent({
      event_id: crypto.randomUUID(),
      type: "bookmark.created",
      payload: bookmark,
      created_at: now,
      retry_count: 0,
      status: "pending"
    });
    setBookmarks(await refreshReaderBookmarks(bookId));
    setToast("Marque-page sauvegarde");
    window.setTimeout(() => setToast(null), 1800);
    if (navigator.onLine) {
      void flushRef.current();
    }
  }

  async function removeBookmark(bookmark: LocalBookmark) {
    if (!bookId) {
      return;
    }
    const now = new Date().toISOString();
    await db.bookmarks.update(bookmark.id, {
      dirty: true,
      deleted: true,
      updated_at: now
    });
    await enqueueSyncEvent({
      event_id: crypto.randomUUID(),
      type: "bookmark.deleted",
      payload: {
        id: bookmark.id,
        book_id: bookmark.book_id,
        updated_at: now,
        client_updated_at: now
      },
      created_at: now,
      retry_count: 0,
      status: "pending"
    });
    setBookmarks(await refreshReaderBookmarks(bookId));
    setToast("Marque-page supprime");
    window.setTimeout(() => setToast(null), 1800);
    if (navigator.onLine) {
      void flushRef.current();
    }
  }

  return (
    <main className="reader-page">
      <header className="reader-topbar">
        <Link to={bookId ? `/books/${bookId}` : "/library"} aria-label="Retour" className="icon-button">
          <ArrowLeft size={20} aria-hidden="true" />
        </Link>
        <div className="reader-title">
          <span>{book?.title ?? "Aurelia Reader"}</span>
          <small>{source === "offline" ? "Offline" : status}</small>
        </div>
        <div className="icon-group">
          <button
            aria-label="Table des matieres"
            className={showToc ? "icon-button active" : "icon-button"}
            onClick={() => {
              setShowToc((value) => !value);
              setShowBookmarks(false);
              setShowSettings(false);
            }}
          >
            <ListTree size={19} aria-hidden="true" />
          </button>
          <button
            aria-label="Marque-pages"
            className={showBookmarks ? "icon-button active" : "icon-button"}
            onClick={() => {
              setShowBookmarks((value) => !value);
              setShowToc(false);
              setShowSettings(false);
            }}
          >
            <Bookmark size={19} aria-hidden="true" />
          </button>
          <button aria-label="Ajouter un marque-page" className="icon-button" onClick={() => void addBookmark()}>
            <BookmarkPlus size={19} aria-hidden="true" />
          </button>
          <button
            aria-label="Reglages"
            className={showSettings ? "icon-button active" : "icon-button"}
            onClick={() => {
              setShowSettings((value) => !value);
              setShowToc(false);
              setShowBookmarks(false);
            }}
          >
            <Settings size={19} aria-hidden="true" />
          </button>
        </div>
      </header>

      <section className="reader-stage">
        <div ref={viewerRef} className="reader-viewer" />
        {status === "loading" && (
          <div className="reader-overlay">
            <Loader2 className="spin" size={24} aria-hidden="true" />
            <span>Chargement EPUB</span>
          </div>
        )}
        {status === "error" && (
          <div className="reader-overlay error">
            <strong>Lecture impossible</strong>
            <span>{error}</span>
          </div>
        )}
      </section>

      {showToc && (
        <aside className="reader-panel" aria-label="Table des matieres">
          <div className="reader-panel-header">
            <strong>Chapitres</strong>
            <button className="icon-button" aria-label="Fermer" onClick={() => setShowToc(false)}>
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="toc-list">
            {toc.length > 0 ? (
              toc.map((item) => (
                <button
                  key={`${item.id}-${item.href}`}
                  style={{ paddingLeft: `${12 + item.depth * 16}px` }}
                  onClick={() => void displayTocItem(item)}
                >
                  {item.label}
                </button>
              ))
            ) : (
              <p className="muted-line">Aucune table des matieres.</p>
            )}
          </div>
        </aside>
      )}

      {showBookmarks && (
        <aside className="reader-panel" aria-label="Marque-pages">
          <div className="reader-panel-header">
            <strong>Marque-pages</strong>
            <button className="icon-button" aria-label="Fermer" onClick={() => setShowBookmarks(false)}>
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="bookmark-list">
            {bookmarks.length > 0 ? (
              bookmarks.map((bookmark) => (
                <div key={bookmark.id} className="bookmark-row">
                  <button onClick={() => void displayBookmark(bookmark)}>
                    <strong>{bookmark.chapter_label ?? "Position sauvegardee"}</strong>
                    <span>{Math.round(bookmark.progress_percent ?? 0)}%</span>
                  </button>
                  <button
                    className="icon-button compact-icon"
                    aria-label="Supprimer le marque-page"
                    onClick={() => void removeBookmark(bookmark)}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </div>
              ))
            ) : (
              <p className="muted-line">Aucun marque-page.</p>
            )}
          </div>
        </aside>
      )}

      {showSettings && (
        <aside className="reader-panel settings" aria-label="Reglages lecture">
          <div className="reader-panel-header">
            <strong>Lecture</strong>
            <button className="icon-button" aria-label="Fermer" onClick={() => setShowSettings(false)}>
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="segmented compact">
            <button
              className={settings.mode === "paged" ? "active" : ""}
              onClick={() => setSettings((current) => ({ ...current, mode: "paged" }))}
            >
              <Columns2 size={16} aria-hidden="true" />
              Pages
            </button>
            <button
              className={settings.mode === "scroll" ? "active" : ""}
              onClick={() => setSettings((current) => ({ ...current, mode: "scroll" }))}
            >
              <ListTree size={16} aria-hidden="true" />
              Scroll
            </button>
          </div>
          <label className="reader-setting">
            <span>Taille</span>
            <input
              type="range"
              min="86"
              max="146"
              value={settings.fontSize}
              onChange={(event) =>
                setSettings((current) => ({ ...current, fontSize: Number(event.target.value) }))
              }
            />
          </label>
          <label className="reader-setting">
            <span>Interligne</span>
            <input
              type="range"
              min="1.35"
              max="2.2"
              step="0.05"
              value={settings.lineHeight}
              onChange={(event) =>
                setSettings((current) => ({ ...current, lineHeight: Number(event.target.value) }))
              }
            />
          </label>
          <label className="reader-setting">
            <span>Marges</span>
            <input
              type="range"
              min="8"
              max="56"
              value={settings.margin}
              onChange={(event) =>
                setSettings((current) => ({ ...current, margin: Number(event.target.value) }))
              }
            />
          </label>
          <label className="reader-setting">
            <span>Police</span>
            <select
              value={settings.fontFamily}
              onChange={(event) =>
                setSettings((current) => ({ ...current, fontFamily: event.target.value }))
              }
            >
              {fontOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </aside>
      )}

      {toast && (
        <div className="reader-toast">
          <Check size={16} aria-hidden="true" />
          <span>{toast}</span>
        </div>
      )}

      <footer className="reader-controls">
        <button className="icon-button" aria-label="Page precedente" onClick={() => void goPrevious()}>
          <ChevronLeft size={22} aria-hidden="true" />
        </button>
        <div className="reader-progress-label">
          <strong>{progressLabel}</strong>
          <span>{position?.chapterLabel ?? book?.authors.join(", ") ?? "Lecture"}</span>
        </div>
        <button className="icon-button" aria-label="Page suivante" onClick={() => void goNext()}>
          <ChevronRight size={22} aria-hidden="true" />
        </button>
      </footer>
      <div className="reader-progress" aria-hidden="true">
        <span style={{ width: progressLabel }} />
      </div>
    </main>
  );
}

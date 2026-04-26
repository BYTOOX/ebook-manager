import Dexie, { type Table } from "dexie";
import type { BookDetail } from "./api";

export type OfflineBook = {
  book_id: string;
  title: string;
  authors: string[];
  cover_blob?: Blob;
  epub_blob?: Blob;
  metadata_snapshot?: BookDetail;
  downloaded_at: string;
  file_size?: number;
  version_hash?: string;
};

export type LocalReadingProgress = {
  book_id: string;
  cfi?: string;
  progress_percent?: number;
  chapter_label?: string;
  chapter_href?: string;
  location_json?: unknown;
  updated_at: string;
  dirty: boolean;
};

export type LocalBookmark = {
  id: string;
  book_id: string;
  cfi: string;
  progress_percent?: number;
  chapter_label?: string;
  excerpt?: string;
  note?: string;
  created_at: string;
  updated_at: string;
  dirty: boolean;
  deleted: boolean;
};

export type SyncEvent = {
  event_id: string;
  type: "progress.updated" | "bookmark.created" | "bookmark.deleted";
  payload: Record<string, unknown>;
  created_at: string;
  retry_count: number;
  status: "pending" | "syncing" | "failed";
};

export type SettingsCache = {
  key: string;
  value: unknown;
  updated_at: string;
};

class AureliaLocalDatabase extends Dexie {
  offline_books!: Table<OfflineBook, string>;
  reading_progress!: Table<LocalReadingProgress, string>;
  bookmarks!: Table<LocalBookmark, string>;
  sync_queue!: Table<SyncEvent, string>;
  settings_cache!: Table<SettingsCache, string>;

  constructor() {
    super("aurelia_local");
    this.version(1).stores({
      offline_books: "book_id, downloaded_at, version_hash",
      reading_progress: "book_id, updated_at, dirty",
      bookmarks: "id, book_id, dirty, deleted",
      sync_queue: "event_id, type, status, created_at",
      settings_cache: "key, updated_at"
    });
  }
}

export const db = new AureliaLocalDatabase();

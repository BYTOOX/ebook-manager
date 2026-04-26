import { apiFetch, type ReadingProgress } from "./api";
import { db, type LocalBookmark, type SyncEvent } from "./db";

type ServerBookmark = {
  id: string;
  book_id: string;
  cfi: string;
  progress_percent: number | null;
  chapter_label: string | null;
  excerpt: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

type ServerSyncEventResult = {
  event_id: string;
  type: SyncEvent["type"] | string;
  status: "processed" | "ignored" | "error" | string;
  resolved?: "client_won" | "server_won" | "ignored" | string | null;
  book_id?: string | null;
  progress?: ReadingProgress | null;
  bookmark?: ServerBookmark | null;
  error?: string | null;
};

type ServerSyncResponse = {
  ok: boolean;
  accepted: number;
  processed: number;
  results?: ServerSyncEventResult[];
};

export async function enqueueSyncEvent(event: SyncEvent) {
  if (event.type === "progress.updated" && typeof event.payload.book_id === "string") {
    const existing = await db.sync_queue
      .filter(
        (queued) =>
          queued.type === "progress.updated" &&
          (queued.status === "pending" || queued.status === "failed") &&
          queued.payload.book_id === event.payload.book_id
      )
      .first();

    if (existing) {
      await db.sync_queue.update(existing.event_id, {
        payload: event.payload,
        created_at: event.created_at,
        retry_count: existing.retry_count
      });
      return;
    }
  }

  await db.sync_queue.put(event);
}

function timeValue(value?: string | null) {
  return value ? Date.parse(value) || 0 : 0;
}

async function applyProgressResult(event: SyncEvent, result: ServerSyncEventResult) {
  if (!result.progress || typeof event.payload.book_id !== "string") {
    return;
  }

  const bookId = event.payload.book_id;
  const local = await db.reading_progress.get(bookId);
  const localTime = timeValue(local?.updated_at);
  const serverTime = timeValue(result.progress.updated_at);
  const eventTime = typeof event.payload.client_updated_at === "string"
    ? timeValue(event.payload.client_updated_at)
    : 0;

  if (result.resolved === "server_won" && serverTime >= localTime) {
    await db.reading_progress.put({
      book_id: bookId,
      cfi: result.progress.cfi ?? undefined,
      progress_percent: result.progress.progress_percent ?? undefined,
      chapter_label: result.progress.chapter_label ?? undefined,
      chapter_href: result.progress.chapter_href ?? undefined,
      location_json: result.progress.location_json ?? undefined,
      updated_at: result.progress.updated_at ?? new Date().toISOString(),
      dirty: false
    });
    return;
  }

  if (!local || local.updated_at === event.payload.client_updated_at || localTime <= eventTime) {
    await db.reading_progress.put({
      book_id: bookId,
      cfi: result.progress.cfi ?? undefined,
      progress_percent: result.progress.progress_percent ?? undefined,
      chapter_label: result.progress.chapter_label ?? undefined,
      chapter_href: result.progress.chapter_href ?? undefined,
      location_json: result.progress.location_json ?? undefined,
      updated_at: result.progress.updated_at ?? new Date().toISOString(),
      dirty: false
    });
  }
}

function serverBookmarkToLocal(bookmark: ServerBookmark): LocalBookmark {
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

async function applyBookmarkResult(event: SyncEvent, result: ServerSyncEventResult) {
  if (!result.bookmark) {
    return;
  }

  const local = await db.bookmarks.get(result.bookmark.id);
  const localTime = timeValue(local?.updated_at);
  const serverTime = timeValue(result.bookmark.updated_at);
  const eventTime = typeof event.payload.updated_at === "string"
    ? timeValue(event.payload.updated_at)
    : timeValue(event.created_at);

  if (result.resolved === "server_won" && serverTime >= localTime) {
    await db.bookmarks.put(serverBookmarkToLocal(result.bookmark));
    return;
  }

  if (!local || local.updated_at === event.payload.updated_at || localTime <= eventTime) {
    await db.bookmarks.put(serverBookmarkToLocal(result.bookmark));
  }
}

export async function flushSyncQueue(deviceId = "android-pwa") {
  if (!navigator.onLine) {
    return { synced: 0 };
  }

  const events = await db.sync_queue
    .filter((event) => event.status === "pending" || event.status === "failed")
    .limit(25)
    .toArray();
  if (events.length === 0) {
    return { synced: 0 };
  }

  const ids = events.map((event) => event.event_id);
  await db.sync_queue.bulkUpdate(ids.map((key) => ({ key, changes: { status: "syncing" } })));

  try {
    const response = await apiFetch<ServerSyncResponse>("/sync/events", {
      method: "POST",
      body: JSON.stringify({
        device_id: deviceId,
        events: events.map((event) => ({
          event_id: event.event_id,
          type: event.type,
          payload: event.payload,
          client_created_at: event.created_at
        }))
      })
    });

    if (response.ok) {
      const resultsByEventId = new Map((response.results ?? []).map((result) => [result.event_id, result]));
      const resolvedIds: string[] = [];
      await Promise.all(
        events.map(async (event) => {
          const result = resultsByEventId.get(event.event_id);
          if (!result) {
            return;
          }
          if (event.type === "progress.updated") {
            await applyProgressResult(event, result);
          }
          if (event.type === "bookmark.created" || event.type === "bookmark.deleted") {
            await applyBookmarkResult(event, result);
          }
          if (result.status === "processed" || result.status === "ignored") {
            resolvedIds.push(event.event_id);
          }
        })
      );
      const unresolvedEvents = events.filter((event) => !resolvedIds.includes(event.event_id));
      if (resolvedIds.length > 0) {
        await db.sync_queue.bulkDelete(resolvedIds);
      }
      if (unresolvedEvents.length > 0) {
        await db.sync_queue.bulkUpdate(
          unresolvedEvents.map((event) => ({
            key: event.event_id,
            changes: {
              status: "failed",
              retry_count: event.retry_count + 1
            }
          }))
        );
      }
      return { synced: response.accepted };
    }
    throw new Error("Sync rejected");
  } catch {
    await db.sync_queue.bulkUpdate(
      events.map((event) => ({
        key: event.event_id,
        changes: {
          status: "failed",
          retry_count: event.retry_count + 1
        }
      }))
    );
  }

  return { synced: 0 };
}

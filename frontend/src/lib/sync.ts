import { apiFetch } from "./api";
import { db, type SyncEvent } from "./db";

type ServerSyncResponse = {
  ok: boolean;
  accepted: number;
  processed: number;
};

export async function enqueueSyncEvent(event: SyncEvent) {
  if (event.type === "progress.updated" && typeof event.payload.book_id === "string") {
    const existing = await db.sync_queue
      .where("status")
      .equals("pending")
      .filter(
        (queued) =>
          queued.type === "progress.updated" &&
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

export async function flushSyncQueue(deviceId = "android-pwa") {
  if (!navigator.onLine) {
    return { synced: 0 };
  }

  const events = await db.sync_queue.where("status").equals("pending").limit(25).toArray();
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
      await db.sync_queue.bulkDelete(ids);
      return { synced: response.accepted };
    }
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

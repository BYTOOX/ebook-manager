package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.data.local.dao.SyncEventDao
import ch.bytoox.aureliareader.data.local.dao.ProgressDao
import ch.bytoox.aureliareader.data.local.entities.ProgressEntity
import ch.bytoox.aureliareader.data.local.entities.SyncEventEntity
import java.time.Instant
import java.util.UUID
import org.json.JSONObject

data class BookProgressSnapshot(
    val locatorJson: String,
    val progressPercent: Float,
    val chapterLabel: String?,
    val updatedAt: Long,
    val dirty: Boolean,
    val syncStatus: String,
    val syncError: String?
)

class ProgressRepository(
    private val progressDao: ProgressDao,
    private val syncEventDao: SyncEventDao
) {
    suspend fun allProgress(): Map<String, BookProgressSnapshot> {
        return progressDao.all().associate { entity ->
            entity.bookId to entity.toSnapshot()
        }
    }

    suspend fun progressForBook(bookId: String): BookProgressSnapshot? {
        return progressDao.progressByBookId(bookId)?.toSnapshot()
    }

    suspend fun saveProgress(
        bookId: String,
        locatorJson: String,
        progressPercent: Float,
        chapterLabel: String?
    ) {
        val now = System.currentTimeMillis()
        val currentProgress = progressDao.progressByBookId(bookId)
        val currentEvent = syncEventDao.eventForBook(bookId)
        val normalizedProgress = progressPercent.normalizedProgress()

        progressDao.upsert(
            ProgressEntity(
                bookId = bookId,
                locatorJson = locatorJson,
                progressPercent = normalizedProgress,
                chapterLabel = chapterLabel,
                updatedAt = now,
                dirty = true,
                syncStatus = "pending",
                lastSyncedAt = currentProgress?.lastSyncedAt,
                syncError = null
            )
        )
        syncEventDao.upsert(
            SyncEventEntity(
                bookId = bookId,
                eventId = currentEvent?.eventId ?: UUID.randomUUID().toString(),
                type = "progress.updated",
                payloadJson = progressPayloadJson(
                    bookId = bookId,
                    locatorJson = locatorJson,
                    progressPercent = normalizedProgress,
                    chapterLabel = chapterLabel,
                    updatedAt = now
                ),
                clientCreatedAt = currentEvent?.clientCreatedAt ?: now,
                updatedAt = now,
                attempts = currentEvent?.attempts ?: 0,
                status = "pending",
                lastError = null
            )
        )
    }

    private fun ProgressEntity.toSnapshot(): BookProgressSnapshot {
        return BookProgressSnapshot(
            locatorJson = locatorJson,
            progressPercent = progressPercent,
            chapterLabel = chapterLabel,
            updatedAt = updatedAt,
            dirty = dirty,
            syncStatus = syncStatus,
            syncError = syncError
        )
    }

    private fun progressPayloadJson(
        bookId: String,
        locatorJson: String,
        progressPercent: Float,
        chapterLabel: String?,
        updatedAt: Long
    ): String {
        val locator = runCatching { JSONObject(locatorJson) }.getOrDefault(JSONObject())
        val locations = locator.optJSONObject("locations")
        val cfi = locations?.optString("cfi")?.takeIf { it.isNotBlank() }
        val chapterHref = locator.optString("href").takeIf { it.isNotBlank() }

        return JSONObject()
            .put("book_id", bookId)
            .putNullable("cfi", cfi)
            .put("progress_percent", progressPercent)
            .putNullable("chapter_label", chapterLabel?.takeIf { it.isNotBlank() })
            .putNullable("chapter_href", chapterHref)
            .put("location_json", locator)
            .put("client_updated_at", Instant.ofEpochMilli(updatedAt).toString())
            .put("device_id", DEVICE_ID)
            .toString()
    }

    private fun JSONObject.putNullable(name: String, value: String?): JSONObject {
        return put(name, value ?: JSONObject.NULL)
    }

    private fun Float.normalizedProgress(): Float {
        val progress = coerceIn(0f, 100f)
        return if (progress >= 99f) 100f else progress
    }

    private companion object {
        const val DEVICE_ID = "android-reader"
    }
}

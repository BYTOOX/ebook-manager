package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.ApiException
import ch.bytoox.aureliareader.core.network.SyncEventResultDto
import ch.bytoox.aureliareader.core.network.SyncEventUploadDto
import ch.bytoox.aureliareader.data.local.dao.ProgressDao
import ch.bytoox.aureliareader.data.local.dao.SyncEventDao
import ch.bytoox.aureliareader.data.local.entities.SyncEventEntity
import java.io.IOException
import java.time.Instant

data class ProgressSyncSummary(
    val attempted: Int,
    val synced: Int,
    val failed: Int
)

class ProgressSyncRepository(
    private val apiClient: ApiClient,
    private val progressDao: ProgressDao,
    private val syncEventDao: SyncEventDao
) {
    suspend fun flushPending(serverUrl: String): ProgressSyncSummary {
        val events = syncEventDao.pending(limit = MAX_BATCH_SIZE)
        if (events.isEmpty()) {
            return ProgressSyncSummary(attempted = 0, synced = 0, failed = 0)
        }

        val api = apiClient.create(serverUrl)
        return if (events.size == 1) {
            flushSingleWithPut(api = api, event = events.single())
        } else {
            flushBatchWithSyncEvents(api = api, events = events)
        }
    }

    private suspend fun flushSingleWithPut(
        api: ch.bytoox.aureliareader.core.network.AureliaApi,
        event: SyncEventEntity
    ): ProgressSyncSummary {
        return try {
            val ok = api.putBookProgress(event.bookId, event.payloadJson)
            if (ok) {
                markSynced(event.bookId)
                ProgressSyncSummary(attempted = 1, synced = 1, failed = 0)
            } else {
                markFailed(event.bookId, "Progression refusee par le serveur.")
                ProgressSyncSummary(attempted = 1, synced = 0, failed = 1)
            }
        } catch (error: Throwable) {
            handleSyncFailure(event.bookId, error)
        }
    }

    private suspend fun flushBatchWithSyncEvents(
        api: ch.bytoox.aureliareader.core.network.AureliaApi,
        events: List<SyncEventEntity>
    ): ProgressSyncSummary {
        return try {
            val response = api.syncEvents(
                deviceId = DEVICE_ID,
                events = events.map { event ->
                    SyncEventUploadDto(
                        eventId = event.eventId,
                        type = event.type,
                        payloadJson = event.payloadJson,
                        clientCreatedAt = Instant.ofEpochMilli(event.clientCreatedAt).toString()
                    )
                }
            )
            val resultsById = response.results.associateBy(SyncEventResultDto::eventId)
            var synced = 0
            var failed = 0

            events.forEach { event ->
                val result = resultsById[event.eventId]
                if (result?.status == "processed") {
                    markSynced(event.bookId)
                    synced += 1
                } else {
                    val message = result?.error ?: "Evenement non traite par le serveur."
                    markFailed(event.bookId, message)
                    failed += 1
                }
            }

            ProgressSyncSummary(attempted = events.size, synced = synced, failed = failed)
        } catch (error: Throwable) {
            if (error is IOException || error.isRetryableServerError()) {
                events.forEach { event -> markNetworkFailure(event.bookId, error) }
                throw error
            }

            events.forEach { event ->
                markFailed(event.bookId, error.message ?: "Synchronisation impossible.")
            }
            ProgressSyncSummary(attempted = events.size, synced = 0, failed = events.size)
        }
    }

    private suspend fun handleSyncFailure(bookId: String, error: Throwable): ProgressSyncSummary {
        if (error is IOException || error.isRetryableServerError()) {
            markNetworkFailure(bookId, error)
            throw error
        }

        markFailed(bookId, error.message ?: "Synchronisation impossible.")
        return ProgressSyncSummary(attempted = 1, synced = 0, failed = 1)
    }

    private suspend fun markSynced(bookId: String) {
        val now = System.currentTimeMillis()
        progressDao.markSynced(bookId, now)
        syncEventDao.deleteForBook(bookId)
    }

    private suspend fun markFailed(bookId: String, message: String) {
        val now = System.currentTimeMillis()
        syncEventDao.markFailed(bookId, message, now)
        progressDao.markSyncState(bookId, "error", message)
    }

    private suspend fun markNetworkFailure(bookId: String, error: Throwable) {
        val message = error.message ?: "Reseau indisponible."
        val now = System.currentTimeMillis()
        syncEventDao.markFailed(bookId, message, now)
        progressDao.markSyncState(bookId, "pending", message)
    }

    private fun Throwable.isRetryableServerError(): Boolean {
        return this is ApiException && statusCode >= 500
    }

    private companion object {
        const val DEVICE_ID = "android-reader"
        const val MAX_BATCH_SIZE = 25
    }
}

package ch.bytoox.aureliareader.data.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.ApiException
import ch.bytoox.aureliareader.core.network.AuthSession
import ch.bytoox.aureliareader.core.storage.DeviceIdStore
import ch.bytoox.aureliareader.core.storage.ServerSettingsStore
import ch.bytoox.aureliareader.core.storage.TokenStore
import ch.bytoox.aureliareader.data.local.AppDatabaseProvider
import ch.bytoox.aureliareader.data.repositories.ProgressSyncRepository
import java.io.IOException

class ProgressSyncWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val context = applicationContext
        val serverUrl = ServerSettingsStore(context).getServerUrl()
        val accessToken = TokenStore(context).getAccessToken()
        if (serverUrl.isBlank() || accessToken.isBlank()) {
            return Result.success()
        }

        val authSession = AuthSession().apply {
            this.accessToken = accessToken
        }
        val database = AppDatabaseProvider.get(context)
        val repository = ProgressSyncRepository(
            apiClient = ApiClient(authSession),
            progressDao = database.progressDao(),
            syncEventDao = database.syncEventDao(),
            deviceIdStore = DeviceIdStore(context)
        )

        return try {
            var loops = 0
            while (loops < MAX_FLUSH_LOOPS) {
                loops += 1
                val summary = repository.flushPending(serverUrl)
                if (summary.attempted < MAX_BATCH_SIZE || summary.synced == 0) {
                    break
                }
            }
            Result.success()
        } catch (error: Throwable) {
            when {
                error is ApiException && error.statusCode == 401 -> Result.failure()
                error is IOException -> Result.retry()
                error is ApiException && error.statusCode >= 500 -> Result.retry()
                else -> Result.success()
            }
        }
    }

    private companion object {
        const val MAX_BATCH_SIZE = 25
        const val MAX_FLUSH_LOOPS = 4
    }
}

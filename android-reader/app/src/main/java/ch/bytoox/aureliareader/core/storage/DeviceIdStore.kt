package ch.bytoox.aureliareader.core.storage

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import java.util.UUID
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

class DeviceIdStore(private val context: Context) {
    private val deviceIdKey = stringPreferencesKey("device_id")

    suspend fun getOrCreateDeviceId(): String {
        return mutex.withLock {
            val existing = context.aureliaDataStore.data
                .map { preferences -> preferences[deviceIdKey].orEmpty() }
                .first()
                .trim()

            if (existing.isNotBlank()) {
                existing
            } else {
                UUID.randomUUID().toString().also { generated ->
                    context.aureliaDataStore.edit { preferences ->
                        preferences[deviceIdKey] = generated
                    }
                }
            }
        }
    }

    private companion object {
        val mutex = Mutex()
    }
}

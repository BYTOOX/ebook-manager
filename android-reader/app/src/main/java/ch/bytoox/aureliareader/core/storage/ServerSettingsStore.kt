package ch.bytoox.aureliareader.core.storage

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

class ServerSettingsStore(private val context: Context) {
    private val serverUrlKey = stringPreferencesKey("server_url")

    val serverUrlFlow = context.aureliaDataStore.data.map { preferences ->
        preferences[serverUrlKey].orEmpty()
    }

    suspend fun getServerUrl(): String = serverUrlFlow.first()

    suspend fun saveServerUrl(serverUrl: String) {
        context.aureliaDataStore.edit { preferences ->
            preferences[serverUrlKey] = serverUrl
        }
    }
}

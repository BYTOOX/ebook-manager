package ch.bytoox.aureliareader.core.storage

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

class TokenStore(private val context: Context) {
    private val accessTokenKey = stringPreferencesKey("access_token")

    val accessTokenFlow = context.aureliaDataStore.data.map { preferences ->
        preferences[accessTokenKey].orEmpty()
    }

    suspend fun getAccessToken(): String = accessTokenFlow.first()

    suspend fun saveAccessToken(accessToken: String) {
        context.aureliaDataStore.edit { preferences ->
            preferences[accessTokenKey] = accessToken
        }
    }

    suspend fun clearAccessToken() {
        context.aureliaDataStore.edit { preferences ->
            preferences.remove(accessTokenKey)
        }
    }
}

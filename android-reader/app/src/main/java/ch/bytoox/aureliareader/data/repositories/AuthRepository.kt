package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.AuthSession
import ch.bytoox.aureliareader.core.network.HealthResponse
import ch.bytoox.aureliareader.core.network.UserDto
import ch.bytoox.aureliareader.core.storage.ServerSettingsStore
import ch.bytoox.aureliareader.core.storage.TokenStore

data class StoredSession(
    val serverUrl: String,
    val accessToken: String
)

data class AuthenticatedSession(
    val user: UserDto,
    val accessToken: String
)

class AuthRepository(
    private val apiClient: ApiClient,
    private val authSession: AuthSession,
    private val serverSettingsStore: ServerSettingsStore,
    private val tokenStore: TokenStore
) {
    suspend fun loadSession(): StoredSession {
        val serverUrl = serverSettingsStore.getServerUrl()
        val accessToken = tokenStore.getAccessToken()
        authSession.accessToken = accessToken.ifBlank { null }
        return StoredSession(serverUrl = serverUrl, accessToken = accessToken)
    }

    suspend fun checkServer(serverUrl: String): HealthResponse {
        val normalizedUrl = serverUrl.trim()
        val health = apiClient.create(normalizedUrl).health()
        serverSettingsStore.saveServerUrl(normalizedUrl)
        return health
    }

    suspend fun login(serverUrl: String, username: String, password: String): AuthenticatedSession {
        authSession.accessToken = null
        tokenStore.clearAccessToken()
        val response = apiClient.create(serverUrl).login(username.trim(), password)
        require(response.ok) { "Connexion refusee par Aurelia." }
        require(response.tokenType.equals("bearer", ignoreCase = true)) {
            "Type de token inattendu."
        }
        authSession.accessToken = response.accessToken
        tokenStore.saveAccessToken(response.accessToken)
        serverSettingsStore.saveServerUrl(serverUrl.trim())
        return AuthenticatedSession(user = response.user, accessToken = response.accessToken)
    }

    suspend fun currentUser(serverUrl: String): UserDto {
        return apiClient.create(serverUrl).currentUser()
    }

    suspend fun logout(serverUrl: String) {
        runCatching {
            if (serverUrl.isNotBlank() && !authSession.accessToken.isNullOrBlank()) {
                apiClient.create(serverUrl).logout()
            }
        }
        tokenStore.clearAccessToken()
        authSession.accessToken = null
    }

    suspend fun clearToken() {
        tokenStore.clearAccessToken()
        authSession.accessToken = null
    }
}

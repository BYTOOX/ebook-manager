package ch.bytoox.aureliareader.core.network

import java.util.concurrent.TimeUnit
import okhttp3.OkHttpClient

class ApiClient(private val authSession: AuthSession) {
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .addInterceptor(AuthInterceptor(authSession))
        .build()

    fun create(serverUrl: String): AureliaApi {
        return AureliaApi(
            httpClient = httpClient,
            baseApiUrl = normalizeBaseApiUrl(serverUrl)
        )
    }

    private fun normalizeBaseApiUrl(serverUrl: String): String {
        val trimmed = serverUrl.trim().trimEnd('/')
        require(trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            "L'URL doit commencer par http:// ou https://"
        }
        return if (trimmed.endsWith("/api/v1")) {
            "$trimmed/"
        } else {
            "$trimmed/api/v1/"
        }
    }
}

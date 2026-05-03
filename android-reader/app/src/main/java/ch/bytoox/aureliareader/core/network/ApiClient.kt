package ch.bytoox.aureliareader.core.network

import ch.bytoox.aureliareader.BuildConfig
import java.util.concurrent.TimeUnit
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient

class ApiClient(private val authSession: AuthSession) {
    private val baseHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(20, TimeUnit.SECONDS)
        .build()

    private val assetHttpClient = baseHttpClient.newBuilder().build()

    private fun authenticatedHttpClient(baseApiUrl: String): OkHttpClient {
        return baseHttpClient.newBuilder()
            .addInterceptor(AuthInterceptor(authSession, baseApiUrl.toHttpUrl()))
            .build()
    }

    fun create(serverUrl: String): AureliaApi {
        val baseApiUrl = normalizeBaseApiUrl(serverUrl)
        return AureliaApi(
            httpClient = authenticatedHttpClient(baseApiUrl),
            assetHttpClient = assetHttpClient,
            baseApiUrl = baseApiUrl
        )
    }

    private fun normalizeBaseApiUrl(serverUrl: String): String {
        val trimmed = serverUrl.trim().trimEnd('/')
        val isHttps = trimmed.startsWith("https://")
        val isHttp = trimmed.startsWith("http://")

        require(isHttps || isHttp) {
            "L'URL doit commencer par http:// ou https://."
        }

        require(isHttps || BuildConfig.ALLOW_CLEARTEXT_SERVER) {
            "La version release d'Aurelia Reader exige une URL HTTPS."
        }

        return if (trimmed.endsWith("/api/v1")) {
            "$trimmed/"
        } else {
            "$trimmed/api/v1/"
        }
    }
}

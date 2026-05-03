package ch.bytoox.aureliareader.core.network

import okhttp3.Interceptor
import okhttp3.HttpUrl
import okhttp3.Response

class AuthInterceptor(
    private val authSession: AuthSession,
    private val allowedOrigin: HttpUrl
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = authSession.accessToken
        val originalRequest = chain.request()

        if (
            token.isNullOrBlank() ||
            originalRequest.header("Authorization") != null ||
            !originalRequest.url.isAllowedOrigin()
        ) {
            return chain.proceed(originalRequest)
        }

        val authenticatedRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $token")
            .build()

        return chain.proceed(authenticatedRequest)
    }

    private fun HttpUrl.isAllowedOrigin(): Boolean {
        return scheme == allowedOrigin.scheme &&
            host == allowedOrigin.host &&
            port == allowedOrigin.port
    }
}

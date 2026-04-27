package ch.bytoox.aureliareader.core.network

import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(private val authSession: AuthSession) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = authSession.accessToken
        val originalRequest = chain.request()

        if (token.isNullOrBlank() || originalRequest.header("Authorization") != null) {
            return chain.proceed(originalRequest)
        }

        val authenticatedRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $token")
            .build()

        return chain.proceed(authenticatedRequest)
    }
}

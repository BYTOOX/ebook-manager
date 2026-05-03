package ch.bytoox.aureliareader.core.network

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AuthInterceptorTest {
    @Test
    fun authorizationHeaderIsOnlyAddedForAllowedOrigin() {
        val aureliaServer = MockWebServer()
        val externalServer = MockWebServer()
        aureliaServer.start()
        externalServer.start()

        try {
            aureliaServer.enqueue(MockResponse().setResponseCode(200))
            externalServer.enqueue(MockResponse().setResponseCode(200))

            val authSession = AuthSession().apply {
                accessToken = "secret-token"
            }
            val client = OkHttpClient.Builder()
                .addInterceptor(AuthInterceptor(authSession, aureliaServer.url("/api/v1/")))
                .build()

            client.newCall(
                Request.Builder()
                    .url(aureliaServer.url("/api/v1/books"))
                    .build()
            ).execute().close()

            client.newCall(
                Request.Builder()
                    .url(externalServer.url("/cover.jpg"))
                    .build()
            ).execute().close()

            assertEquals("Bearer secret-token", aureliaServer.takeRequest().getHeader("Authorization"))
            assertNull(externalServer.takeRequest().getHeader("Authorization"))
        } finally {
            aureliaServer.shutdown()
            externalServer.shutdown()
        }
    }
}

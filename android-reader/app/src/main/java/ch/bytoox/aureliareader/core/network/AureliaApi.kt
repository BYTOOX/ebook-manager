package ch.bytoox.aureliareader.core.network

import java.io.File
import java.io.IOException
import java.net.URI
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.HttpUrl.Companion.toHttpUrl
import org.json.JSONArray
import org.json.JSONObject

class AureliaApi(
    private val httpClient: OkHttpClient,
    private val baseApiUrl: String
) {
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun health(): HealthResponse = withContext(Dispatchers.IO) {
        val json = executeJson(
            Request.Builder()
                .url(url("health"))
                .get()
                .build()
        )

        HealthResponse(
            status = json.optString("status"),
            app = json.optString("app")
        )
    }

    suspend fun login(username: String, password: String): LoginResponse = withContext(Dispatchers.IO) {
        val body = JSONObject()
            .put("username", username)
            .put("password", password)
            .toString()
            .toRequestBody(jsonMediaType)

        val json = executeJson(
            Request.Builder()
                .url(url("auth/login"))
                .post(body)
                .build()
        )

        LoginResponse(
            ok = json.optBoolean("ok"),
            accessToken = json.getString("access_token"),
            tokenType = json.optString("token_type"),
            expiresIn = json.optLong("expires_in"),
            user = json.getJSONObject("user").toUserDto()
        )
    }

    suspend fun currentUser(): UserDto = withContext(Dispatchers.IO) {
        executeJson(
            Request.Builder()
                .url(url("auth/me"))
                .get()
                .build()
        ).toUserDto()
    }

    suspend fun logout(): Boolean = withContext(Dispatchers.IO) {
        val json = executeJson(
            Request.Builder()
                .url(url("auth/logout"))
                .post(ByteArray(0).toRequestBody(null))
                .build()
        )

        json.optBoolean("ok", true)
    }

    suspend fun listBooks(
        query: String?,
        limit: Int,
        offset: Int,
        sort: String = "last_opened_at",
        order: String = "desc"
    ): BookListResponseDto = withContext(Dispatchers.IO) {
        val httpUrl = url("books").toHttpUrl().newBuilder()
            .addQueryParameter("limit", limit.toString())
            .addQueryParameter("offset", offset.toString())
            .addQueryParameter("sort", sort)
            .addQueryParameter("order", order)
            .apply {
                val cleanQuery = query?.trim().orEmpty()
                if (cleanQuery.isNotBlank()) {
                    addQueryParameter("q", cleanQuery)
                }
            }
            .build()

        val json = executeJson(
            Request.Builder()
                .url(httpUrl)
                .get()
                .build()
        )

        BookListResponseDto(
            items = json.optJSONArray("items").toBookListItems(),
            total = json.optInt("total")
        )
    }

    suspend fun bookDetail(bookId: String): BookDetailDto = withContext(Dispatchers.IO) {
        executeJson(
            Request.Builder()
                .url(url("books/$bookId"))
                .get()
                .build()
        ).toBookDetail()
    }

    suspend fun downloadBookFile(
        bookId: String,
        targetFile: File,
        onProgress: (Int) -> Unit
    ): Long = withContext(Dispatchers.IO) {
        executeFile(
            request = Request.Builder()
                .url(url("books/$bookId/file"))
                .get()
                .build(),
            targetFile = targetFile,
            onProgress = onProgress
        )
    }

    suspend fun downloadCover(coverUrl: String?, targetFile: File): Boolean = withContext(Dispatchers.IO) {
        val resolvedUrl = coverUrl?.trim().orEmpty()
        if (resolvedUrl.isBlank()) {
            return@withContext false
        }

        runCatching {
            executeFile(
                request = Request.Builder()
                    .url(resolvedUrl)
                    .get()
                    .build(),
                targetFile = targetFile,
                onProgress = {}
            )
            targetFile.exists() && targetFile.length() > 0L
        }.getOrDefault(false)
    }

    suspend fun putBookProgress(bookId: String, payloadJson: String): Boolean = withContext(Dispatchers.IO) {
        val body = JSONObject(payloadJson)
            .toString()
            .toRequestBody(jsonMediaType)

        val json = executeJson(
            Request.Builder()
                .url(url("books/$bookId/progress"))
                .put(body)
                .build()
        )

        json.optBoolean("ok", true)
    }

    suspend fun syncEvents(deviceId: String, events: List<SyncEventUploadDto>): SyncEventsResponseDto =
        withContext(Dispatchers.IO) {
            val body = JSONObject()
                .put("device_id", deviceId)
                .put(
                    "events",
                    JSONArray(
                        events.map { event ->
                            JSONObject()
                                .put("event_id", event.eventId)
                                .put("type", event.type)
                                .put("payload", JSONObject(event.payloadJson))
                                .put("client_created_at", event.clientCreatedAt)
                        }
                    )
                )
                .toString()
                .toRequestBody(jsonMediaType)

            val json = executeJson(
                Request.Builder()
                    .url(url("sync/events"))
                    .post(body)
                    .build()
            )

            SyncEventsResponseDto(
                ok = json.optBoolean("ok"),
                accepted = json.optInt("accepted"),
                processed = json.optInt("processed"),
                results = json.optJSONArray("results").toSyncEventResults()
            )
        }

    private fun url(path: String): String = baseApiUrl + path.trimStart('/')

    private fun absoluteUrl(pathOrUrl: String?): String? {
        val value = pathOrUrl?.trim().orEmpty()
        if (value.isBlank()) {
            return null
        }
        return if (value.startsWith("http://") || value.startsWith("https://")) {
            value
        } else {
            URI(baseApiUrl).resolve(value).toString()
        }
    }

    private fun executeJson(request: Request): JSONObject {
        try {
            httpClient.newCall(request).execute().use { response ->
                val responseBody = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    throw ApiException(
                        statusCode = response.code,
                        message = readableError(response.code, responseBody)
                    )
                }
                return if (responseBody.isBlank()) JSONObject() else JSONObject(responseBody)
            }
        } catch (exception: IOException) {
            throw IOException("Connexion impossible au serveur Aurelia.", exception)
        }
    }

    private fun executeFile(
        request: Request,
        targetFile: File,
        onProgress: (Int) -> Unit
    ): Long {
        targetFile.parentFile?.mkdirs()
        val tempFile = File(targetFile.parentFile, "${targetFile.name}.part")
        if (tempFile.exists()) {
            tempFile.delete()
        }

        try {
            httpClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val responseBody = response.body?.string().orEmpty()
                    throw ApiException(
                        statusCode = response.code,
                        message = readableError(response.code, responseBody)
                    )
                }

                val body = response.body ?: throw IOException("Reponse fichier vide.")
                val totalBytes = body.contentLength()
                var copiedBytes = 0L
                var lastProgress = -1

                body.byteStream().use { input ->
                    tempFile.outputStream().use { output ->
                        val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                        while (true) {
                            val read = input.read(buffer)
                            if (read == -1) {
                                break
                            }
                            output.write(buffer, 0, read)
                            copiedBytes += read

                            if (totalBytes > 0L) {
                                val progress = ((copiedBytes * 100L) / totalBytes).toInt().coerceIn(0, 100)
                                if (progress != lastProgress) {
                                    onProgress(progress)
                                    lastProgress = progress
                                }
                            }
                        }
                    }
                }

                if (copiedBytes <= 0L) {
                    throw IOException("Fichier telecharge vide.")
                }

                if (targetFile.exists()) {
                    targetFile.delete()
                }
                if (!tempFile.renameTo(targetFile)) {
                    tempFile.copyTo(targetFile, overwrite = true)
                    tempFile.delete()
                }
                onProgress(100)
                return copiedBytes
            }
        } catch (exception: IOException) {
            tempFile.delete()
            throw IOException("Telechargement impossible depuis Aurelia.", exception)
        } catch (exception: Exception) {
            tempFile.delete()
            throw exception
        }
    }

    private fun readableError(statusCode: Int, responseBody: String): String {
        val detail = runCatching {
            JSONObject(responseBody).optString("detail")
        }.getOrNull().orEmpty()

        return when {
            statusCode == 401 -> "Session invalide ou identifiants incorrects."
            detail.isNotBlank() -> detail
            statusCode >= 500 -> "Erreur serveur Aurelia."
            else -> "Erreur HTTP $statusCode."
        }
    }

    private fun JSONObject.toUserDto(): UserDto {
        return UserDto(
            id = optString("id"),
            username = optString("username"),
            displayName = optString("display_name").ifBlank { null }
        )
    }

    private fun JSONArray?.toStringList(): List<String> {
        if (this == null) {
            return emptyList()
        }
        return buildList {
            for (index in 0 until length()) {
                optString(index).takeIf { it.isNotBlank() }?.let(::add)
            }
        }
    }

    private fun JSONArray?.toBookListItems(): List<BookListItemDto> {
        if (this == null) {
            return emptyList()
        }
        return buildList {
            for (index in 0 until length()) {
                optJSONObject(index)?.let { add(it.toBookListItem()) }
            }
        }
    }

    private fun JSONArray?.toSyncEventResults(): List<SyncEventResultDto> {
        if (this == null) {
            return emptyList()
        }
        return buildList {
            for (index in 0 until length()) {
                optJSONObject(index)?.let { json ->
                    add(
                        SyncEventResultDto(
                            eventId = json.optString("event_id"),
                            type = json.optString("type"),
                            status = json.optString("status"),
                            resolved = json.optNullableString("resolved"),
                            bookId = json.optNullableString("book_id"),
                            error = json.optNullableString("error")
                        )
                    )
                }
            }
        }
    }

    private fun JSONObject.optNullableString(name: String): String? {
        return if (isNull(name)) null else optString(name).ifBlank { null }
    }

    private fun JSONObject.optNullableInt(name: String): Int? {
        return if (isNull(name)) null else optInt(name)
    }

    private fun JSONObject.optNullableFloat(name: String): Float? {
        return if (isNull(name)) null else optDouble(name).toFloat()
    }

    private fun JSONObject.optNullableLong(name: String): Long? {
        return if (isNull(name)) null else optLong(name)
    }

    private fun JSONObject.toBookListItem(): BookListItemDto {
        return BookListItemDto(
            id = optString("id"),
            title = optString("title"),
            authors = optJSONArray("authors").toStringList(),
            coverUrl = absoluteUrl(optNullableString("cover_url")),
            status = optString("status"),
            rating = optNullableInt("rating"),
            favorite = optBoolean("favorite"),
            progressPercent = optNullableFloat("progress_percent"),
            isOfflineAvailable = optBoolean("is_offline_available"),
            addedAt = optString("added_at"),
            lastOpenedAt = optNullableString("last_opened_at")
        )
    }

    private fun JSONObject.toBookSeries(): BookSeriesDto {
        return BookSeriesDto(
            name = optString("name"),
            index = optNullableFloat("index"),
            source = optString("source")
        )
    }

    private fun JSONObject.toBookDetail(): BookDetailDto {
        return BookDetailDto(
            id = optString("id"),
            title = optString("title"),
            authors = optJSONArray("authors").toStringList(),
            coverUrl = absoluteUrl(optNullableString("cover_url")),
            status = optString("status"),
            rating = optNullableInt("rating"),
            favorite = optBoolean("favorite"),
            progressPercent = optNullableFloat("progress_percent"),
            isOfflineAvailable = optBoolean("is_offline_available"),
            addedAt = optString("added_at"),
            lastOpenedAt = optNullableString("last_opened_at"),
            subtitle = optNullableString("subtitle"),
            description = optNullableString("description"),
            language = optNullableString("language"),
            isbn = optNullableString("isbn"),
            publisher = optNullableString("publisher"),
            publishedDate = optNullableString("published_date"),
            originalFilename = optNullableString("original_filename"),
            fileSize = optNullableLong("file_size"),
            metadataSource = optNullableString("metadata_source"),
            series = optJSONObject("series")?.toBookSeries(),
            relatedBooks = optJSONArray("related_books").toBookListItems(),
            subjects = optJSONArray("subjects").toStringList(),
            contributors = optJSONArray("contributors").toStringList(),
            characters = optJSONArray("characters").toStringList(),
            tags = optJSONArray("tags").toStringList()
        )
    }
}

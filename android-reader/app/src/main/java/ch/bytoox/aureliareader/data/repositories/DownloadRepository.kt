package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.core.files.BookFileStore
import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.data.local.dao.BookDao
import ch.bytoox.aureliareader.data.local.dao.DownloadDao
import ch.bytoox.aureliareader.data.local.entities.BookEntity
import ch.bytoox.aureliareader.data.local.entities.DownloadEntity
import java.io.File
import org.json.JSONArray
import org.json.JSONObject

class DownloadRepository(
    private val apiClient: ApiClient,
    private val bookDao: BookDao,
    private val downloadDao: DownloadDao,
    private val fileStore: BookFileStore
) {
    suspend fun downloadedBookIds(): Set<String> {
        val ids = bookDao.downloadedBookIds()
        val existingIds = ids.filter(fileStore::hasBookFile).toSet()
        ids.filterNot(existingIds::contains).forEach { missingId ->
            bookDao.clearDownload(missingId, now())
            downloadDao.delete(missingId)
        }
        return existingIds
    }

    suspend fun downloadBook(
        serverUrl: String,
        book: BookDetailDto,
        onProgress: (Int) -> Unit
    ) {
        val api = apiClient.create(serverUrl)
        val epubFile = fileStore.bookFile(book.id)
        val coverFile = fileStore.coverFile(book.id)

        downloadDao.upsert(
            DownloadEntity(
                bookId = book.id,
                status = "downloading",
                progress = 0,
                error = null,
                updatedAt = now()
            )
        )
        onProgress(0)

        runCatching {
            val downloadedSize = api.downloadBookFile(book.id, epubFile, onProgress)
            val hasLocalCover = api.downloadCover(book.coverUrl, coverFile)

            bookDao.upsert(
                book.toEntity(
                    localFilePath = epubFile.absolutePath,
                    localCoverPath = coverFile.takeIf { hasLocalCover }?.absolutePath,
                    downloadedSize = downloadedSize
                )
            )
            downloadDao.upsert(
                DownloadEntity(
                    bookId = book.id,
                    status = "downloaded",
                    progress = 100,
                    error = null,
                    updatedAt = now()
                )
            )
        }.onFailure { error ->
            downloadDao.upsert(
                DownloadEntity(
                    bookId = book.id,
                    status = "failed",
                    progress = 0,
                    error = error.message ?: "Telechargement impossible.",
                    updatedAt = now()
                )
            )
            throw error
        }.getOrThrow()
    }

    suspend fun removeDownload(bookId: String) {
        fileStore.deleteBookFiles(bookId)
        bookDao.clearDownload(bookId, now())
        downloadDao.delete(bookId)
    }

    suspend fun prepareBookForReading(
        serverUrl: String,
        book: BookDetailDto,
        onProgress: (Int) -> Unit
    ): String {
        localFilePath(book.id)?.let { localPath ->
            onProgress(100)
            return localPath
        }

        val tempFile = fileStore.readerTempFile(book.id)
        if (tempFile.exists() && tempFile.length() > 0L) {
            onProgress(100)
            return tempFile.absolutePath
        }

        onProgress(0)
        apiClient.create(serverUrl).downloadBookFile(book.id, tempFile, onProgress)
        return tempFile.absolutePath
    }

    suspend fun localFilePath(bookId: String): String? {
        val entity = bookDao.bookById(bookId) ?: return null
        val localPath = entity.localFilePath ?: return null
        val file = File(localPath)
        if (entity.isDownloaded && file.exists() && file.length() > 0L) {
            return localPath
        }

        bookDao.clearDownload(bookId, now())
        downloadDao.delete(bookId)
        return null
    }

    private fun BookDetailDto.toEntity(
        localFilePath: String,
        localCoverPath: String?,
        downloadedSize: Long
    ): BookEntity {
        val metadata = JSONObject()
            .put("subtitle", subtitle)
            .put("description", description)
            .put("language", language)
            .put("isbn", isbn)
            .put("publisher", publisher)
            .put("publishedDate", publishedDate)
            .put("originalFilename", originalFilename)
            .put("metadataSource", metadataSource)
            .put("subjects", JSONArray(subjects))
            .put("contributors", JSONArray(contributors))
            .put("characters", JSONArray(characters))
            .put("tags", JSONArray(tags))

        return BookEntity(
            id = id,
            title = title,
            authorsJson = JSONArray(authors).toString(),
            coverUrl = coverUrl,
            localCoverPath = localCoverPath,
            localFilePath = localFilePath,
            isDownloaded = true,
            fileSize = fileSize ?: downloadedSize,
            progressPercent = progressPercent,
            lastOpenedAt = lastOpenedAt,
            metadataJson = metadata.toString(),
            updatedAt = now()
        )
    }

    private fun now(): Long = System.currentTimeMillis()
}

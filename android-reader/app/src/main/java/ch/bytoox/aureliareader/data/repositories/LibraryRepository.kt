package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.core.network.BookListResponseDto
import ch.bytoox.aureliareader.core.network.BookUpdateDto
import ch.bytoox.aureliareader.core.network.CollectionListResponseDto
import ch.bytoox.aureliareader.core.network.ReadingProgressDto
import ch.bytoox.aureliareader.core.network.SeriesDetailDto
import ch.bytoox.aureliareader.core.network.SeriesListResponseDto
import ch.bytoox.aureliareader.core.network.UploadBookResponseDto

class LibraryRepository(
    private val apiClient: ApiClient
) {
    suspend fun listBooks(
        serverUrl: String,
        query: String?,
        limit: Int,
        offset: Int
    ): BookListResponseDto {
        return apiClient.create(serverUrl).listBooks(
            query = query,
            limit = limit,
            offset = offset
        )
    }

    suspend fun getBook(serverUrl: String, bookId: String): BookDetailDto {
        return apiClient.create(serverUrl).bookDetail(bookId)
    }

    suspend fun updateBook(
        serverUrl: String,
        bookId: String,
        payload: BookUpdateDto
    ): BookDetailDto {
        return apiClient.create(serverUrl).updateBook(bookId, payload)
    }

    suspend fun uploadBook(serverUrl: String, filename: String, bytes: ByteArray): UploadBookResponseDto {
        return apiClient.create(serverUrl).uploadBook(filename, bytes)
    }

    suspend fun listCollections(serverUrl: String): CollectionListResponseDto {
        return apiClient.create(serverUrl).listCollections()
    }

    suspend fun listSeries(serverUrl: String): SeriesListResponseDto {
        return apiClient.create(serverUrl).listSeries()
    }

    suspend fun getSeries(serverUrl: String, seriesId: String): SeriesDetailDto {
        return apiClient.create(serverUrl).seriesDetail(seriesId)
    }

    suspend fun putBookProgress(serverUrl: String, bookId: String, payloadJson: String): Boolean {
        return apiClient.create(serverUrl).putBookProgress(bookId, payloadJson).ok
    }

    suspend fun getBookProgress(serverUrl: String, bookId: String): ReadingProgressDto {
        return apiClient.create(serverUrl).getBookProgress(bookId)
    }
}

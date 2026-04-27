package ch.bytoox.aureliareader.data.repositories

import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.core.network.BookListResponseDto

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
}

package ch.bytoox.aureliareader.core.network

data class HealthResponse(
    val status: String,
    val app: String
)

data class UserDto(
    val id: String,
    val username: String,
    val displayName: String?
)

data class LoginResponse(
    val ok: Boolean,
    val accessToken: String,
    val tokenType: String,
    val expiresIn: Long,
    val user: UserDto
)

data class BookListItemDto(
    val id: String,
    val title: String,
    val authors: List<String>,
    val coverUrl: String?,
    val status: String,
    val rating: Int?,
    val favorite: Boolean,
    val progressPercent: Float?,
    val isOfflineAvailable: Boolean,
    val addedAt: String,
    val lastOpenedAt: String?
) {
    val authorLine: String
        get() = authors.joinToString(", ").ifBlank { "Auteur inconnu" }
}

data class BookSeriesDto(
    val name: String,
    val index: Float?,
    val source: String
)

data class BookDetailDto(
    val id: String,
    val title: String,
    val authors: List<String>,
    val coverUrl: String?,
    val status: String,
    val rating: Int?,
    val favorite: Boolean,
    val progressPercent: Float?,
    val isOfflineAvailable: Boolean,
    val addedAt: String,
    val lastOpenedAt: String?,
    val subtitle: String?,
    val description: String?,
    val language: String?,
    val isbn: String?,
    val publisher: String?,
    val publishedDate: String?,
    val originalFilename: String?,
    val fileSize: Long?,
    val metadataSource: String?,
    val series: BookSeriesDto?,
    val relatedBooks: List<BookListItemDto>,
    val subjects: List<String>,
    val contributors: List<String>,
    val characters: List<String>,
    val tags: List<String>
) {
    val authorLine: String
        get() = authors.joinToString(", ").ifBlank { "Auteur inconnu" }
}

data class BookListResponseDto(
    val items: List<BookListItemDto>,
    val total: Int
)

data class BookUpdateDto(
    val title: String? = null,
    val authors: List<String>? = null,
    val seriesName: String? = null,
    val seriesIndex: Float? = null,
    val tags: List<String>? = null,
    val status: String? = null,
    val rating: Int? = null,
    val favorite: Boolean? = null
)

data class UploadBookResponseDto(
    val jobId: String,
    val bookId: String?,
    val status: String,
    val warning: String?
)

data class CollectionSummaryDto(
    val id: String,
    val name: String,
    val description: String?,
    val bookCount: Int,
    val coverUrl: String?
)

data class CollectionListResponseDto(
    val items: List<CollectionSummaryDto>,
    val total: Int
)

data class SeriesSummaryDto(
    val id: String,
    val name: String,
    val description: String?,
    val bookCount: Int,
    val coverUrl: String?
)

data class SeriesListResponseDto(
    val items: List<SeriesSummaryDto>,
    val total: Int
)

data class SeriesDetailDto(
    val id: String,
    val name: String,
    val description: String?,
    val bookCount: Int,
    val coverUrl: String?,
    val books: List<BookListItemDto>
)

data class SyncEventUploadDto(
    val eventId: String,
    val type: String,
    val payloadJson: String,
    val clientCreatedAt: String
)

data class SyncEventResultDto(
    val eventId: String,
    val type: String,
    val status: String,
    val resolved: String?,
    val bookId: String?,
    val error: String?
)

data class SyncEventsResponseDto(
    val ok: Boolean,
    val accepted: Int,
    val processed: Int,
    val results: List<SyncEventResultDto>
)

class ApiException(
    val statusCode: Int,
    message: String
) : Exception(message)

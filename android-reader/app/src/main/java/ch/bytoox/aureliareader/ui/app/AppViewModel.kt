package ch.bytoox.aureliareader.ui.app

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import ch.bytoox.aureliareader.core.files.BookFileStore
import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.ApiException
import ch.bytoox.aureliareader.core.network.AuthSession
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.core.network.BookListItemDto
import ch.bytoox.aureliareader.core.network.BookUpdateDto
import ch.bytoox.aureliareader.core.network.CollectionSummaryDto
import ch.bytoox.aureliareader.core.network.SeriesDetailDto
import ch.bytoox.aureliareader.core.network.SeriesSummaryDto
import ch.bytoox.aureliareader.core.network.UserDto
import ch.bytoox.aureliareader.core.storage.ServerSettingsStore
import ch.bytoox.aureliareader.core.storage.TokenStore
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import ch.bytoox.aureliareader.data.local.AppDatabaseProvider
import ch.bytoox.aureliareader.data.repositories.AuthRepository
import ch.bytoox.aureliareader.data.repositories.BookProgressSnapshot
import ch.bytoox.aureliareader.data.repositories.DownloadRepository
import ch.bytoox.aureliareader.data.repositories.LibraryRepository
import ch.bytoox.aureliareader.data.repositories.ProgressRepository
import ch.bytoox.aureliareader.data.sync.ProgressSyncScheduler
import java.io.IOException
import java.time.Instant
import kotlinx.coroutines.Job
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

enum class DownloadStatus {
    Idle,
    Downloading,
    Downloaded,
    Failed
}

data class BookDownloadUiState(
    val status: DownloadStatus = DownloadStatus.Idle,
    val progress: Int = 0,
    val error: String? = null
)

data class ReaderLaunchRequest(
    val requestId: Long,
    val bookId: String,
    val title: String,
    val filePath: String
)

data class AppUiState(
    val isInitialized: Boolean = false,
    val serverUrl: String = "",
    val accessToken: String = "",
    val currentUser: UserDto? = null,
    val isOfflineMode: Boolean = false,
    val offlineBookCount: Int = 0,
    val serverStatus: String? = null,
    val serverError: String? = null,
    val loginError: String? = null,
    val sessionMessage: String? = null,
    val books: List<BookListItemDto> = emptyList(),
    val booksTotal: Int = 0,
    val booksQuery: String = "",
    val booksError: String? = null,
    val isLoadingBooks: Boolean = false,
    val isLoadingMoreBooks: Boolean = false,
    val selectedBookId: String? = null,
    val selectedBook: BookDetailDto? = null,
    val selectedBookError: String? = null,
    val isLoadingBookDetail: Boolean = false,
    val offlineBookIds: Set<String> = emptySet(),
    val downloadStates: Map<String, BookDownloadUiState> = emptyMap(),
    val localProgress: Map<String, BookProgressSnapshot> = emptyMap(),
    val isPreparingReader: Boolean = false,
    val readerPrepareProgress: Int? = null,
    val readerError: String? = null,
    val readerLaunchRequest: ReaderLaunchRequest? = null,
    val collections: List<CollectionSummaryDto> = emptyList(),
    val series: List<SeriesSummaryDto> = emptyList(),
    val selectedSeries: SeriesDetailDto? = null,
    val selectedSeriesError: String? = null,
    val isLoadingSeriesDetail: Boolean = false,
    val isLoadingOrganization: Boolean = false,
    val organizationError: String? = null,
    val isImportingBook: Boolean = false,
    val importMessage: String? = null,
    val bookActionMessage: String? = null,
    val bookActionError: String? = null,
    val isMutatingBook: Boolean = false,
    val isReconnecting: Boolean = false,
    val isCheckingServer: Boolean = false,
    val isLoggingIn: Boolean = false,
    val isLoggingOut: Boolean = false
) {
    val canContinueOffline: Boolean
        get() = offlineBookCount > 0

    val isAuthenticated: Boolean
        get() = currentUser != null || isOfflineMode
}

class AppViewModel(
    private val appContext: Context,
    private val authRepository: AuthRepository,
    private val libraryRepository: LibraryRepository,
    private val downloadRepository: DownloadRepository,
    private val progressRepository: ProgressRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()
    private var booksJob: Job? = null

    init {
        restoreSession()
        refreshOfflineBookIds()
        refreshLocalProgress()
    }

    fun updateServerUrl(serverUrl: String) {
        _uiState.update {
            it.copy(
                serverUrl = serverUrl,
                isOfflineMode = false,
                serverStatus = null,
                serverError = null,
                sessionMessage = null
            )
        }
    }

    fun checkServer(onSuccess: () -> Unit) {
        val serverUrl = uiState.value.serverUrl.trim()
        if (serverUrl.isBlank()) {
            _uiState.update { it.copy(serverError = "URL serveur requise.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isCheckingServer = true,
                    serverStatus = null,
                    serverError = null,
                    sessionMessage = null
                )
            }

            runCatching {
                authRepository.checkServer(serverUrl)
            }.onSuccess { health ->
                _uiState.update {
                    it.copy(
                        serverUrl = serverUrl,
                        serverStatus = "${health.app} repond: ${health.status}",
                        isOfflineMode = false,
                        isCheckingServer = false
                    )
                }
                onSuccess()
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        serverError = error.toFriendlyMessage(),
                        isCheckingServer = false
                    )
                }
            }
        }
    }

    fun login(username: String, password: String, onSuccess: () -> Unit) {
        val serverUrl = uiState.value.serverUrl.trim()
        if (serverUrl.isBlank()) {
            _uiState.update { it.copy(loginError = "Configure d'abord l'URL du serveur.") }
            return
        }
        if (username.isBlank() || password.isBlank()) {
            _uiState.update { it.copy(loginError = "Identifiant et mot de passe sont requis.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoggingIn = true,
                    loginError = null,
                    sessionMessage = null
                )
            }

            runCatching {
                authRepository.login(serverUrl, username, password)
            }.onSuccess { session ->
                _uiState.update {
                    it.copy(
                        currentUser = session.user,
                        accessToken = session.accessToken,
                        isOfflineMode = false,
                        isLoggingIn = false,
                        loginError = null,
                        sessionMessage = "Connecte en Bearer."
                    )
                }
                refreshOfflineBookIds()
                ProgressSyncScheduler.enqueue(appContext)
                loadBooks(reset = true)
                loadOrganization()
                onSuccess()
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        currentUser = null,
                        isLoggingIn = false,
                        loginError = error.toFriendlyMessage()
                    )
                }
            }
        }
    }

    fun continueOffline(onSuccess: () -> Unit) {
        viewModelScope.launch {
            val enteredOffline = enterOfflineMode(
                message = "Mode hors ligne: livres telecharges uniquement.",
                query = uiState.value.booksQuery
            )
            if (enteredOffline) {
                onSuccess()
            } else {
                _uiState.update {
                    it.copy(
                        serverError = "Aucun livre telecharge disponible hors ligne.",
                        loginError = "Aucun livre telecharge disponible hors ligne."
                    )
                }
            }
        }
    }

    fun reconnectServer() {
        val serverUrl = uiState.value.serverUrl.trim()
        if (serverUrl.isBlank()) {
            _uiState.update {
                it.copy(
                    serverError = "URL serveur requise.",
                    bookActionError = "URL serveur requise."
                )
            }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isReconnecting = true,
                    isCheckingServer = true,
                    serverError = null,
                    booksError = null,
                    bookActionError = null,
                    sessionMessage = null
                )
            }

            runCatching {
                val health = authRepository.checkServer(serverUrl)
                val user = if (uiState.value.accessToken.isNotBlank()) {
                    authRepository.currentUser(serverUrl)
                } else {
                    null
                }
                health to user
            }.onSuccess { (health, user) ->
                _uiState.update {
                    it.copy(
                        currentUser = user,
                        isOfflineMode = user == null && it.isOfflineMode,
                        serverStatus = "${health.app} repond: ${health.status}",
                        sessionMessage = if (user != null) {
                            "Reconnecte au serveur."
                        } else {
                            "Serveur disponible, reconnecte-toi."
                        },
                        isCheckingServer = false,
                        isReconnecting = false
                    )
                }
                if (user != null) {
                    ProgressSyncScheduler.enqueue(appContext)
                    refreshOfflineBookIds()
                    refreshLocalProgress()
                    loadBooks(reset = true)
                    loadOrganization()
                }
            }.onFailure { error ->
                handleApiFailure(error)
                _uiState.update {
                    it.copy(
                        serverError = error.toFriendlyMessage(),
                        bookActionError = error.toFriendlyMessage(),
                        isCheckingServer = false,
                        isReconnecting = false
                    )
                }
            }
        }
    }

    fun logout(onLoggedOut: () -> Unit) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoggingOut = true, sessionMessage = null) }
            authRepository.logout(uiState.value.serverUrl)
            val offlineIds = downloadRepository.downloadedBookIds()
            _uiState.update {
                it.copy(
                    accessToken = "",
                    currentUser = null,
                    isOfflineMode = false,
                    books = emptyList(),
                    booksTotal = 0,
                    booksQuery = "",
                    booksError = null,
                    selectedBookId = null,
                    selectedBook = null,
                    selectedBookError = null,
                    offlineBookIds = offlineIds,
                    offlineBookCount = offlineIds.size,
                    downloadStates = emptyMap(),
                    localProgress = emptyMap(),
                    isPreparingReader = false,
                    readerPrepareProgress = null,
                    readerError = null,
                    readerLaunchRequest = null,
                    collections = emptyList(),
                    series = emptyList(),
                    organizationError = null,
                    importMessage = null,
                    bookActionMessage = null,
                    bookActionError = null,
                    isLoggingOut = false,
                    sessionMessage = "Session supprimee localement."
                )
            }
            onLoggedOut()
        }
    }

    fun refreshBooks() {
        loadBooks(reset = true)
    }

    fun searchBooks(query: String) {
        val cleanQuery = query.trim()
        if (uiState.value.booksQuery == cleanQuery && uiState.value.books.isNotEmpty()) {
            return
        }
        _uiState.update { it.copy(booksQuery = cleanQuery) }
        loadBooks(reset = true)
    }

    fun loadMoreBooks() {
        if (uiState.value.isOfflineMode) {
            return
        }
        if (uiState.value.isLoadingMoreBooks || uiState.value.books.size >= uiState.value.booksTotal) {
            return
        }
        loadBooks(reset = false)
    }

    fun loadOrganization() {
        val state = uiState.value
        val serverUrl = state.serverUrl
        if (state.isOfflineMode || serverUrl.isBlank() || state.accessToken.isBlank()) {
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoadingOrganization = true,
                    organizationError = null
                )
            }

            runCatching {
                libraryRepository.listCollections(serverUrl) to libraryRepository.listSeries(serverUrl)
            }.onSuccess { (collections, series) ->
                _uiState.update {
                    it.copy(
                        collections = collections.items,
                        series = series.items,
                        isLoadingOrganization = false,
                        organizationError = null
                    )
                }
            }.onFailure { error ->
                handleApiFailure(error)
                _uiState.update {
                    it.copy(
                        isLoadingOrganization = false,
                        organizationError = error.toFriendlyMessage()
                    )
                }
            }
        }
    }

    fun openSeries(seriesId: String) {
        val state = uiState.value
        val serverUrl = state.serverUrl
        if (state.isOfflineMode || serverUrl.isBlank() || state.accessToken.isBlank()) {
            _uiState.update { it.copy(selectedSeriesError = "Reconnecte Aurelia pour ouvrir cette serie.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    selectedSeries = null,
                    selectedSeriesError = null,
                    isLoadingSeriesDetail = true
                )
            }

            runCatching {
                libraryRepository.getSeries(serverUrl, seriesId)
            }.onSuccess { series ->
                _uiState.update {
                    it.copy(
                        selectedSeries = series,
                        selectedSeriesError = null,
                        isLoadingSeriesDetail = false
                    )
                }
            }.onFailure { error ->
                handleApiFailure(error)
                _uiState.update {
                    it.copy(
                        selectedSeries = null,
                        selectedSeriesError = error.toFriendlyMessage(),
                        isLoadingSeriesDetail = false
                    )
                }
            }
        }
    }

    fun dismissSeries() {
        _uiState.update {
            it.copy(
                selectedSeries = null,
                selectedSeriesError = null,
                isLoadingSeriesDetail = false
            )
        }
    }

    fun openBookAndRead(bookId: String) {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isPreparingReader = true,
                    readerPrepareProgress = 0,
                    readerError = null,
                    bookActionError = null,
                    bookActionMessage = null
                )
            }

            runCatching {
                val book = loadBookDetailForAction(bookId)
                    ?: error("Livre indisponible.")
                val filePath = downloadRepository.prepareBookForReading(uiState.value.serverUrl, book) { progress ->
                    _uiState.update { state -> state.copy(readerPrepareProgress = progress.coerceIn(0, 100)) }
                }
                book to filePath
            }.onSuccess { (book, filePath) ->
                _uiState.update {
                    it.copy(
                        selectedBookId = book.id,
                        selectedBook = book.withLocalProgress(it.localProgress),
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                        readerError = null,
                        readerLaunchRequest = ReaderLaunchRequest(
                            requestId = System.currentTimeMillis(),
                            bookId = book.id,
                            title = book.title,
                            filePath = filePath
                        )
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                        readerError = error.toFriendlyMessage(),
                        bookActionError = error.toFriendlyMessage()
                    )
                }
            }
        }
    }

    fun downloadBook(bookId: String) {
        val state = uiState.value
        if (state.isOfflineMode) {
            _uiState.update { it.copy(bookActionError = "Telechargement indisponible en mode hors ligne.") }
            return
        }
        if (state.serverUrl.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Serveur non configure.") }
            return
        }

        viewModelScope.launch {
            val result = runCatching {
                libraryRepository.getBook(state.serverUrl, bookId)
            }
            val book = result.getOrElse { error ->
                handleApiFailure(error)
                _uiState.update { it.copy(bookActionError = error.toFriendlyMessage()) }
                return@launch
            }
            downloadBookDetail(book)
        }
    }

    fun markBookFinished(bookId: String) {
        val state = uiState.value
        if (state.isOfflineMode || state.serverUrl.isBlank() || state.accessToken.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Reconnecte Aurelia avant de marquer le livre comme lu.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isMutatingBook = true,
                    bookActionError = null,
                    bookActionMessage = null
                )
            }

            val progressPayload = finishedProgressPayload()
            val result = runCatching {
                progressRepository.saveProgress(
                    bookId = bookId,
                    locatorJson = "{}",
                    progressPercent = 100f,
                    chapterLabel = "Termine"
                )
                val updated = libraryRepository.updateBook(
                    serverUrl = state.serverUrl,
                    bookId = bookId,
                    payload = BookUpdateDto(status = "finished")
                )
                runCatching {
                    libraryRepository.putBookProgress(
                        serverUrl = state.serverUrl,
                        bookId = bookId,
                        payloadJson = progressPayload
                    )
                }
                ProgressSyncScheduler.enqueue(appContext)
                updated
            }

            val updated = result.getOrElse { error ->
                handleApiFailure(error)
                _uiState.update {
                    it.copy(
                        isMutatingBook = false,
                        bookActionError = error.toFriendlyMessage()
                    )
                }
                return@launch
            }

            downloadRepository.updateLocalMetadata(updated.copy(status = "finished", progressPercent = 100f))
            val progress = loadLocalProgress()
            _uiState.update {
                val finishedDetail = updated.copy(status = "finished", progressPercent = 100f)
                    .withLocalProgress(progress)
                val finishedListItem = updated.toListItem()
                    .copy(status = "finished", progressPercent = 100f)
                it.copy(
                    localProgress = progress,
                    selectedBook = if (it.selectedBook?.id == updated.id) {
                        finishedDetail
                    } else {
                        it.selectedBook
                    },
                    books = it.books.replace(finishedListItem).withLocalProgress(progress),
                    isMutatingBook = false,
                    bookActionMessage = "Livre marque comme lu a 100%."
                )
            }
            loadOrganization()
        }
    }

    fun toggleFavorite(book: BookListItemDto) {
        updateBook(
            bookId = book.id,
            payload = BookUpdateDto(favorite = !book.favorite),
            successMessage = if (book.favorite) "Livre retire des favoris." else "Livre ajoute aux favoris."
        )
    }

    fun renameBook(bookId: String, title: String) {
        val cleanTitle = title.trim()
        if (cleanTitle.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Le titre est requis.") }
            return
        }
        updateBook(
            bookId = bookId,
            payload = BookUpdateDto(title = cleanTitle),
            successMessage = "Titre mis a jour."
        )
    }

    fun updateBookBasics(
        bookId: String,
        title: String,
        status: String,
        ratingText: String,
        favorite: Boolean
    ) {
        val cleanTitle = title.trim()
        val cleanStatus = status.trim()
        val rating = ratingText.trim().takeIf { it.isNotBlank() }?.toIntOrNull()
        if (cleanTitle.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Le titre est requis.") }
            return
        }
        if (cleanStatus !in setOf("unread", "in_progress", "finished", "abandoned")) {
            _uiState.update { it.copy(bookActionError = "Statut invalide.") }
            return
        }
        if (ratingText.isNotBlank() && (rating == null || rating !in 0..5)) {
            _uiState.update { it.copy(bookActionError = "La note doit etre entre 0 et 5.") }
            return
        }

        updateBook(
            bookId = bookId,
            payload = BookUpdateDto(
                title = cleanTitle,
                status = cleanStatus,
                rating = rating,
                favorite = favorite
            ),
            successMessage = "Livre mis a jour."
        )
    }

    fun importBook(uri: Uri) {
        val state = uiState.value
        if (state.isOfflineMode || state.serverUrl.isBlank() || state.accessToken.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Reconnecte Aurelia avant d'importer un EPUB.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isImportingBook = true,
                    importMessage = null,
                    bookActionError = null
                )
            }

            runCatching {
                val upload = readImportFile(appContext.contentResolver, uri)
                libraryRepository.uploadBook(state.serverUrl, upload.filename, upload.bytes)
            }.onSuccess { response ->
                _uiState.update {
                    it.copy(
                        isImportingBook = false,
                        importMessage = response.warning
                            ?: if (response.bookId != null) "EPUB importe." else "Import termine: ${response.status}."
                    )
                }
                loadBooks(reset = true)
                loadOrganization()
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isImportingBook = false,
                        bookActionError = error.toFriendlyMessage()
                    )
                }
            }
        }
    }

    fun openBook(bookId: String) {
        val state = uiState.value
        val serverUrl = state.serverUrl
        if (state.isOfflineMode) {
            openLocalBook(bookId)
            return
        }
        if (serverUrl.isBlank()) {
            openLocalBook(bookId, fallbackError = "Serveur non configure.")
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    selectedBookId = bookId,
                    selectedBookError = null,
                    isLoadingBookDetail = true
                )
            }

            runCatching {
                libraryRepository.getBook(serverUrl, bookId)
            }.onSuccess { book ->
                _uiState.update {
                    it.copy(
                        selectedBook = book.withLocalProgress(it.localProgress),
                        selectedBookError = null,
                        isLoadingBookDetail = false
                    )
                }
            }.onFailure { error ->
                handleApiFailure(error)
                val localBook = downloadRepository.localBookDetail(bookId)
                if (localBook != null && error !is ApiException) {
                    val progress = loadLocalProgress()
                    _uiState.update {
                        it.copy(
                            isOfflineMode = true,
                            selectedBook = localBook.withLocalProgress(progress),
                            selectedBookError = null,
                            isLoadingBookDetail = false,
                            sessionMessage = "Serveur indisponible, fiche locale ouverte."
                        )
                    }
                } else {
                    _uiState.update {
                        it.copy(
                            selectedBookError = error.toFriendlyMessage(),
                            isLoadingBookDetail = false
                        )
                    }
                }
            }
        }
    }

    fun downloadSelectedBook() {
        val state = uiState.value
        val book = state.selectedBook ?: return
        val serverUrl = state.serverUrl
        if (state.isOfflineMode) {
            setDownloadState(
                book.id,
                BookDownloadUiState(
                    status = DownloadStatus.Failed,
                    error = "Telechargement indisponible en mode hors ligne."
                )
            )
            return
        }
        if (serverUrl.isBlank()) {
            _uiState.update {
                it.copy(
                    downloadStates = it.downloadStates + (
                        book.id to BookDownloadUiState(
                            status = DownloadStatus.Failed,
                            error = "Serveur non configure."
                        )
                    )
                )
            }
            return
        }

        viewModelScope.launch {
            setDownloadState(book.id, BookDownloadUiState(status = DownloadStatus.Downloading, progress = 0))

            runCatching {
                downloadRepository.downloadBook(serverUrl, book) { progress ->
                    setDownloadState(
                        book.id,
                        BookDownloadUiState(
                            status = DownloadStatus.Downloading,
                            progress = progress
                        )
                    )
                }
            }.onSuccess {
                _uiState.update {
                    val offlineIds = it.offlineBookIds + book.id
                    it.copy(
                        offlineBookIds = offlineIds,
                        offlineBookCount = offlineIds.size,
                        selectedBook = it.selectedBook?.takeIf { selected -> selected.id == book.id }
                            ?.copy(isOfflineAvailable = true) ?: it.selectedBook,
                        downloadStates = it.downloadStates + (
                            book.id to BookDownloadUiState(
                                status = DownloadStatus.Downloaded,
                                progress = 100
                            )
                        )
                    )
                }
            }.onFailure { error ->
                setDownloadState(
                    book.id,
                    BookDownloadUiState(
                        status = DownloadStatus.Failed,
                        error = error.toFriendlyMessage()
                    )
                )
            }
        }
    }

    fun removeSelectedBookDownload() {
        val bookId = uiState.value.selectedBook?.id ?: return
        removeBookDownload(bookId)
    }

    fun removeBookDownload(bookId: String) {
        viewModelScope.launch {
            runCatching {
                downloadRepository.removeDownload(bookId)
            }.onSuccess {
                val offlineIds = downloadRepository.downloadedBookIds()
                _uiState.update {
                    it.copy(
                        offlineBookIds = offlineIds,
                        offlineBookCount = offlineIds.size,
                        isOfflineMode = it.isOfflineMode && offlineIds.isNotEmpty(),
                        selectedBook = it.selectedBook?.takeIf { selected -> selected.id == bookId }
                            ?.copy(isOfflineAvailable = false) ?: it.selectedBook,
                        books = it.books.map { row ->
                            if (row.id == bookId) row.copy(isOfflineAvailable = false) else row
                        },
                        downloadStates = it.downloadStates - bookId
                    )
                }
            }.onFailure { error ->
                setDownloadState(
                    bookId,
                    BookDownloadUiState(
                        status = DownloadStatus.Failed,
                        error = error.toFriendlyMessage()
                    )
                )
            }
        }
    }

    fun openSelectedBookReader() {
        val book = uiState.value.selectedBook ?: return
        val serverUrl = uiState.value.serverUrl

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isPreparingReader = true,
                    readerPrepareProgress = 0,
                    readerError = null
                )
            }

            runCatching {
                downloadRepository.prepareBookForReading(serverUrl, book) { progress ->
                    _uiState.update {
                        it.copy(readerPrepareProgress = progress.coerceIn(0, 100))
                    }
                }
            }.onSuccess { filePath ->
                _uiState.update {
                    it.copy(
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                        readerError = null,
                        readerLaunchRequest = ReaderLaunchRequest(
                            requestId = System.currentTimeMillis(),
                            bookId = book.id,
                            title = book.title,
                            filePath = filePath
                        )
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                        readerError = error.toFriendlyMessage()
                    )
                }
            }
        }
    }

    fun consumeReaderLaunchRequest() {
        _uiState.update { it.copy(readerLaunchRequest = null) }
    }

    fun refreshLocalProgress() {
        viewModelScope.launch {
            runCatching {
                progressRepository.allProgress()
            }.onSuccess { progress ->
                _uiState.update {
                    it.copy(
                        localProgress = progress,
                        books = it.books.withLocalProgress(progress),
                        selectedBook = it.selectedBook?.withLocalProgress(progress)
                    )
                }
            }
        }
    }

    private fun updateBook(bookId: String, payload: BookUpdateDto, successMessage: String) {
        val state = uiState.value
        if (state.isOfflineMode || state.serverUrl.isBlank() || state.accessToken.isBlank()) {
            _uiState.update { it.copy(bookActionError = "Reconnecte Aurelia avant de modifier ce livre.") }
            return
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isMutatingBook = true,
                    bookActionError = null,
                    bookActionMessage = null
                )
            }

            val result = runCatching {
                libraryRepository.updateBook(state.serverUrl, bookId, payload)
            }
            val updated = result.getOrElse { error ->
                handleApiFailure(error)
                _uiState.update {
                    it.copy(
                        isMutatingBook = false,
                        bookActionError = error.toFriendlyMessage()
                    )
                }
                return@launch
            }

            downloadRepository.updateLocalMetadata(updated)
            _uiState.update {
                it.copy(
                    selectedBook = if (it.selectedBook?.id == updated.id) {
                        updated.withLocalProgress(it.localProgress)
                    } else {
                        it.selectedBook
                    },
                    books = it.books.replace(updated.toListItem()).withLocalProgress(it.localProgress),
                    isMutatingBook = false,
                    bookActionMessage = successMessage
                )
            }
            loadOrganization()
        }
    }

    private suspend fun downloadBookDetail(book: BookDetailDto) {
        setDownloadState(book.id, BookDownloadUiState(status = DownloadStatus.Downloading, progress = 0))

        runCatching {
            downloadRepository.downloadBook(uiState.value.serverUrl, book) { progress ->
                setDownloadState(
                    book.id,
                    BookDownloadUiState(
                        status = DownloadStatus.Downloading,
                        progress = progress
                    )
                )
            }
        }.onSuccess {
            _uiState.update {
                val offlineIds = it.offlineBookIds + book.id
                it.copy(
                    offlineBookIds = offlineIds,
                    offlineBookCount = offlineIds.size,
                    selectedBook = it.selectedBook?.takeIf { selected -> selected.id == book.id }
                        ?.copy(isOfflineAvailable = true) ?: it.selectedBook,
                    books = it.books.map { row ->
                        if (row.id == book.id) row.copy(isOfflineAvailable = true) else row
                    },
                    downloadStates = it.downloadStates + (
                        book.id to BookDownloadUiState(
                            status = DownloadStatus.Downloaded,
                            progress = 100
                        )
                    ),
                    bookActionMessage = "Livre telecharge pour le hors ligne."
                )
            }
        }.onFailure { error ->
            setDownloadState(
                book.id,
                BookDownloadUiState(
                    status = DownloadStatus.Failed,
                    error = error.toFriendlyMessage()
                )
            )
            _uiState.update { it.copy(bookActionError = error.toFriendlyMessage()) }
        }
    }

    private suspend fun loadBookDetailForAction(bookId: String): BookDetailDto? {
        val state = uiState.value
        return if (state.isOfflineMode || state.serverUrl.isBlank()) {
            downloadRepository.localBookDetail(bookId)
        } else {
            runCatching {
                libraryRepository.getBook(state.serverUrl, bookId)
            }.getOrElse { error ->
                if (error !is ApiException) {
                    downloadRepository.localBookDetail(bookId)
                } else {
                    throw error
                }
            }
        }
    }

    private data class ImportFile(
        val filename: String,
        val bytes: ByteArray
    )

    private suspend fun readImportFile(contentResolver: ContentResolver, uri: Uri): ImportFile =
        withContext(Dispatchers.IO) {
            val filename = contentResolver.displayName(uri)
                ?.takeIf { it.lowercase().endsWith(".epub") }
                ?: "aurelia-import.epub"
            val bytes = contentResolver.openInputStream(uri)?.use { it.readBytes() }
                ?: throw IOException("Fichier EPUB inaccessible.")
            require(bytes.isNotEmpty()) { "Fichier EPUB vide." }
            ImportFile(filename = filename, bytes = bytes)
        }

    private fun restoreSession() {
        viewModelScope.launch {
            val storedSession = authRepository.loadSession()
            val offlineIds = downloadRepository.downloadedBookIds()
            _uiState.update {
                it.copy(
                    serverUrl = storedSession.serverUrl,
                    accessToken = storedSession.accessToken,
                    offlineBookIds = offlineIds,
                    offlineBookCount = offlineIds.size,
                    sessionMessage = null
                )
            }

            if (storedSession.serverUrl.isBlank() || storedSession.accessToken.isBlank()) {
                _uiState.update { it.copy(isInitialized = true) }
                return@launch
            }

            runCatching {
                authRepository.currentUser(storedSession.serverUrl)
            }.onSuccess { user ->
                _uiState.update {
                    it.copy(
                        currentUser = user,
                        isOfflineMode = false,
                        isInitialized = true,
                        sessionMessage = "Session restauree."
                    )
                }
                refreshOfflineBookIds()
                refreshLocalProgress()
                ProgressSyncScheduler.enqueue(appContext)
                loadBooks(reset = true)
                loadOrganization()
            }.onFailure { error ->
                if (error is ApiException && error.statusCode == 401) {
                    authRepository.clearToken()
                    _uiState.update {
                        it.copy(
                            accessToken = "",
                            currentUser = null,
                            isOfflineMode = false,
                            isInitialized = true,
                            sessionMessage = "Session expiree, reconnecte-toi."
                        )
                    }
                    return@onFailure
                }

                val enteredOffline = enterOfflineMode(
                    message = "Serveur indisponible, mode hors ligne active.",
                    query = uiState.value.booksQuery
                )
                if (!enteredOffline) {
                    _uiState.update {
                        it.copy(
                            currentUser = null,
                            isOfflineMode = false,
                            isInitialized = true,
                            sessionMessage = "Serveur indisponible pour restaurer la session."
                        )
                    }
                }
            }
        }
    }

    private fun loadBooks(reset: Boolean) {
        val state = uiState.value
        val serverUrl = state.serverUrl
        if (state.isOfflineMode) {
            viewModelScope.launch {
                loadOfflineBooks(query = state.booksQuery)
            }
            return
        }
        if (serverUrl.isBlank() || state.accessToken.isBlank()) {
            return
        }
        val offset = if (reset) 0 else state.books.size
        val query = state.booksQuery
        val limit = 50

        if (reset) {
            booksJob?.cancel()
        }

        val job = viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoadingBooks = reset,
                    isLoadingMoreBooks = !reset,
                    books = if (reset && it.books.isEmpty()) emptyList() else it.books,
                    booksError = null
                )
            }

            runCatching {
                libraryRepository.listBooks(
                    serverUrl = serverUrl,
                    query = query.ifBlank { null },
                    limit = limit,
                    offset = offset
                )
            }.onSuccess { response ->
                val progress = loadLocalProgress()
                _uiState.update {
                    it.copy(
                        localProgress = progress,
                        books = if (reset) {
                            response.items.withLocalProgress(progress)
                        } else {
                            (it.books + response.items).withLocalProgress(progress)
                        },
                        booksTotal = response.total,
                        booksError = null,
                        isLoadingBooks = false,
                        isLoadingMoreBooks = false
                    )
                }
            }.onFailure { error ->
                handleApiFailure(error)
                if (error !is ApiException) {
                    val enteredOffline = enterOfflineMode(
                        message = "Serveur indisponible, bibliotheque hors ligne affichee.",
                        query = query
                    )
                    if (enteredOffline) {
                        return@onFailure
                    }
                }
                _uiState.update {
                    it.copy(
                        booksError = error.toFriendlyMessage(),
                        isLoadingBooks = false,
                        isLoadingMoreBooks = false
                    )
                }
            }
        }

        if (reset) {
            booksJob = job
        }
    }

    private fun refreshOfflineBookIds() {
        viewModelScope.launch {
            runCatching {
                downloadRepository.downloadedBookIds()
            }.onSuccess { ids ->
                _uiState.update {
                    it.copy(
                        offlineBookIds = ids,
                        offlineBookCount = ids.size
                    )
                }
            }
        }
    }

    private fun openLocalBook(bookId: String, fallbackError: String = "Livre hors ligne indisponible.") {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    selectedBookId = bookId,
                    selectedBookError = null,
                    isLoadingBookDetail = true
                )
            }

            val localBook = downloadRepository.localBookDetail(bookId)
            val progress = loadLocalProgress()
            _uiState.update {
                if (localBook == null) {
                    it.copy(
                        selectedBookError = fallbackError,
                        isLoadingBookDetail = false
                    )
                } else {
                    it.copy(
                        selectedBook = localBook.withLocalProgress(progress),
                        selectedBookError = null,
                        isLoadingBookDetail = false,
                        localProgress = progress
                    )
                }
            }
        }
    }

    private suspend fun enterOfflineMode(message: String, query: String): Boolean {
        val hasOfflineBooks = loadOfflineBooks(query = query, message = message)
        if (!hasOfflineBooks) {
            return false
        }
        _uiState.update {
            it.copy(
                currentUser = null,
                isOfflineMode = true,
                isInitialized = true,
                isLoadingBooks = false,
                isLoadingMoreBooks = false,
                booksError = null,
                serverError = null,
                loginError = null
            )
        }
        return true
    }

    private suspend fun loadOfflineBooks(query: String, message: String? = null): Boolean {
        val allBooks = downloadRepository.downloadedBooks()
        val progress = loadLocalProgress()
        val filteredBooks = allBooks
            .matchingOfflineQuery(query)
            .withLocalProgress(progress)

        _uiState.update {
            it.copy(
                books = filteredBooks,
                booksTotal = filteredBooks.size,
                offlineBookIds = allBooks.map { book -> book.id }.toSet(),
                offlineBookCount = allBooks.size,
                localProgress = progress,
                booksError = null,
                isLoadingBooks = false,
                isLoadingMoreBooks = false,
                sessionMessage = message ?: it.sessionMessage
            )
        }
        return allBooks.isNotEmpty()
    }

    private suspend fun loadLocalProgress(): Map<String, BookProgressSnapshot> {
        return runCatching { progressRepository.allProgress() }.getOrDefault(uiState.value.localProgress)
    }

    private fun setDownloadState(bookId: String, state: BookDownloadUiState) {
        _uiState.update {
            it.copy(downloadStates = it.downloadStates + (bookId to state))
        }
    }

    private fun finishedProgressPayload(): String {
        return JSONObject()
            .put("progress_percent", 100f)
            .put("chapter_label", "Termine")
            .put("location_json", JSONObject())
            .put("client_updated_at", Instant.now().toString())
            .put("device_id", "android-reader")
            .toString()
    }

    private fun handleApiFailure(error: Throwable) {
        if (error is ApiException && error.statusCode == 401) {
            viewModelScope.launch {
                authRepository.clearToken()
                _uiState.update {
                    it.copy(
                        accessToken = "",
                        currentUser = null,
                        sessionMessage = "Session expiree, reconnecte-toi."
                    )
                }
            }
        }
    }

    private fun Throwable.toFriendlyMessage(): String {
        return when (this) {
            is ApiException -> message ?: "Erreur API Aurelia."
            is IllegalArgumentException -> message ?: "Configuration invalide."
            is IOException -> "Connexion impossible. Verifie l'adresse IP, le port et le reseau."
            else -> message ?: "Erreur inattendue."
        }
    }

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory {
            val appContext = context.applicationContext
            val authSession = AuthSession()
            val apiClient = ApiClient(authSession)
            val authRepository = AuthRepository(
                apiClient = apiClient,
                authSession = authSession,
                serverSettingsStore = ServerSettingsStore(appContext),
                tokenStore = TokenStore(appContext)
            )
            val libraryRepository = LibraryRepository(apiClient = apiClient)
            val database = AppDatabaseProvider.get(appContext)
            val downloadRepository = DownloadRepository(
                apiClient = apiClient,
                bookDao = database.bookDao(),
                downloadDao = database.downloadDao(),
                fileStore = BookFileStore(appContext)
            )
            val progressRepository = ProgressRepository(
                progressDao = database.progressDao(),
                syncEventDao = database.syncEventDao()
            )

            return object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return AppViewModel(
                        appContext,
                        authRepository,
                        libraryRepository,
                        downloadRepository,
                        progressRepository
                    ) as T
                }
            }
        }
    }
}

private fun List<BookListItemDto>.withLocalProgress(
    progress: Map<String, BookProgressSnapshot>
): List<BookListItemDto> {
    return map { book ->
        progress[book.id]?.let { snapshot ->
            book.copy(progressPercent = snapshot.progressPercent)
        } ?: book
    }
}

private fun List<BookListItemDto>.replace(book: BookListItemDto): List<BookListItemDto> {
    return map { current -> if (current.id == book.id) book else current }
}

private fun BookDetailDto.toListItem(): BookListItemDto {
    return BookListItemDto(
        id = id,
        title = title,
        authors = authors,
        coverUrl = coverUrl,
        status = status,
        rating = rating,
        favorite = favorite,
        progressPercent = progressPercent,
        isOfflineAvailable = isOfflineAvailable,
        addedAt = addedAt,
        lastOpenedAt = lastOpenedAt
    )
}

private fun List<BookListItemDto>.matchingOfflineQuery(query: String): List<BookListItemDto> {
    val cleanQuery = query.trim()
    if (cleanQuery.isBlank()) {
        return this
    }
    return filter { book ->
        book.title.contains(cleanQuery, ignoreCase = true) ||
            book.authors.any { author -> author.contains(cleanQuery, ignoreCase = true) }
    }
}

private fun BookDetailDto.withLocalProgress(
    progress: Map<String, BookProgressSnapshot>
): BookDetailDto {
    return progress[id]?.let { copy(progressPercent = it.progressPercent) } ?: this
}

private fun ContentResolver.displayName(uri: Uri): String? {
    return query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
        val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        if (index >= 0 && cursor.moveToFirst()) {
            cursor.getString(index)
        } else {
            null
        }
    }
}

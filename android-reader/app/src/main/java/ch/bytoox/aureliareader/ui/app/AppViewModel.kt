package ch.bytoox.aureliareader.ui.app

import android.content.Context
import ch.bytoox.aureliareader.core.files.BookFileStore
import ch.bytoox.aureliareader.core.network.ApiClient
import ch.bytoox.aureliareader.core.network.ApiException
import ch.bytoox.aureliareader.core.network.AuthSession
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.core.network.BookListItemDto
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
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

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
    val isCheckingServer: Boolean = false,
    val isLoggingIn: Boolean = false,
    val isLoggingOut: Boolean = false
) {
    val isAuthenticated: Boolean
        get() = currentUser != null
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
                        isLoggingIn = false,
                        loginError = null,
                        sessionMessage = "Connecte en Bearer."
                    )
                }
                refreshOfflineBookIds()
                ProgressSyncScheduler.enqueue(appContext)
                loadBooks(reset = true)
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

    fun logout(onLoggedOut: () -> Unit) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoggingOut = true, sessionMessage = null) }
            authRepository.logout(uiState.value.serverUrl)
            _uiState.update {
                it.copy(
                    accessToken = "",
                    currentUser = null,
                    books = emptyList(),
                    booksTotal = 0,
                    booksQuery = "",
                    booksError = null,
                    selectedBookId = null,
                    selectedBook = null,
                    selectedBookError = null,
                        offlineBookIds = emptySet(),
                        downloadStates = emptyMap(),
                        localProgress = emptyMap(),
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                    readerError = null,
                    readerLaunchRequest = null,
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
        if (uiState.value.isLoadingMoreBooks || uiState.value.books.size >= uiState.value.booksTotal) {
            return
        }
        loadBooks(reset = false)
    }

    fun openBook(bookId: String) {
        val serverUrl = uiState.value.serverUrl
        if (serverUrl.isBlank()) {
            _uiState.update { it.copy(selectedBookError = "Serveur non configure.") }
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
                _uiState.update {
                    it.copy(
                        selectedBookError = error.toFriendlyMessage(),
                        isLoadingBookDetail = false
                    )
                }
            }
        }
    }

    fun downloadSelectedBook() {
        val state = uiState.value
        val book = state.selectedBook ?: return
        val serverUrl = state.serverUrl
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
                    it.copy(
                        offlineBookIds = it.offlineBookIds + book.id,
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

        viewModelScope.launch {
            runCatching {
                downloadRepository.removeDownload(bookId)
            }.onSuccess {
                _uiState.update {
                    it.copy(
                        offlineBookIds = it.offlineBookIds - bookId,
                        selectedBook = it.selectedBook?.takeIf { selected -> selected.id == bookId }
                            ?.copy(isOfflineAvailable = false) ?: it.selectedBook,
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
            if (serverUrl.isBlank()) {
                _uiState.update {
                    it.copy(
                        isPreparingReader = false,
                        readerPrepareProgress = null,
                        readerError = "Serveur non configure."
                    )
                }
                return@launch
            }

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

    private fun restoreSession() {
        viewModelScope.launch {
            val storedSession = authRepository.loadSession()
            _uiState.update {
                it.copy(
                    serverUrl = storedSession.serverUrl,
                    accessToken = storedSession.accessToken,
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
                        isInitialized = true,
                        sessionMessage = "Session restauree."
                    )
                }
                refreshOfflineBookIds()
                refreshLocalProgress()
                ProgressSyncScheduler.enqueue(appContext)
                loadBooks(reset = true)
            }.onFailure { error ->
                if (error is ApiException && error.statusCode == 401) {
                    authRepository.clearToken()
                }
                _uiState.update {
                    it.copy(
                        accessToken = "",
                        currentUser = null,
                        isInitialized = true,
                        sessionMessage = if (error is ApiException && error.statusCode == 401) {
                            "Session expiree, reconnecte-toi."
                        } else {
                            "Serveur indisponible pour restaurer la session."
                        }
                    )
                }
            }
        }
    }

    private fun loadBooks(reset: Boolean) {
        val state = uiState.value
        val serverUrl = state.serverUrl
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
                _uiState.update { it.copy(offlineBookIds = ids) }
            }
        }
    }

    private suspend fun loadLocalProgress(): Map<String, BookProgressSnapshot> {
        return runCatching { progressRepository.allProgress() }.getOrDefault(uiState.value.localProgress)
    }

    private fun setDownloadState(bookId: String, state: BookDownloadUiState) {
        _uiState.update {
            it.copy(downloadStates = it.downloadStates + (bookId to state))
        }
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

private fun BookDetailDto.withLocalProgress(
    progress: Map<String, BookProgressSnapshot>
): BookDetailDto {
    return progress[id]?.let { copy(progressPercent = it.progressPercent) } ?: this
}

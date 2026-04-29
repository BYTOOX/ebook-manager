package ch.bytoox.aureliareader.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.SizeTransform
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.CloudDone
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Favorite
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.MoreVert
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Upload
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import ch.bytoox.aureliareader.core.network.BookDetailDto
import ch.bytoox.aureliareader.core.network.BookListItemDto
import ch.bytoox.aureliareader.core.network.CollectionSummaryDto
import ch.bytoox.aureliareader.core.network.SeriesDetailDto
import ch.bytoox.aureliareader.core.network.SeriesSummaryDto
import ch.bytoox.aureliareader.ui.app.BookDownloadUiState
import ch.bytoox.aureliareader.ui.app.DownloadStatus
import coil.compose.AsyncImage
import coil.request.ImageRequest
import kotlin.math.roundToInt
import kotlinx.coroutines.delay

@Composable
fun LoadingScreen() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            CircularProgressIndicator()
            Text("Chargement Aurelia Reader", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun ServerSetupScreen(
    serverUrl: String,
    isCheckingServer: Boolean,
    serverStatus: String?,
    serverError: String?,
    canContinueOffline: Boolean,
    offlineBookCount: Int,
    onServerUrlChange: (String) -> Unit,
    onCheckServer: () -> Unit,
    onContinueOffline: () -> Unit
) {
    AureliaScreen {
        HeaderBlock(
            eyebrow = "Serveur",
            title = "Adresse Aurelia",
            subtitle = "Adresse accessible depuis ce telephone. Indique le port utilise par le serveur."
        )
        OutlinedTextField(
            value = serverUrl,
            onValueChange = onServerUrlChange,
            label = { Text("URL serveur") },
            placeholder = { Text("http://192.168.2.6:3000") },
            leadingIcon = { Icon(Icons.Outlined.Wifi, contentDescription = null) },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Uri,
                imeAction = ImeAction.Done,
                autoCorrectEnabled = false
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = onCheckServer, enabled = !isCheckingServer) {
                if (isCheckingServer) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Text("Verifier")
                }
            }
        }
        if (canContinueOffline) {
            OutlinedButton(onClick = onContinueOffline, modifier = Modifier.fillMaxWidth()) {
                Text("Continuer hors ligne ($offlineBookCount)")
            }
        }
        serverStatus?.let { StatusPill(label = it) }
        serverError?.let { ErrorText(message = it) }
    }
}

@Composable
fun LoginScreen(
    serverUrl: String,
    isLoggingIn: Boolean,
    loginError: String?,
    sessionMessage: String?,
    canContinueOffline: Boolean,
    offlineBookCount: Int,
    onLogin: (String, String) -> Unit,
    onChangeServer: () -> Unit,
    onContinueOffline: () -> Unit
) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }

    AureliaScreen {
        HeaderBlock(
            eyebrow = "Compte",
            title = "Connexion",
            subtitle = "Merci de rentrer vos identifiants."
        )
        StatusPill(label = serverUrl.ifBlank { "Serveur non configure" })
        sessionMessage?.let { StatusPill(label = it) }
        OutlinedButton(onClick = onChangeServer, modifier = Modifier.fillMaxWidth()) {
            Text("Modifier le serveur")
        }
        if (canContinueOffline) {
            OutlinedButton(onClick = onContinueOffline, modifier = Modifier.fillMaxWidth()) {
                Text("Continuer hors ligne ($offlineBookCount)")
            }
        }
        OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            label = { Text("Identifiant") },
            placeholder = { Text("admin") },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Text,
                imeAction = ImeAction.Next,
                autoCorrectEnabled = false
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Mot de passe") },
            placeholder = { Text("Mot de passe") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done,
                autoCorrectEnabled = false
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = { onLogin(username, password) },
            enabled = !isLoggingIn,
            modifier = Modifier.fillMaxWidth()
        ) {
            if (isLoggingIn) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Text("Se connecter")
            }
        }
        loginError?.let { ErrorText(message = it) }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun HomeScreen(
    displayName: String?,
    serverUrl: String,
    books: List<BookListItemDto>,
    total: Int,
    accessToken: String,
    offlineBookIds: Set<String>,
    isOfflineMode: Boolean,
    isLoading: Boolean,
    isReconnecting: Boolean,
    isMutatingBook: Boolean,
    error: String?,
    actionMessage: String?,
    actionError: String?,
    onRefresh: () -> Unit,
    onReconnect: () -> Unit,
    onOpenLibrary: () -> Unit,
    onOpenBook: (BookListItemDto) -> Unit,
    onReadBook: (BookListItemDto) -> Unit,
    onDownloadBook: (BookListItemDto) -> Unit,
    onRemoveDownload: (BookListItemDto) -> Unit,
    onMarkFinished: (BookListItemDto) -> Unit,
    onToggleFavorite: (BookListItemDto) -> Unit,
    onRenameBook: (BookListItemDto, String) -> Unit
) {
    val currentBook = books.firstOrNull()
    var actionBookId by rememberSaveable { mutableStateOf<String?>(null) }
    var renameBookId by rememberSaveable { mutableStateOf<String?>(null) }
    val actionBook = actionBookId?.let { id -> books.firstOrNull { it.id == id } }
    val renameBook = renameBookId?.let { id -> books.firstOrNull { it.id == id } }

    AureliaScreen {
        HeaderBlock(
            eyebrow = if (isOfflineMode) {
                "Hors ligne"
            } else {
                displayName?.let { "Connecte: $it" } ?: "Connecte"
            },
            title = currentBook?.title ?: "Bibliotheque Aurelia",
            subtitle = currentBook?.authorLine ?: "Aucun livre charge"
        )
        StatusPill(
            label = if (isOfflineMode) {
                "Mode hors ligne: livres telecharges uniquement"
            } else {
                "API connectee: $serverUrl"
            }
        )
        currentBook?.progressPercent?.let { progress ->
            LinearProgressIndicator(
                progress = { progressFraction(progress) },
                modifier = Modifier.fillMaxWidth()
            )
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(onClick = { currentBook?.let(onOpenBook) }, enabled = currentBook != null) {
                Icon(Icons.Outlined.PlayArrow, contentDescription = null)
                Text("Fiche")
            }
            OutlinedButton(onClick = onOpenLibrary) {
                Text("Bibliotheque")
            }
            OutlinedButton(onClick = onReconnect, enabled = !isReconnecting) {
                if (isReconnecting) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Outlined.Refresh, contentDescription = null)
                }
                Text("Reconnecter")
            }
        }
        StatusPill(label = if (isOfflineMode) "$total livre(s) hors ligne" else "$total livre(s) serveur")
        actionMessage?.let { StatusPill(label = it) }
        error?.let { ErrorText(message = it) }
        actionError?.let { ErrorText(message = it) }
        if (isLoading) {
            LoadingRow("Chargement des livres")
        } else if (books.isEmpty()) {
            EmptyState(
                title = if (isOfflineMode) "Aucun livre hors ligne" else "Aucun livre",
                message = if (isOfflineMode) {
                    "Reconnecte Aurelia puis telecharge un livre pour le garder sur ce telephone."
                } else {
                    "Importe un EPUB depuis Aurelia Web, puis recharge la bibliotheque Android."
                }
            )
            OutlinedButton(onClick = onReconnect, enabled = !isReconnecting) {
                if (isReconnecting) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                }
                Text("Reconnecter au serveur")
            }
            OutlinedButton(onClick = onRefresh, enabled = !isOfflineMode && !isLoading) {
                Text("Recharger")
            }
        } else {
            SectionTitle("Recents")
            books.take(5).forEach { book ->
                BookRow(
                    book = book,
                    accessToken = accessToken,
                    isDownloaded = book.isOfflineAvailable || book.id in offlineBookIds,
                    onClick = { onOpenBook(book) },
                    onAction = { actionBookId = book.id }
                )
            }
        }
    }
    BookActionSheet(
        book = actionBook,
        isDownloaded = actionBook?.let { it.isOfflineAvailable || it.id in offlineBookIds } == true,
        isOfflineMode = isOfflineMode,
        isBusy = isMutatingBook,
        onDismiss = { actionBookId = null },
        onRead = {
            actionBookId = null
            onReadBook(it)
        },
        onDownload = {
            actionBookId = null
            onDownloadBook(it)
        },
        onRemoveDownload = {
            actionBookId = null
            onRemoveDownload(it)
        },
        onMarkFinished = {
            actionBookId = null
            onMarkFinished(it)
        },
        onToggleFavorite = {
            actionBookId = null
            onToggleFavorite(it)
        },
        onRename = {
            renameBookId = it.id
            actionBookId = null
        }
    )
    RenameBookDialog(
        book = renameBook,
        isBusy = isMutatingBook,
        onDismiss = { renameBookId = null },
        onConfirm = { book, title ->
            renameBookId = null
            onRenameBook(book, title)
        }
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LibraryScreen(
    books: List<BookListItemDto>,
    total: Int,
    searchQuery: String,
    accessToken: String,
    offlineBookIds: Set<String>,
    isOfflineMode: Boolean,
    isLoading: Boolean,
    isLoadingMore: Boolean,
    isReconnecting: Boolean,
    isMutatingBook: Boolean,
    error: String?,
    actionMessage: String?,
    actionError: String?,
    onSearch: (String) -> Unit,
    onRefresh: () -> Unit,
    onReconnect: () -> Unit,
    onLoadMore: () -> Unit,
    onOpenBook: (BookListItemDto) -> Unit,
    onReadBook: (BookListItemDto) -> Unit,
    onDownloadBook: (BookListItemDto) -> Unit,
    onRemoveDownload: (BookListItemDto) -> Unit,
    onMarkFinished: (BookListItemDto) -> Unit,
    onToggleFavorite: (BookListItemDto) -> Unit,
    onRenameBook: (BookListItemDto, String) -> Unit
) {
    var localSearchQuery by rememberSaveable { mutableStateOf(searchQuery) }
    var actionBookId by rememberSaveable { mutableStateOf<String?>(null) }
    var renameBookId by rememberSaveable { mutableStateOf<String?>(null) }
    val actionBook = actionBookId?.let { id -> books.firstOrNull { it.id == id } }
    val renameBook = renameBookId?.let { id -> books.firstOrNull { it.id == id } }

    LaunchedEffect(searchQuery) {
        if (searchQuery != localSearchQuery) {
            localSearchQuery = searchQuery
        }
    }

    LaunchedEffect(localSearchQuery) {
        delay(550)
        onSearch(localSearchQuery)
    }

    AureliaScreen {
        HeaderBlock(
            eyebrow = "Bibliotheque",
            title = if (isOfflineMode) "Livres hors ligne" else "Livres serveur",
            subtitle = if (isOfflineMode) {
                "$total livre(s) telecharge(s) sur ce telephone."
            } else {
                "$total livre(s) dans Aurelia."
            }
        )
        OutlinedTextField(
            value = localSearchQuery,
            onValueChange = { localSearchQuery = it },
            label = { Text("Recherche") },
            leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null) },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Text,
                imeAction = ImeAction.Search,
                autoCorrectEnabled = false
            ),
            modifier = Modifier.fillMaxWidth()
        )
        if (isLoading && books.isNotEmpty()) {
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton(onClick = onRefresh, enabled = !isLoading && !isOfflineMode) {
                Text(if (isOfflineMode) "Hors ligne" else "Recharger")
            }
            OutlinedButton(onClick = onReconnect, enabled = !isReconnecting) {
                if (isReconnecting) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Outlined.Refresh, contentDescription = null)
                }
                Text("Reconnecter")
            }
            if (localSearchQuery.isNotBlank()) {
                TextButton(onClick = { localSearchQuery = "" }) {
                    Text("Effacer")
                }
            }
        }
        actionMessage?.let { StatusPill(label = it) }
        error?.let { ErrorText(message = it) }
        actionError?.let { ErrorText(message = it) }
        if (isLoading && books.isEmpty()) {
            LoadingRow("Chargement bibliotheque")
        } else if (books.isEmpty()) {
            EmptyState(
                title = "Aucun resultat",
                message = if (isOfflineMode) {
                    "Aucun livre telecharge ne correspond a cette recherche."
                } else {
                    "Aucun livre ne correspond a cette recherche."
                }
            )
        } else {
            books.forEach { book ->
                BookRow(
                    book = book,
                    accessToken = accessToken,
                    isDownloaded = book.isOfflineAvailable || book.id in offlineBookIds,
                    onClick = { onOpenBook(book) },
                    onAction = { actionBookId = book.id }
                )
            }
            if (!isOfflineMode && books.size < total) {
                OutlinedButton(
                    onClick = onLoadMore,
                    enabled = !isLoadingMore,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (isLoadingMore) {
                        CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    } else {
                        Text("Charger plus")
                    }
                }
            }
        }
    }
    BookActionSheet(
        book = actionBook,
        isDownloaded = actionBook?.let { it.isOfflineAvailable || it.id in offlineBookIds } == true,
        isOfflineMode = isOfflineMode,
        isBusy = isMutatingBook,
        onDismiss = { actionBookId = null },
        onRead = {
            actionBookId = null
            onReadBook(it)
        },
        onDownload = {
            actionBookId = null
            onDownloadBook(it)
        },
        onRemoveDownload = {
            actionBookId = null
            onRemoveDownload(it)
        },
        onMarkFinished = {
            actionBookId = null
            onMarkFinished(it)
        },
        onToggleFavorite = {
            actionBookId = null
            onToggleFavorite(it)
        },
        onRename = {
            renameBookId = it.id
            actionBookId = null
        }
    )
    RenameBookDialog(
        book = renameBook,
        isBusy = isMutatingBook,
        onDismiss = { renameBookId = null },
        onConfirm = { book, title ->
            renameBookId = null
            onRenameBook(book, title)
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun BookDetailScreen(
    book: BookDetailDto?,
    accessToken: String,
    offlineBookIds: Set<String>,
    downloadState: BookDownloadUiState?,
    progressSyncLabel: String?,
    loadingBookId: String?,
    isPreparingReader: Boolean,
    readerPrepareProgress: Int?,
    readerError: String?,
    isOfflineMode: Boolean,
    isMutatingBook: Boolean,
    isLoading: Boolean,
    error: String?,
    actionMessage: String?,
    actionError: String?,
    onRead: () -> Unit,
    onDownload: () -> Unit,
    onRemoveDownload: () -> Unit,
    onMarkFinished: () -> Unit,
    onUpdateBook: (String, String, String, Boolean) -> Unit,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onOpenRelatedBook: (BookListItemDto) -> Unit
) {
    val detailListState = rememberLazyListState()
    var showEditDialog by rememberSaveable(book?.id) { mutableStateOf(false) }

    LaunchedEffect(loadingBookId) {
        if (!loadingBookId.isNullOrBlank()) {
            detailListState.animateScrollToItem(0)
        }
    }

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Fiche livre") },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Retour")
                }
            }
        )
        AureliaScreen(listState = detailListState) {
            when {
                isLoading && book == null -> LoadingRow("Chargement de la fiche")
                error != null -> {
                    ErrorText(message = error)
                    OutlinedButton(onClick = onRetry) {
                        Text("Reessayer")
                    }
                }
                book == null -> EmptyState("Livre indisponible", "Selectionne un livre depuis la bibliotheque.")
                else -> {
                    AnimatedVisibility(visible = isLoading) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    }
                    AnimatedContent(
                        targetState = book,
                        transitionSpec = {
                            (
                                slideInHorizontally(animationSpec = tween(160)) { width -> width / 8 } +
                                    fadeIn(animationSpec = tween(140))
                                ) togetherWith
                                (
                                    slideOutHorizontally(animationSpec = tween(120)) { width -> -width / 10 } +
                                        fadeOut(animationSpec = tween(100))
                                    ) using
                                SizeTransform(clip = false)
                        },
                        label = "book-detail-content"
                    ) { visibleBook ->
                        val isDownloaded = visibleBook.isOfflineAvailable || visibleBook.id in offlineBookIds
                        val currentDownloadState = downloadState ?: BookDownloadUiState()

                        Column(verticalArrangement = Arrangement.spacedBy(18.dp)) {
                            BookCover(
                                coverUrl = visibleBook.coverUrl,
                                title = visibleBook.title,
                                accessToken = accessToken,
                                contentScale = ContentScale.Fit,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(260.dp)
                                    .clip(RoundedCornerShape(8.dp))
                            )
                            HeaderBlock(
                                eyebrow = statusLabel(visibleBook.status),
                                title = visibleBook.title,
                                subtitle = visibleBook.authorLine
                            )
                            visibleBook.progressPercent?.let { progress ->
                                LinearProgressIndicator(
                                    progress = { progressFraction(progress) },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                StatusPill(label = "${progressDisplayPercent(progress)}% lu")
                            }
                            progressSyncLabel?.takeIf { it.isNotBlank() }?.let { label ->
                                StatusPill(label = label)
                            }
                            FlowRow(
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                                verticalArrangement = Arrangement.spacedBy(10.dp)
                            ) {
                                Button(
                                    onClick = onRead,
                                    enabled = !isPreparingReader
                                ) {
                                    if (isPreparingReader) {
                                        CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                                    } else {
                                        Icon(Icons.Outlined.PlayArrow, contentDescription = null)
                                    }
                                    Text(
                                        when {
                                            isPreparingReader -> "Ouverture ${readerPrepareProgress ?: 0}%"
                                            isDownloaded -> "Lire hors ligne"
                                            else -> "Lire"
                                        }
                                    )
                                }
                                DownloadActionButton(
                                    isDownloaded = isDownloaded,
                                    downloadState = currentDownloadState,
                                    canDownload = !isOfflineMode,
                                    onDownload = onDownload,
                                    onRemoveDownload = onRemoveDownload
                                )
                                OutlinedButton(
                                    onClick = { showEditDialog = true },
                                    enabled = !isOfflineMode && !isMutatingBook
                                ) {
                                    Icon(Icons.Outlined.Edit, contentDescription = null)
                                    Text("Modifier")
                                }
                                OutlinedButton(
                                    onClick = onMarkFinished,
                                    enabled = !isOfflineMode && !isMutatingBook && visibleBook.status != "finished"
                                ) {
                                    Icon(Icons.Outlined.CheckCircle, contentDescription = null)
                                    Text("Marquer lu")
                                }
                            }
                            actionMessage?.let { StatusPill(label = it) }
                            actionError?.let { ErrorText(message = it) }
                            if (isDownloaded) {
                                StatusPill(label = "Disponible hors ligne")
                            }
                            if (isOfflineMode) {
                                StatusPill(label = "Mode hors ligne")
                            }
                            readerError?.let { ErrorText(message = it) }
                            currentDownloadState.error?.let { ErrorText(message = it) }
                            visibleBook.description?.let {
                                Text(text = it, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            MetadataSection(
                                book = visibleBook,
                                accessToken = accessToken,
                                offlineBookIds = offlineBookIds,
                                onOpenRelatedBook = onOpenRelatedBook
                            )
                        }
                    }
                }
            }
        }
    }
    EditBookDialog(
        book = book.takeIf { showEditDialog },
        isBusy = isMutatingBook,
        onDismiss = { showEditDialog = false },
        onConfirm = { title, status, rating, favorite ->
            showEditDialog = false
            onUpdateBook(title, status, rating, favorite)
        }
    )
}

@Composable
fun SettingsScreen(
    serverUrl: String,
    username: String?,
    isOfflineMode: Boolean,
    offlineBookCount: Int,
    collectionsCount: Int,
    seriesCount: Int,
    sessionMessage: String?,
    importMessage: String?,
    actionError: String?,
    isImportingBook: Boolean,
    isReconnecting: Boolean,
    isLoggingOut: Boolean,
    onReconnect: () -> Unit,
    onImportBook: (Uri) -> Unit,
    onLogout: () -> Unit
) {
    val importLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri?.let(onImportBook)
    }

    AureliaScreen {
        HeaderBlock(
            eyebrow = "Parametres",
            title = "Aurelia Reader",
            subtitle = if (isOfflineMode) {
                "Lecture locale sans connexion serveur."
            } else {
                "Session Android connectee au serveur Aurelia."
            }
        )
        SettingsRow("Serveur", if (isOfflineMode) "Hors ligne" else serverUrl.ifBlank { "Non configure" })
        SettingsRow("Compte", username ?: if (isOfflineMode) "Session locale" else "Non connecte")
        SettingsRow("Cache offline", "$offlineBookCount livre(s)")
        SettingsRow("Sync", if (isOfflineMode) "En attente de reconnexion" else "Disponible")
        SettingsRow("Organisation", "$collectionsCount collection(s), $seriesCount serie(s)")
        SettingsRow("Theme app", "Noir et or")
        SettingsRow("Reglages lecteur", "Dans le lecteur EPUB")
        SettingsRow("Version", "0.1.2")
        sessionMessage?.let { StatusPill(label = it) }
        importMessage?.let { StatusPill(label = it) }
        actionError?.let { ErrorText(message = it) }
        OutlinedButton(onClick = onReconnect, enabled = !isReconnecting, modifier = Modifier.fillMaxWidth()) {
            if (isReconnecting) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Icon(Icons.Outlined.Refresh, contentDescription = null)
            }
            Text("Reconnecter au serveur")
        }
        OutlinedButton(
            onClick = {
                importLauncher.launch(
                    arrayOf(
                        "application/epub+zip",
                        "application/octet-stream",
                        "application/zip"
                    )
                )
            },
            enabled = !isOfflineMode && !isImportingBook,
            modifier = Modifier.fillMaxWidth()
        ) {
            if (isImportingBook) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Icon(Icons.Outlined.Upload, contentDescription = null)
            }
            Text("Importer un EPUB")
        }
        OutlinedButton(onClick = onLogout, enabled = !isLoggingOut, modifier = Modifier.fillMaxWidth()) {
            if (isLoggingOut) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Text("Se deconnecter")
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrganizationScreen(
    collections: List<CollectionSummaryDto>,
    series: List<SeriesSummaryDto>,
    selectedSeries: SeriesDetailDto?,
    isLoadingSeriesDetail: Boolean,
    seriesDetailError: String?,
    accessToken: String,
    isOfflineMode: Boolean,
    isLoading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    onOpenSeries: (SeriesSummaryDto) -> Unit,
    onDismissSeries: () -> Unit,
    onOpenBook: (BookListItemDto) -> Unit
) {
    AureliaScreen {
        HeaderBlock(
            eyebrow = "Organisation",
            title = "Collections et series",
            subtitle = if (isOfflineMode) {
                "Reconnecte le serveur pour mettre a jour l'organisation."
            } else {
                "${collections.size} collection(s), ${series.size} serie(s)."
            }
        )
        OutlinedButton(onClick = onRefresh, enabled = !isOfflineMode && !isLoading) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Icon(Icons.Outlined.Refresh, contentDescription = null)
            }
            Text("Recharger")
        }
        error?.let { ErrorText(message = it) }
        if (isLoading) {
            LoadingRow("Chargement organisation")
        }
        SectionTitle("Collections")
        if (collections.isEmpty() && !isLoading) {
            EmptyState("Aucune collection", "Les collections serveur apparaitront ici apres synchronisation.")
        } else {
            collections.forEach { collection ->
                OrganizationRow(
                    title = collection.name,
                    subtitle = collection.description ?: "${collection.bookCount} livre(s)",
                    coverUrl = collection.coverUrl,
                    accessToken = accessToken,
                    onClick = null
                )
            }
        }
        SectionTitle("Series")
        if (series.isEmpty() && !isLoading) {
            EmptyState("Aucune serie", "Les series serveur apparaitront ici apres synchronisation.")
        } else {
            series.forEach { seriesItem ->
                OrganizationRow(
                    title = seriesItem.name,
                    subtitle = seriesItem.description ?: "${seriesItem.bookCount} livre(s)",
                    coverUrl = seriesItem.coverUrl,
                    accessToken = accessToken,
                    onClick = { onOpenSeries(seriesItem) }
                )
            }
        }
    }
    if (isLoadingSeriesDetail || selectedSeries != null || seriesDetailError != null) {
        ModalBottomSheet(onDismissRequest = onDismissSeries) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(start = 20.dp, end = 20.dp, bottom = 28.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                when {
                    isLoadingSeriesDetail -> LoadingRow("Ouverture de la serie")
                    seriesDetailError != null -> {
                        ErrorText(message = seriesDetailError)
                        OutlinedButton(onClick = onDismissSeries) {
                            Text("Fermer")
                        }
                    }
                    selectedSeries != null -> {
                        HeaderBlock(
                            eyebrow = "Serie",
                            title = selectedSeries.name,
                            subtitle = "${selectedSeries.bookCount} livre(s)"
                        )
                        selectedSeries.description?.let {
                            Text(text = it, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        selectedSeries.books.forEach { book ->
                            BookRow(
                                book = book,
                                accessToken = accessToken,
                                isDownloaded = book.isOfflineAvailable,
                                onClick = {
                                    onDismissSeries()
                                    onOpenBook(book)
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun OrganizationRow(
    title: String,
    subtitle: String,
    coverUrl: String?,
    accessToken: String,
    onClick: (() -> Unit)? = null
) {
    val content: @Composable () -> Unit = {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            BookCover(
                coverUrl = coverUrl,
                title = title,
                accessToken = accessToken,
                modifier = Modifier
                    .size(48.dp)
                    .aspectRatio(2f / 3f)
                    .clip(RoundedCornerShape(4.dp))
            )
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(subtitle, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (onClick != null) {
                Icon(Icons.AutoMirrored.Outlined.ArrowForward, contentDescription = "Ouvrir")
            }
        }
    }

    if (onClick != null) {
        Card(
            onClick = onClick,
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            content()
        }
    } else {
        Surface(
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            content()
        }
    }
}

@Composable
private fun AureliaScreen(
    listState: LazyListState = rememberLazyListState(),
    content: @Composable ColumnScope.() -> Unit
) {
    LazyColumn(
        state = listState,
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(18.dp), content = content)
        }
    }
}

@Composable
private fun HeaderBlock(eyebrow: String, title: String, subtitle: String) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            text = eyebrow.uppercase(),
            color = MaterialTheme.colorScheme.primary,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = title,
            color = MaterialTheme.colorScheme.onBackground,
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Black
        )
        Text(
            text = subtitle,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodyLarge
        )
    }
}

@Composable
private fun SectionTitle(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.titleLarge,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onBackground
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BookRow(book: BookListItemDto, accessToken: String, onClick: () -> Unit) {
    BookRow(
        book = book,
        accessToken = accessToken,
        isDownloaded = book.isOfflineAvailable,
        onClick = onClick,
        onAction = null
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BookRow(
    book: BookListItemDto,
    accessToken: String,
    isDownloaded: Boolean,
    onClick: () -> Unit,
    onAction: (() -> Unit)? = null
) {
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            BookCover(
                coverUrl = book.coverUrl,
                title = book.title,
                accessToken = accessToken,
                modifier = Modifier
                    .size(56.dp)
                    .aspectRatio(2f / 3f)
                    .clip(RoundedCornerShape(4.dp))
            )
            Column(modifier = Modifier.weight(1f)) {
                Text(book.title, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(book.authorLine, color = MaterialTheme.colorScheme.onSurfaceVariant)
                book.progressPercent?.let { progress ->
                    LinearProgressIndicator(
                        progress = { progressFraction(progress) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp)
                    )
                }
            }
            if (isDownloaded) {
                Icon(Icons.Outlined.CloudDone, contentDescription = "Telecharge")
            }
            if (onAction != null) {
                IconButton(onClick = onAction) {
                    Icon(Icons.Outlined.MoreVert, contentDescription = "Actions livre")
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BookActionSheet(
    book: BookListItemDto?,
    isDownloaded: Boolean,
    isOfflineMode: Boolean,
    isBusy: Boolean,
    onDismiss: () -> Unit,
    onRead: (BookListItemDto) -> Unit,
    onDownload: (BookListItemDto) -> Unit,
    onRemoveDownload: (BookListItemDto) -> Unit,
    onMarkFinished: (BookListItemDto) -> Unit,
    onToggleFavorite: (BookListItemDto) -> Unit,
    onRename: (BookListItemDto) -> Unit
) {
    val visibleBook = book ?: return

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 20.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(visibleBook.title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(visibleBook.authorLine, color = MaterialTheme.colorScheme.onSurfaceVariant)
            SheetAction(
                label = "Lire",
                enabled = true,
                icon = { Icon(Icons.Outlined.PlayArrow, contentDescription = null) },
                onClick = { onRead(visibleBook) }
            )
            SheetAction(
                label = "Modifier le titre",
                enabled = !isOfflineMode && !isBusy,
                icon = { Icon(Icons.Outlined.Edit, contentDescription = null) },
                onClick = { onRename(visibleBook) }
            )
            SheetAction(
                label = if (visibleBook.favorite) "Retirer des favoris" else "Ajouter aux favoris",
                enabled = !isOfflineMode && !isBusy,
                icon = {
                    Icon(
                        if (visibleBook.favorite) Icons.Outlined.Favorite else Icons.Outlined.FavoriteBorder,
                        contentDescription = null
                    )
                },
                onClick = { onToggleFavorite(visibleBook) }
            )
            SheetAction(
                label = "Marquer lu",
                enabled = !isOfflineMode && !isBusy && visibleBook.status != "finished",
                icon = { Icon(Icons.Outlined.CheckCircle, contentDescription = null) },
                onClick = { onMarkFinished(visibleBook) }
            )
            SheetAction(
                label = if (isDownloaded) "Supprimer hors ligne" else "Telecharger hors ligne",
                enabled = !isBusy && (isDownloaded || !isOfflineMode),
                icon = {
                    Icon(
                        if (isDownloaded) Icons.Outlined.Delete else Icons.Outlined.Download,
                        contentDescription = null
                    )
                },
                onClick = {
                    if (isDownloaded) {
                        onRemoveDownload(visibleBook)
                    } else {
                        onDownload(visibleBook)
                    }
                }
            )
        }
    }
}

@Composable
private fun SheetAction(
    label: String,
    enabled: Boolean,
    icon: @Composable () -> Unit,
    onClick: () -> Unit
) {
    TextButton(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            icon()
            Text(label)
        }
    }
}

@Composable
private fun RenameBookDialog(
    book: BookListItemDto?,
    isBusy: Boolean,
    onDismiss: () -> Unit,
    onConfirm: (BookListItemDto, String) -> Unit
) {
    val visibleBook = book ?: return
    var title by rememberSaveable(visibleBook.id) { mutableStateOf(visibleBook.title) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Modifier le titre") },
        text = {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("Titre") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(visibleBook, title.trim()) },
                enabled = !isBusy && title.isNotBlank()
            ) {
                Text("Enregistrer")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Annuler")
            }
        }
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun EditBookDialog(
    book: BookDetailDto?,
    isBusy: Boolean,
    onDismiss: () -> Unit,
    onConfirm: (String, String, String, Boolean) -> Unit
) {
    val visibleBook = book ?: return
    var title by rememberSaveable(visibleBook.id, "title") { mutableStateOf(visibleBook.title) }
    var status by rememberSaveable(visibleBook.id, "status") { mutableStateOf(visibleBook.status) }
    var rating by rememberSaveable(visibleBook.id, "rating") { mutableStateOf(visibleBook.rating?.toString().orEmpty()) }
    var favorite by rememberSaveable(visibleBook.id, "favorite") { mutableStateOf(visibleBook.favorite) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Modifier le livre") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Titre") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                StatusChoiceRow(value = status, onChange = { status = it })
                OutlinedTextField(
                    value = rating,
                    onValueChange = { rating = it.filter(Char::isDigit).take(1) },
                    label = { Text("Note 0-5") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = favorite, onCheckedChange = { favorite = it })
                    Text("Favori")
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(title.trim(), status, rating.trim(), favorite) },
                enabled = !isBusy && title.isNotBlank()
            ) {
                Text("Enregistrer")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Annuler")
            }
        }
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun StatusChoiceRow(value: String, onChange: (String) -> Unit) {
    val choices = listOf(
        "unread" to "Non lu",
        "in_progress" to "En cours",
        "finished" to "Lu",
        "abandoned" to "Abandonne"
    )

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Statut", fontWeight = FontWeight.Bold)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            choices.forEach { (status, label) ->
                OutlinedButton(onClick = { onChange(status) }) {
                    if (value == status) {
                        Icon(Icons.Outlined.CheckCircle, contentDescription = null)
                    }
                    Text(label)
                }
            }
        }
    }
}

@Composable
private fun DownloadActionButton(
    isDownloaded: Boolean,
    downloadState: BookDownloadUiState,
    canDownload: Boolean,
    onDownload: () -> Unit,
    onRemoveDownload: () -> Unit
) {
    val mode = when {
        downloadState.status == DownloadStatus.Downloading -> DownloadButtonMode.Downloading
        isDownloaded -> DownloadButtonMode.Downloaded
        else -> DownloadButtonMode.Ready
    }

    AnimatedContent(
        targetState = mode,
        transitionSpec = {
            (
                slideInVertically(animationSpec = tween(140)) { height -> height / 4 } +
                    fadeIn(animationSpec = tween(120))
                ) togetherWith
                (
                    slideOutVertically(animationSpec = tween(100)) { height -> -height / 5 } +
                        fadeOut(animationSpec = tween(90))
                    ) using SizeTransform(clip = false)
        },
        label = "download-action-button"
    ) { targetMode ->
        when (targetMode) {
            DownloadButtonMode.Downloading -> {
                OutlinedButton(
                    onClick = {},
                    enabled = false,
                    modifier = Modifier.animateContentSize(animationSpec = tween(180))
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    Text("${downloadState.progress}%")
                }
            }

            DownloadButtonMode.Downloaded -> {
                OutlinedButton(
                    onClick = onRemoveDownload,
                    modifier = Modifier.animateContentSize(animationSpec = tween(180))
                ) {
                    Icon(Icons.Outlined.Delete, contentDescription = null)
                    Text("Supprimer hors ligne")
                }
            }

            DownloadButtonMode.Ready -> {
                OutlinedButton(
                    onClick = onDownload,
                    enabled = canDownload,
                    modifier = Modifier.animateContentSize(animationSpec = tween(180))
                ) {
                    Icon(Icons.Outlined.Download, contentDescription = null)
                    Text(if (canDownload) "Telecharger" else "Hors ligne")
                }
            }
        }
    }
}

private enum class DownloadButtonMode {
    Ready,
    Downloading,
    Downloaded
}

@Composable
private fun BookCover(
    coverUrl: String?,
    title: String,
    accessToken: String,
    contentScale: ContentScale = ContentScale.Crop,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    if (coverUrl.isNullOrBlank()) {
        CoverFallback(title = title, modifier = modifier)
        return
    }

    val requestBuilder = ImageRequest.Builder(context)
        .data(coverUrl)
        .crossfade(true)
    if (accessToken.isNotBlank() && coverUrl.startsWith("http", ignoreCase = true)) {
        requestBuilder.addHeader("Authorization", "Bearer $accessToken")
    }
    val request = requestBuilder.build()

    Box(
        modifier = modifier.background(MaterialTheme.colorScheme.surfaceVariant),
        contentAlignment = Alignment.Center
    ) {
        AsyncImage(
            model = request,
            contentDescription = null,
            contentScale = contentScale,
            modifier = Modifier.fillMaxSize()
        )
    }
}

@Composable
private fun CoverFallback(title: String, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier.background(
            Brush.linearGradient(
                listOf(
                    MaterialTheme.colorScheme.primary,
                    MaterialTheme.colorScheme.surfaceVariant
                )
            )
        ),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = title.firstOrNull()?.uppercase().orEmpty(),
            color = MaterialTheme.colorScheme.onPrimary,
            fontWeight = FontWeight.Black
        )
    }
}

@Composable
private fun MetadataSection(
    book: BookDetailDto,
    accessToken: String,
    offlineBookIds: Set<String>,
    onOpenRelatedBook: (BookListItemDto) -> Unit
) {
    SectionTitle("Infos livre")
    SettingsRow("Statut", statusLabel(book.status))
    book.rating?.let { SettingsRow("Note", "$it / 5") }
    book.publisher?.let { SettingsRow("Editeur", it) }
    book.publishedDate?.let { SettingsRow("Publication", it) }
    book.language?.let { SettingsRow("Langue", it.uppercase()) }
    book.isbn?.let { SettingsRow("ISBN", it) }
    book.series?.let { series ->
        SettingsRow(
            "Serie",
            listOfNotNull(series.name, series.index?.let { "Tome $it" }).joinToString(" - ")
        )
    }
    book.originalFilename?.let { SettingsRow("Fichier", it) }
    book.fileSize?.let { SettingsRow("Taille", formatBytes(it)) }
    if (book.tags.isNotEmpty()) {
        ChipList("Tags", book.tags)
    }
    if (book.subjects.isNotEmpty()) {
        ChipList("Sujets", book.subjects.take(12))
    }
    if (book.relatedBooks.isNotEmpty()) {
        SectionTitle("Meme serie")
        book.relatedBooks.take(6).forEach { related ->
            BookRow(
                book = related,
                accessToken = accessToken,
                isDownloaded = related.isOfflineAvailable || related.id in offlineBookIds,
                onClick = { onOpenRelatedBook(related) }
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ChipList(title: String, values: List<String>) {
    Text(title, fontWeight = FontWeight.Bold)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        values.forEach { value ->
            StatusPill(label = value)
        }
    }
}

@Composable
private fun LoadingRow(label: String) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun EmptyState(title: String, message: String) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, fontWeight = FontWeight.Bold)
            Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun statusLabel(status: String): String {
    return when (status) {
        "unread" -> "Non lu"
        "in_progress" -> "En cours"
        "finished" -> "Termine"
        "abandoned" -> "Abandonne"
        else -> status
    }
}

private fun progressDisplayPercent(progress: Float): Int {
    val normalized = progress.coerceIn(0f, 100f).let { value ->
        if (value >= 99f) 100f else value
    }
    return normalized.roundToInt().coerceIn(0, 100)
}

private fun progressFraction(progress: Float): Float {
    return progressDisplayPercent(progress) / 100f
}

private fun formatBytes(size: Long): String {
    val units = listOf("B", "KB", "MB", "GB")
    var value = size.toDouble()
    var unit = 0
    while (value >= 1024 && unit < units.lastIndex) {
        value /= 1024
        unit += 1
    }
    return "${if (unit == 0) value.toInt().toString() else "%.1f".format(value)} ${units[unit]}"
}

@Composable
private fun StatusPill(label: String) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(999.dp)
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun ErrorText(message: String) {
    Text(
        text = message,
        color = MaterialTheme.colorScheme.error,
        style = MaterialTheme.typography.bodyMedium
    )
}

@Composable
private fun SettingsRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, fontWeight = FontWeight.Bold)
    }
}

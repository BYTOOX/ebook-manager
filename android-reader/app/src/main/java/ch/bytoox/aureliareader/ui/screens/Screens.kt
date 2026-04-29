package ch.bytoox.aureliareader.ui.screens

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
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CloudDone
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
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
    error: String?,
    onRefresh: () -> Unit,
    onOpenLibrary: () -> Unit,
    onOpenBook: (BookListItemDto) -> Unit
) {
    val currentBook = books.firstOrNull()

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
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = { currentBook?.let(onOpenBook) }, enabled = currentBook != null) {
                Icon(Icons.Outlined.PlayArrow, contentDescription = null)
                Text("Fiche")
            }
            OutlinedButton(onClick = onOpenLibrary) {
                Text("Bibliotheque")
            }
        }
        StatusPill(label = if (isOfflineMode) "$total livre(s) hors ligne" else "$total livre(s) serveur")
        error?.let { ErrorText(message = it) }
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
            OutlinedButton(onClick = onRefresh, enabled = !isOfflineMode) {
                Text("Recharger")
            }
        } else {
            SectionTitle("Recents")
            books.take(5).forEach { book ->
                BookRow(
                    book = book,
                    accessToken = accessToken,
                    isDownloaded = book.isOfflineAvailable || book.id in offlineBookIds,
                    onClick = { onOpenBook(book) }
                )
            }
        }
    }
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
    error: String?,
    onSearch: (String) -> Unit,
    onRefresh: () -> Unit,
    onLoadMore: () -> Unit,
    onOpenBook: (BookListItemDto) -> Unit
) {
    var localSearchQuery by rememberSaveable { mutableStateOf(searchQuery) }

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
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick = onRefresh, enabled = !isLoading && !isOfflineMode) {
                Text(if (isOfflineMode) "Hors ligne" else "Recharger")
            }
            if (localSearchQuery.isNotBlank()) {
                TextButton(onClick = { localSearchQuery = "" }) {
                    Text("Effacer")
                }
            }
        }
        error?.let { ErrorText(message = it) }
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
                    onClick = { onOpenBook(book) }
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
}

@OptIn(ExperimentalMaterial3Api::class)
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
    isLoading: Boolean,
    error: String?,
    onRead: () -> Unit,
    onDownload: () -> Unit,
    onRemoveDownload: () -> Unit,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onOpenRelatedBook: (BookListItemDto) -> Unit
) {
    val detailListState = rememberLazyListState()

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
                                slideInHorizontally(animationSpec = tween(260)) { width -> width / 3 } +
                                    fadeIn(animationSpec = tween(180)) +
                                    scaleIn(animationSpec = tween(220), initialScale = 0.97f)
                                ) togetherWith
                                (
                                    slideOutHorizontally(animationSpec = tween(180)) { width -> -width / 4 } +
                                        fadeOut(animationSpec = tween(120)) +
                                        scaleOut(animationSpec = tween(180), targetScale = 0.98f)
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
                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
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
                            }
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
}

@Composable
fun SettingsScreen(
    serverUrl: String,
    username: String?,
    isOfflineMode: Boolean,
    sessionMessage: String?,
    isLoggingOut: Boolean,
    onLogout: () -> Unit
) {
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
        SettingsRow("Theme app", "Noir et or")
        SettingsRow("Version", "0.1.1")
        sessionMessage?.let { StatusPill(label = it) }
        OutlinedButton(onClick = onLogout, enabled = !isLoggingOut, modifier = Modifier.fillMaxWidth()) {
            if (isLoggingOut) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                Text("Se deconnecter")
            }
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
        onClick = onClick
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BookRow(
    book: BookListItemDto,
    accessToken: String,
    isDownloaded: Boolean,
    onClick: () -> Unit
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
                slideInVertically(animationSpec = tween(180)) { height -> height / 2 } +
                    fadeIn(animationSpec = tween(140)) +
                    scaleIn(animationSpec = tween(180), initialScale = 0.92f)
                ) togetherWith
                (
                    slideOutVertically(animationSpec = tween(120)) { height -> -height / 2 } +
                        fadeOut(animationSpec = tween(100)) +
                        scaleOut(animationSpec = tween(120), targetScale = 0.94f)
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

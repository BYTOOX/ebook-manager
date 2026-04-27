package ch.bytoox.aureliareader.ui.navigation

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.LibraryBooks
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import ch.bytoox.aureliareader.reader.ReadiumReaderActivity
import ch.bytoox.aureliareader.data.repositories.BookProgressSnapshot
import ch.bytoox.aureliareader.ui.app.AppViewModel
import ch.bytoox.aureliareader.ui.screens.BookDetailScreen
import ch.bytoox.aureliareader.ui.screens.HomeScreen
import ch.bytoox.aureliareader.ui.screens.LibraryScreen
import ch.bytoox.aureliareader.ui.screens.LoginScreen
import ch.bytoox.aureliareader.ui.screens.LoadingScreen
import ch.bytoox.aureliareader.ui.screens.ServerSetupScreen
import ch.bytoox.aureliareader.ui.screens.SettingsScreen

private data class BottomRoute(
    val route: Route,
    val label: String,
    val icon: @Composable () -> Unit
)

private val bottomRoutes = listOf(
    BottomRoute(Route.Home, "Accueil") {
        Icon(Icons.Outlined.Home, contentDescription = null)
    },
    BottomRoute(Route.Library, "Bibliotheque") {
        Icon(Icons.AutoMirrored.Outlined.LibraryBooks, contentDescription = null)
    },
    BottomRoute(Route.Settings, "Reglages") {
        Icon(Icons.Outlined.Settings, contentDescription = null)
    }
)

@Composable
fun AppNavGraph(appViewModel: AppViewModel) {
    val uiState by appViewModel.uiState.collectAsState()
    val navController = rememberNavController()
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = backStackEntry?.destination
    val currentRoute = currentDestination?.route
    val showBottomBar = uiState.isAuthenticated &&
        currentRoute in bottomRoutes.map { it.route.path }

    LaunchedEffect(uiState.readerLaunchRequest?.requestId) {
        uiState.readerLaunchRequest?.let { request ->
            context.startActivity(
                ReadiumReaderActivity.newIntent(
                    context = context,
                    bookId = request.bookId,
                    title = request.title,
                    filePath = request.filePath
                )
            )
            appViewModel.consumeReaderLaunchRequest()
        }
    }

    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                appViewModel.refreshLocalProgress()
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    LaunchedEffect(uiState.isInitialized, uiState.isAuthenticated, uiState.serverUrl, currentRoute) {
        if (uiState.isInitialized && currentRoute == Route.Loading.path) {
            val target = when {
                uiState.isAuthenticated -> Route.Home.path
                uiState.serverUrl.isNotBlank() -> Route.Login.path
                else -> Route.SetupServer.path
            }
            navController.navigate(target) {
                popUpTo(Route.Loading.path) { inclusive = true }
                launchSingleTop = true
            }
        }
    }

    Scaffold(
        bottomBar = {
            AnimatedVisibility(
                visible = showBottomBar,
                enter = fadeIn(animationSpec = tween(120)),
                exit = fadeOut(animationSpec = tween(120))
            ) {
                NavigationBar {
                    bottomRoutes.forEach { destination ->
                        val selected = currentDestination?.hierarchy?.any {
                            it.route == destination.route.path
                        } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(destination.route.path) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = destination.icon,
                            label = { Text(destination.label) }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Route.Loading.path,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Route.Loading.path) {
                LoadingScreen()
            }
            composable(Route.SetupServer.path) {
                ServerSetupScreen(
                    serverUrl = uiState.serverUrl,
                    isCheckingServer = uiState.isCheckingServer,
                    serverStatus = uiState.serverStatus,
                    serverError = uiState.serverError,
                    onServerUrlChange = appViewModel::updateServerUrl,
                    onCheckServer = {
                        appViewModel.checkServer {
                            navController.navigate(Route.Login.path) {
                                launchSingleTop = true
                            }
                        }
                    }
                )
            }
            composable(Route.Login.path) {
                LoginScreen(
                    serverUrl = uiState.serverUrl,
                    isLoggingIn = uiState.isLoggingIn,
                    loginError = uiState.loginError,
                    sessionMessage = uiState.sessionMessage,
                    onLogin = { username, password ->
                        appViewModel.login(username, password) {
                            navController.navigate(Route.Home.path) {
                                popUpTo(Route.Login.path) { inclusive = true }
                                launchSingleTop = true
                            }
                        }
                    },
                    onChangeServer = {
                        navController.navigate(Route.SetupServer.path) {
                            launchSingleTop = true
                        }
                    }
                )
            }
            composable(Route.Home.path) {
                HomeScreen(
                    displayName = uiState.currentUser?.displayName ?: uiState.currentUser?.username,
                    serverUrl = uiState.serverUrl,
                    books = uiState.books,
                    total = uiState.booksTotal,
                    accessToken = uiState.accessToken,
                    offlineBookIds = uiState.offlineBookIds,
                    isLoading = uiState.isLoadingBooks,
                    error = uiState.booksError,
                    onRefresh = appViewModel::refreshBooks,
                    onOpenLibrary = { navController.navigate(Route.Library.path) },
                    onOpenBook = { book ->
                        appViewModel.openBook(book.id)
                        navController.navigate(Route.BookDetail.path)
                    }
                )
            }
            composable(Route.Library.path) {
                LibraryScreen(
                    books = uiState.books,
                    total = uiState.booksTotal,
                    searchQuery = uiState.booksQuery,
                    accessToken = uiState.accessToken,
                    offlineBookIds = uiState.offlineBookIds,
                    isLoading = uiState.isLoadingBooks,
                    isLoadingMore = uiState.isLoadingMoreBooks,
                    error = uiState.booksError,
                    onSearch = appViewModel::searchBooks,
                    onRefresh = appViewModel::refreshBooks,
                    onLoadMore = appViewModel::loadMoreBooks,
                    onOpenBook = { book ->
                        appViewModel.openBook(book.id)
                        navController.navigate(Route.BookDetail.path)
                    }
                )
            }
            composable(Route.BookDetail.path) {
                BookDetailScreen(
                    book = uiState.selectedBook,
                    accessToken = uiState.accessToken,
                    offlineBookIds = uiState.offlineBookIds,
                    downloadState = uiState.selectedBookId?.let { uiState.downloadStates[it] }
                        ?: uiState.selectedBook?.id?.let { uiState.downloadStates[it] },
                    progressSyncLabel = uiState.selectedBook?.id
                        ?.let { uiState.localProgress[it] }
                        ?.syncLabel(),
                    loadingBookId = uiState.selectedBookId,
                    isPreparingReader = uiState.isPreparingReader,
                    readerPrepareProgress = uiState.readerPrepareProgress,
                    readerError = uiState.readerError,
                    isLoading = uiState.isLoadingBookDetail,
                    error = uiState.selectedBookError,
                    onRead = appViewModel::openSelectedBookReader,
                    onDownload = appViewModel::downloadSelectedBook,
                    onRemoveDownload = appViewModel::removeSelectedBookDownload,
                    onBack = { navController.popBackStack() },
                    onRetry = {
                        uiState.selectedBookId?.let(appViewModel::openBook)
                    },
                    onOpenRelatedBook = { book ->
                        appViewModel.openBook(book.id)
                    }
                )
            }
            composable(Route.Settings.path) {
                SettingsScreen(
                    serverUrl = uiState.serverUrl,
                    username = uiState.currentUser?.username,
                    sessionMessage = uiState.sessionMessage,
                    isLoggingOut = uiState.isLoggingOut,
                    onLogout = {
                        appViewModel.logout {
                            navController.navigate(Route.Login.path) {
                                popUpTo(Route.Home.path) { inclusive = true }
                                launchSingleTop = true
                            }
                        }
                    }
                )
            }
        }
    }
}

private fun BookProgressSnapshot.syncLabel(): String? {
    return when {
        syncStatus == "synced" -> "Progression synchronisee"
        syncStatus == "error" -> "Erreur sync progression"
        dirty -> "Progression en attente de sync"
        else -> null
    }
}

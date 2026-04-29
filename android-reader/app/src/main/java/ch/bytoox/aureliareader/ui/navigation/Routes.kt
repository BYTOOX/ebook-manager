package ch.bytoox.aureliareader.ui.navigation

sealed class Route(val path: String) {
    data object Loading : Route("loading")
    data object SetupServer : Route("setup")
    data object Login : Route("login")
    data object Home : Route("home")
    data object Library : Route("library")
    data object Organization : Route("organization")
    data object BookDetail : Route("book-detail")
    data object Settings : Route("settings")
}

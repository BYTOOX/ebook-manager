package ch.bytoox.aureliareader

import androidx.compose.runtime.Composable
import ch.bytoox.aureliareader.ui.app.AppViewModel
import ch.bytoox.aureliareader.ui.navigation.AppNavGraph
import ch.bytoox.aureliareader.ui.theme.AureliaReaderTheme

@Composable
fun AureliaReaderApp(appViewModel: AppViewModel) {
    AureliaReaderTheme {
        AppNavGraph(appViewModel = appViewModel)
    }
}

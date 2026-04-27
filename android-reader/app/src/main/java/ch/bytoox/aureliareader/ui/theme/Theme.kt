package ch.bytoox.aureliareader.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = AureliaGold,
    onPrimary = AureliaBlack,
    secondary = AureliaMutedGold,
    onSecondary = AureliaBlack,
    background = AureliaBlack,
    onBackground = AureliaText,
    surface = AureliaSurface,
    onSurface = AureliaText,
    surfaceVariant = AureliaSurface2,
    onSurfaceVariant = AureliaMutedText,
    error = AureliaError
)

@Composable
fun AureliaReaderTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = AureliaBlack.toArgb()
            window.navigationBarColor = AureliaBlack.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = false
            }
        }
    }

    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = AureliaTypography,
        content = content
    )
}

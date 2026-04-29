package ch.bytoox.aureliareader.reader

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color as AndroidColor
import org.readium.r2.navigator.epub.EpubPreferences
import org.readium.r2.navigator.preferences.Color as ReadiumColor
import org.readium.r2.navigator.preferences.FontFamily
import org.readium.r2.navigator.preferences.TextAlign
import org.readium.r2.navigator.preferences.Theme
import org.readium.r2.shared.ExperimentalReadiumApi

enum class ReaderFlow {
    Auto,
    Paged,
    Scrolled
}

enum class ReaderTheme {
    White,
    Gray,
    Black,
    Sepia,
    Aurelia
}

enum class ReaderTextAlign {
    Left,
    Justify
}

enum class ReaderFont {
    Original,
    Serif,
    Sans,
    Dyslexic,
    Mono
}

data class ReaderPreferences(
    val flow: ReaderFlow = ReaderFlow.Paged,
    val brightness: Float = 0.72f,
    val theme: ReaderTheme = ReaderTheme.Aurelia,
    val fontSize: Double = 1.12,
    val textAlign: ReaderTextAlign = ReaderTextAlign.Justify,
    val pageMargins: Double = 1.0,
    val lineHeight: Double = 1.55,
    val font: ReaderFont = ReaderFont.Original
)

class ReaderPreferencesStore(context: Context) {
    private val preferences: SharedPreferences = context.applicationContext.getSharedPreferences(
        "aurelia_reader_preferences",
        Context.MODE_PRIVATE
    )

    fun load(): ReaderPreferences {
        return ReaderPreferences(
            flow = enumValue("flow", ReaderFlow.Paged),
            brightness = preferences.getFloat("brightness", 0.72f).coerceIn(0.2f, 1f),
            theme = enumValue("theme", ReaderTheme.Aurelia),
            fontSize = preferences.getFloat("fontSize", 1.12f).toDouble().coerceIn(0.75, 1.7),
            textAlign = enumValue("textAlign", ReaderTextAlign.Justify),
            pageMargins = preferences.getFloat("pageMargins", 1.0f).toDouble().coerceIn(0.5, 2.0),
            lineHeight = preferences.getFloat("lineHeight", 1.55f).toDouble().coerceIn(1.1, 2.2),
            font = enumValue("font", ReaderFont.Original)
        )
    }

    fun save(readerPreferences: ReaderPreferences) {
        preferences.edit()
            .putString("flow", readerPreferences.flow.name)
            .putFloat("brightness", readerPreferences.brightness)
            .putString("theme", readerPreferences.theme.name)
            .putFloat("fontSize", readerPreferences.fontSize.toFloat())
            .putString("textAlign", readerPreferences.textAlign.name)
            .putFloat("pageMargins", readerPreferences.pageMargins.toFloat())
            .putFloat("lineHeight", readerPreferences.lineHeight.toFloat())
            .putString("font", readerPreferences.font.name)
            .apply()
    }

    private inline fun <reified T : Enum<T>> enumValue(key: String, fallback: T): T {
        val value = preferences.getString(key, fallback.name).orEmpty()
        return runCatching { enumValueOf<T>(value) }.getOrDefault(fallback)
    }
}

@OptIn(ExperimentalReadiumApi::class)
fun ReaderPreferences.toEpubPreferences(): EpubPreferences {
    val themeColors = theme.themeColors()

    return EpubPreferences(
        theme = themeColors.readiumTheme,
        backgroundColor = themeColors.backgroundColor?.let(::ReadiumColor),
        textColor = themeColors.textColor?.let(::ReadiumColor),
        scroll = when (flow) {
            ReaderFlow.Auto -> null
            ReaderFlow.Paged -> false
            ReaderFlow.Scrolled -> true
        },
        fontSize = fontSize,
        lineHeight = lineHeight,
        pageMargins = pageMargins,
        textAlign = when (textAlign) {
            ReaderTextAlign.Left -> TextAlign.START
            ReaderTextAlign.Justify -> TextAlign.JUSTIFY
        },
        textNormalization = true,
        fontFamily = when (font) {
            ReaderFont.Original -> null
            ReaderFont.Serif -> FontFamily.SERIF
            ReaderFont.Sans -> FontFamily.SANS_SERIF
            ReaderFont.Dyslexic -> FontFamily.OPEN_DYSLEXIC
            ReaderFont.Mono -> FontFamily.MONOSPACE
        },
        publisherStyles = false
    )
}

data class ReaderContentTheme(
    val background: String,
    val text: String,
    val link: String
)

fun ReaderPreferences.contentTheme(): ReaderContentTheme {
    return when (theme) {
        ReaderTheme.White -> ReaderContentTheme(
            background = "#FFFFFF",
            text = "#121212",
            link = "#8A6D1D"
        )
        ReaderTheme.Gray -> ReaderContentTheme(
            background = "#1D1D1D",
            text = "#E8E3D4",
            link = "#C9A227"
        )
        ReaderTheme.Black -> ReaderContentTheme(
            background = "#000000",
            text = "#FEFEFE",
            link = "#C9A227"
        )
        ReaderTheme.Sepia -> ReaderContentTheme(
            background = "#FAF4E8",
            text = "#121212",
            link = "#7A5C19"
        )
        ReaderTheme.Aurelia -> ReaderContentTheme(
            background = "#0B0B08",
            text = "#C9A227",
            link = "#E3C55D"
        )
    }
}

private data class ReaderThemeColors(
    val readiumTheme: Theme?,
    val backgroundColor: Int?,
    val textColor: Int?
)

private fun ReaderTheme.themeColors(): ReaderThemeColors {
    return when (this) {
        ReaderTheme.White -> ReaderThemeColors(Theme.LIGHT, null, null)
        ReaderTheme.Gray -> ReaderThemeColors(
            readiumTheme = Theme.DARK,
            backgroundColor = AndroidColor.parseColor("#1D1D1D"),
            textColor = AndroidColor.parseColor("#E8E3D4")
        )
        ReaderTheme.Black -> ReaderThemeColors(Theme.DARK, null, null)
        ReaderTheme.Sepia -> ReaderThemeColors(Theme.SEPIA, null, null)
        ReaderTheme.Aurelia -> ReaderThemeColors(
            readiumTheme = Theme.DARK,
            backgroundColor = AndroidColor.parseColor("#0B0B08"),
            textColor = AndroidColor.parseColor("#C9A227")
        )
    }
}

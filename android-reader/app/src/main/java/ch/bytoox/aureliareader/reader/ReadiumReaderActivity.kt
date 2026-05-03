package ch.bytoox.aureliareader.reader

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.activity.compose.setContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.NavigateBefore
import androidx.compose.material.icons.automirrored.outlined.NavigateNext
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.fragment.app.FragmentActivity
import androidx.fragment.app.FragmentFactory
import androidx.fragment.app.commitNow
import androidx.lifecycle.lifecycleScope
import ch.bytoox.aureliareader.core.storage.DeviceIdStore
import ch.bytoox.aureliareader.data.local.AppDatabaseProvider
import ch.bytoox.aureliareader.data.repositories.ProgressRepository
import ch.bytoox.aureliareader.data.sync.ProgressSyncScheduler
import ch.bytoox.aureliareader.ui.theme.AureliaReaderTheme
import java.io.File
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.roundToInt
import kotlinx.coroutines.delay
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.readium.r2.navigator.epub.EpubNavigatorFragment
import org.readium.r2.navigator.input.InputListener
import org.readium.r2.navigator.input.TapEvent
import org.readium.r2.shared.ExperimentalReadiumApi
import org.readium.r2.shared.publication.Link
import org.readium.r2.shared.publication.Locator

class ReadiumReaderActivity : FragmentActivity() {
    private var currentPublication: org.readium.r2.shared.publication.Publication? = null
    private lateinit var progressRepository: ProgressRepository
    private var readerChromeVisible: Boolean = false
    internal var activeBookId: String = ""
        private set

    override fun onCreate(savedInstanceState: Bundle?) {
        supportFragmentManager.fragmentFactory = EpubNavigatorFragment.createDummyFactory()
        super.onCreate(savedInstanceState)
        removeRestoredNavigatorIfNeeded(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        configureSystemBars()
        useSystemBrightness()

        activeBookId = intent.getStringExtra(EXTRA_BOOK_ID).orEmpty()
        val database = AppDatabaseProvider.get(applicationContext)
        progressRepository = ProgressRepository(
            progressDao = database.progressDao(),
            syncEventDao = database.syncEventDao(),
            deviceIdStore = DeviceIdStore(applicationContext)
        )
        val title = intent.getStringExtra(EXTRA_TITLE).orEmpty().ifBlank { "Lecture" }
        val filePath = intent.getStringExtra(EXTRA_FILE_PATH).orEmpty()

        setContent {
            AureliaReaderTheme {
                ReadiumReaderScreen(
                    title = title,
                    filePath = filePath,
                    onBack = { finish() }
                )
            }
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            setReaderChromeVisible(readerChromeVisible)
        }
    }

    override fun onPause() {
        saveCurrentLocator()
        super.onPause()
    }

    override fun onDestroy() {
        currentPublication?.close()
        currentPublication = null
        super.onDestroy()
    }

    internal fun useSystemBrightness() {
        window.attributes = window.attributes.apply {
            screenBrightness = -1f
        }
    }

    internal fun attachNavigator(
        fragmentFactory: FragmentFactory,
        containerId: Int,
        publication: org.readium.r2.shared.publication.Publication
    ) {
        currentPublication?.close()
        currentPublication = publication
        supportFragmentManager.fragmentFactory = fragmentFactory
        if (!supportFragmentManager.isStateSaved) {
            supportFragmentManager.commitNow {
                replace(containerId, EpubNavigatorFragment::class.java, Bundle(), NAVIGATOR_TAG)
            }
        }
    }

    internal fun removeNavigator() {
        val fragment = supportFragmentManager.findFragmentByTag(NAVIGATOR_TAG) ?: return
        supportFragmentManager.beginTransaction()
            .remove(fragment)
            .commitAllowingStateLoss()
    }

    private fun removeRestoredNavigatorIfNeeded(savedInstanceState: Bundle?) {
        if (savedInstanceState == null) {
            return
        }
        val restoredNavigators = supportFragmentManager.fragments
            .filterIsInstance<EpubNavigatorFragment>()
        if (restoredNavigators.isEmpty()) {
            return
        }
        supportFragmentManager.commitNow(allowStateLoss = true) {
            restoredNavigators.forEach { fragment -> remove(fragment) }
        }
    }

    internal fun navigator(): EpubNavigatorFragment? {
        return supportFragmentManager.findFragmentByTag(NAVIGATOR_TAG) as? EpubNavigatorFragment
    }

    internal suspend fun applyContentTheme(preferences: ReaderPreferences): Boolean {
        val script = buildContentThemeScript(preferences.contentTheme())
        val navigator = navigator() ?: return false
        return runCatching {
            navigator.evaluateJavascript(script)
            true
        }.getOrDefault(false)
    }

    internal suspend fun loadInitialLocator(): Locator? {
        val bookId = activeBookId.takeIf { it.isNotBlank() } ?: return null
        return progressRepository.progressForBook(bookId)
            ?.locatorJson
            ?.let { json -> runCatching { Locator.fromJSON(JSONObject(json)) }.getOrNull() }
    }

    internal suspend fun loadInitialProgressPercent(): Float {
        val bookId = activeBookId.takeIf { it.isNotBlank() } ?: return 0f
        return progressRepository.progressForBook(bookId)?.progressPercent ?: 0f
    }

    internal suspend fun saveLocator(locator: Locator, chapterLabel: String?) {
        val bookId = activeBookId.takeIf { it.isNotBlank() } ?: return
        progressRepository.saveProgress(
            bookId = bookId,
            locatorJson = locator.toJSON().toString(),
            progressPercent = locator.progressPercent(),
            chapterLabel = chapterLabel
        )
    }

    private fun configureSystemBars() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = android.graphics.Color.BLACK
        window.navigationBarColor = android.graphics.Color.BLACK
        hideReaderSystemBars()
    }

    internal fun setReaderChromeVisible(visible: Boolean) {
        readerChromeVisible = visible
        if (visible) {
            showReaderStatusBar()
        } else {
            hideReaderSystemBars()
        }
    }

    private fun showReaderStatusBar() {
        WindowInsetsControllerCompat(window, window.decorView).apply {
            systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            show(WindowInsetsCompat.Type.statusBars())
            hide(WindowInsetsCompat.Type.navigationBars())
        }
    }

    private fun hideReaderSystemBars() {
        WindowInsetsControllerCompat(window, window.decorView).apply {
            systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            hide(WindowInsetsCompat.Type.systemBars())
        }
    }

    private fun saveCurrentLocator() {
        val locator = navigator()?.currentLocator?.value ?: return
        lifecycleScope.launch(Dispatchers.IO) {
            saveLocator(locator, locator.title)
            ProgressSyncScheduler.enqueue(applicationContext)
        }
    }

    companion object {
        private const val EXTRA_BOOK_ID = "bookId"
        private const val EXTRA_TITLE = "title"
        private const val EXTRA_FILE_PATH = "filePath"
        private const val NAVIGATOR_TAG = "aurelia-readium-navigator"

        fun newIntent(context: Context, bookId: String, title: String, filePath: String): Intent {
            return Intent(context, ReadiumReaderActivity::class.java)
                .putExtra(EXTRA_BOOK_ID, bookId)
                .putExtra(EXTRA_TITLE, title)
                .putExtra(EXTRA_FILE_PATH, filePath)
        }
    }
}

private data class TocItem(
    val title: String,
    val link: Link,
    val depth: Int
)

@OptIn(ExperimentalMaterial3Api::class, ExperimentalReadiumApi::class)
@Composable
private fun ReadiumReaderScreen(
    title: String,
    filePath: String,
    onBack: () -> Unit
) {
    val activity = LocalContext.current as ReadiumReaderActivity
    val publicationFactory = remember { ReadiumPublicationFactory(activity.applicationContext) }
    val preferencesStore = remember { ReaderPreferencesStore(activity.applicationContext) }
    val coroutineScope = rememberCoroutineScope()
    val containerId = remember { View.generateViewId() }
    var readerPreferences by remember { mutableStateOf(preferencesStore.load()) }
    var overlayVisible by rememberSaveable { mutableStateOf(false) }
    var settingsVisible by rememberSaveable { mutableStateOf(false) }
    var chaptersVisible by rememberSaveable { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(true) }
    var isContentThemed by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var progressLabel by remember { mutableStateOf("0%") }
    var chapterLabel by remember { mutableStateOf("Debut") }
    var clockLabel by remember { mutableStateOf(currentTimeLabel()) }
    var tocItems by remember { mutableStateOf(emptyList<TocItem>()) }
    var lastThemePatchHref by remember { mutableStateOf<String?>(null) }
    val readerChromeVisible = (overlayVisible && error == null) || settingsVisible || chaptersVisible || isLoading || error != null

    DisposableEffect(containerId) {
        onDispose {
            activity.removeNavigator()
        }
    }

    LaunchedEffect(readerChromeVisible) {
        activity.setReaderChromeVisible(readerChromeVisible)
    }

    LaunchedEffect(Unit) {
        while (true) {
            clockLabel = currentTimeLabel()
            delay(30_000)
        }
    }

    LaunchedEffect(readerPreferences) {
        preferencesStore.save(readerPreferences)
        activity.navigator()?.let { navigator ->
            isContentThemed = false
            navigator.submitPreferences(readerPreferences.toEpubPreferences())
            isContentThemed = activity.applyContentTheme(readerPreferences)
        }
        lastThemePatchHref = null
    }

    LaunchedEffect(filePath, containerId) {
        if (filePath.isBlank()) {
            isLoading = false
            isContentThemed = true
            error = "Aucun fichier local a ouvrir."
            return@LaunchedEffect
        }

        runCatching {
            val epubFile = File(filePath)
            if (!epubFile.exists()) {
                error("Fichier EPUB local introuvable. Retelcharge le livre.")
            }
            if (epubFile.length() <= 0L) {
                error("Fichier EPUB local vide. Supprime puis retelcharge le livre.")
            }
            withContext(Dispatchers.IO) {
                publicationFactory.openEpub(epubFile)
            }
        }.onSuccess { session ->
            val initialLocator = withContext(Dispatchers.IO) {
                activity.loadInitialLocator()
            }
            val initialStoredProgress = withContext(Dispatchers.IO) {
                activity.loadInitialProgressPercent()
            }
            tocItems = flattenToc(session.publication.tableOfContents)
            val initialDisplayProgress = initialLocator?.progressPercent()
                ?.takeIf { it > 0f }
                ?: initialStoredProgress
            if (initialDisplayProgress > 0f) {
                progressLabel = "${initialDisplayProgress.roundToInt()}%"
            }
            initialLocator?.let { locator ->
                chapterLabel = locator.title?.takeIf { it.isNotBlank() }
                    ?: matchingChapterTitle(tocItems, locator.href.toString())
                    ?: chapterLabel
            }
            val fragmentFactory = session.navigatorFactory.createFragmentFactory(
                initialLocator = initialLocator,
                initialPreferences = readerPreferences.toEpubPreferences()
            )
            activity.attachNavigator(
                fragmentFactory = fragmentFactory,
                containerId = containerId,
                publication = session.publication
            )
            val navigator = activity.navigator()
            if (navigator != null) {
                isContentThemed = activity.applyContentTheme(readerPreferences)
                navigator.addInputListener(
                    object : InputListener {
                        override fun onTap(event: TapEvent): Boolean {
                            overlayVisible = !overlayVisible
                            if (!overlayVisible) {
                                settingsVisible = false
                            }
                            return true
                        }
                    }
                )
            } else {
                isContentThemed = true
            }
            isLoading = false

            val initialProgress = maxOf(initialLocator?.progressPercent() ?: 0f, initialStoredProgress)
            var hasSeenLocator = false
            activity.navigator()?.currentLocator?.collect { locator ->
                val percentValue = locator.progressPercent()
                val shouldSkipInitialZero = !hasSeenLocator && initialProgress > 0.5f && percentValue <= 0.5f
                hasSeenLocator = true
                if (shouldSkipInitialZero) {
                    return@collect
                }

                val percent = percentValue.roundToInt()
                progressLabel = "$percent%"
                val currentChapter = locator.title?.takeIf { it.isNotBlank() }
                    ?: matchingChapterTitle(tocItems, locator.href.toString())
                    ?: "Chapitre"
                chapterLabel = currentChapter
                val href = locator.href.toString()
                if (href != lastThemePatchHref) {
                    lastThemePatchHref = href
                    isContentThemed = false
                    isContentThemed = activity.applyContentTheme(readerPreferences)
                }
                withContext(Dispatchers.IO) {
                    activity.saveLocator(locator, currentChapter)
                }
            }
        }.onFailure { throwable ->
            isLoading = false
            isContentThemed = true
            error = throwable.message ?: "Impossible d'ouvrir cet EPUB."
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        AndroidView(
            factory = { context ->
                FrameLayout(context).apply {
                    id = containerId
                    layoutParams = FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT
                    )
                }
            },
            modifier = Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
        )

        ReaderBrightnessLayer(brightness = readerPreferences.brightness)

        if (!isContentThemed && error == null) {
            ReaderThemeCover()
        }

        if (isLoading || error != null) {
            ReaderStatusOverlay(
                isLoading = isLoading,
                error = error,
                onBack = onBack
            )
        }

        AnimatedVisibility(
            visible = overlayVisible && error == null,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            ReaderOverlay(
                title = title,
                progressLabel = progressLabel,
                chapterLabel = chapterLabel,
                timeLabel = clockLabel,
                onBack = onBack,
                onSettings = { settingsVisible = !settingsVisible },
                onOpenChapters = { chaptersVisible = true },
                onPrevious = { activity.navigator()?.goBackward(animated = true) },
                onNext = { activity.navigator()?.goForward(animated = true) }
            )
        }

        if (chaptersVisible) {
            ChapterListSheet(
                chapters = tocItems,
                onChapterClick = { item ->
                    activity.navigator()?.go(item.link, animated = true)
                    chaptersVisible = false
                    overlayVisible = false
                    settingsVisible = false
                    lastThemePatchHref = null
                    coroutineScope.launch {
                        delay(180)
                        activity.navigator()?.submitPreferences(readerPreferences.toEpubPreferences())
                        isContentThemed = activity.applyContentTheme(readerPreferences)
                    }
                },
                onDismiss = { chaptersVisible = false }
            )
        }

        if (settingsVisible) {
            ReaderSettingsMenu(
                preferences = readerPreferences,
                onPreferencesChange = { readerPreferences = it }
            )
        }
    }
}

@Composable
private fun ReaderBrightnessLayer(brightness: Float) {
    val dimAlpha = ((1f - brightness.coerceIn(0.2f, 1f)) * 0.78f).coerceIn(0f, 0.62f)
    if (dimAlpha > 0.01f) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = dimAlpha))
        )
    }
}

@Composable
private fun ReaderThemeCover() {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {}
}

@Composable
private fun ReaderStatusOverlay(
    isLoading: Boolean,
    error: String?,
    onBack: () -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator()
                    Text("Ouverture EPUB")
                } else {
                    Text(error ?: "Erreur reader", color = MaterialTheme.colorScheme.error)
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Outlined.ArrowBack,
                            contentDescription = "Retour",
                            tint = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ReaderOverlay(
    title: String,
    progressLabel: String,
    chapterLabel: String,
    timeLabel: String,
    onBack: () -> Unit,
    onSettings: () -> Unit,
    onOpenChapters: () -> Unit,
    onPrevious: () -> Unit,
    onNext: () -> Unit
) {
    val overlayText = MaterialTheme.colorScheme.primary
    val overlayMuted = MaterialTheme.colorScheme.primary.copy(alpha = 0.78f)

    Box(modifier = Modifier.fillMaxSize()) {
        Surface(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = 12.dp, vertical = 8.dp),
            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.88f),
            contentColor = overlayText,
            tonalElevation = 6.dp,
            shape = RoundedCornerShape(999.dp)
        ) {
            Row(
                modifier = Modifier.padding(start = 4.dp, end = 8.dp, top = 4.dp, bottom = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                IconButton(onClick = onBack, modifier = Modifier.size(44.dp)) {
                    Icon(
                        Icons.AutoMirrored.Outlined.ArrowBack,
                        contentDescription = "Retour",
                        tint = overlayText
                    )
                }
                Text(
                    text = title,
                    color = overlayText,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = timeLabel,
                    color = overlayMuted,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold
                )
                IconButton(onClick = onSettings, modifier = Modifier.size(44.dp)) {
                    Icon(
                        Icons.Outlined.Settings,
                        contentDescription = "Reglages",
                        tint = overlayText
                    )
                }
            }
        }

        Surface(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = 12.dp, vertical = 8.dp),
            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.94f),
            contentColor = overlayText,
            tonalElevation = 6.dp,
            shape = RoundedCornerShape(999.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onPrevious, modifier = Modifier.size(48.dp)) {
                        Icon(
                            Icons.AutoMirrored.Outlined.NavigateBefore,
                            contentDescription = "Page precedente",
                            tint = overlayText
                        )
                }
                TextButton(
                    onClick = onOpenChapters,
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "$progressLabel - $chapterLabel",
                        color = overlayMuted,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                IconButton(onClick = onNext, modifier = Modifier.size(48.dp)) {
                        Icon(
                            Icons.AutoMirrored.Outlined.NavigateNext,
                            contentDescription = "Page suivante",
                            tint = overlayText
                        )
                }
            }
        }
    }
}

@Composable
private fun ReaderSettingsMenu(
    preferences: ReaderPreferences,
    onPreferencesChange: (ReaderPreferences) -> Unit
) {
    val gold = MaterialTheme.colorScheme.primary

    Box(modifier = Modifier.fillMaxSize()) {
        Surface(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(top = 54.dp, start = 20.dp, end = 10.dp)
                .fillMaxWidth(0.70f)
                .widthIn(max = 260.dp),
            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.94f),
            contentColor = gold,
            tonalElevation = 6.dp,
            shape = RoundedCornerShape(12.dp),
            border = BorderStroke(1.dp, gold.copy(alpha = 0.18f))
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 360.dp)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 10.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    "Reglages",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = gold
                )

                SettingGroup("Lecture") {
                    DropdownSetting(
                        value = preferences.flow,
                        options = ReaderFlow.values().toList(),
                        labelFor = { it.label },
                        onSelect = { onPreferencesChange(preferences.copy(flow = it)) }
                    )
                }

                SliderSetting(
                    label = "Lumiere",
                    valueLabel = "${(preferences.brightness * 100).roundToInt()}%",
                    value = preferences.brightness,
                    valueRange = 0.2f..1f,
                    onValueChange = { onPreferencesChange(preferences.copy(brightness = it)) }
                )

                SettingGroup("Theme") {
                    DropdownSetting(
                        value = preferences.theme,
                        options = ReaderTheme.values().toList(),
                        labelFor = { it.label },
                        onSelect = { onPreferencesChange(preferences.copy(theme = it)) }
                    )
                }

                SliderSetting(
                    label = "Taille texte",
                    valueLabel = "${(preferences.fontSize * 100).roundToInt()}%",
                    value = preferences.fontSize.toFloat(),
                    valueRange = 0.8f..1.6f,
                    onValueChange = { onPreferencesChange(preferences.copy(fontSize = it.toDouble())) }
                )

                SettingGroup("Alignement") {
                    DropdownSetting(
                        value = preferences.textAlign,
                        options = ReaderTextAlign.values().toList(),
                        labelFor = { it.label },
                        onSelect = { onPreferencesChange(preferences.copy(textAlign = it)) }
                    )
                }

                SliderSetting(
                    label = "Marges",
                    valueLabel = formatDecimal(preferences.pageMargins),
                    value = preferences.pageMargins.toFloat(),
                    valueRange = 0.5f..2.0f,
                    onValueChange = { onPreferencesChange(preferences.copy(pageMargins = it.toDouble())) }
                )

                SliderSetting(
                    label = "Interligne",
                    valueLabel = formatDecimal(preferences.lineHeight),
                    value = preferences.lineHeight.toFloat(),
                    valueRange = 1.1f..2.2f,
                    onValueChange = { onPreferencesChange(preferences.copy(lineHeight = it.toDouble())) }
                )

                SettingGroup("Police") {
                    DropdownSetting(
                        value = preferences.font,
                        options = ReaderFont.values().toList(),
                        labelFor = { it.label },
                        onSelect = { onPreferencesChange(preferences.copy(font = it)) }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChapterListSheet(
    chapters: List<TocItem>,
    onChapterClick: (TocItem) -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val gold = MaterialTheme.colorScheme.primary

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        contentColor = gold
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Chapitres",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = gold
                )
                TextButton(onClick = onDismiss) {
                    Text("Fermer", color = gold)
                }
            }
            if (chapters.isEmpty()) {
                Text("Table des matieres indisponible.", color = gold.copy(alpha = 0.72f))
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(420.dp)
                ) {
                    items(chapters) { chapter ->
                        TextButton(
                            onClick = { onChapterClick(chapter) },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = chapter.title,
                                color = gold,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(start = (chapter.depth * 16).dp),
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun SettingGroup(title: String, content: @Composable () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
        Text(
            title,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary.copy(alpha = 0.82f)
        )
        content()
    }
}

@Composable
private fun <T> DropdownSetting(
    value: T,
    options: List<T>,
    labelFor: (T) -> String,
    onSelect: (T) -> Unit
) {
    var expanded by remember { mutableStateOf(false) }

    Box {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { expanded = !expanded },
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.42f),
            contentColor = MaterialTheme.colorScheme.primary,
            shape = RoundedCornerShape(10.dp)
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = labelFor(value),
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = "v",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.72f)
                )
            }
        }
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.width(220.dp)
        ) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = {
                        Text(
                            text = labelFor(option),
                            color = MaterialTheme.colorScheme.primary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    },
                    onClick = {
                        onSelect(option)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
private fun SliderSetting(
    label: String,
    valueLabel: String,
    value: Float,
    valueRange: ClosedFloatingPointRange<Float>,
    onValueChange: (Float) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                label,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.82f)
            )
            Text(
                valueLabel,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.64f)
            )
        }
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = valueRange
        )
    }
}

private val ReaderTheme.label: String
    get() = when (this) {
        ReaderTheme.White -> "Clair"
        ReaderTheme.Gray -> "Gris"
        ReaderTheme.Black -> "Noir"
        ReaderTheme.Sepia -> "Sepia"
        ReaderTheme.Aurelia -> "Aurelia"
    }

private val ReaderFlow.label: String
    get() = when (this) {
        ReaderFlow.Auto -> "Auto"
        ReaderFlow.Paged -> "Pages"
        ReaderFlow.Scrolled -> "Defilement"
    }

private val ReaderTextAlign.label: String
    get() = when (this) {
        ReaderTextAlign.Left -> "Gauche"
        ReaderTextAlign.Justify -> "Justifie"
    }

private val ReaderFont.label: String
    get() = when (this) {
        ReaderFont.Original -> "Original"
        ReaderFont.Serif -> "Serif"
        ReaderFont.Sans -> "Sans"
        ReaderFont.Dyslexic -> "Dyslexie"
        ReaderFont.Mono -> "Mono"
    }

private fun formatDecimal(value: Double): String {
    return String.format(Locale.US, "%.1f", value)
}

private fun currentTimeLabel(): String {
    return LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm"))
}

private fun buildContentThemeScript(theme: ReaderContentTheme): String {
    val css = """
        html, body {
          background-color: ${theme.background} !important;
          color: ${theme.text} !important;
          -webkit-text-fill-color: ${theme.text} !important;
        }
        html *,
        body *:not(img):not(svg):not(video):not(canvas) {
          color: ${theme.text} !important;
          -webkit-text-fill-color: ${theme.text} !important;
          border-color: currentColor !important;
          text-shadow: none !important;
        }
        p, span, div, section, article, main, header, footer, aside,
        blockquote, figcaption, dt, dd, li {
          color: ${theme.text} !important;
          -webkit-text-fill-color: ${theme.text} !important;
        }
        h1, h2, h3, h4, h5, h6,
        [class*="title"], [class*="titre"], [class*="chapter"], [class*="chapitre"],
        [id*="title"], [id*="titre"], [id*="chapter"], [id*="chapitre"],
        [role*="doc-chapter"], [epub\:type*="chapter"], [epub\:type*="titlepage"] {
          color: ${theme.text} !important;
          -webkit-text-fill-color: ${theme.text} !important;
          background-color: transparent !important;
        }
        a, a * {
          color: ${theme.link} !important;
          -webkit-text-fill-color: ${theme.link} !important;
        }
        svg text {
          fill: ${theme.text} !important;
          stroke: none !important;
        }
    """.trimIndent()

    return """
        (function() {
          var id = 'aurelia-reader-theme';
          var style = document.getElementById(id);
          if (!style) {
            style = document.createElement('style');
            style.id = id;
            (document.head || document.documentElement).appendChild(style);
          }
          style.textContent = ${JSONObject.quote(css)};
        })();
    """.trimIndent()
}

private fun flattenToc(links: List<Link>, depth: Int = 0): List<TocItem> {
    return links.flatMap { link ->
        val title = link.title?.takeIf { it.isNotBlank() } ?: "Chapitre"
        listOf(TocItem(title = title, link = link, depth = depth)) + flattenToc(link.children, depth + 1)
    }
}

private fun matchingChapterTitle(chapters: List<TocItem>, href: String): String? {
    val key = href.chapterKey()
    return chapters.lastOrNull { item ->
        key.startsWith(item.link.href.toString().chapterKey())
    }?.title
}

private fun String.chapterKey(): String {
    return substringBefore('#').substringBefore('?')
}

private fun Locator.progressPercent(): Float {
    val progress = ((locations.totalProgression ?: 0.0) * 100.0)
        .toFloat()
        .coerceIn(0f, 100f)
    return if (progress >= 99f) 100f else progress
}

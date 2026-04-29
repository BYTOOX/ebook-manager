package ch.bytoox.aureliareader

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import ch.bytoox.aureliareader.data.sync.ProgressSyncScheduler
import ch.bytoox.aureliareader.ui.app.AppViewModel

class MainActivity : ComponentActivity() {
    private val appViewModel: AppViewModel by viewModels {
        AppViewModel.factory(applicationContext)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        ProgressSyncScheduler.schedulePeriodic(applicationContext)
        ProgressSyncScheduler.enqueue(applicationContext)
        setContent {
            AureliaReaderApp(appViewModel = appViewModel)
        }
    }
}

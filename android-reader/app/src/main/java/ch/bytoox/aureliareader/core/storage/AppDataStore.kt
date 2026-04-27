package ch.bytoox.aureliareader.core.storage

import android.content.Context
import androidx.datastore.preferences.preferencesDataStore

val Context.aureliaDataStore by preferencesDataStore(name = "aurelia_reader")

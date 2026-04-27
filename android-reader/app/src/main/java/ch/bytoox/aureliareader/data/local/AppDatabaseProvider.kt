package ch.bytoox.aureliareader.data.local

import android.content.Context
import androidx.room.Room

object AppDatabaseProvider {
    @Volatile
    private var database: AppDatabase? = null

    fun get(context: Context): AppDatabase {
        return database ?: synchronized(this) {
            database ?: Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                "aurelia_reader.db"
            )
                .addMigrations(DatabaseMigrations.MIGRATION_1_2)
                .addMigrations(DatabaseMigrations.MIGRATION_2_3)
                .build()
                .also { database = it }
        }
    }
}

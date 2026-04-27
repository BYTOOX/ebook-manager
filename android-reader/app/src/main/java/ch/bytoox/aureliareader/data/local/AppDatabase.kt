package ch.bytoox.aureliareader.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import ch.bytoox.aureliareader.data.local.dao.BookDao
import ch.bytoox.aureliareader.data.local.dao.DownloadDao
import ch.bytoox.aureliareader.data.local.dao.ProgressDao
import ch.bytoox.aureliareader.data.local.dao.SyncEventDao
import ch.bytoox.aureliareader.data.local.entities.BookEntity
import ch.bytoox.aureliareader.data.local.entities.DownloadEntity
import ch.bytoox.aureliareader.data.local.entities.ProgressEntity
import ch.bytoox.aureliareader.data.local.entities.SyncEventEntity

@Database(
    entities = [
        BookEntity::class,
        DownloadEntity::class,
        ProgressEntity::class,
        SyncEventEntity::class
    ],
    version = 3,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun bookDao(): BookDao
    abstract fun downloadDao(): DownloadDao
    abstract fun progressDao(): ProgressDao
    abstract fun syncEventDao(): SyncEventDao
}

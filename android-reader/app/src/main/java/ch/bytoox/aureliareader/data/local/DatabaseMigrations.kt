package ch.bytoox.aureliareader.data.local

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

object DatabaseMigrations {
    val MIGRATION_1_2 = object : Migration(1, 2) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL(
                """
                CREATE TABLE IF NOT EXISTS progress (
                    bookId TEXT NOT NULL PRIMARY KEY,
                    locatorJson TEXT NOT NULL,
                    progressPercent REAL NOT NULL,
                    chapterLabel TEXT,
                    updatedAt INTEGER NOT NULL,
                    dirty INTEGER NOT NULL
                )
                """.trimIndent()
            )
        }
    }

    val MIGRATION_2_3 = object : Migration(2, 3) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL("ALTER TABLE progress ADD COLUMN syncStatus TEXT NOT NULL DEFAULT 'pending'")
            db.execSQL("ALTER TABLE progress ADD COLUMN lastSyncedAt INTEGER")
            db.execSQL("ALTER TABLE progress ADD COLUMN syncError TEXT")
            db.execSQL(
                """
                CREATE TABLE IF NOT EXISTS sync_events (
                    bookId TEXT NOT NULL PRIMARY KEY,
                    eventId TEXT NOT NULL,
                    type TEXT NOT NULL,
                    payloadJson TEXT NOT NULL,
                    clientCreatedAt INTEGER NOT NULL,
                    updatedAt INTEGER NOT NULL,
                    attempts INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    lastError TEXT
                )
                """.trimIndent()
            )
        }
    }
}

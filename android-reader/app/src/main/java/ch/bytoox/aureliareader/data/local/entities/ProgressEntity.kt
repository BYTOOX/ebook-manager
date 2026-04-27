package ch.bytoox.aureliareader.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "progress")
data class ProgressEntity(
    @PrimaryKey val bookId: String,
    val locatorJson: String,
    val progressPercent: Float,
    val chapterLabel: String?,
    val updatedAt: Long,
    val dirty: Boolean,
    val syncStatus: String,
    val lastSyncedAt: Long?,
    val syncError: String?
)

package ch.bytoox.aureliareader.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "books")
data class BookEntity(
    @PrimaryKey val id: String,
    val title: String,
    val authorsJson: String,
    val coverUrl: String?,
    val localCoverPath: String?,
    val localFilePath: String?,
    val isDownloaded: Boolean,
    val fileSize: Long?,
    val progressPercent: Float?,
    val lastOpenedAt: String?,
    val metadataJson: String,
    val updatedAt: Long
)

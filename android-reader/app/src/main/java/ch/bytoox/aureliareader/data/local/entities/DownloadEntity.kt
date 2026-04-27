package ch.bytoox.aureliareader.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "downloads")
data class DownloadEntity(
    @PrimaryKey val bookId: String,
    val status: String,
    val progress: Int,
    val error: String?,
    val updatedAt: Long
)

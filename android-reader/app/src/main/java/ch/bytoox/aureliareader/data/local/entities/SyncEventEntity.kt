package ch.bytoox.aureliareader.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "sync_events")
data class SyncEventEntity(
    @PrimaryKey val bookId: String,
    val eventId: String,
    val type: String,
    val payloadJson: String,
    val clientCreatedAt: Long,
    val updatedAt: Long,
    val attempts: Int,
    val status: String,
    val lastError: String?
)

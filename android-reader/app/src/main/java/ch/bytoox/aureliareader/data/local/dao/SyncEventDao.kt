package ch.bytoox.aureliareader.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import ch.bytoox.aureliareader.data.local.entities.SyncEventEntity

@Dao
interface SyncEventDao {
    @Query("SELECT * FROM sync_events WHERE status IN ('pending', 'failed') ORDER BY updatedAt ASC LIMIT :limit")
    suspend fun pending(limit: Int): List<SyncEventEntity>

    @Query("SELECT * FROM sync_events WHERE bookId = :bookId LIMIT 1")
    suspend fun eventForBook(bookId: String): SyncEventEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(event: SyncEventEntity)

    @Query(
        """
        UPDATE sync_events
        SET status = 'failed',
            attempts = attempts + 1,
            lastError = :error,
            updatedAt = :updatedAt
        WHERE bookId = :bookId
        """
    )
    suspend fun markFailed(bookId: String, error: String, updatedAt: Long)

    @Query("DELETE FROM sync_events WHERE bookId = :bookId")
    suspend fun deleteForBook(bookId: String)
}

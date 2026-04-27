package ch.bytoox.aureliareader.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import ch.bytoox.aureliareader.data.local.entities.ProgressEntity

@Dao
interface ProgressDao {
    @Query("SELECT * FROM progress")
    suspend fun all(): List<ProgressEntity>

    @Query("SELECT * FROM progress WHERE bookId = :bookId LIMIT 1")
    suspend fun progressByBookId(bookId: String): ProgressEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(progress: ProgressEntity)

    @Query(
        """
        UPDATE progress
        SET dirty = 0,
            syncStatus = 'synced',
            lastSyncedAt = :syncedAt,
            syncError = NULL
        WHERE bookId = :bookId
        """
    )
    suspend fun markSynced(bookId: String, syncedAt: Long)

    @Query(
        """
        UPDATE progress
        SET dirty = 1,
            syncStatus = :syncStatus,
            syncError = :syncError
        WHERE bookId = :bookId
        """
    )
    suspend fun markSyncState(bookId: String, syncStatus: String, syncError: String?)
}

package ch.bytoox.aureliareader.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import ch.bytoox.aureliareader.data.local.entities.DownloadEntity

@Dao
interface DownloadDao {
    @Query("SELECT * FROM downloads WHERE bookId = :bookId LIMIT 1")
    suspend fun downloadByBookId(bookId: String): DownloadEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(download: DownloadEntity)

    @Query("DELETE FROM downloads WHERE bookId = :bookId")
    suspend fun delete(bookId: String)
}

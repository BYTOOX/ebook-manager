package ch.bytoox.aureliareader.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import ch.bytoox.aureliareader.data.local.entities.BookEntity

@Dao
interface BookDao {
    @Query("SELECT id FROM books WHERE isDownloaded = 1 AND localFilePath IS NOT NULL")
    suspend fun downloadedBookIds(): List<String>

    @Query("SELECT * FROM books WHERE isDownloaded = 1 AND localFilePath IS NOT NULL ORDER BY updatedAt DESC")
    suspend fun downloadedBooks(): List<BookEntity>

    @Query("SELECT * FROM books WHERE id = :bookId LIMIT 1")
    suspend fun bookById(bookId: String): BookEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(book: BookEntity)

    @Query(
        """
        UPDATE books
        SET isDownloaded = 0,
            localFilePath = NULL,
            localCoverPath = NULL,
            updatedAt = :updatedAt
        WHERE id = :bookId
        """
    )
    suspend fun clearDownload(bookId: String, updatedAt: Long)
}

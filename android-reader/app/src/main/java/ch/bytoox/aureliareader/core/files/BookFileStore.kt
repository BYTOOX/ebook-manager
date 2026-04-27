package ch.bytoox.aureliareader.core.files

import android.content.Context
import java.io.File

class BookFileStore(context: Context) {
    private val appContext = context.applicationContext
    private val filesDir = appContext.filesDir
    private val cacheDir = appContext.cacheDir
    private val booksDir = File(filesDir, "books")
    private val coversDir = File(filesDir, "covers")
    private val readerCacheDir = File(cacheDir, "reader-books")

    fun bookFile(bookId: String): File {
        booksDir.mkdirs()
        return File(booksDir, "$bookId.epub")
    }

    fun coverFile(bookId: String): File {
        coversDir.mkdirs()
        return File(coversDir, "$bookId.jpg")
    }

    fun readerTempFile(bookId: String): File {
        readerCacheDir.mkdirs()
        return File(readerCacheDir, "$bookId.epub")
    }

    fun hasBookFile(bookId: String): Boolean {
        val file = bookFile(bookId)
        return file.exists() && file.length() > 0L
    }

    fun deleteBookFiles(bookId: String) {
        listOf(bookFile(bookId), coverFile(bookId)).forEach { file ->
            if (file.exists()) {
                file.delete()
            }
        }
    }
}

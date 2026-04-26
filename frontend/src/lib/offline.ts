import { apiBlob, type BookDetail } from "./api";
import { db } from "./db";

async function fetchOptionalBlob(url: string | null) {
  if (!url) {
    return undefined;
  }
  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) {
    return undefined;
  }
  return response.blob();
}

export async function isBookOffline(bookId: string) {
  const book = await db.offline_books.get(bookId);
  return Boolean(book?.epub_blob);
}

export async function listOfflineBookIds() {
  const books = await db.offline_books.toArray();
  return books.filter((book) => Boolean(book.epub_blob)).map((book) => book.book_id);
}

export function applyLocalOfflineAvailability<T extends { id: string; is_offline_available: boolean }>(
  books: T[],
  offlineBookIds: Set<string>
) {
  return books.map((book) => {
    if (book.is_offline_available || !offlineBookIds.has(book.id)) {
      return book;
    }
    return { ...book, is_offline_available: true };
  });
}

export async function getOfflineBookDetail(bookId: string) {
  const book = await db.offline_books.get(bookId);
  if (!book?.epub_blob || !book.metadata_snapshot) {
    return null;
  }
  return {
    ...book.metadata_snapshot,
    title: book.title,
    authors: book.authors,
    tags: book.metadata_snapshot.tags ?? [],
    is_offline_available: true
  };
}

export async function getOfflineCoverObjectUrl(bookId: string) {
  const book = await db.offline_books.get(bookId);
  if (!book?.cover_blob) {
    return null;
  }
  return URL.createObjectURL(book.cover_blob);
}

export async function downloadBookForOffline(book: BookDetail) {
  const [epubBlob, coverBlob] = await Promise.all([
    apiBlob(`/books/${book.id}/file`),
    fetchOptionalBlob(book.cover_url)
  ]);

  await db.offline_books.put({
    book_id: book.id,
    title: book.title,
    authors: book.authors,
    cover_blob: coverBlob,
    epub_blob: epubBlob,
    metadata_snapshot: { ...book, is_offline_available: true },
    downloaded_at: new Date().toISOString(),
    file_size: book.file_size ?? epubBlob.size,
    version_hash: `${book.file_size ?? epubBlob.size}:${book.original_filename ?? book.id}`
  });
}

export async function refreshOfflineBookMetadata(book: BookDetail) {
  const offlineBook = await db.offline_books.get(book.id);
  if (!offlineBook) {
    return false;
  }
  const coverBlob = await fetchOptionalBlob(book.cover_url);
  await db.offline_books.update(book.id, {
    title: book.title,
    authors: book.authors,
    cover_blob: coverBlob ?? offlineBook.cover_blob,
    metadata_snapshot: { ...book, is_offline_available: true }
  });
  return true;
}

export async function removeOfflineBook(bookId: string) {
  await db.offline_books.delete(bookId);
}

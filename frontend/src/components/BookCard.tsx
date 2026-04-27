import { Bookmark, Star } from "lucide-react";
import { Link } from "react-router-dom";
import type { BookListItem } from "../lib/api";
import { AuthenticatedImage } from "./AuthenticatedImage";

export function BookCard({ book, dense = false }: { book: BookListItem; dense?: boolean }) {
  const progress = Math.max(0, Math.min(100, book.progress_percent ?? 0));
  const author = book.authors[0] ?? "Auteur inconnu";

  return (
    <Link className={dense ? "book-row" : "book-card"} to={`/books/${book.id}`}>
      <div className="cover">
        <AuthenticatedImage src={book.cover_url} alt="" loading="lazy" fallback={<span>{book.title[0]}</span>} />
        {book.is_offline_available && (
          <span className="cover-badge" aria-label="Disponible hors ligne">
            <Bookmark size={13} aria-hidden="true" />
          </span>
        )}
      </div>
      <div className="book-meta">
        <strong>{book.title}</strong>
        <span>{author}</span>
        <div className="book-signals">
          <span className="stars" aria-label={`${book.rating ?? 0} etoiles`}>
            <Star size={13} aria-hidden="true" />
            {book.rating ?? "-"}
          </span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-track" aria-hidden="true">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>
    </Link>
  );
}

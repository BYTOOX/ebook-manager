import { BookOpen, Download, FileText, Play, Star, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { apiFetch, type BookDetail } from "../lib/api";
import { BookCard } from "../components/BookCard";

function formatBytes(size: number | null) {
  if (!size) {
    return "Inconnu";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const suffix = units[unit] ?? "B";
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${suffix}`;
}

export function BookDetailPage() {
  const { bookId } = useParams();
  const { data } = useQuery({
    queryKey: ["book", bookId],
    queryFn: () => apiFetch<BookDetail>(`/books/${bookId}`),
    enabled: Boolean(bookId)
  });

  if (!data) {
    return <main className="page"><div className="skeleton tall" /></main>;
  }

  return (
    <main className="book-detail">
      <div className="detail-cover">
        {data.cover_url ? <img src={data.cover_url} alt="" /> : <span>{data.title[0]}</span>}
      </div>
      <section className="detail-body">
        <p className="eyebrow">{data.status}</p>
        <h1>{data.title}</h1>
        <p>{data.authors.join(", ") || "Auteur inconnu"}</p>
        <div className="rating-line">
          <Star size={18} aria-hidden="true" />
          <span>{data.rating ?? "-"} / 5</span>
        </div>
        <div className="progress-track large" aria-hidden="true">
          <span style={{ width: `${data.progress_percent ?? 0}%` }} />
        </div>
        <div className="action-row">
          <Link className="primary-action" to={`/reader/${data.id}`}>
            <Play size={18} aria-hidden="true" />
            Lire
          </Link>
          <button className="secondary-action">
            <Download size={18} aria-hidden="true" />
            Offline
          </button>
        </div>
        {data.description && <p className="description">{data.description}</p>}
        <section className="metadata-band" aria-label="Metadonnees du livre">
          <div className="metadata-heading">
            <FileText size={18} aria-hidden="true" />
            <h2>Infos livre</h2>
          </div>
          <dl className="metadata-grid">
            <div>
              <dt>Auteur</dt>
              <dd>{data.authors.join(", ") || "Auteur inconnu"}</dd>
            </div>
            {data.publisher && (
              <div>
                <dt>Editeur</dt>
                <dd>{data.publisher}</dd>
              </div>
            )}
            {data.published_date && (
              <div>
                <dt>Publication</dt>
                <dd>{data.published_date}</dd>
              </div>
            )}
            {data.language && (
              <div>
                <dt>Langue</dt>
                <dd>{data.language.toUpperCase()}</dd>
              </div>
            )}
            {data.isbn && (
              <div>
                <dt>ISBN</dt>
                <dd>{data.isbn}</dd>
              </div>
            )}
            <div>
              <dt>Fichier</dt>
              <dd>{data.original_filename ?? "EPUB local"} - {formatBytes(data.file_size)}</dd>
            </div>
          </dl>
        </section>
        {data.series && (
          <section className="metadata-band" aria-label="Serie">
            <div className="metadata-heading">
              <BookOpen size={18} aria-hidden="true" />
              <h2>{data.series.name}</h2>
            </div>
            <p className="muted-line">
              {data.series.index ? `Tome ${data.series.index}` : "Serie detectee depuis le dossier d'import."}
            </p>
            {data.related_books.length > 0 && (
              <div className="related-rail">
                {data.related_books.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            )}
          </section>
        )}
        {(data.characters.length > 0 || data.subjects.length > 0 || data.contributors.length > 0) && (
          <section className="metadata-band" aria-label="Sujets et personnages">
            <div className="metadata-heading">
              <Users size={18} aria-hidden="true" />
              <h2>Univers</h2>
            </div>
            {data.characters.length > 0 && (
              <>
                <h3>Personnages</h3>
                <div className="chip-list">
                  {data.characters.map((character) => <span key={character}>{character}</span>)}
                </div>
              </>
            )}
            {data.subjects.length > 0 && (
              <>
                <h3>Sujets</h3>
                <div className="chip-list">
                  {data.subjects.map((subject) => <span key={subject}>{subject}</span>)}
                </div>
              </>
            )}
            {data.contributors.length > 0 && (
              <>
                <h3>Contributeurs</h3>
                <div className="chip-list">
                  {data.contributors.map((contributor) => <span key={contributor}>{contributor}</span>)}
                </div>
              </>
            )}
          </section>
        )}
      </section>
    </main>
  );
}

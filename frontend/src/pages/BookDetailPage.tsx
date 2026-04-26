import { Download, Play, Star } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { apiFetch, type BookListItem } from "../lib/api";

type BookDetail = BookListItem & {
  subtitle: string | null;
  description: string | null;
  language: string | null;
  isbn: string | null;
  publisher: string | null;
  published_date: string | null;
};

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
      </section>
    </main>
  );
}

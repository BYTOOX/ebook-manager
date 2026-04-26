import { ArrowRight, Download, Play } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiFetch, type BookListResponse } from "../lib/api";
import { BookCard } from "../components/BookCard";
import { EmptyLibrary } from "../components/EmptyLibrary";

export function HomePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["books", "home"],
    queryFn: () => apiFetch<BookListResponse>("/books?limit=12")
  });

  const books = data?.items ?? [];
  const continueBook = books.find((book) => book.status === "in_progress") ?? books[0];

  if (!isLoading && books.length === 0) {
    return <EmptyLibrary />;
  }

  return (
    <main className="page">
      <section className="continue-panel">
        <p className="eyebrow">Continuer la lecture</p>
        {continueBook ? (
          <div className="continue-content">
            <div className="hero-cover">
              {continueBook.cover_url ? <img src={continueBook.cover_url} alt="" /> : <span>{continueBook.title[0]}</span>}
            </div>
            <div>
              <h1>{continueBook.title}</h1>
              <p>{continueBook.authors[0] ?? "Auteur inconnu"}</p>
              <div className="progress-track large" aria-hidden="true">
                <span style={{ width: `${continueBook.progress_percent ?? 0}%` }} />
              </div>
              <Link className="primary-action" to={`/reader/${continueBook.id}`}>
                <Play size={18} aria-hidden="true" />
                Lire
              </Link>
            </div>
          </div>
        ) : (
          <div className="skeleton tall" />
        )}
      </section>

      <section className="section-heading">
        <h2>Telecharges</h2>
        <Download size={18} aria-hidden="true" />
      </section>
      <div className="horizontal-rail">
        {books
          .filter((book) => book.is_offline_available)
          .slice(0, 6)
          .map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        {!books.some((book) => book.is_offline_available) && <p className="muted-line">Aucun EPUB hors ligne.</p>}
      </div>

      <section className="section-heading">
        <h2>Recemment ajoutes</h2>
        <Link to="/library" className="text-action">
          Voir
          <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </section>
      <div className="book-grid">
        {books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </main>
  );
}

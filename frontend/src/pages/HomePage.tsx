import { ArrowRight, Download, Play } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, type BookListResponse } from "../lib/api";
import { BookCard } from "../components/BookCard";
import { EmptyLibrary } from "../components/EmptyLibrary";
import { applyLocalOfflineAvailability, listOfflineBookIds } from "../lib/offline";

export function HomePage() {
  const [offlineBookIds, setOfflineBookIds] = useState<Set<string>>(new Set());
  const { data, isLoading } = useQuery({
    queryKey: ["books", "home"],
    queryFn: () => apiFetch<BookListResponse>("/books?limit=12")
  });

  const books = data?.items ?? [];
  const booksWithOffline = useMemo(
    () => applyLocalOfflineAvailability(books, offlineBookIds),
    [books, offlineBookIds]
  );
  const downloadedBooks = booksWithOffline.filter((book) => book.is_offline_available).slice(0, 6);
  const continueBook = booksWithOffline.find((book) => book.status === "in_progress") ?? booksWithOffline[0];

  useEffect(() => {
    let mounted = true;
    listOfflineBookIds()
      .then((ids) => {
        if (mounted) {
          setOfflineBookIds(new Set(ids));
        }
      })
      .catch(() => {
        if (mounted) {
          setOfflineBookIds(new Set());
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (!isLoading && booksWithOffline.length === 0) {
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
        {downloadedBooks.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
        {downloadedBooks.length === 0 && <p className="muted-line">Aucun EPUB hors ligne.</p>}
      </div>

      <section className="section-heading">
        <h2>Recemment ajoutes</h2>
        <Link to="/library" className="text-action">
          Voir
          <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </section>
      <div className="book-grid">
        {booksWithOffline.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </main>
  );
}

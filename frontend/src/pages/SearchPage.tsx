import { Search } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookCard } from "../components/BookCard";
import { apiFetch, type BookListResponse } from "../lib/api";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const cleanQuery = query.trim();
  const { data, isLoading } = useQuery({
    queryKey: ["books", "search", cleanQuery],
    queryFn: () => {
      const params = new URLSearchParams({
        q: cleanQuery,
        limit: "120",
        sort: "title",
        order: "asc"
      });
      return apiFetch<BookListResponse>(`/books?${params.toString()}`);
    },
    enabled: cleanQuery.length > 0
  });
  const books = data?.items ?? [];

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Recherche</p>
          <h1>Search</h1>
        </div>
      </header>
      <label className="search-field">
        <Search size={20} aria-hidden="true" />
        <input
          value={query}
          placeholder="Titre, auteur ou fichier"
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {cleanQuery && <p className="result-summary">{data?.total ?? 0} resultat(s)</p>}
      {isLoading && <div className="skeleton tall" />}
      {!isLoading && books.length > 0 && (
        <div className="book-grid search-results">
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
      {!isLoading && cleanQuery && books.length === 0 && (
        <p className="empty-results">Aucun resultat.</p>
      )}
    </main>
  );
}

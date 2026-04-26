import { Grid2X2, List, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch, type BookListResponse } from "../lib/api";
import { BookCard } from "../components/BookCard";
import { EmptyLibrary } from "../components/EmptyLibrary";

const filters = ["All", "Unread", "In Progress", "Finished", "Downloaded", "Favorites"];

export function LibraryPage() {
  const [view, setView] = useState<"grid" | "list">("grid");
  const [filter, setFilter] = useState("All");
  const { data, isLoading } = useQuery({
    queryKey: ["books", "library"],
    queryFn: () => apiFetch<BookListResponse>("/books?limit=48")
  });
  const books = data?.items ?? [];

  if (!isLoading && books.length === 0) {
    return <EmptyLibrary />;
  }

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Bibliotheque</p>
          <h1>Library</h1>
        </div>
        <div className="icon-group">
          <button aria-label="Grille" className={view === "grid" ? "icon-button active" : "icon-button"} onClick={() => setView("grid")}>
            <Grid2X2 size={19} aria-hidden="true" />
          </button>
          <button aria-label="Liste" className={view === "list" ? "icon-button active" : "icon-button"} onClick={() => setView("list")}>
            <List size={19} aria-hidden="true" />
          </button>
          <button aria-label="Tri" className="icon-button">
            <SlidersHorizontal size={19} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="filter-rail" aria-label="Filtres bibliotheque">
        {filters.map((item) => (
          <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>
            {item}
          </button>
        ))}
      </div>

      <div className={view === "grid" ? "book-grid" : "book-list"}>
        {books.map((book) => (
          <BookCard key={book.id} book={book} dense={view === "list"} />
        ))}
      </div>
    </main>
  );
}

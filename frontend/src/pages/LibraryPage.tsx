import { Grid2X2, List, Search, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch, type BookListResponse } from "../lib/api";
import { BookCard } from "../components/BookCard";
import { EmptyLibrary } from "../components/EmptyLibrary";
import { applyLocalOfflineAvailability, listOfflineBookIds } from "../lib/offline";

type LibraryFilter = {
  label: string;
  status?: string;
  favorite?: boolean;
};

const allFilter: LibraryFilter = { label: "Tous" };
const filters: LibraryFilter[] = [
  allFilter,
  { label: "Non lus", status: "unread" },
  { label: "En cours", status: "in_progress" },
  { label: "Termines", status: "finished" },
  { label: "Favoris", favorite: true }
];

export function LibraryPage() {
  const [view, setView] = useState<"grid" | "list">("grid");
  const [filter, setFilter] = useState<LibraryFilter>(allFilter);
  const [search, setSearch] = useState("");
  const [offlineBookIds, setOfflineBookIds] = useState<Set<string>>(new Set());
  const cleanSearch = search.trim();
  const { data, isLoading } = useQuery({
    queryKey: ["books", "library", cleanSearch, filter.label],
    queryFn: () => {
      const params = new URLSearchParams({
        limit: "120",
        sort: "added_at",
        order: "desc"
      });
      if (cleanSearch) {
        params.set("q", cleanSearch);
      }
      if (filter.status) {
        params.set("status", filter.status);
      }
      if (filter.favorite) {
        params.set("favorite", "true");
      }
      return apiFetch<BookListResponse>(`/books?${params.toString()}`);
    }
  });
  const books = data?.items ?? [];
  const booksWithOffline = useMemo(
    () => applyLocalOfflineAvailability(books, offlineBookIds),
    [books, offlineBookIds]
  );
  const hasActiveSearch = cleanSearch.length > 0 || filter.label !== allFilter.label;

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

  if (!isLoading && booksWithOffline.length === 0 && !hasActiveSearch) {
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

      <label className="search-field library-search">
        <Search size={20} aria-hidden="true" />
        <input
          value={search}
          placeholder="Titre, auteur ou fichier"
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>

      <div className="filter-rail" aria-label="Filtres bibliotheque">
        {filters.map((item) => (
          <button key={item.label} className={filter.label === item.label ? "active" : ""} onClick={() => setFilter(item)}>
            {item.label}
          </button>
        ))}
      </div>

      <p className="result-summary">{data?.total ?? 0} livre(s)</p>

      {booksWithOffline.length > 0 ? (
        <div className={view === "grid" ? "book-grid" : "book-list"}>
          {booksWithOffline.map((book) => (
            <BookCard key={book.id} book={book} dense={view === "list"} />
          ))}
        </div>
      ) : (
        <p className="empty-results">Aucun resultat.</p>
      )}
    </main>
  );
}

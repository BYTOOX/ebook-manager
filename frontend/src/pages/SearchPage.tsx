import { Bookmark, Grid2X2, List, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookCard } from "../components/BookCard";
import { apiFetch, type BookListResponse, type TagListResponse } from "../lib/api";
import { applyLocalOfflineAvailability, listOfflineBookIds } from "../lib/offline";

type SearchFilter = {
  label: string;
  status?: string;
  favorite?: boolean;
};

const allFilter: SearchFilter = { label: "Tous" };
const filters: SearchFilter[] = [
  allFilter,
  { label: "Non lus", status: "unread" },
  { label: "En cours", status: "in_progress" },
  { label: "Termines", status: "finished" },
  { label: "Favoris", favorite: true }
];

export function SearchPage() {
  const [view, setView] = useState<"grid" | "list">("grid");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SearchFilter>(allFilter);
  const [tagFilter, setTagFilter] = useState("");
  const [offlineOnly, setOfflineOnly] = useState(false);
  const [offlineBookIds, setOfflineBookIds] = useState<Set<string>>(new Set());
  const cleanQuery = query.trim();
  const hasActiveSearch =
    cleanQuery.length > 0 ||
    filter.label !== allFilter.label ||
    Boolean(tagFilter) ||
    offlineOnly;

  const { data, isLoading } = useQuery({
    queryKey: ["books", "search", cleanQuery, filter.label, tagFilter, offlineOnly],
    queryFn: () => {
      const params = new URLSearchParams({
        limit: "120",
        sort: "title",
        order: "asc"
      });
      if (cleanQuery) {
        params.set("q", cleanQuery);
      }
      if (filter.status) {
        params.set("status", filter.status);
      }
      if (filter.favorite) {
        params.set("favorite", "true");
      }
      if (tagFilter) {
        params.set("tag", tagFilter);
      }
      return apiFetch<BookListResponse>(`/books?${params.toString()}`);
    },
    enabled: hasActiveSearch
  });

  const tags = useQuery({
    queryKey: ["organization", "tags"],
    queryFn: () => apiFetch<TagListResponse>("/organization/tags")
  });

  const books = data?.items ?? [];
  const booksWithOffline = useMemo(
    () => {
      const marked = applyLocalOfflineAvailability(books, offlineBookIds);
      return offlineOnly ? marked.filter((book) => book.is_offline_available) : marked;
    },
    [books, offlineBookIds]
  );

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

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Recherche</p>
          <h1>Search</h1>
        </div>
        <div className="icon-group">
          <button aria-label="Grille" className={view === "grid" ? "icon-button active" : "icon-button"} onClick={() => setView("grid")}>
            <Grid2X2 size={19} aria-hidden="true" />
          </button>
          <button aria-label="Liste" className={view === "list" ? "icon-button active" : "icon-button"} onClick={() => setView("list")}>
            <List size={19} aria-hidden="true" />
          </button>
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

      <div className="filter-rail search-filter-rail" aria-label="Filtres recherche">
        {filters.map((item) => (
          <button key={item.label} className={filter.label === item.label ? "active" : ""} onClick={() => setFilter(item)}>
            {item.favorite && <Star size={15} aria-hidden="true" />}
            {item.label}
          </button>
        ))}
        <button className={offlineOnly ? "active" : ""} onClick={() => setOfflineOnly((value) => !value)}>
          <Bookmark size={15} aria-hidden="true" />
          Offline
        </button>
      </div>

      {(tags.data?.items.length ?? 0) > 0 && (
        <div className="filter-rail tag-filter-rail" aria-label="Filtres tags">
          <button className={!tagFilter ? "active" : ""} onClick={() => setTagFilter("")}>
            Tous tags
          </button>
          {tags.data?.items.map((tag) => (
            <button key={tag.id} className={tagFilter === tag.name ? "active" : ""} onClick={() => setTagFilter(tag.name)}>
              {tag.name}
            </button>
          ))}
        </div>
      )}

      {hasActiveSearch && <p className="result-summary">{booksWithOffline.length} resultat(s)</p>}
      {isLoading && <div className="skeleton tall" />}
      {!isLoading && booksWithOffline.length > 0 && (
        <div className={view === "grid" ? "book-grid search-results" : "book-list search-results"}>
          {booksWithOffline.map((book) => (
            <BookCard key={book.id} book={book} dense={view === "list"} />
          ))}
        </div>
      )}
      {!isLoading && hasActiveSearch && booksWithOffline.length === 0 && (
        <p className="empty-results">Aucun resultat.</p>
      )}
      {!hasActiveSearch && (
        <section className="search-empty">
          <Search size={28} aria-hidden="true" />
          <h2>Recherche ta bibliotheque</h2>
        </section>
      )}
    </main>
  );
}

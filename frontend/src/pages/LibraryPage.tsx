import { ArrowDownAZ, ArrowUpAZ, Calendar, Clock, Grid2X2, List, Search, SlidersHorizontal, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch, type BookListResponse, type TagListResponse } from "../lib/api";
import { BookCard } from "../components/BookCard";
import { EmptyLibrary } from "../components/EmptyLibrary";
import { applyLocalOfflineAvailability, listOfflineBookIds } from "../lib/offline";

type LibraryFilter = {
  label: string;
  status?: string;
  favorite?: boolean;
};

type LibrarySort = "added_at" | "title" | "last_opened_at" | "rating";
type SortOrder = "asc" | "desc";

const allFilter: LibraryFilter = { label: "Tous" };
const filters: LibraryFilter[] = [
  allFilter,
  { label: "Non lus", status: "unread" },
  { label: "En cours", status: "in_progress" },
  { label: "Termines", status: "finished" },
  { label: "Favoris", favorite: true }
];

const sortOptions: { key: LibrarySort; label: string }[] = [
  { key: "added_at", label: "Ajout" },
  { key: "title", label: "Titre" },
  { key: "last_opened_at", label: "Lecture" },
  { key: "rating", label: "Note" }
];

export function LibraryPage() {
  const [view, setView] = useState<"grid" | "list">("grid");
  const [filter, setFilter] = useState<LibraryFilter>(allFilter);
  const [tagFilter, setTagFilter] = useState<string>("");
  const [sort, setSort] = useState<LibrarySort>("added_at");
  const [order, setOrder] = useState<SortOrder>("desc");
  const [showSort, setShowSort] = useState(false);
  const [search, setSearch] = useState("");
  const [offlineBookIds, setOfflineBookIds] = useState<Set<string>>(new Set());
  const cleanSearch = search.trim();
  const { data, isLoading } = useQuery({
    queryKey: ["books", "library", cleanSearch, filter.label, tagFilter, sort, order],
    queryFn: () => {
      const params = new URLSearchParams({
        limit: "120",
        sort,
        order
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
      if (tagFilter) {
        params.set("tag", tagFilter);
      }
      return apiFetch<BookListResponse>(`/books?${params.toString()}`);
    }
  });
  const tags = useQuery({
    queryKey: ["organization", "tags"],
    queryFn: () => apiFetch<TagListResponse>("/organization/tags")
  });
  const books = data?.items ?? [];
  const booksWithOffline = useMemo(
    () => applyLocalOfflineAvailability(books, offlineBookIds),
    [books, offlineBookIds]
  );
  const hasActiveSearch = cleanSearch.length > 0 || filter.label !== allFilter.label || Boolean(tagFilter);
  const activeSort = sortOptions.find((option) => option.key === sort) ?? { key: "added_at", label: "Ajout" };

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
          <button
            aria-label="Tri"
            className={showSort ? "icon-button active" : "icon-button"}
            onClick={() => setShowSort((current) => !current)}
          >
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

      {showSort && (
        <div className="sort-panel">
          <div className="sort-panel-heading">
            <SlidersHorizontal size={17} aria-hidden="true" />
            <strong>{activeSort.label}</strong>
            <span>{order === "asc" ? "Ascendant" : "Descendant"}</span>
          </div>
          <div className="filter-rail sort-rail" aria-label="Tri bibliotheque">
            {sortOptions.map((option) => (
              <button
                key={option.key}
                className={sort === option.key ? "active" : ""}
                onClick={() => setSort(option.key)}
              >
                {option.key === "added_at" && <Calendar size={15} aria-hidden="true" />}
                {option.key === "title" && <ArrowDownAZ size={15} aria-hidden="true" />}
                {option.key === "last_opened_at" && <Clock size={15} aria-hidden="true" />}
                {option.key === "rating" && <Star size={15} aria-hidden="true" />}
                {option.label}
              </button>
            ))}
          </div>
          <div className="segmented compact sort-order" aria-label="Sens du tri">
            <button className={order === "desc" ? "active" : ""} onClick={() => setOrder("desc")}>
              <ArrowDownAZ size={16} aria-hidden="true" />
              Desc
            </button>
            <button className={order === "asc" ? "active" : ""} onClick={() => setOrder("asc")}>
              <ArrowUpAZ size={16} aria-hidden="true" />
              Asc
            </button>
          </div>
        </div>
      )}

      <div className="filter-rail" aria-label="Filtres bibliotheque">
        {filters.map((item) => (
          <button key={item.label} className={filter.label === item.label ? "active" : ""} onClick={() => setFilter(item)}>
            {item.label}
          </button>
        ))}
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

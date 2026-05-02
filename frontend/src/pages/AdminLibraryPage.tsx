import {
  ArchiveRestore,
  Check,
  Layers3,
  Loader2,
  RotateCcw,
  Search,
  Sparkles,
  Star,
  Tags,
  Trash2
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  apiFetch,
  bulkBookAction,
  listTrashBooks,
  type BookListItem,
  type BookListResponse,
  type BookTrashItem,
  type CollectionListResponse,
  type TagListResponse
} from "../lib/api";

type AdminTab = "library" | "trash";
type AdminSort = "added_at" | "title" | "last_opened_at" | "rating";

const statusOptions = [
  { value: "unread", label: "Non lu" },
  { value: "in_progress", label: "En cours" },
  { value: "finished", label: "Termine" },
  { value: "abandoned", label: "Abandonne" }
];

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("fr-CH", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function firstAuthor(book: BookListItem) {
  return book.authors[0] ?? "Auteur inconnu";
}

function isTrashBook(book: BookListItem | BookTrashItem): book is BookTrashItem {
  return "deleted_at" in book;
}

function formatBulkFailure(detail: string) {
  if (detail === "Book is not purgeable yet") {
    return "Purge disponible uniquement apres l'echeance indiquee.";
  }
  if (detail === "Book is not in trash") {
    return "Le livre n'est plus dans la corbeille.";
  }
  if (detail === "Book already in trash") {
    return "Le livre est deja dans la corbeille.";
  }
  return detail;
}

export function AdminLibraryPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<AdminTab>("library");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState<AdminSort>("added_at");
  const [bulkStatus, setBulkStatus] = useState("finished");
  const [favorite, setFavorite] = useState("true");
  const [rating, setRating] = useState("");
  const [tagText, setTagText] = useState("");
  const [collectionId, setCollectionId] = useState("");
  const [seriesName, setSeriesName] = useState("");
  const [seriesIndex, setSeriesIndex] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cleanSearch = search.trim();
  const books = useQuery({
    queryKey: ["books", "admin", cleanSearch, status, sort],
    queryFn: () => {
      const params = new URLSearchParams({ limit: "200", sort, order: sort === "title" ? "asc" : "desc" });
      if (cleanSearch) {
        params.set("q", cleanSearch);
      }
      if (status) {
        params.set("status", status);
      }
      return apiFetch<BookListResponse>(`/books?${params.toString()}`);
    },
    enabled: tab === "library"
  });

  const trash = useQuery({
    queryKey: ["books", "trash"],
    queryFn: () => listTrashBooks(500),
    enabled: tab === "trash"
  });

  const tags = useQuery({
    queryKey: ["organization", "tags"],
    queryFn: () => apiFetch<TagListResponse>("/organization/tags")
  });

  const collections = useQuery({
    queryKey: ["organization", "collections"],
    queryFn: () => apiFetch<CollectionListResponse>("/organization/collections")
  });

  const rows = useMemo(() => {
    const items = tab === "trash" ? trash.data?.items ?? [] : books.data?.items ?? [];
    if (tab === "library" || !cleanSearch) {
      return items;
    }
    const query = cleanSearch.toLowerCase();
    return items.filter((book) =>
      [book.title, firstAuthor(book), book.status].some((value) => value.toLowerCase().includes(query))
    );
  }, [books.data?.items, cleanSearch, tab, trash.data?.items]);

  const selectedIds = [...selected].filter((id) => rows.some((book) => book.id === id));
  const allVisibleSelected = rows.length > 0 && rows.every((book) => selected.has(book.id));
  const selectedTrashBooks = selectedIds
    .map((id) => rows.find((item) => item.id === id))
    .filter((book): book is BookTrashItem => Boolean(book && isTrashBook(book)));
  const selectedTrashIds = selectedTrashBooks.map((book) => book.id);
  const selectedPurgeableTrashIds = selectedTrashBooks.filter((book) => book.can_purge).map((book) => book.id);
  const hasLockedTrashSelection = selectedTrashBooks.some((book) => !book.can_purge);

  const actionMutation = useMutation({
    mutationFn: ({ action, payload, ids }: { action: string; payload?: Record<string, unknown>; ids?: string[] }) =>
      bulkBookAction(ids ?? selectedIds, action, payload ?? {}),
    onSuccess: async (result) => {
      const failedMessages = result.failed.map((failure) => formatBulkFailure(failure.detail));
      setError(
        failedMessages.length
          ? `${failedMessages.length} erreur(s): ${failedMessages.slice(0, 3).join(" ")}`
          : null
      );
      setNotice(`${result.updated} livre(s) traite(s).`);
      setSelected(new Set(result.failed.map((failure) => failure.book_id)));
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["books"] }),
        queryClient.invalidateQueries({ queryKey: ["organization", "tags"] }),
        queryClient.invalidateQueries({ queryKey: ["organization", "collections"] })
      ]);
    },
    onError: (caught) => {
      setNotice(null);
      setError(caught instanceof Error ? caught.message : "Action impossible");
    }
  });

  function toggleBook(bookId: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(bookId)) {
        next.delete(bookId);
      } else {
        next.add(bookId);
      }
      return next;
    });
  }

  function toggleAllVisible() {
    setSelected((current) => {
      const next = new Set(current);
      if (allVisibleSelected) {
        rows.forEach((book) => next.delete(book.id));
      } else {
        rows.forEach((book) => next.add(book.id));
      }
      return next;
    });
  }

  function tagPayload() {
    return {
      tags: tagText
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean)
    };
  }

  const busy = actionMutation.isPending;
  const canAct = selectedIds.length > 0 && !busy;

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Gestion bibliotheque</h1>
        </div>
      </header>

      <section className="admin-toolbar">
        <div className="segmented compact">
          <button className={tab === "library" ? "active" : ""} onClick={() => setTab("library")}>
            <Layers3 size={16} aria-hidden="true" />
            Bibliotheque
          </button>
          <button className={tab === "trash" ? "active" : ""} onClick={() => setTab("trash")}>
            <Trash2 size={16} aria-hidden="true" />
            Corbeille
          </button>
        </div>
        <label className="search-field compact-search">
          <Search size={18} aria-hidden="true" />
          <input value={search} placeholder="Titre, auteur ou statut" onChange={(event) => setSearch(event.target.value)} />
        </label>
        {tab === "library" && (
          <div className="admin-filter-row">
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">Tous statuts</option>
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select value={sort} onChange={(event) => setSort(event.target.value as AdminSort)}>
              <option value="added_at">Ajout</option>
              <option value="title">Titre</option>
              <option value="last_opened_at">Lecture</option>
              <option value="rating">Note</option>
            </select>
          </div>
        )}
      </section>

      <section className="settings-section">
        <div className="metadata-heading">
          <Check size={18} aria-hidden="true" />
          <h2>{selectedIds.length} selectionne(s)</h2>
        </div>
        {tab === "library" ? (
          <>
            <div className="admin-action-grid">
              <button className="secondary-action" disabled={!canAct} onClick={() => actionMutation.mutate({ action: "set_status", payload: { status: bulkStatus } })}>
                <Check size={18} aria-hidden="true" />
                Statut
              </button>
              <select value={bulkStatus} onChange={(event) => setBulkStatus(event.target.value)}>
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button className="secondary-action" disabled={!canAct} onClick={() => actionMutation.mutate({ action: "set_favorite", payload: { favorite: favorite === "true" } })}>
                <Star size={18} aria-hidden="true" />
                Favori
              </button>
              <select value={favorite} onChange={(event) => setFavorite(event.target.value)}>
                <option value="true">Oui</option>
                <option value="false">Non</option>
              </select>
              <button className="secondary-action" disabled={!canAct} onClick={() => actionMutation.mutate({ action: "set_rating", payload: { rating: rating || null } })}>
                <Star size={18} aria-hidden="true" />
                Note
              </button>
              <input value={rating} inputMode="numeric" placeholder="0-5 ou vide" onChange={(event) => setRating(event.target.value)} />
              <button className="secondary-action" disabled={!canAct || !tagPayload().tags.length} onClick={() => actionMutation.mutate({ action: "add_tags", payload: tagPayload() })}>
                <Tags size={18} aria-hidden="true" />
                Ajouter tags
              </button>
              <button className="secondary-action" disabled={!canAct || !tagPayload().tags.length} onClick={() => actionMutation.mutate({ action: "remove_tags", payload: tagPayload() })}>
                <Tags size={18} aria-hidden="true" />
                Retirer tags
              </button>
              <input value={tagText} placeholder="tag, tag" onChange={(event) => setTagText(event.target.value)} list="known-tags" />
              <datalist id="known-tags">
                {(tags.data?.items ?? []).map((tag) => (
                  <option key={tag.id} value={tag.name} />
                ))}
              </datalist>
              <button className="secondary-action" disabled={!canAct || !collectionId} onClick={() => actionMutation.mutate({ action: "add_to_collection", payload: { collection_id: collectionId } })}>
                <Layers3 size={18} aria-hidden="true" />
                Collection
              </button>
              <select value={collectionId} onChange={(event) => setCollectionId(event.target.value)}>
                <option value="">Choisir collection</option>
                {(collections.data?.items ?? []).map((collection) => (
                  <option key={collection.id} value={collection.id}>
                    {collection.name}
                  </option>
                ))}
              </select>
              <button className="secondary-action" disabled={!canAct || !seriesName.trim()} onClick={() => actionMutation.mutate({ action: "set_series", payload: { series_name: seriesName, series_index: seriesIndex || null } })}>
                <Layers3 size={18} aria-hidden="true" />
                Serie
              </button>
              <div className="admin-two-inputs">
                <input value={seriesName} placeholder="Serie" onChange={(event) => setSeriesName(event.target.value)} />
                <input value={seriesIndex} placeholder="Tome" inputMode="decimal" onChange={(event) => setSeriesIndex(event.target.value)} />
              </div>
              <button className="secondary-action" disabled={!canAct} onClick={() => actionMutation.mutate({ action: "metadata_auto" })}>
                <Sparkles size={18} aria-hidden="true" />
                Metadata
              </button>
              <button className="secondary-action danger" disabled={!canAct} onClick={() => actionMutation.mutate({ action: "trash" })}>
                <Trash2 size={18} aria-hidden="true" />
                Corbeille
              </button>
            </div>
          </>
        ) : (
          <div className="admin-action-grid">
            <button className="secondary-action" disabled={selectedTrashIds.length === 0 || busy} onClick={() => actionMutation.mutate({ action: "restore", ids: selectedTrashIds })}>
              <ArchiveRestore size={18} aria-hidden="true" />
              Restaurer
            </button>
            <button
              className="secondary-action danger"
              disabled={selectedPurgeableTrashIds.length === 0 || hasLockedTrashSelection || busy}
              title={hasLockedTrashSelection ? "Purge disponible apres l'echeance indiquee" : undefined}
              onClick={() => actionMutation.mutate({ action: "purge", ids: selectedPurgeableTrashIds })}
            >
              <Trash2 size={18} aria-hidden="true" />
              Purger
            </button>
            <button
              className="secondary-action danger"
              disabled={busy || !(trash.data?.items.some((book) => book.can_purge) ?? false)}
              onClick={() =>
                actionMutation.mutate({
                  action: "purge",
                  ids: (trash.data?.items ?? []).filter((book) => book.can_purge).map((book) => book.id)
                })
              }
            >
              <RotateCcw size={18} aria-hidden="true" />
              Purger eligibles
            </button>
          </div>
        )}
        {busy && (
          <p className="notice pending">
            <Loader2 className="spin" size={16} aria-hidden="true" />
            Action en cours...
          </p>
        )}
        {tab === "trash" && hasLockedTrashSelection && !busy && (
          <p className="notice pending">Purge disponible apres l'echeance indiquee.</p>
        )}
        {notice && <p className="notice success">{notice}</p>}
        {error && <p className="notice error">{error}</p>}
      </section>

      <section className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>
                <input type="checkbox" checked={allVisibleSelected} onChange={toggleAllVisible} />
              </th>
              <th>Titre</th>
              <th>Auteur</th>
              <th>Statut</th>
              <th>Note</th>
              <th>{tab === "trash" ? "Purge" : "Ajout"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((book) => (
              <tr key={book.id} className={selected.has(book.id) ? "selected" : ""}>
                <td>
                  <input type="checkbox" checked={selected.has(book.id)} onChange={() => toggleBook(book.id)} />
                </td>
                <td>
                  <strong>{book.title}</strong>
                  <span>{book.id}</span>
                </td>
                <td>{firstAuthor(book)}</td>
                <td>{book.status}</td>
                <td>{book.rating ?? "-"}</td>
                <td>
                  {isTrashBook(book)
                    ? book.can_purge
                      ? "eligible"
                      : formatDate(book.trash_expires_at)
                    : formatDate(book.added_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(tab === "library" ? books.isLoading : trash.isLoading) && <div className="skeleton tall" />}
        {rows.length === 0 && !(tab === "library" ? books.isLoading : trash.isLoading) && (
          <p className="empty-results">Aucun livre.</p>
        )}
      </section>
    </main>
  );
}

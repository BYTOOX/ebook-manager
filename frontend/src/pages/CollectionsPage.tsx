import { BookMarked, Check, FolderPlus, Hash, Layers3, Library, Loader2, Save, Search } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import {
  apiFetch,
  createCollection,
  createTag,
  setCollectionBooks,
  type BookListResponse,
  type CollectionDetail,
  type CollectionListResponse,
  type SeriesDetail,
  type SeriesListResponse,
  type TagListResponse
} from "../lib/api";
import { BookCard } from "../components/BookCard";

type OrganizationTab = "collections" | "series" | "tags";

const tabs: { key: OrganizationTab; label: string }[] = [
  { key: "collections", label: "Collections" },
  { key: "series", label: "Series" },
  { key: "tags", label: "Tags" }
];

export function CollectionsPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<OrganizationTab>("collections");
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
  const [collectionName, setCollectionName] = useState("");
  const [collectionDescription, setCollectionDescription] = useState("");
  const [tagName, setTagName] = useState("");
  const [tagColor, setTagColor] = useState("#f5c542");
  const [pickerSearch, setPickerSearch] = useState("");
  const [draftBookIds, setDraftBookIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const collections = useQuery({
    queryKey: ["organization", "collections"],
    queryFn: () => apiFetch<CollectionListResponse>("/organization/collections")
  });

  const series = useQuery({
    queryKey: ["organization", "series"],
    queryFn: () => apiFetch<SeriesListResponse>("/organization/series")
  });

  const tags = useQuery({
    queryKey: ["organization", "tags"],
    queryFn: () => apiFetch<TagListResponse>("/organization/tags")
  });

  const books = useQuery({
    queryKey: ["books", "organization-picker"],
    queryFn: () => apiFetch<BookListResponse>("/books?limit=200&sort=title&order=asc")
  });

  const collectionDetail = useQuery({
    queryKey: ["organization", "collection", selectedCollectionId],
    queryFn: () => apiFetch<CollectionDetail>(`/organization/collections/${selectedCollectionId}`),
    enabled: Boolean(selectedCollectionId)
  });

  const seriesDetail = useQuery({
    queryKey: ["organization", "series", selectedSeriesId],
    queryFn: () => apiFetch<SeriesDetail>(`/organization/series/${selectedSeriesId}`),
    enabled: Boolean(selectedSeriesId)
  });

  useEffect(() => {
    const firstCollection = collections.data?.items[0];
    if (!selectedCollectionId && firstCollection) {
      setSelectedCollectionId(firstCollection.id);
    }
  }, [collections.data?.items, selectedCollectionId]);

  useEffect(() => {
    const firstSeries = series.data?.items[0];
    if (!selectedSeriesId && firstSeries) {
      setSelectedSeriesId(firstSeries.id);
    }
  }, [series.data?.items, selectedSeriesId]);

  useEffect(() => {
    if (collectionDetail.data) {
      setDraftBookIds(collectionDetail.data.books.map((book) => book.id));
    }
  }, [collectionDetail.data]);

  const filteredBooks = useMemo(() => {
    const query = pickerSearch.trim().toLowerCase();
    const items = books.data?.items ?? [];
    if (!query) {
      return items;
    }
    return items.filter((book) =>
      [book.title, ...book.authors].some((value) => value.toLowerCase().includes(query))
    );
  }, [books.data?.items, pickerSearch]);

  async function handleCreateCollection() {
    const name = collectionName.trim();
    if (!name || busy) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const created = await createCollection({
        name,
        description: collectionDescription.trim() || null
      });
      setCollectionName("");
      setCollectionDescription("");
      setSelectedCollectionId(created.id);
      setMessage("Collection creee");
      await queryClient.invalidateQueries({ queryKey: ["organization", "collections"] });
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveCollectionBooks() {
    if (!selectedCollectionId || busy) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await setCollectionBooks(selectedCollectionId, draftBookIds);
      setMessage("Collection mise a jour");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["organization", "collections"] }),
        queryClient.invalidateQueries({ queryKey: ["organization", "collection", selectedCollectionId] })
      ]);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateTag() {
    const name = tagName.trim();
    if (!name || busy) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await createTag({ name, color: tagColor });
      setTagName("");
      setMessage("Tag cree");
      await queryClient.invalidateQueries({ queryKey: ["organization", "tags"] });
    } finally {
      setBusy(false);
    }
  }

  function toggleDraftBook(bookId: string) {
    setDraftBookIds((current) =>
      current.includes(bookId) ? current.filter((id) => id !== bookId) : [...current, bookId]
    );
  }

  const collectionCount = collections.data?.total ?? 0;
  const seriesCount = series.data?.total ?? 0;
  const tagCount = tags.data?.total ?? 0;

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Organisation</p>
          <h1>Collections</h1>
        </div>
      </header>

      <div className="stat-grid organization-stats">
        <div>
          <span>Collections</span>
          <strong>{collectionCount}</strong>
        </div>
        <div>
          <span>Series</span>
          <strong>{seriesCount}</strong>
        </div>
        <div>
          <span>Tags</span>
          <strong>{tagCount}</strong>
        </div>
      </div>

      <div className="segmented compact">
        {tabs.map((item) => (
          <button key={item.key} className={tab === item.key ? "active" : ""} onClick={() => setTab(item.key)}>
            {item.key === "collections" && <Layers3 size={16} aria-hidden="true" />}
            {item.key === "series" && <BookMarked size={16} aria-hidden="true" />}
            {item.key === "tags" && <Hash size={16} aria-hidden="true" />}
            {item.label}
          </button>
        ))}
      </div>

      {message && (
        <p className="notice success">
          <Check size={16} aria-hidden="true" />
          {message}
        </p>
      )}

      {tab === "collections" && (
        <section className="organization-grid">
          <div className="settings-section">
            <div className="metadata-heading">
              <FolderPlus size={18} aria-hidden="true" />
              <h2>Nouvelle collection</h2>
            </div>
            <label>
              <span>Nom</span>
              <input value={collectionName} onChange={(event) => setCollectionName(event.target.value)} />
            </label>
            <label>
              <span>Description</span>
              <input value={collectionDescription} onChange={(event) => setCollectionDescription(event.target.value)} />
            </label>
            <button className="primary-action wide" onClick={() => void handleCreateCollection()} disabled={busy || !collectionName.trim()}>
              {busy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <FolderPlus size={18} aria-hidden="true" />}
              Creer
            </button>
          </div>

          <div className="settings-section">
            <div className="metadata-heading">
              <Layers3 size={18} aria-hidden="true" />
              <h2>Collections</h2>
            </div>
            <div className="organization-list">
              {(collections.data?.items ?? []).map((collection) => (
                <button
                  key={collection.id}
                  className={selectedCollectionId === collection.id ? "organization-item active" : "organization-item"}
                  onClick={() => setSelectedCollectionId(collection.id)}
                >
                  <span>{collection.name}</span>
                  <strong>{collection.book_count}</strong>
                </button>
              ))}
              {!collections.isLoading && collectionCount === 0 && <p className="muted-line">Aucune collection.</p>}
            </div>
          </div>

          <div className="settings-section organization-wide">
            <div className="metadata-heading">
              <Library size={18} aria-hidden="true" />
              <h2>{collectionDetail.data?.name ?? "Livres"}</h2>
            </div>
            <label className="search-field compact-search">
              <Search size={18} aria-hidden="true" />
              <input value={pickerSearch} placeholder="Titre ou auteur" onChange={(event) => setPickerSearch(event.target.value)} />
            </label>
            <div className="book-picker">
              {filteredBooks.map((book) => (
                <label key={book.id} className={draftBookIds.includes(book.id) ? "pick-row active" : "pick-row"}>
                  <input type="checkbox" checked={draftBookIds.includes(book.id)} onChange={() => toggleDraftBook(book.id)} />
                  <span>{book.title}</span>
                  <small>{book.authors[0] ?? "Auteur inconnu"}</small>
                </label>
              ))}
            </div>
            <button className="primary-action wide" onClick={() => void handleSaveCollectionBooks()} disabled={busy || !selectedCollectionId}>
              {busy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Save size={18} aria-hidden="true" />}
              Enregistrer
            </button>
          </div>
        </section>
      )}

      {tab === "series" && (
        <section className="organization-grid">
          <div className="settings-section">
            <div className="metadata-heading">
              <BookMarked size={18} aria-hidden="true" />
              <h2>Series</h2>
            </div>
            <div className="organization-list">
              {(series.data?.items ?? []).map((item) => (
                <button
                  key={item.id}
                  className={selectedSeriesId === item.id ? "organization-item active" : "organization-item"}
                  onClick={() => setSelectedSeriesId(item.id)}
                >
                  <span>{item.name}</span>
                  <strong>{item.book_count}</strong>
                </button>
              ))}
              {!series.isLoading && seriesCount === 0 && <p className="muted-line">Aucune serie.</p>}
            </div>
          </div>
          <div className="settings-section organization-wide">
            <div className="metadata-heading">
              <Library size={18} aria-hidden="true" />
              <h2>{seriesDetail.data?.name ?? "Livres"}</h2>
            </div>
            {seriesDetail.data?.books.length ? (
              <div className="book-grid">
                {seriesDetail.data.books.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            ) : (
              <p className="muted-line">Aucun livre.</p>
            )}
          </div>
        </section>
      )}

      {tab === "tags" && (
        <section className="organization-grid">
          <div className="settings-section">
            <div className="metadata-heading">
              <Hash size={18} aria-hidden="true" />
              <h2>Nouveau tag</h2>
            </div>
            <label>
              <span>Nom</span>
              <input value={tagName} onChange={(event) => setTagName(event.target.value)} />
            </label>
            <label>
              <span>Couleur</span>
              <input value={tagColor} onChange={(event) => setTagColor(event.target.value)} />
            </label>
            <button className="primary-action wide" onClick={() => void handleCreateTag()} disabled={busy || !tagName.trim()}>
              {busy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Hash size={18} aria-hidden="true" />}
              Creer
            </button>
          </div>
          <div className="settings-section organization-wide">
            <div className="metadata-heading">
              <Hash size={18} aria-hidden="true" />
              <h2>Tags</h2>
            </div>
            <div className="tag-grid">
              {(tags.data?.items ?? []).map((tag) => (
                <div key={tag.id} className="tag-item">
                  <span className="tag-swatch" style={{ background: tag.color ?? "#f5c542" }} />
                  <strong>{tag.name}</strong>
                  <span>{tag.book_count}</span>
                </div>
              ))}
              {!tags.isLoading && tagCount === 0 && <p className="muted-line">Aucun tag.</p>}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

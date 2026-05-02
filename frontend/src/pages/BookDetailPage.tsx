import {
  BookOpen,
  Check,
  Download,
  FileText,
  Loader2,
  Pencil,
  Play,
  Save,
  Search,
  Sparkles,
  Star,
  Trash2,
  Users,
  X
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  apiFetch,
  applyBookMetadata,
  searchBookMetadata,
  updateBook,
  type BookDetail,
  type MetadataApplyField,
  type MetadataCandidate
} from "../lib/api";
import { AuthenticatedImage } from "../components/AuthenticatedImage";
import { BookCard } from "../components/BookCard";
import {
  downloadBookForOffline,
  getOfflineBookDetail,
  getOfflineCoverObjectUrl,
  isBookOffline,
  refreshOfflineBookMetadata,
  removeOfflineBook
} from "../lib/offline";

function formatBytes(size: number | null) {
  if (!size) {
    return "Inconnu";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const suffix = units[unit] ?? "B";
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${suffix}`;
}

const providerLabels: Record<MetadataCandidate["provider"], string> = {
  openlibrary: "Open Library",
  googlebooks: "Google Books"
};

const metadataApplyFields: { key: MetadataApplyField; label: string }[] = [
  { key: "title", label: "Titre" },
  { key: "subtitle", label: "Sous-titre" },
  { key: "authors", label: "Auteurs" },
  { key: "description", label: "Description" },
  { key: "language", label: "Langue" },
  { key: "isbn", label: "ISBN" },
  { key: "publisher", label: "Editeur" },
  { key: "published_date", label: "Date" },
  { key: "cover", label: "Couverture" }
];

function candidateValue(candidate: MetadataCandidate, field: MetadataApplyField) {
  if (field === "authors") {
    return candidate.authors.join(", ");
  }
  if (field === "cover") {
    return candidate.cover_url ? "Image provider" : "";
  }
  const value = candidate[field];
  return typeof value === "string" ? value : "";
}

function currentValue(book: BookDetail, field: MetadataApplyField) {
  if (field === "authors") {
    return book.authors.join(", ");
  }
  if (field === "cover") {
    return book.cover_url ? "Couverture locale" : "Vide";
  }
  if (field === "description") {
    return book.description ?? "";
  }
  const value = book[field];
  return typeof value === "string" ? value : "";
}

function fieldsAvailable(candidate: MetadataCandidate) {
  return metadataApplyFields
    .filter((field) => candidateValue(candidate, field.key))
    .map((field) => field.key);
}

function versionedCoverUrl(url: string | null, revision: number) {
  if (!url || revision === 0) {
    return url;
  }
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}ui=${revision}`;
}

function metadataSearchSuggestion(book: BookDetail) {
  const seriesName = book.series?.name;
  const titleHasSeries = Boolean(
    seriesName && book.title.toLocaleLowerCase().includes(seriesName.toLocaleLowerCase())
  );
  const seriesParts = titleHasSeries
    ? []
    : [seriesName, book.series?.index ? `Tome ${book.series.index}` : null];
  return [...seriesParts, book.title, book.authors[0]].filter(Boolean).join(" ");
}

export function BookDetailPage() {
  const { bookId } = useParams();
  const queryClient = useQueryClient();
  const [offlineReady, setOfflineReady] = useState(false);
  const [offlineBusy, setOfflineBusy] = useState(false);
  const [offlineError, setOfflineError] = useState<string | null>(null);
  const [coverObjectUrl, setCoverObjectUrl] = useState<string | null>(null);
  const [coverRevision, setCoverRevision] = useState(0);
  const [editing, setEditing] = useState(false);
  const [metadataBusy, setMetadataBusy] = useState(false);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [metadataForm, setMetadataForm] = useState({
    title: "",
    authors: "",
    seriesName: "",
    seriesIndex: "",
    tags: "",
    status: "unread",
    rating: "",
    favorite: false
  });
  const [providerPanelOpen, setProviderPanelOpen] = useState(false);
  const [providerBusy, setProviderBusy] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [providerMessage, setProviderMessage] = useState<string | null>(null);
  const [providerQuery, setProviderQuery] = useState("");
  const [metadataCandidates, setMetadataCandidates] = useState<MetadataCandidate[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [selectedFields, setSelectedFields] = useState<MetadataApplyField[]>([]);
  const { data } = useQuery({
    queryKey: ["book", bookId],
    queryFn: async () => {
      if (!bookId) {
        throw new Error("Livre introuvable");
      }
      try {
        return await apiFetch<BookDetail>(`/books/${bookId}`);
      } catch (caught) {
        const offlineBook = await getOfflineBookDetail(bookId);
        if (offlineBook) {
          return offlineBook;
        }
        throw caught;
      }
    },
    enabled: Boolean(bookId)
  });

  useEffect(() => {
    let alive = true;
    if (!bookId) {
      return;
    }
    isBookOffline(bookId).then((available) => {
      if (alive) {
        setOfflineReady(available);
      }
    });
    return () => {
      alive = false;
    };
  }, [bookId]);

  useEffect(() => {
    let alive = true;
    let objectUrl: string | null = null;
    setCoverObjectUrl(null);
    if (!bookId) {
      return;
    }
    getOfflineCoverObjectUrl(bookId).then((url) => {
      objectUrl = url;
      if (alive) {
        setCoverObjectUrl(url);
      } else if (url) {
        URL.revokeObjectURL(url);
      }
    });
    return () => {
      alive = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [bookId, offlineReady, coverRevision]);

  useEffect(() => {
    if (!data) {
      return;
    }
    setMetadataForm({
      title: data.title,
      authors: data.authors.join(", "),
      seriesName: data.series?.name ?? "",
      seriesIndex: data.series?.index?.toString() ?? "",
      tags: data.tags.join(", "),
      status: data.status,
      rating: data.rating?.toString() ?? "",
      favorite: data.favorite
    });
    setProviderQuery((current) => current || metadataSearchSuggestion(data));
  }, [data]);

  async function handleOfflineDownload() {
    if (!data || offlineBusy || offlineReady) {
      return;
    }
    setOfflineBusy(true);
    setOfflineError(null);
    try {
      await downloadBookForOffline(data);
      setOfflineReady(true);
    } catch (caught) {
      setOfflineError(caught instanceof Error ? caught.message : "Telechargement offline impossible");
    } finally {
      setOfflineBusy(false);
    }
  }

  async function handleOfflineRemove() {
    if (!data || offlineBusy || !offlineReady) {
      return;
    }
    setOfflineBusy(true);
    setOfflineError(null);
    try {
      await removeOfflineBook(data.id);
      setOfflineReady(false);
      await queryClient.invalidateQueries({ queryKey: ["books"] });
    } catch (caught) {
      setOfflineError(caught instanceof Error ? caught.message : "Suppression offline impossible");
    } finally {
      setOfflineBusy(false);
    }
  }

  async function handleMetadataSave() {
    if (!data || metadataBusy) {
      return;
    }
    setMetadataBusy(true);
    setMetadataError(null);
    try {
      const updated = await updateBook(data.id, {
        title: metadataForm.title.trim(),
        authors: metadataForm.authors
          .split(",")
          .map((author) => author.trim())
          .filter(Boolean),
        series_name: metadataForm.seriesName.trim() || null,
        series_index: metadataForm.seriesIndex.trim() ? Number(metadataForm.seriesIndex) : null,
        tags: metadataForm.tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        status: metadataForm.status,
        rating: metadataForm.rating.trim() ? Number(metadataForm.rating) : null,
        favorite: metadataForm.favorite
      });
      queryClient.setQueryData(["book", bookId], updated);
      if (await refreshOfflineBookMetadata(updated)) {
        setCoverRevision((current) => current + 1);
      }
      await queryClient.invalidateQueries({ queryKey: ["books"] });
      setEditing(false);
    } catch (caught) {
      setMetadataError(caught instanceof Error ? caught.message : "Edition impossible");
    } finally {
      setMetadataBusy(false);
    }
  }

  async function handleProviderSearch() {
    if (!data || providerBusy) {
      return;
    }
    setProviderBusy(true);
    setProviderError(null);
    setProviderMessage(null);
    try {
      const response = await searchBookMetadata(data.id, {
        providers: ["googlebooks"],
        query: providerQuery.trim() || null,
        isbn: data.isbn
      });
      setMetadataCandidates(response.items);
      const first = response.items[0] ?? null;
      setSelectedCandidateId(first?.id ?? null);
      setSelectedFields(first ? fieldsAvailable(first) : []);
      setProviderMessage(response.total ? `${response.total} proposition(s)` : "Aucune proposition");
    } catch (caught) {
      setProviderError(caught instanceof Error ? caught.message : "Recherche metadata impossible");
    } finally {
      setProviderBusy(false);
    }
  }

  function handleSelectCandidate(candidate: MetadataCandidate) {
    setSelectedCandidateId(candidate.id);
    setSelectedFields(fieldsAvailable(candidate));
  }

  function toggleSelectedField(field: MetadataApplyField) {
    setSelectedFields((current) =>
      current.includes(field) ? current.filter((item) => item !== field) : [...current, field]
    );
  }

  async function applyProviderFields(fields: MetadataApplyField[], candidateId = selectedCandidateId) {
    if (!data || !candidateId || fields.length === 0 || providerBusy) {
      return;
    }
    setProviderBusy(true);
    setProviderError(null);
    setProviderMessage(null);
    try {
      const updated = await applyBookMetadata(data.id, candidateId, fields);
      queryClient.setQueryData(["book", bookId], updated);
      if (fields.includes("cover")) {
        setCoverObjectUrl(null);
        setCoverRevision((current) => current + 1);
      }
      if (await refreshOfflineBookMetadata(updated)) {
        setCoverRevision((current) => current + 1);
      }
      await queryClient.invalidateQueries({ queryKey: ["books"] });
      setProviderMessage(fields.length === 1 && fields[0] === "cover" ? "Couverture remplacee" : "Metadonnees appliquees");
    } catch (caught) {
      setProviderError(caught instanceof Error ? caught.message : "Application metadata impossible");
    } finally {
      setProviderBusy(false);
    }
  }

  async function handleProviderApply() {
    await applyProviderFields(selectedFields);
  }

  async function handleProviderCoverApply() {
    await applyProviderFields(["cover"]);
  }

  async function handleCandidateCoverApply(candidate: MetadataCandidate) {
    handleSelectCandidate(candidate);
    await applyProviderFields(["cover"], candidate.id);
  }

  if (!data) {
    return <main className="page"><div className="skeleton tall" /></main>;
  }

  const coverUrl = coverObjectUrl ?? versionedCoverUrl(data.cover_url, coverRevision);
  const selectedCandidate = metadataCandidates.find((candidate) => candidate.id === selectedCandidateId) ?? null;

  return (
    <main className="book-detail">
      <div className="detail-cover">
        <AuthenticatedImage src={coverUrl} alt="" fallback={<span>{data.title[0]}</span>} />
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
          <button className="secondary-action" onClick={() => void handleOfflineDownload()} disabled={offlineBusy || offlineReady}>
            {offlineBusy ? (
              <Loader2 className="spin" size={18} aria-hidden="true" />
            ) : offlineReady ? (
              <Check size={18} aria-hidden="true" />
            ) : (
              <Download size={18} aria-hidden="true" />
            )}
            {offlineReady ? "Disponible offline" : offlineBusy ? "Telechargement" : "Offline"}
          </button>
          {offlineReady && (
            <button className="secondary-action" onClick={() => void handleOfflineRemove()} disabled={offlineBusy}>
              {offlineBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Trash2 size={18} aria-hidden="true" />}
              Retirer offline
            </button>
          )}
          <button className="secondary-action" onClick={() => setEditing((value) => !value)}>
            {editing ? <X size={18} aria-hidden="true" /> : <Pencil size={18} aria-hidden="true" />}
            {editing ? "Annuler" : "Modifier"}
          </button>
          <button className="secondary-action" onClick={() => setProviderPanelOpen((value) => !value)}>
            {providerPanelOpen ? <X size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
            {providerPanelOpen ? "Fermer" : "Enrichir"}
          </button>
        </div>
        {offlineError && <p className="form-error">{offlineError}</p>}
        {editing && (
          <section className="metadata-edit-panel" aria-label="Edition metadonnees">
            <label>
              <span>Titre</span>
              <input
                value={metadataForm.title}
                onChange={(event) => setMetadataForm((current) => ({ ...current, title: event.target.value }))}
              />
            </label>
            <label>
              <span>Auteurs</span>
              <input
                value={metadataForm.authors}
                onChange={(event) => setMetadataForm((current) => ({ ...current, authors: event.target.value }))}
              />
            </label>
            <div className="metadata-edit-grid">
              <label>
                <span>Serie</span>
                <input
                  value={metadataForm.seriesName}
                  onChange={(event) => setMetadataForm((current) => ({ ...current, seriesName: event.target.value }))}
                />
              </label>
              <label>
                <span>Tome</span>
                <input
                  inputMode="decimal"
                  value={metadataForm.seriesIndex}
                  onChange={(event) => setMetadataForm((current) => ({ ...current, seriesIndex: event.target.value }))}
                />
              </label>
            </div>
            <label>
              <span>Tags</span>
              <input
                value={metadataForm.tags}
                onChange={(event) => setMetadataForm((current) => ({ ...current, tags: event.target.value }))}
              />
            </label>
            <div className="metadata-edit-grid">
              <label>
                <span>Statut</span>
                <select
                  value={metadataForm.status}
                  onChange={(event) => setMetadataForm((current) => ({ ...current, status: event.target.value }))}
                >
                  <option value="unread">Non lu</option>
                  <option value="in_progress">En cours</option>
                  <option value="finished">Termine</option>
                  <option value="abandoned">Abandonne</option>
                </select>
              </label>
              <label>
                <span>Note</span>
                <input
                  inputMode="numeric"
                  value={metadataForm.rating}
                  onChange={(event) => setMetadataForm((current) => ({ ...current, rating: event.target.value }))}
                />
              </label>
            </div>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={metadataForm.favorite}
                onChange={(event) => setMetadataForm((current) => ({ ...current, favorite: event.target.checked }))}
              />
              <span>Favori</span>
            </label>
            {metadataError && <p className="form-error">{metadataError}</p>}
            <button className="primary-action wide" onClick={() => void handleMetadataSave()} disabled={metadataBusy}>
              {metadataBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Save size={18} aria-hidden="true" />}
              Enregistrer
            </button>
          </section>
        )}
        {providerPanelOpen && (
          <section className="metadata-band metadata-provider-panel" aria-label="Recherche metadonnees">
            <div className="metadata-heading">
              <Sparkles size={18} aria-hidden="true" />
              <h2>Metadonnees externes</h2>
            </div>
            <div className="metadata-provider-search">
              <label className="search-field compact-search">
                <Search size={18} aria-hidden="true" />
                <input
                  value={providerQuery}
                  placeholder="Titre, auteur ou ISBN"
                  onChange={(event) => setProviderQuery(event.target.value)}
                />
              </label>
              <button className="primary-action" onClick={() => void handleProviderSearch()} disabled={providerBusy}>
                {providerBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Search size={18} aria-hidden="true" />}
                Rechercher
              </button>
            </div>
            {providerError && <p className="notice error">{providerError}</p>}
            {providerMessage && <p className="notice success">{providerMessage}</p>}
            {metadataCandidates.length > 0 && (
              <div className="metadata-candidate-list">
                {metadataCandidates.map((candidate) => (
                  <div
                    key={candidate.id}
                    className={selectedCandidateId === candidate.id ? "metadata-candidate active" : "metadata-candidate"}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleSelectCandidate(candidate)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        handleSelectCandidate(candidate);
                      }
                    }}
                  >
                    <span className="metadata-candidate-cover">
                      {candidate.cover_url ? <img src={candidate.cover_url} alt="" loading="lazy" /> : <Sparkles size={24} aria-hidden="true" />}
                    </span>
                    <span className="metadata-candidate-body">
                      <strong>{candidate.title}</strong>
                      <small>{candidate.authors.join(", ") || "Auteur inconnu"}</small>
                      <span>
                        {providerLabels[candidate.provider]} - {Math.round(candidate.score * 100)}%
                      </span>
                      {candidate.publisher && <small>{candidate.publisher}</small>}
                      {candidate.cover_url && (
                        <button
                          className="secondary-action metadata-cover-action"
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleCandidateCoverApply(candidate);
                          }}
                          disabled={providerBusy}
                        >
                          {providerBusy ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <Download size={16} aria-hidden="true" />}
                          Prendre
                        </button>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {selectedCandidate && (
              <div className="metadata-apply-panel">
                <div className="metadata-heading">
                  <Check size={18} aria-hidden="true" />
                  <h2>Appliquer</h2>
                </div>
                {selectedCandidate.cover_url && (
                  <div className="cover-compare">
                    <div>
                      <span>Actuelle</span>
                      <div className="cover-preview">
                        <AuthenticatedImage src={coverUrl} alt="" fallback={<strong>{data.title[0]}</strong>} />
                      </div>
                    </div>
                    <div>
                      <span>Provider</span>
                      <div className="cover-preview">
                        <img src={selectedCandidate.cover_url} alt="" loading="lazy" />
                      </div>
                    </div>
                    <button
                      className="secondary-action wide"
                      onClick={() => void handleProviderCoverApply()}
                      disabled={providerBusy}
                    >
                      {providerBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Download size={18} aria-hidden="true" />}
                      Prendre cette couverture
                    </button>
                  </div>
                )}
                <div className="metadata-field-list">
                  {metadataApplyFields.map((field) => {
                    const next = candidateValue(selectedCandidate, field.key);
                    return (
                      <label key={field.key} className={next ? "metadata-field-row" : "metadata-field-row disabled"}>
                        <input
                          type="checkbox"
                          disabled={!next}
                          checked={Boolean(next) && selectedFields.includes(field.key)}
                          onChange={() => toggleSelectedField(field.key)}
                        />
                        <span>
                          <strong>{field.label}</strong>
                          <small>{currentValue(data, field.key) || "Vide"}</small>
                          <small>{next || "Non fourni"}</small>
                        </span>
                      </label>
                    );
                  })}
                </div>
                <button
                  className="primary-action wide"
                  onClick={() => void handleProviderApply()}
                  disabled={providerBusy || selectedFields.length === 0}
                >
                  {providerBusy ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Save size={18} aria-hidden="true" />}
                  Appliquer la selection
                </button>
              </div>
            )}
          </section>
        )}
        {data.description && <p className="description">{data.description}</p>}
        <section className="metadata-band" aria-label="Metadonnees du livre">
          <div className="metadata-heading">
            <FileText size={18} aria-hidden="true" />
            <h2>Infos livre</h2>
          </div>
          <dl className="metadata-grid">
            <div>
              <dt>Auteur</dt>
              <dd>{data.authors.join(", ") || "Auteur inconnu"}</dd>
            </div>
            {data.publisher && (
              <div>
                <dt>Editeur</dt>
                <dd>{data.publisher}</dd>
              </div>
            )}
            {data.published_date && (
              <div>
                <dt>Publication</dt>
                <dd>{data.published_date}</dd>
              </div>
            )}
            {data.language && (
              <div>
                <dt>Langue</dt>
                <dd>{data.language.toUpperCase()}</dd>
              </div>
            )}
            {data.isbn && (
              <div>
                <dt>ISBN</dt>
                <dd>{data.isbn}</dd>
              </div>
            )}
            <div>
              <dt>Fichier</dt>
              <dd>{data.original_filename ?? "EPUB local"} - {formatBytes(data.file_size)}</dd>
            </div>
          </dl>
        </section>
        {data.series && (
          <section className="metadata-band" aria-label="Serie">
            <div className="metadata-heading">
              <BookOpen size={18} aria-hidden="true" />
              <h2>{data.series.name}</h2>
            </div>
            <p className="muted-line">
              {data.series.index ? `Tome ${data.series.index}` : "Serie detectee depuis le dossier d'import."}
            </p>
            {data.related_books.length > 0 && (
              <div className="related-rail">
                {data.related_books.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            )}
          </section>
        )}
        {(data.characters.length > 0 || data.subjects.length > 0 || data.contributors.length > 0 || data.tags.length > 0) && (
          <section className="metadata-band" aria-label="Sujets et personnages">
            <div className="metadata-heading">
              <Users size={18} aria-hidden="true" />
              <h2>Univers</h2>
            </div>
            {data.characters.length > 0 && (
              <>
                <h3>Personnages</h3>
                <div className="chip-list">
                  {data.characters.map((character) => <span key={character}>{character}</span>)}
                </div>
              </>
            )}
            {data.subjects.length > 0 && (
              <>
                <h3>Sujets</h3>
                <div className="chip-list">
                  {data.subjects.map((subject) => <span key={subject}>{subject}</span>)}
                </div>
              </>
            )}
            {data.tags.length > 0 && (
              <>
                <h3>Tags</h3>
                <div className="chip-list">
                  {data.tags.map((tag) => <span key={tag}>{tag}</span>)}
                </div>
              </>
            )}
            {data.contributors.length > 0 && (
              <>
                <h3>Contributeurs</h3>
                <div className="chip-list">
                  {data.contributors.map((contributor) => <span key={contributor}>{contributor}</span>)}
                </div>
              </>
            )}
          </section>
        )}
      </section>
    </main>
  );
}

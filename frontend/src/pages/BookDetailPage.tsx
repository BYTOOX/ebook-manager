import { BookOpen, Check, Download, FileText, Loader2, Pencil, Play, Save, Star, Trash2, Users, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch, updateBook, type BookDetail } from "../lib/api";
import { BookCard } from "../components/BookCard";
import {
  downloadBookForOffline,
  getOfflineBookDetail,
  getOfflineCoverObjectUrl,
  isBookOffline,
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

export function BookDetailPage() {
  const { bookId } = useParams();
  const queryClient = useQueryClient();
  const [offlineReady, setOfflineReady] = useState(false);
  const [offlineBusy, setOfflineBusy] = useState(false);
  const [offlineError, setOfflineError] = useState<string | null>(null);
  const [coverObjectUrl, setCoverObjectUrl] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [metadataBusy, setMetadataBusy] = useState(false);
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [metadataForm, setMetadataForm] = useState({
    title: "",
    authors: "",
    seriesName: "",
    seriesIndex: "",
    status: "unread",
    rating: "",
    favorite: false
  });
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
  }, [bookId, offlineReady]);

  useEffect(() => {
    if (!data) {
      return;
    }
    setMetadataForm({
      title: data.title,
      authors: data.authors.join(", "),
      seriesName: data.series?.name ?? "",
      seriesIndex: data.series?.index?.toString() ?? "",
      status: data.status,
      rating: data.rating?.toString() ?? "",
      favorite: data.favorite
    });
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
        status: metadataForm.status,
        rating: metadataForm.rating.trim() ? Number(metadataForm.rating) : null,
        favorite: metadataForm.favorite
      });
      queryClient.setQueryData(["book", bookId], updated);
      await queryClient.invalidateQueries({ queryKey: ["books"] });
      setEditing(false);
    } catch (caught) {
      setMetadataError(caught instanceof Error ? caught.message : "Edition impossible");
    } finally {
      setMetadataBusy(false);
    }
  }

  if (!data) {
    return <main className="page"><div className="skeleton tall" /></main>;
  }

  const coverUrl = coverObjectUrl ?? data.cover_url;

  return (
    <main className="book-detail">
      <div className="detail-cover">
        {coverUrl ? <img src={coverUrl} alt="" /> : <span>{data.title[0]}</span>}
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
        {(data.characters.length > 0 || data.subjects.length > 0 || data.contributors.length > 0) && (
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

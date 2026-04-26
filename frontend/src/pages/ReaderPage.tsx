import { ArrowLeft, Bookmark, Settings } from "lucide-react";
import { Link, useParams } from "react-router-dom";

export function ReaderPage() {
  const { bookId } = useParams();

  return (
    <main className="reader-page">
      <header className="reader-topbar">
        <Link to={bookId ? `/books/${bookId}` : "/library"} aria-label="Retour" className="icon-button">
          <ArrowLeft size={20} aria-hidden="true" />
        </Link>
        <span>Aurelia Reader</span>
        <div className="icon-group">
          <button aria-label="Bookmark" className="icon-button">
            <Bookmark size={19} aria-hidden="true" />
          </button>
          <button aria-label="Reglages" className="icon-button">
            <Settings size={19} aria-hidden="true" />
          </button>
        </div>
      </header>
      <article className="reader-surface">
        <p className="eyebrow">Mode noir/or</p>
        <h1>Lecteur EPUB</h1>
        <p>
          Le conteneur reader est pret pour epub.js, la reprise CFI, le mode pagine et le mode scroll.
        </p>
      </article>
      <div className="reader-progress">
        <span style={{ width: "12%" }} />
      </div>
    </main>
  );
}

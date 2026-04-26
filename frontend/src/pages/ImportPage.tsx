import { FolderSearch, Upload } from "lucide-react";

export function ImportPage() {
  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Gestion discrete</p>
          <h1>Import EPUB</h1>
        </div>
      </header>
      <section className="import-panel">
        <Upload size={28} aria-hidden="true" />
        <h2>Upload EPUB</h2>
        <p>Le pipeline upload arrive en Phase 2.</p>
        <button className="primary-action" disabled>
          <Upload size={18} aria-hidden="true" />
          Choisir un EPUB
        </button>
      </section>
      <section className="quiet-panel">
        <FolderSearch size={22} aria-hidden="true" />
        <h2>Scan incoming</h2>
        <p>Le dossier `/data/library/incoming` est reserve pour le scan serveur.</p>
      </section>
    </main>
  );
}

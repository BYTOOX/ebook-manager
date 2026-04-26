import { Upload } from "lucide-react";
import { Link } from "react-router-dom";

export function EmptyLibrary() {
  return (
    <section className="empty-state">
      <div className="brand-mark">A</div>
      <h2>Choisis ton prochain livre</h2>
      <p>La bibliotheque est prete pour le premier EPUB.</p>
      <Link className="primary-action" to="/import">
        <Upload size={18} aria-hidden="true" />
        Importer
      </Link>
    </section>
  );
}

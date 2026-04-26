import { BookMarked, Layers3 } from "lucide-react";

export function CollectionsPage() {
  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Organisation</p>
          <h1>Collections</h1>
        </div>
      </header>
      <div className="two-panel">
        <section className="quiet-panel">
          <Layers3 size={22} aria-hidden="true" />
          <h2>Collections</h2>
          <p>Les groupes personnels arriveront apres le socle bibliotheque.</p>
        </section>
        <section className="quiet-panel">
          <BookMarked size={22} aria-hidden="true" />
          <h2>Series</h2>
          <p>La structure serie est deja prevue cote base de donnees.</p>
        </section>
      </div>
    </main>
  );
}

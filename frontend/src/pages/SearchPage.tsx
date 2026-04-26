import { Search } from "lucide-react";

export function SearchPage() {
  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Recherche</p>
          <h1>Search</h1>
        </div>
      </header>
      <label className="search-field">
        <Search size={20} aria-hidden="true" />
        <input placeholder="Titre, auteur, tag, serie" />
      </label>
    </main>
  );
}

async function loadBookDetail() {
  const root = document.getElementById("book-detail");
  const bookId = root.dataset.bookId;
  const response = await fetch(`/books/${bookId}`);
  if (!response.ok) {
    root.innerHTML = "<p>Livre introuvable.</p>";
    return;
  }

  const { book, reading_path: readingPath } = await response.json();
  const author = book.authors?.map((a) => a.name).join(", ") || "Auteur inconnu";
  const tags = (book.tags || []).join(", ") || "Aucun tag";

  root.innerHTML = `
    <h1>${book.title}</h1>
    <p><strong>Auteur(s):</strong> ${author}</p>
    <p><strong>Format:</strong> ${book.format.toUpperCase()}</p>
    <p><strong>Tags:</strong> ${tags}</p>
    <p><strong>Fichier:</strong> ${book.file_path}</p>
    <p><a href="${readingPath}">Ouvrir la lecture</a></p>
    <p><a href="/ui/library">← Retour à la bibliothèque</a></p>
  `;
}

loadBookDetail();

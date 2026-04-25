async function loadLibrary() {
  const container = document.getElementById("book-grid");
  const response = await fetch("/books?sort_by=title&order=asc");
  const books = await response.json();

  if (!books.length) {
    container.innerHTML = "<p>Aucun livre importé.</p>";
    return;
  }

  container.innerHTML = books
    .map((book) => {
      const cover = book.cover_path ? `/static/${book.cover_path}` : "";
      const author = book.authors?.[0]?.name || "Auteur inconnu";
      return `
      <a class="book-card" href="/ui/books/${book.id}">
        ${cover ? `<img class="book-cover" src="${cover}" alt="Couverture ${book.title}" />` : `<div class="book-cover"></div>`}
        <p class="book-title">${book.title}</p>
        <p class="book-author">${author}</p>
      </a>
      `;
    })
    .join("");
}

loadLibrary();

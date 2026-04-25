async function loadReader() {
  const root = document.getElementById("epub-reader");
  const frame = document.getElementById("reader-frame");
  const bookId = root.dataset.bookId;

  const response = await fetch(`/books/${bookId}`);
  if (!response.ok) {
    root.innerHTML += "<p>Impossible de charger ce livre.</p>";
    return;
  }

  const { book } = await response.json();
  if (book.format !== "epub") {
    root.innerHTML += "<p>La vue EPUB est réservée aux fichiers EPUB.</p>";
    return;
  }

  frame.src = `/static/${book.file_path}`;
}

loadReader();

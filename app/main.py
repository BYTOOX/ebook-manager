from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4
import zipfile

from bs4 import BeautifulSoup
from ebooklib import ITEM_COVER, ITEM_DOCUMENT, epub
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pypdf import PdfReader

from app.models import Author, Book
from app.store import store

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
COVERS_DIR = DATA_DIR / "covers"
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Ebook Manager")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class BookDetailResponse(BaseModel):
    book: Book
    reading_path: str


def _extract_epub_metadata(file_path: Path, book_id: str) -> tuple[str, list[str], str | None]:
    epub_book = epub.read_epub(str(file_path))
    title = (epub_book.get_metadata("DC", "title") or [[file_path.stem]])[0][0]
    creators = [meta[0] for meta in epub_book.get_metadata("DC", "creator")]

    cover_path: str | None = None
    cover_items = list(epub_book.get_items_of_type(ITEM_COVER))
    if cover_items:
        cover_item = cover_items[0]
        cover_ext = Path(cover_item.file_name).suffix or ".jpg"
        local_cover = COVERS_DIR / f"{book_id}{cover_ext}"
        local_cover.write_bytes(cover_item.get_content())
        cover_path = str(local_cover.relative_to(BASE_DIR))
    return title, creators, cover_path


def _extract_pdf_metadata(file_path: Path) -> tuple[str, list[str], str | None]:
    reader = PdfReader(str(file_path))
    meta = reader.metadata or {}
    title = meta.get("/Title") or file_path.stem
    author = meta.get("/Author")
    authors = [author] if author else []
    return title, authors, None


def _extract_epub_spine_path(file_path: Path) -> str | None:
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            opf_files = [name for name in zf.namelist() if name.endswith(".opf")]
            if not opf_files:
                return None
            opf_name = opf_files[0]
            opf_xml = zf.read(opf_name)
            soup = BeautifulSoup(opf_xml, "xml")
            first_itemref = soup.find("itemref")
            if not first_itemref:
                return None
            idref = first_itemref.get("idref")
            item = soup.find("item", {"id": idref})
            if not item:
                return None
            href = item.get("href")
            if not href:
                return None
            base = str(Path(opf_name).parent)
            return str(Path(base) / href)
    except zipfile.BadZipFile:
        return None


@app.post("/books/import", response_model=Book)
async def import_book(file: UploadFile = File(...)) -> Book:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".epub", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only EPUB and PDF are supported")

    book_id = str(uuid4())
    destination = BOOKS_DIR / f"{book_id}{suffix}"
    destination.write_bytes(await file.read())

    if suffix == ".epub":
        title, author_names, cover_path = _extract_epub_metadata(destination, book_id)
        fmt = "epub"
    else:
        title, author_names, cover_path = _extract_pdf_metadata(destination)
        fmt = "pdf"

    authors = [Author(name=name) for name in author_names if name]
    book = Book(
        id=book_id,
        title=title,
        authors=authors,
        format=fmt,
        file_path=str(destination.relative_to(BASE_DIR)),
        cover_path=cover_path,
        updated_at=datetime.utcnow(),
    )
    return store.upsert_book(book)


@app.get("/books", response_model=list[Book])
def list_books(
    title: str | None = Query(default=None),
    author: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated tags"),
    sort_by: str = Query(default="created_at", pattern="^(title|author|created_at)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> list[Book]:
    books = store.list_books()

    if title:
        books = [b for b in books if title.lower() in b.title.lower()]
    if author:
        books = [
            b
            for b in books
            if any(author.lower() in book_author.name.lower() for book_author in b.authors)
        ]
    if tags:
        requested_tags = {tag.strip().lower() for tag in tags.split(",") if tag.strip()}
        books = [b for b in books if requested_tags.issubset({tag.lower() for tag in b.tags})]

    def sort_key(book: Book):
        if sort_by == "title":
            return book.title.lower()
        if sort_by == "author":
            return (book.authors[0].name.lower() if book.authors else "")
        return book.created_at

    reverse = order == "desc"
    return sorted(books, key=sort_key, reverse=reverse)


@app.get("/books/{book_id}", response_model=BookDetailResponse)
def get_book(book_id: str) -> BookDetailResponse:
    book = store.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    reading_path = f"/ui/reader/{book.id}" if book.format == "epub" else f"/static/{book.file_path}"
    return BookDetailResponse(book=book, reading_path=reading_path)


@app.get("/ui/library", response_class=HTMLResponse)
def library_page(request: Request):
    return templates.TemplateResponse("library.html", {"request": request})


@app.get("/ui/books/{book_id}", response_class=HTMLResponse)
def detail_page(request: Request, book_id: str):
    return templates.TemplateResponse("detail.html", {"request": request, "book_id": book_id})


@app.get("/ui/reader/{book_id}", response_class=HTMLResponse)
def reader_page(request: Request, book_id: str):
    return templates.TemplateResponse("reader.html", {"request": request, "book_id": book_id})

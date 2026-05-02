export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
export const ACCESS_TOKEN_STORAGE_KEY = "aurelia:access_token";
export const AUTH_UNAUTHORIZED_EVENT = "aurelia:auth:unauthorized";

export type ApiError = {
  detail?: unknown;
};

function formatApiError(error: ApiError, fallback: string): string {
  if (typeof error.detail === "string") {
    return error.detail;
  }

  if (Array.isArray(error.detail)) {
    return error.detail
      .map((item) => {
        if (item && typeof item === "object") {
          const detail = item as { loc?: unknown[]; msg?: unknown };
          const location = Array.isArray(detail.loc)
            ? detail.loc.filter((part) => part !== "body").join(".")
            : "";
          const message = typeof detail.msg === "string" ? detail.msg : JSON.stringify(item);
          return location ? `${location}: ${message}` : message;
        }
        return String(item);
      })
      .join(" ");
  }

  if (error.detail && typeof error.detail === "object") {
    return JSON.stringify(error.detail);
  }

  return fallback;
}

export function readAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function writeAccessToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    }
  } catch {
    // localStorage can be unavailable in private or constrained browser contexts.
  }
}

function withBearerAuth(headersInit?: HeadersInit, token = readAccessToken()): Headers {
  const headers = new Headers(headersInit);
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

function isApiUrl(url: string): boolean {
  if (url.startsWith("/api/")) {
    return true;
  }
  if (API_BASE_URL.startsWith("/") && url.startsWith(API_BASE_URL)) {
    return true;
  }
  if (!API_BASE_URL.startsWith("http")) {
    return false;
  }

  try {
    const origin = typeof window === "undefined" ? "http://localhost" : window.location.origin;
    const target = new URL(url, origin);
    const apiBase = new URL(API_BASE_URL);
    return target.origin === apiBase.origin && target.pathname.startsWith(apiBase.pathname);
  } catch {
    return false;
  }
}

export function authHeadersForUrl(url: string, headersInit?: HeadersInit): Headers {
  if (!isApiUrl(url)) {
    return new Headers(headersInit);
  }
  return withBearerAuth(headersInit);
}

function handleUnauthorized(response: Response, requestToken: string | null): void {
  if (response.status !== 401) {
    return;
  }
  if (!requestToken || readAccessToken() !== requestToken) {
    return;
  }
  writeAccessToken(null);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const requestToken = readAccessToken();
  const headers = withBearerAuth(init.headers, requestToken);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    handleUnauthorized(response, requestToken);
    let message = response.statusText;
    try {
      const error = (await response.json()) as ApiError;
      message = formatApiError(error, message);
    } catch {
      // Keep the HTTP status text when the API returns no JSON body.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const requestToken = readAccessToken();
  const headers = withBearerAuth(init.headers, requestToken);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    handleUnauthorized(response, requestToken);
    let message = response.statusText;
    try {
      const error = (await response.json()) as ApiError;
      message = formatApiError(error, message);
    } catch {
      // Keep the HTTP status text when the API returns no JSON body.
    }
    throw new Error(message);
  }

  return response.blob();
}

export type User = {
  id: string;
  username: string;
  display_name: string | null;
};

export type BookListItem = {
  id: string;
  title: string;
  authors: string[];
  cover_url: string | null;
  status: string;
  rating: number | null;
  favorite: boolean;
  progress_percent: number | null;
  is_offline_available: boolean;
  added_at: string;
  last_opened_at: string | null;
};

export type BookListResponse = {
  items: BookListItem[];
  total: number;
};

export type BookSeriesInfo = {
  name: string;
  index: number | null;
  source: string;
};

export type BookDetail = BookListItem & {
  subtitle: string | null;
  description: string | null;
  language: string | null;
  isbn: string | null;
  publisher: string | null;
  published_date: string | null;
  original_filename: string | null;
  file_size: number | null;
  metadata_source: string | null;
  metadata_provider_id: string | null;
  series: BookSeriesInfo | null;
  related_books: BookListItem[];
  subjects: string[];
  contributors: string[];
  characters: string[];
  tags: string[];
};

export type BookUpdate = {
  title?: string;
  authors?: string[];
  series_name?: string | null;
  series_index?: number | null;
  tags?: string[] | null;
  status?: string;
  rating?: number | null;
  favorite?: boolean;
};

export type ReadingProgress = {
  cfi: string | null;
  progress_percent: number | null;
  chapter_label: string | null;
  chapter_href: string | null;
  location_json: Record<string, unknown> | null;
  device_id: string | null;
  updated_at: string | null;
};

export type ReadingProgressResponse = {
  ok: boolean;
  resolved: "client_won" | "server_won" | string;
  progress: ReadingProgress;
};

export type ReadingSettings = {
  id: string;
  theme: string;
  reader_theme: string;
  font_family: string | null;
  font_size: number;
  line_height: number | string;
  margin_size: number;
  reading_mode: "paged" | "scroll" | string;
  updated_at: string;
};

export type ReadingSettingsUpdate = Partial<
  Pick<
    ReadingSettings,
    "theme" | "reader_theme" | "font_family" | "font_size" | "line_height" | "margin_size" | "reading_mode"
  >
>;

export type ImportJob = {
  id: string;
  source: "upload" | "scan" | string;
  status: "pending" | "running" | "success" | "warning" | "failed" | string;
  filename: string | null;
  file_path: string | null;
  error_message: string | null;
  result_book_id: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type ImportJobsResponse = {
  items: ImportJob[];
  total: number;
};

export type UploadBookResponse = {
  job_id: string;
  book_id: string | null;
  status: string;
  warning: string | null;
};

export type ScanResponse = {
  scanned: number;
  imported: number;
  warnings: number;
  failed: number;
  jobs: ImportJob[];
};

export type CollectionSummary = {
  id: string;
  name: string;
  description: string | null;
  book_count: number;
  cover_book_id: string | null;
  cover_url: string | null;
  created_at: string;
  updated_at: string;
};

export type CollectionDetail = CollectionSummary & {
  books: BookListItem[];
};

export type CollectionListResponse = {
  items: CollectionSummary[];
  total: number;
};

export type SeriesSummary = {
  id: string;
  name: string;
  description: string | null;
  book_count: number;
  cover_book_id: string | null;
  cover_url: string | null;
  created_at: string;
  updated_at: string;
};

export type SeriesDetail = SeriesSummary & {
  books: BookListItem[];
};

export type SeriesListResponse = {
  items: SeriesSummary[];
  total: number;
};

export type TagSummary = {
  id: string;
  name: string;
  color: string | null;
  book_count: number;
  created_at: string;
};

export type TagListResponse = {
  items: TagSummary[];
  total: number;
};

export type MetadataProvider = "openlibrary" | "googlebooks";

export type MetadataApplyField =
  | "association"
  | "title"
  | "subtitle"
  | "authors"
  | "description"
  | "language"
  | "isbn"
  | "publisher"
  | "published_date"
  | "cover";

export type MetadataCandidate = {
  id: string;
  provider: MetadataProvider;
  provider_item_id: string | null;
  score: number;
  title: string;
  subtitle: string | null;
  authors: string[];
  description: string | null;
  language: string | null;
  isbn: string | null;
  publisher: string | null;
  published_date: string | null;
  cover_url: string | null;
  raw: Record<string, unknown>;
};

export type MetadataSearchResponse = {
  items: MetadataCandidate[];
  total: number;
};

export type MetadataAutoApplyResponse = {
  status: "applied" | "needs_review" | "no_match";
  message: string;
  candidate: MetadataCandidate | null;
  items: MetadataCandidate[];
  total: number;
  applied_fields: MetadataApplyField[];
  book: BookDetail | null;
};

export type BookmarkItem = {
  id: string;
  book_id: string;
  cfi: string;
  progress_percent: number | null;
  chapter_label: string | null;
  excerpt: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type BookmarkListResponse = {
  items: BookmarkItem[];
  total: number;
};

export async function uploadBook(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<UploadBookResponse>("/books/upload", {
    method: "POST",
    body: formData
  });
}

export async function scanIncoming() {
  return apiFetch<ScanResponse>("/library/scan", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export async function updateBook(bookId: string, payload: BookUpdate) {
  return apiFetch<BookDetail>(`/books/${bookId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function searchBookMetadata(
  bookId: string,
  payload: { providers?: MetadataProvider[]; query?: string | null; isbn?: string | null }
) {
  return apiFetch<MetadataSearchResponse>(`/books/${bookId}/metadata/search`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function autoApplyBookMetadata(
  bookId: string,
  payload: {
    providers?: MetadataProvider[];
    query?: string | null;
    isbn?: string | null;
    fields?: MetadataApplyField[];
    min_score?: number;
    review_margin?: number;
  }
) {
  return apiFetch<MetadataAutoApplyResponse>(`/books/${bookId}/metadata/auto`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function applyBookMetadata(bookId: string, resultId: string, fields: MetadataApplyField[]) {
  return apiFetch<BookDetail>(`/books/${bookId}/metadata/apply`, {
    method: "POST",
    body: JSON.stringify({ result_id: resultId, fields })
  });
}

export async function listBookBookmarks(bookId: string) {
  return apiFetch<BookmarkListResponse>(`/books/${bookId}/bookmarks`);
}

export async function getReadingSettings() {
  return apiFetch<ReadingSettings>("/settings/reading");
}

export async function updateReadingSettings(payload: ReadingSettingsUpdate) {
  return apiFetch<ReadingSettings>("/settings/reading", {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function createCollection(payload: { name: string; description?: string | null }) {
  return apiFetch<CollectionDetail>("/organization/collections", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateCollection(collectionId: string, payload: { name: string; description?: string | null }) {
  return apiFetch<CollectionDetail>(`/organization/collections/${collectionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteCollection(collectionId: string) {
  return apiFetch<void>(`/organization/collections/${collectionId}`, {
    method: "DELETE"
  });
}

export async function setCollectionBooks(collectionId: string, bookIds: string[]) {
  return apiFetch<CollectionDetail>(`/organization/collections/${collectionId}/books`, {
    method: "PUT",
    body: JSON.stringify({ book_ids: bookIds })
  });
}

export async function createTag(payload: { name: string; color?: string | null }) {
  return apiFetch<TagSummary>("/organization/tags", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateTag(tagId: string, payload: { name: string; color?: string | null }) {
  return apiFetch<TagSummary>(`/organization/tags/${tagId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteTag(tagId: string) {
  return apiFetch<void>(`/organization/tags/${tagId}`, {
    method: "DELETE"
  });
}

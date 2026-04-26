export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

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

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
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
  series: BookSeriesInfo | null;
  related_books: BookListItem[];
  subjects: string[];
  contributors: string[];
  characters: string[];
};

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

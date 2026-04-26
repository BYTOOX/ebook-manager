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

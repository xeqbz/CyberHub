import { API_URL } from "@/src/shared/config/api";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
};

function prettifyFieldName(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1).replaceAll("_", " ");
}

function extractErrorMessage(errorData: unknown): string {
  if (!errorData) {
    return "Request failed";
  }

  if (typeof errorData === "string") {
    return errorData;
  }

  if (typeof errorData !== "object") {
    return "Request failed";
  }

  const record = errorData as Record<string, unknown>;
  const detail = record.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }

        const entry = item as Record<string, unknown>;
        const msg =
          typeof entry.msg === "string"
            ? entry.msg
            : typeof entry.message === "string"
              ? entry.message
              : null;

        if (!msg) {
          return null;
        }

        const rawLoc = Array.isArray(entry.loc)
          ? entry.loc.filter(
              (part) => typeof part === "string" || typeof part === "number",
            )
          : [];

        const cleanedLoc = rawLoc.filter(
          (part) =>
            part !== "body" &&
            part !== "query" &&
            part !== "path" &&
            part !== "header",
        );

        const field =
          cleanedLoc.length > 0
            ? prettifyFieldName(String(cleanedLoc[cleanedLoc.length - 1]))
            : null;

        return field ? `${field}: ${msg}` : msg;
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  if (typeof record.message === "string") {
    return record.message;
  }

  return "Request failed";
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error(
      "Cannot connect to backend. Check that the backend is running and CORS is configured.",
    );
  }

  if (!response.ok) {
    let message = "Request failed";

    try {
      const errorData = await response.json();
      message = extractErrorMessage(errorData);
    } catch {
      // ignore json parse errors
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
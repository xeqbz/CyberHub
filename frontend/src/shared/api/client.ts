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

function normalizeValidationMessage(msg: string): string {
  if (msg === "String should have at least 8 characters") {
    return "Must contain at least 8 characters";
  }

  if (msg === "Field required") {
    return "This field is required";
  }

  return msg;
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
        const rawMsg =
          typeof entry.msg === "string"
            ? entry.msg
            : typeof entry.message === "string"
              ? entry.message
              : null;

        if (!rawMsg) {
          return null;
        }

        const msg = normalizeValidationMessage(rawMsg);

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

        if (
          msg === "Must contain at least 8 characters" ||
          msg === "This field is required"
        ) {
          return field ? `${field}: ${msg}` : msg;
        }

        return field ? `${field}: ${msg}` : msg;
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  if (detail && typeof detail === "object") {
    const detailRecord = detail as Record<string, unknown>;

    if (typeof detailRecord.message === "string") {
      return detailRecord.message;
    }

    if (typeof detailRecord.error === "string") {
      return detailRecord.error;
    }
  }

  if (typeof record.message === "string") {
    return record.message;
  }

  if (typeof record.error === "string") {
    return record.error;
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
      "Cannot connect to backend. Check that the backend is running.",
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
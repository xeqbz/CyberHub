import { API_URL } from "@/src/shared/config/api";

type RequsetOptions = {
    method?: "GET" | "POST" | "PATCH" | "DELETE";
    body?: unknown;
    token?: string | null;
};

export async function apiRequest<T>(
    path: string,
    options: RequestOptions = {},
): Promise<T> {
    const { method = "GET", body, token} = options;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
        let message = "Request failed";

        try {
            const errorData = await response.json();
            message = errorData.detail || message;
        } catch {
            // ignore json parser error
        }

        throw new Error(message);
    }

    if (response.status === 204) {
        return {} as T;
    } 

    return response.json() as Promise<T>;
}
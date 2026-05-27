const DEFAULT_API_URL = "/api/v1";
const LOCAL_API_HOSTS = new Set([
  "localhost",
  "127.0.0.1",
  "0.0.0.0",
  "::1",
  "[::1]",
]);

function stripTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

function isLocalHost(hostname: string): boolean {
  return LOCAL_API_HOSTS.has(hostname);
}

function shouldUseSameOriginProxy(apiUrl: string): boolean {
  if (typeof window === "undefined" || isLocalHost(window.location.hostname)) {
    return false;
  }

  try {
    return isLocalHost(new URL(apiUrl).hostname);
  } catch {
    return false;
  }
}

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const normalizedConfiguredApiUrl = configuredApiUrl
  ? stripTrailingSlashes(configuredApiUrl)
  : "";

export const API_URL =
  normalizedConfiguredApiUrl &&
  !shouldUseSameOriginProxy(normalizedConfiguredApiUrl)
    ? normalizedConfiguredApiUrl
    : DEFAULT_API_URL;

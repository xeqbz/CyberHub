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
const configuredWsUrl = process.env.NEXT_PUBLIC_WS_URL?.trim();
const normalizedConfiguredWsUrl = configuredWsUrl
  ? stripTrailingSlashes(configuredWsUrl)
  : "";

export const API_URL =
  normalizedConfiguredApiUrl &&
  !shouldUseSameOriginProxy(normalizedConfiguredApiUrl)
    ? normalizedConfiguredApiUrl
    : DEFAULT_API_URL;

function formatHostname(hostname: string): string {
  return hostname.includes(":") && !hostname.startsWith("[")
    ? `[${hostname}]`
    : hostname;
}

function toWebSocketOrigin(value: string): string {
  if (value.startsWith("ws://") || value.startsWith("wss://")) {
    return value;
  }

  const url = new URL(value);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.origin;
}

export function getWebSocketUrl(path: string, token?: string | null): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  let origin: string;

  if (normalizedConfiguredWsUrl) {
    origin = toWebSocketOrigin(normalizedConfiguredWsUrl);
  } else if (API_URL.startsWith("http://") || API_URL.startsWith("https://")) {
    origin = toWebSocketOrigin(API_URL);
  } else if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const hostname = formatHostname(window.location.hostname);
    const port = isLocalHost(window.location.hostname)
      ? "8000"
      : window.location.port;
    origin = `${protocol}//${hostname}${port ? `:${port}` : ""}`;
  } else {
    origin = "ws://127.0.0.1:8000";
  }

  const url = new URL(normalizedPath, `${origin}/`);
  if (token) {
    url.searchParams.set("token", token);
  }
  return url.toString();
}

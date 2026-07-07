function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, "");
}

/** Normalize API base URL for local dev, Render host-only env vars, and full URLs. */
export function resolveApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL?.trim();
  if (!raw) {
    return "http://localhost:8000";
  }
  if (raw.startsWith("http://") || raw.startsWith("https://")) {
    return stripTrailingSlash(raw);
  }
  return stripTrailingSlash(`https://${raw}`);
}

/** Convert HTTP(S) API base URL to WS(S) base URL for signal streaming. */
export function resolveWebSocketBaseUrl(): string {
  return resolveApiBaseUrl().replace(/^http/, "ws");
}

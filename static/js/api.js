let csrfToken = "";

export async function initializeCsrf() {
  const response = await fetch("/api/csrf", { credentials: "same-origin" });
  const body = await response.json();
  csrfToken = body.csrf_token;
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes((options.method || "GET").toUpperCase())) headers.set("X-CSRFToken", csrfToken);
  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error?.message || "Richiesta non riuscita.");
  return body;
}

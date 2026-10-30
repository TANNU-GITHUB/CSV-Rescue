export class ApiError extends Error {
  code: string;
  hint: string;
  constructor(code: string, message: string, hint = "") {
    super(message);
    this.code = code;
    this.hint = hint;
  }
}

const BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(init?.headers || {}) },
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = data.error || {};
    throw new ApiError(err.code || "INTERNAL", err.message || res.statusText, err.hint || "");
  }
  return data as T;
}

export const apiBase = BASE;

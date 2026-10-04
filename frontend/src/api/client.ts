import { getAccessToken, expireSession } from "./session";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "")
  ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "omit",
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/")) expireSession(token);
    throw new ApiError(response.status, data);
  }

  return data as T;
}

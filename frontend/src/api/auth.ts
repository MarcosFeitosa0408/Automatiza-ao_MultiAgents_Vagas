import { apiRequest } from "./client";
export type AccountUser = { id: string; name: string; email: string };
export type AccountSession = { user: AccountUser; access_token: string; expires_in: number };
export function loginAccount(email: string, password: string): Promise<AccountSession> {
  return apiRequest("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}
export function registerAccount(name: string, email: string, password: string): Promise<AccountSession> {
  return apiRequest("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
}
export function logoutAccount() {
  return apiRequest("/auth/logout", { method: "POST" });
}

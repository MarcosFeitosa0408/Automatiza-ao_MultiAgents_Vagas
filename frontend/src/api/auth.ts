import { apiRequest } from "./client";
export type AccountUser = { id: string; name: string; email: string; role?: "user" | "admin"; state?: "pending" | "active" | "blocked" };
export type AccountSession = { user: AccountUser; access_token: string; expires_in: number };
export function loginAccount(email: string, password: string): Promise<AccountSession> {
  return apiRequest("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}
export type RegistrationResult = { pending_approval: true; message: string };
export function registerAccount(name: string, email: string, password: string): Promise<RegistrationResult> {
  return apiRequest("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
}
export function logoutAccount() {
  return apiRequest("/auth/logout", { method: "POST" });
}

export function requestPasswordRecovery(email: string): Promise<{ message: string }> {
  return apiRequest("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) });
}
export function resetAccountPassword(token: string, password: string): Promise<{ message: string }> {
  return apiRequest("/auth/reset-password", { method: "POST", body: JSON.stringify({ token, password }) });
}

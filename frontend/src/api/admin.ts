import { apiRequest } from "./client";
export type ManagedAccount = {
  id: string; name: string; email: string;
  role: "user" | "admin";
  state: "pending" | "active" | "blocked";
};
export type AccessAction = "authorize" | "block" | "reactivate";
export function listAccounts(): Promise<ManagedAccount[]> {
  return apiRequest("/admin/users");
}
export function changeAccess(id: string, action: AccessAction): Promise<ManagedAccount> {
  return apiRequest(`/admin/users/${encodeURIComponent(id)}/access`, { method: "PATCH", body: JSON.stringify({ action }) });
}
export function deleteAccount(id: string, email: string): Promise<{ deleted: boolean; user_id: string }> {
  return apiRequest(`/admin/users/${encodeURIComponent(id)}`, { method: "DELETE", body: JSON.stringify({ confirmation_email: email }) });
}

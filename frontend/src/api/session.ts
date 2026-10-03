// Sessão somente em memória: ao recarregar ou fechar a aba, faça login novamente.
let accessToken: string | null = null;
export function getAccessToken() { return accessToken; }
export function setAccessToken(token: string | null) { accessToken = token; }
export function expireSession(expectedToken: string | null) {
  if (expectedToken && accessToken === expectedToken) {
    accessToken = null;
    window.dispatchEvent(new Event("session-expired"));
  }
}

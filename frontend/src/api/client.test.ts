import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest, ApiError } from "./client";
import { getAccessToken, setAccessToken } from "./session";

afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null); });
describe("Sessão das chamadas à API", () => {
  it("envia o token da conta e encerra a sessão após um 401 privado", async () => {
    setAccessToken("token-a");
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Sessão expirada" }), { status: 401, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiRequest("/profile")).rejects.toBeInstanceOf(ApiError);
    const options = fetchMock.mock.calls[0][1] as RequestInit;
    expect(new Headers(options.headers).get("Authorization")).toBe("Bearer token-a");
    expect(getAccessToken()).toBeNull();
  });
  it("uma resposta atrasada da sessão antiga não encerra a nova conta", async () => {
    setAccessToken("token-a");
    let complete!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { complete = resolve; })));
    const pending = apiRequest("/profile");
    setAccessToken("token-b");
    complete(new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }));
    await expect(pending).rejects.toBeInstanceOf(ApiError);
    expect(getAccessToken()).toBe("token-b");
  });
});

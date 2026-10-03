import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { loginAccount, logoutAccount, registerAccount } from "./api/auth";
import { expireSession, getAccessToken, setAccessToken } from "./api/session";
import { act } from "react";

vi.mock("./Platform", () => ({ default: () => <p>Área privada do candidato</p> }));
vi.mock("./api/auth", () => ({ loginAccount: vi.fn(), registerAccount: vi.fn(), logoutAccount: vi.fn() }));
const session = { user: { id: "user-a", name: "Pessoa teste", email: "teste@example.com" }, access_token: "test-token", token_type: "bearer", expires_in: 28800 };
const password = "senha longa para teste";
afterEach(() => { cleanup(); vi.resetAllMocks(); setAccessToken(null); });
async function fillLogin() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("E-mail de acesso"), session.user.email);
  await user.type(screen.getByLabelText("Senha", { exact: true }), password);
  return user;
}
describe("Privacidade na interface", () => {
  it("exibe apenas o login antes da autenticação", () => {
    render(<App />);
    expect(screen.queryByText("Área privada do candidato")).toBeNull();
    expect(screen.getByRole("heading", { name: "Entrar na plataforma" })).toBeTruthy();
  });
  it("entra e remove a área privada e o token ao sair", async () => {
    vi.mocked(loginAccount).mockResolvedValue(session);
    vi.mocked(logoutAccount).mockResolvedValue({ logged_out: true });
    render(<App />);
    const user = await fillLogin();
    await user.click(screen.getByRole("button", { name: /^Entrar$/ }));
    expect(await screen.findByText("Área privada do candidato")).toBeTruthy();
    expect(getAccessToken()).toBe(session.access_token);
    await user.click(screen.getByRole("button", { name: "Sair da conta" }));
    expect(await screen.findByText("Você saiu da sua conta.")).toBeTruthy();
    expect(screen.queryByText("Área privada do candidato")).toBeNull();
    expect(getAccessToken()).toBeNull();
  });
  it("fecha a área privada quando a sessão expira", async () => {
    vi.mocked(loginAccount).mockResolvedValue(session);
    render(<App />);
    const user = await fillLogin();
    await user.click(screen.getByRole("button", { name: /^Entrar$/ }));
    await screen.findByText("Área privada do candidato");
    act(() => expireSession(session.access_token));
    expect(screen.queryByText("Área privada do candidato")).toBeNull();
    expect(screen.getByText("Sua sessão terminou. Entre novamente.")).toBeTruthy();
  });
  it("exige confirmação da senha no cadastro e preserva os campos após falha", async () => {
    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Criar conta" }));
    await user.type(screen.getByLabelText("Nome"), session.user.name);
    await user.type(screen.getByLabelText("E-mail de acesso"), session.user.email);
    await user.type(screen.getByLabelText("Senha", { exact: true }), password);
    await user.type(screen.getByLabelText("Confirmar senha"), "outra senha longa");
    await user.click(screen.getByRole("button", { name: "Cadastrar e entrar" }));
    expect(screen.getByRole("alert").textContent).toBe("As senhas não coincidem.");
    expect(registerAccount).not.toHaveBeenCalled();
    await user.clear(screen.getByLabelText("Confirmar senha"));
    await user.type(screen.getByLabelText("Confirmar senha"), password);
    vi.mocked(registerAccount).mockRejectedValue(new Error("offline"));
    await user.click(screen.getByRole("button", { name: "Cadastrar e entrar" }));
    expect((await screen.findByRole("alert")).textContent).toContain("conectar");
    expect((screen.getByLabelText("Nome") as HTMLInputElement).value).toBe(session.user.name);
    expect(screen.queryByText("Área privada do candidato")).toBeNull();
  });
});

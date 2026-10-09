import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { activateTrial, getSubscriptionStatus } from "./api/subscription";

vi.mock("./api/subscription", () => ({
  getSubscriptionStatus: vi.fn(),
  activateTrial: vi.fn(),
}));
vi.mock("./components/ConsultationView", () => ({
  default: () => <p>Consulta dos dados preservados</p>,
}));

const existingAccess = {
  access_allowed: true,
  read_allowed: true,
  kind: "existing" as const,
  trial_available: false,
  trial_started_at: null,
  trial_ends_at: null,
  consultation_ends_at: null,
};

beforeEach(() => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue(existingAccess);
});
import { loginAccount, logoutAccount, registerTrialAccount } from "./api/auth";
import { expireSession, getAccessToken, setAccessToken } from "./api/session";

vi.mock("./pages/Admin/AdminAccounts", () => ({ default: () => <p>Painel de administração</p> }));
vi.mock("./Platform", () => ({ default: () => <p>Área privada do candidato</p> }));
vi.mock("./api/auth", () => ({ loginAccount: vi.fn(), registerTrialAccount: vi.fn(), logoutAccount: vi.fn() }));
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
    expect(screen.getByText(/Bem-vindo, Pessoa teste!/)).toBeTruthy();
    expect(getAccessToken()).toBe(session.access_token);
    expect(screen.queryByRole("button", { name: "Administrar acessos" })).toBeNull();
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
    await user.click(screen.getByRole("button", { name: "Criar conta para testar" }));
    expect(screen.getByRole("alert").textContent).toBe("As senhas não coincidem.");
    expect(registerTrialAccount).not.toHaveBeenCalled();
    await user.clear(screen.getByLabelText("Confirmar senha"));
    await user.type(screen.getByLabelText("Confirmar senha"), password);
    vi.mocked(registerTrialAccount).mockRejectedValue(new Error("offline"));
    await user.click(screen.getByRole("button", { name: "Criar conta para testar" }));
    expect((await screen.findByRole("alert")).textContent).toContain("conectar");
    expect((screen.getByLabelText("Nome") as HTMLInputElement).value).toBe(session.user.name);
    expect(screen.queryByText("Área privada do candidato")).toBeNull();
  });
});


it("cria a conta e exige ativar as 24 horas antes de abrir as funções", async () => {
  vi.mocked(registerTrialAccount).mockResolvedValue(session);
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...existingAccess,
    access_allowed: false,
    read_allowed: false,
    kind: "trial_available",
    trial_available: true,
  });
  vi.mocked(activateTrial).mockResolvedValue({
    ...existingAccess,
    kind: "trial",
    trial_started_at: 1000,
    trial_ends_at: 87400,
  });

  render(<App />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Criar conta" }));
  await user.type(screen.getByLabelText("Nome"), "Teste");
  await user.type(screen.getByLabelText("E-mail de acesso"), session.user.email);
  await user.type(screen.getByLabelText("Senha", { exact: true }), password);
  await user.type(screen.getByLabelText("Confirmar senha"), password);
  await user.click(screen.getByRole("button", { name: "Criar conta para testar" }));

  const trial = await screen.findByRole("button", {
    name: "Testar grátis por 24 horas",
  });
  expect(registerTrialAccount).toHaveBeenCalledWith(
    "Teste", session.user.email, password,
  );
  expect(screen.queryByText("Área privada do candidato")).toBeNull();
  expect(activateTrial).not.toHaveBeenCalled();
  expect(getAccessToken()).toBe(session.access_token);

  await user.click(trial);
  expect(await screen.findByText("Área privada do candidato")).toBeTruthy();
  expect(activateTrial).toHaveBeenCalledTimes(1);
});

it("somente a conta administradora recebe o botão administrativo", async () => {
  vi.mocked(loginAccount).mockResolvedValue({ ...session, user: { ...session.user, role: "admin", state: "active" } });
  render(<App />);
  const user = await fillLogin();
  await user.click(screen.getByRole("button", { name: /^Entrar$/ }));
  await user.click(await screen.findByRole("button", { name: "Administrar acessos" }));
  expect(screen.getByText("Painel de administração")).toBeTruthy();
  expect(screen.queryByText("Área privada do candidato")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Voltar à plataforma" }));
  expect(screen.getByText("Área privada do candidato")).toBeTruthy();
});


it("impede o uso da plataforma quando o teste e a consulta terminaram", async () => {
  vi.mocked(loginAccount).mockResolvedValue(session);
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...existingAccess,
    access_allowed: false,
    read_allowed: false,
    kind: "trial_expired",
  });

  render(<App />);
  const user = await fillLogin();
  await user.click(screen.getByRole("button", { name: /^Entrar$/ }));

  const purchase = await screen.findByRole("button", {
    name: /Ativar 1.*19,90/,
  });
  expect(screen.queryByText("\u00c1rea privada do candidato")).toBeNull();
  expect(screen.queryByText("Consulta dos dados preservados")).toBeNull();
  expect(screen.queryByRole("button", {
    name: "Testar gr\u00e1tis por 24 horas",
  })).toBeNull();

  await user.click(purchase);
  expect(await screen.findByRole("heading", {
    name: "Continue sua prepara\u00e7\u00e3o",
  })).toBeTruthy();
  expect(screen.getByLabelText("CPF do pagador")).toBeTruthy();
  expect(screen.queryByText("\u00c1rea privada do candidato")).toBeNull();
});

it("abre somente a consulta durante os sete dias seguintes ao teste", async () => {
  vi.mocked(loginAccount).mockResolvedValue(session);
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...existingAccess,
    access_allowed: false,
    kind: "consultation",
    consultation_ends_at: 2000000000,
  });

  render(<App />);
  const user = await fillLogin();
  await user.click(screen.getByRole("button", { name: /^Entrar$/ }));

  expect(await screen.findByText(
    "Consulta dos dados preservados",
  )).toBeTruthy();
  expect(screen.queryByText("\u00c1rea privada do candidato")).toBeNull();
});

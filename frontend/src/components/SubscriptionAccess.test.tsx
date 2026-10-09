import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { activateTrial, getSubscriptionStatus } from "../api/subscription";
import type { SubscriptionStatus } from "../api/subscription";
import SubscriptionAccess from "./SubscriptionAccess";

vi.mock("../api/subscription", () => ({
  activateTrial: vi.fn(),
  getSubscriptionStatus: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

const available: SubscriptionStatus = {
  access_allowed: false,
  read_allowed: false,
  kind: "trial_available",
  trial_available: true,
  trial_started_at: null,
  trial_ends_at: null,
  consultation_ends_at: null,
};

function show(onPurchase = vi.fn()) {
  return render(
    <SubscriptionAccess
      consultation={<p>Histórico em consulta</p>}
      onPurchase={onPurchase}
    >
      <p>Funções completas</p>
    </SubscriptionAccess>,
  );
}

it("só abre as funções depois de confirmar a ativação do teste", async () => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue(available);
  vi.mocked(activateTrial).mockResolvedValue({
    ...available,
    kind: "trial",
    trial_available: false,
    access_allowed: true,
    read_allowed: true,
    trial_started_at: 1000,
    trial_ends_at: 87400,
    consultation_ends_at: 692200,
  });
  show();
  expect(screen.queryByText("Funções completas")).toBeNull();
  const user = userEvent.setup();
  await user.click(await screen.findByRole("button", {
    name: "Testar grátis por 24 horas",
  }));
  expect(await screen.findByText("Funções completas")).toBeTruthy();
  expect(activateTrial).toHaveBeenCalledTimes(1);
});

it("mostra somente a consulta após as 24 horas e permite abrir a oferta", async () => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...available,
    kind: "consultation",
    trial_available: false,
    read_allowed: true,
    consultation_ends_at: 692200,
  });
  const purchase = vi.fn();
  show(purchase);
  expect(await screen.findByText("Histórico em consulta")).toBeTruthy();
  expect(screen.queryByText("Funções completas")).toBeNull();
  expect(screen.queryByRole("button", {
    name: "Testar grátis por 24 horas",
  })).toBeNull();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", {
    name: "Ativar 1º mês — R$ 19,90",
  }));
  expect(purchase).toHaveBeenCalledTimes(1);
});

it("não abre consulta nem oferece outro teste após o prazo final", async () => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...available,
    kind: "trial_expired",
    trial_available: false,
  });
  show();
  await screen.findByRole("button", { name: "Ativar 1º mês — R$ 19,90" });
  expect(screen.queryByText("Histórico em consulta")).toBeNull();
  expect(screen.queryByText("Funções completas")).toBeNull();
  expect(screen.queryByRole("button", {
    name: "Testar grátis por 24 horas",
  })).toBeNull();
});

it("preserva o acesso completo das contas existentes", async () => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    ...available,
    kind: "existing",
    trial_available: false,
    access_allowed: true,
    read_allowed: true,
  });
  show();
  expect(await screen.findByText("Funções completas")).toBeTruthy();
  expect(screen.queryByRole("button", {
    name: "Ativar 1º mês — R$ 19,90",
  })).toBeNull();
});

it("não libera funções quando a conferência de acesso falha", async () => {
  vi.mocked(getSubscriptionStatus).mockRejectedValue(new Error("offline"));
  show();
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(screen.queryByText("Funções completas")).toBeNull();
  expect(screen.queryByText("Histórico em consulta")).toBeNull();
});

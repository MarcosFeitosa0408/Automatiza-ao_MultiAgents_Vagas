import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { apiRequest } from "../../api/client";
import AdminMembers from "./AdminMembers";

vi.mock("../../api/client", () => ({ apiRequest: vi.fn() }));

const subscription = {
  access_allowed: true,
  read_allowed: true,
  trial_available: false,
  trial_started_at: 1000,
  trial_ends_at: 87400,
  consultation_ends_at: 692200,
};

beforeEach(() => {
  vi.mocked(apiRequest).mockResolvedValue({
    members: [
      {
        id: "trial-user",
        name: "Candidato em teste",
        email: "trial@example.invalid",
        role: "user",
        state: "active",
        subscription: { ...subscription, kind: "trial" },
        payments: [],
        access_history: [{ event: "LOGIN", occurred_at: 1000 }],
      },
      {
        id: "paid-user",
        name: "Candidato pagante",
        email: "paid@example.invalid",
        role: "user",
        state: "active",
        subscription: {
          ...subscription,
          kind: "paid",
          paid_ends_at: 2593000,
        },
        payments: [{
          id: "test-payment",
          amount: 1990,
          state: "PAID",
          environment: "sandbox",
          created_at: 1000,
          period_start: 1000,
          period_end: 2593000,
        }],
        access_history: [],
      },
    ],
  });
});

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("diferencia teste e pagamento e identifica Sandbox e entradas", async () => {
  const user = userEvent.setup();
  render(<AdminMembers />);
  expect(await screen.findByText("Candidato em teste")).toBeTruthy();
  expect(screen.getByText("Em teste gratuito")).toBeTruthy();
  expect(screen.getByText("Membro com pagamento confirmado")).toBeTruthy();
  expect(screen.getByText("R$ 19,90")).toBeTruthy();
  expect(screen.getByText("TESTE — Sandbox", { exact: false })).toBeTruthy();
  expect(screen.getByText(/Entrada bem-sucedida/)).toBeTruthy();

  await user.click(screen.getByRole("button", { name: "Atualizar membros" }));
  expect(await screen.findByText("Candidato pagante")).toBeTruthy();
  expect(apiRequest).toHaveBeenCalledTimes(2);
  expect(apiRequest).toHaveBeenCalledWith("/admin/members");
});

it("mostra falha da consulta e permite atualizar novamente", async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockRejectedValueOnce(new Error("Falha de teste"));
  render(<AdminMembers />);
  expect(await screen.findByRole("alert")).toBeTruthy();

  await user.click(screen.getByRole("button", { name: "Atualizar membros" }));
  expect(await screen.findByText("Candidato em teste")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

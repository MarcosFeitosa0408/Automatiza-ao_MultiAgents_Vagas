import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PixPaymentPage from "./PixPaymentPage";
import { createPixPayment, getPixPayment } from "../api/payment";
import type { PixPayment } from "../api/payment";
import { getSubscriptionStatus } from "../api/subscription";

vi.mock("../api/payment", () => ({
  createPixPayment: vi.fn(),
  getPixPayment: vi.fn(),
}));
vi.mock("../api/subscription", () => ({
  getSubscriptionStatus: vi.fn(),
}));
vi.mock("qrcode", () => ({
  default: {
    toDataURL: async () => "data:image/png;base64,dGVzdA==",
  },
}));

const payment: PixPayment = {
  id: "payment-test",
  amount: 1990,
  state: "WAITING",
  environment: "sandbox",
  qr_text: "codigo-pix-apenas-para-teste",
  period_start: null,
  period_end: null,
};

beforeEach(() => {
  vi.mocked(getSubscriptionStatus).mockResolvedValue({
    access_allowed: false,
    read_allowed: false,
    kind: "trial_expired",
    trial_available: false,
    trial_started_at: 1000,
    trial_ends_at: 87400,
    consultation_ends_at: 692200,
    next_payment_amount: 1990,
  });
  vi.mocked(createPixPayment).mockResolvedValue(payment);
  vi.mocked(getPixPayment).mockImplementation(async () => ({ ...payment }));
});

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("mostra o Pix sem liberar acesso enquanto o servidor informa WAITING", async () => {
  const user = userEvent.setup();
  const confirmed = vi.fn();
  render(<PixPaymentPage onBack={vi.fn()} onConfirmed={confirmed} />);
  await screen.findByRole("heading", { name: /19,90/ });
  await user.type(screen.getByLabelText("CPF do pagador"), "12345678909");
  await user.click(screen.getByRole("button", { name: "Pagar com Pix" }));

  expect(createPixPayment).toHaveBeenCalledWith("12345678909");
  expect(await screen.findByLabelText("Pix Copia e Cola")).toBeTruthy();
  await waitFor(() => expect(getPixPayment).toHaveBeenCalledTimes(1));
  expect(confirmed).not.toHaveBeenCalled();
});

it("retorna somente apos a consulta do servidor confirmar PAID", async () => {
  const user = userEvent.setup();
  const confirmed = vi.fn();
  render(<PixPaymentPage onBack={vi.fn()} onConfirmed={confirmed} />);
  await screen.findByRole("heading", { name: /19,90/ });
  await user.type(screen.getByLabelText("CPF do pagador"), "12345678909");
  await user.click(screen.getByRole("button", { name: "Pagar com Pix" }));
  await waitFor(() => expect(getPixPayment).toHaveBeenCalledTimes(1));
  expect(confirmed).not.toHaveBeenCalled();

  vi.mocked(getPixPayment).mockResolvedValueOnce({
    ...payment,
    state: "PAID",
    period_start: 1000,
    period_end: 2593000,
  });
  await user.click(screen.getByRole("button", { name: "Conferir pagamento" }));
  await waitFor(() => expect(confirmed).toHaveBeenCalledTimes(1));
});

it("preserva o CPF apos falha e permite tentar novamente", async () => {
  const user = userEvent.setup();
  vi.mocked(createPixPayment).mockRejectedValueOnce(new Error("Falha de teste"));
  render(<PixPaymentPage onBack={vi.fn()} onConfirmed={vi.fn()} />);
  await screen.findByRole("heading", { name: /19,90/ });
  const field = screen.getByLabelText("CPF do pagador");
  await user.type(field, "12345678909");
  await user.click(screen.getByRole("button", { name: "Pagar com Pix" }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect((field as HTMLInputElement).value).toBe("12345678909");

  await user.click(screen.getByRole("button", { name: "Pagar com Pix" }));
  expect(await screen.findByLabelText("Pix Copia e Cola")).toBeTruthy();
  expect(createPixPayment).toHaveBeenCalledTimes(2);
});

import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HelpRobot from "./HelpRobot";
import { askHelp, forwardHelp, helpInfo } from "../api/help";
vi.mock("../api/help", () => ({ askHelp: vi.fn(), forwardHelp: vi.fn(), helpInfo: vi.fn() }));
const quota = { remaining: 3, week: "2026-10-05", renews_at: "2026-10-12T00:00:00-03:00" };
afterEach(() => { cleanup(); vi.resetAllMocks(); });
beforeEach(() => { vi.mocked(helpInfo).mockResolvedValue({ ...quota, suggestions: [] }); });

it("só encaminha dúvida desconhecida com consentimento e preserva o texto após falha", async () => {
  const user = userEvent.setup(); render(<HelpRobot />);
  expect(helpInfo).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: /Tirar dúvidas/ }));
  await user.type(screen.getByLabelText("Sua dúvida sobre a plataforma"), "Posso mudar a cor?");
  vi.mocked(askHelp).mockResolvedValue({ ...quota, known: false, answer: "Ainda não tenho uma resposta." });
  await user.click(screen.getByRole("button", { name: "Perguntar ao robô" }));
  expect(forwardHelp).not.toHaveBeenCalled();
  const send = screen.getByRole("button", { name: "Enviar dúvida para melhoria" }) as HTMLButtonElement;
  expect(send.disabled).toBe(true);
  await user.click(screen.getByRole("checkbox"));
  vi.mocked(forwardHelp).mockRejectedValueOnce(new Error("offline"));
  await user.click(send);
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect((screen.getByLabelText("Sua dúvida sobre a plataforma") as HTMLTextAreaElement).value).toBe("Posso mudar a cor?");
  vi.mocked(forwardHelp).mockResolvedValue({ ...quota, remaining: 2, sent: true, duplicate: false });
  await user.click(send);
  expect(await screen.findByText(/Dúvida encaminhada/)).toBeTruthy();
  expect(vi.mocked(forwardHelp).mock.calls[0][1]).toBe(vi.mocked(forwardHelp).mock.calls[1][1]);
  expect(screen.queryByRole("button", { name: "Enviar dúvida para melhoria" })).toBeNull();
  await user.click(screen.getByRole("button", { name: "Fechar dúvidas" }));
  expect(screen.queryByLabelText("Sua dúvida sobre a plataforma")).toBeNull();
});

it("continua respondendo orientações conhecidas depois do limite", async () => {
  vi.mocked(helpInfo).mockResolvedValue({ ...quota, remaining: 0, suggestions: ["Como salvo o PDF?"] });
  vi.mocked(askHelp).mockResolvedValue({ ...quota, remaining: 0, known: true, answer: "Escolha Salvar como PDF." });
  const user = userEvent.setup(); render(<HelpRobot />);
  await user.click(screen.getByRole("button", { name: /Tirar dúvidas/ }));
  await user.click(await screen.findByRole("button", { name: "Como salvo o PDF?" }));
  expect(await screen.findByText(/Escolha Salvar como PDF/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Enviar dúvida para melhoria" })).toBeNull();
  expect(forwardHelp).not.toHaveBeenCalled();
});

import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InterviewPanel from "./InterviewPanel";
import { evaluateInterviewAnswer, generateInterviewPlan } from "../../api/interview";

vi.mock("../../api/interview", () => ({ generateInterviewPlan: vi.fn(), evaluateInterviewAnswer: vi.fn() }));
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(generateInterviewPlan).mockResolvedValue({ job_id: "job", job_title: "Analista", company: "Empresa", preparation_notes: [], questions: [{ question_id: "presentation", category: "Apresentação", question: "Apresente-se", guidance: [] }] });
  vi.mocked(evaluateInterviewAnswer).mockResolvedValue({ question_id: "presentation", score: 48, criteria: [{ name: "Trajetória", score: 12, maximum: 25, guidance: "Explique sua prática real." }], limitation: "Não prevê aprovação." });
});
afterEach(cleanup);

it("avalia somente ao clicar, mostra orientação e remove nota ao editar", async () => {
  const user = userEvent.setup();
  render(<InterviewPanel applicationId="private-job" />);
  await user.click(screen.getByRole("button", { name: "Preparar entrevista" }));
  const field = await screen.findByRole("textbox");
  await user.type(field, "Minha formação e projeto de estudo.");
  expect(evaluateInterviewAnswer).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Avaliar resposta" }));
  expect(await screen.findByText("Nota de estrutura: 48/100")).toBeTruthy();
  expect(evaluateInterviewAnswer).toHaveBeenCalledWith("private-job", "presentation", "Minha formação e projeto de estudo.");
  expect(screen.getByText("Não prevê aprovação.")).toBeTruthy();
  await user.type(field, " Aprendi SQL.");
  expect(screen.queryByText("Nota de estrutura: 48/100")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Avaliar resposta" }));
  expect(await screen.findByText("Nota de estrutura: 48/100")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "Preparar entrevista" }));
  expect(screen.queryByText("Nota de estrutura: 48/100")).toBeNull();
  expect((field as HTMLTextAreaElement).value).toContain("Aprendi SQL.");
});

it("preserva resposta após erro e permite tentar novamente", async () => {
  vi.mocked(evaluateInterviewAnswer).mockRejectedValueOnce(new Error("offline"));
  const user = userEvent.setup();
  render(<InterviewPanel applicationId="private-job" />);
  await user.click(screen.getByRole("button", { name: "Preparar entrevista" }));
  const field = await screen.findByRole("textbox");
  expect((screen.getByRole("button", { name: "Avaliar resposta" }) as HTMLButtonElement).disabled).toBe(true);
  await user.type(field, "Meu projeto real");
  await user.click(screen.getByRole("button", { name: "Avaliar resposta" }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect((field as HTMLTextAreaElement).value).toBe("Meu projeto real");
  await user.click(screen.getByRole("button", { name: "Avaliar resposta" }));
  expect(await screen.findByText("Nota de estrutura: 48/100")).toBeTruthy();
});

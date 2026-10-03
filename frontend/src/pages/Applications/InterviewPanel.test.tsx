import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InterviewPanel from "./InterviewPanel";
import { ApiError } from "../../api/client";
import { generateInterviewPlan } from "../../api/interview";
import type { InterviewPlan } from "../../api/interview";

vi.mock("../../api/interview", () => ({
  generateInterviewPlan: vi.fn(),
}));

const plan: InterviewPlan = {
  job_id: "job-test",
  job_title: "Analista de Dados",
  company: "Empresa Teste",
  questions: [
    {
      question_id: "technical-1",
      category: "Técnica",
      question: "Como você utiliza SQL em um projeto?",
      guidance: ["Use um exemplo real e explique sua participação."],
    },
  ],
  preparation_notes: [
    "Revise o anúncio completo antes da entrevista.",
  ],
};

describe("Preparação para entrevista", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(generateInterviewPlan).mockResolvedValue(plan);
  });

  afterEach(() => {
    cleanup();
  });

  it("consulta a candidatura escolhida e mostra as perguntas", async () => {
    const user = userEvent.setup();

    render(<InterviewPanel applicationId="application-test" />);

    expect(generateInterviewPlan).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: "Preparar entrevista" }),
    );

    expect(
      await screen.findByText("Preparação para entrevista"),
    ).toBeTruthy();

    expect(generateInterviewPlan).toHaveBeenCalledExactlyOnceWith(
      "application-test",
    );

    expect(
      screen.getByText("Use um exemplo real e explique sua participação."),
    ).toBeTruthy();

    expect(
      screen.getByRole("textbox", {
        name: "1. Como você utiliza SQL em um projeto?",
      }),
    ).toBeTruthy();
  });

  it("permite praticar e mantém a resposta ao regenerar o roteiro", async () => {
    const user = userEvent.setup();

    render(<InterviewPanel applicationId="application-test" />);

    await user.click(
      screen.getByRole("button", { name: "Preparar entrevista" }),
    );

    const answer = await screen.findByRole("textbox", {
      name: "1. Como você utiliza SQL em um projeto?",
    });

    await user.type(answer, "Usei SQL para consultar e validar dados.");

    await user.click(
      screen.getByRole("button", { name: "Preparar entrevista" }),
    );

    expect(
      (screen.getByRole("textbox") as HTMLTextAreaElement).value,
    ).toBe("Usei SQL para consultar e validar dados.");

    // A chamada envia apenas o identificador, sem a resposta digitada.
    expect(vi.mocked(generateInterviewPlan).mock.calls).toEqual([
      ["application-test"],
      ["application-test"],
    ]);
  });

  it("mostra a validação e permite tentar novamente", async () => {
    const user = userEvent.setup();

    vi.mocked(generateInterviewPlan).mockRejectedValueOnce(
      new ApiError(400, {
        message: "Informe os requisitos da vaga antes de preparar a entrevista.",
      }),
    );

    render(<InterviewPanel applicationId="application-test" />);

    await user.click(
      screen.getByRole("button", { name: "Preparar entrevista" }),
    );

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Informe os requisitos",
    );

    await user.click(
      screen.getByRole("button", { name: "Preparar entrevista" }),
    );

    expect(
      await screen.findByText("Preparação para entrevista"),
    ).toBeTruthy();

    expect(screen.queryByRole("alert")).toBeNull();
  });
});
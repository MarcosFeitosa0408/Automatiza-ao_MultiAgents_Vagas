import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResumePanel from "./ResumePanel";
import { ApiError } from "../../api/client";
import { generateResumePreview } from "../../api/resume";
import type { ResumePreview } from "../../api/resume";

vi.mock("../../api/resume", () => ({
  generateResumePreview: vi.fn(),
}));

const preview: ResumePreview = {
  application_id: "application-test",
  job_title: "Analista de Dados",
  company: "Empresa Teste",
  name: "Pessoa de Teste",
  email: "pessoa@example.com",
  phone: "11900000000",
  location: "São Paulo, SP, Brasil",
  professional_title: "Analista de Dados",
  professional_summary: "Análise de dados e relatórios.",
  skills: ["SQL", "Power BI"],
  education: [
    {
      degree: "Análise e Desenvolvimento de Sistemas",
      institution: "Instituição Teste",
      status: "Concluído",
    },
  ],
  experience: [
    {
      company: "Empresa Anterior",
      role: "Analista",
      employment_type: "Freelance",
      start: "2025-03",
      end: "2025-06",
      current: false,
      location: "São Paulo",
      work_model: "Remoto",
      technologies: ["SQL"],
      responsibilities: ["Criar relatórios"],
      achievements: [],
    },
  ],
  projects: [
    {
      name: "Dashboard de Vendas",
      description: "Análise de indicadores comerciais.",
      technologies: ["Power BI"],
    },
  ],
  languages: {
    portuguese: "Nativo",
    english: "Intermediário",
  },
  links: {
    portfolio_url: "https://example.com/portfolio",
  },
  ats_keywords: ["SQL", "Power BI"],
  unsupported_requirements: ["Kubernetes"],
  warnings: ["Revise o conteúdo antes de usar."],
};

describe("Prévia do currículo", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(generateResumePreview).mockResolvedValue(preview);
  });

  afterEach(() => {
    cleanup();
  });

  it("gera a prévia da candidatura escolhida e mostra o conteúdo", async () => {
    const user = userEvent.setup();

    render(<ResumePanel applicationId="application-test" />);

    expect(generateResumePreview).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: "Gerar prévia do currículo" }),
    );

    expect(await screen.findByText("Pessoa de Teste")).toBeTruthy();
    expect(generateResumePreview).toHaveBeenCalledExactlyOnceWith(
      "application-test",
    );

    expect(screen.getByText("Criar relatórios")).toBeTruthy();
    expect(screen.getByText("Dashboard de Vendas")).toBeTruthy();
    expect(
      screen.getByText("Análise e Desenvolvimento de Sistemas"),
    ).toBeTruthy();
    expect(screen.getByText("Kubernetes")).toBeTruthy();
  });

  it("mostra o motivo da validação e permite tentar novamente", async () => {
    const user = userEvent.setup();

    vi.mocked(generateResumePreview).mockRejectedValueOnce(
      new ApiError(400, {
        message: "Informe os requisitos da vaga antes de calcular a compatibilidade.",
      }),
    );

    render(<ResumePanel applicationId="application-test" />);

    await user.click(
      screen.getByRole("button", { name: "Gerar prévia do currículo" }),
    );

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Informe os requisitos",
    );
    expect(screen.queryByText("Pessoa de Teste")).toBeNull();

    await user.click(
      screen.getByRole("button", { name: "Gerar prévia do currículo" }),
    );

    expect(await screen.findByText("Pessoa de Teste")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("fecha a prévia sem gerar outra solicitação", async () => {
    const user = userEvent.setup();

    render(<ResumePanel applicationId="application-test" />);

    await user.click(
      screen.getByRole("button", { name: "Gerar prévia do currículo" }),
    );

    await screen.findByText("Pessoa de Teste");

    await user.click(
      screen.getByRole("button", { name: "Fechar prévia" }),
    );

    expect(screen.queryByText("Pessoa de Teste")).toBeNull();
    expect(generateResumePreview).toHaveBeenCalledTimes(1);
  });
});

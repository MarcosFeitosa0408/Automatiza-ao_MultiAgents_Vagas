import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResumePanel from "./ResumePanel";
import { ApiError } from "../../api/client";
import { generateResumePreview, translateResumePreview } from "../../api/resume";
import type { ResumePreview } from "../../api/resume";

vi.mock("../../api/resume", () => ({
  generateResumePreview: vi.fn(),
  translateResumePreview: vi.fn(),
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
    vi.restoreAllMocks();
  });

  it("traduz somente ao clicar, exporta o idioma escolhido e restaura o original", async () => {
    const user = userEvent.setup();
    vi.mocked(translateResumePreview).mockResolvedValue({ ...preview, language: "en-US", professional_summary: "Data analysis" });
    const doc = document.implementation.createHTMLDocument();
    vi.spyOn(window, "open").mockReturnValue({ document: doc, focus: vi.fn(), print: vi.fn(), close: vi.fn() } as unknown as Window);
    render(<ResumePanel applicationId="application-test" />);
    await user.click(screen.getByRole("button", { name: "Gerar prévia do currículo" }));
    await user.selectOptions(screen.getByLabelText("Idioma do currículo"), "en-US");
    expect(translateResumePreview).not.toHaveBeenCalled();
    expect((screen.getByRole("button", { name: /Salvar currículo em PDF/ }) as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "Traduzir currículo" }));
    expect(await screen.findByText("Data analysis")).toBeTruthy();
    expect(translateResumePreview).toHaveBeenCalledExactlyOnceWith("application-test", "en-US");
    expect(screen.getByText("Professional summary")).toBeTruthy();
    await user.click(screen.getByRole("checkbox", { name: /Revisei o conteúdo/ }));
    await user.click(screen.getByRole("button", { name: /Salvar currículo em PDF/ }));
    expect(doc.documentElement.lang).toBe("en-US");
    expect(doc.body.textContent).toContain("Data analysis");
    await user.selectOptions(screen.getByLabelText("Idioma do currículo"), "pt-BR");
    expect(screen.getByText("Análise de dados e relatórios.")).toBeTruthy();
    expect(translateResumePreview).toHaveBeenCalledTimes(1);
  });

  it("preserva o original após falha de tradução e permite tentar novamente", async () => {
    const user = userEvent.setup();
    vi.mocked(translateResumePreview).mockRejectedValueOnce(new ApiError(503, {detail: "Cota indisponível"}));
    render(<ResumePanel applicationId="application-test" />);
    await user.click(screen.getByRole("button", { name: "Gerar prévia do currículo" }));
    await user.selectOptions(screen.getByLabelText("Idioma do currículo"), "es");
    await user.click(screen.getByRole("button", { name: "Traduzir currículo" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Cota indisponível");
    expect(screen.getByText("Análise de dados e relatórios.")).toBeTruthy();
    vi.mocked(translateResumePreview).mockResolvedValue({...preview, language: "es", professional_summary: "Análisis de datos"});
    await user.click(screen.getByRole("button", { name: "Traduzir currículo" }));
    expect(await screen.findByText("Análisis de datos")).toBeTruthy();
  });

  it("abre o PDF da prévia escolhida sem exportar os avisos da análise", async () => {
    const user = userEvent.setup();
    const doc = document.implementation.createHTMLDocument();
    const print = vi.fn();
    vi.spyOn(window, "open").mockReturnValue({
      document: doc, focus: vi.fn(), print, close: vi.fn(),
    } as unknown as Window);
    render(<ResumePanel applicationId="application-test" />);
    expect(screen.queryByRole("button", { name: /Salvar currículo em PDF/ })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Gerar prévia do currículo" }));
    await screen.findByText("Pessoa de Teste");
    await user.click(screen.getByRole("checkbox", { name: /Revisei o conteúdo/ }));
    await user.click(screen.getByRole("button", { name: /Salvar currículo em PDF/ }));
    expect(print).toHaveBeenCalledOnce();
    expect(doc.body.textContent).toContain("Pessoa de Teste");
    expect(doc.body.textContent).toContain("Criar relatórios");
    expect(doc.body.textContent).not.toContain("Kubernetes");
    expect(doc.body.textContent).not.toContain("Revisei o conteúdo");
    expect(doc.body.textContent).not.toContain("Revise o conteúdo antes de usar.");
    expect(generateResumePreview).toHaveBeenCalledTimes(1);
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

it("exige revisão da prévia e reinicia a confirmação ao trocar idioma ou gerar novamente", async () => {
  const user = userEvent.setup();
  vi.mocked(generateResumePreview).mockResolvedValue(preview);
  render(<ResumePanel applicationId="application-test" />);
  await user.click(screen.getByRole("button", {name: "Gerar prévia do currículo"}));
  const pdf = screen.getByRole("button", {name: /Salvar currículo em PDF/}) as HTMLButtonElement;
  expect(pdf.disabled).toBe(true);
  await user.click(screen.getByRole("checkbox", {name: /Revisei o conteúdo/}));
  expect(pdf.disabled).toBe(false);
  await user.selectOptions(screen.getByLabelText("Idioma do currículo"), "es");
  await user.selectOptions(screen.getByLabelText("Idioma do currículo"), "pt-BR");
  expect(pdf.disabled).toBe(true);
  await user.click(screen.getByRole("checkbox", {name: /Revisei o conteúdo/}));
  await user.click(screen.getByRole("button", {name: "Gerar prévia do currículo"}));
  expect((await screen.findByRole("button", {name: /Salvar currículo em PDF/}) as HTMLButtonElement).disabled).toBe(true);
  cleanup();
});

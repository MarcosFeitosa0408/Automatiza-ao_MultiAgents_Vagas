import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Profile from "./Profile";
import {
  getCandidateProfile,
  saveCandidateProfile,
} from "../../api/profile";
import type { MasterProfile } from "../../types/profile";

vi.mock("../../api/profile", () => ({
  getCandidateProfile: vi.fn(),
  saveCandidateProfile: vi.fn(),
}));

function makeProfile(): MasterProfile {
  return {
    schema_version: "1.0",
    candidate_id: "pessoa-teste",
    candidate: {
      name: "Pessoa de Teste",
      location: {
        city: "São Paulo",
        state: "SP",
        country: "Brasil",
      },
      employment_status: {
        currently_clt: false,
        actively_seeking: true,
        priority: "Normal",
        primary_goal: "Trabalhar com dados",
      },
      career_target: {
        primary_roles: ["Analista de Dados"],
        secondary_roles: [],
        seniority: ["Júnior"],
      },
      work_preferences: {
        employment_type_priority: ["CLT"],
        remote: true,
        hybrid: true,
        onsite: false,
        preferred_location: ["São Paulo"],
        relocation: false,
      },
    },
    professional_positioning: {
      title: "Analista de Dados",
      summary: "Experiência prática com análise de dados.",
      focus: ["Business Intelligence"],
    },
    skills: {
      core: ["Power BI"],
      database: ["SQL"],
      python: [],
      analytics: [],
      tools: ["Excel"],
      automation: [],
    },
    languages: {
      portuguese: "Nativo",
      english: "Intermediário",
    },
    portfolio: {
      portfolio_url: "https://example.com/portfolio",
      github_url: "",
      linkedin_url: "",
    },
    education: [
      {
        degree: "Análise e Desenvolvimento de Sistemas",
        institution: "Instituição Teste",
        status: "Concluído",
      },
    ],
    experience: [
      {
        company: "Empresa Teste",
        role: "Analista",
        responsibilities: ["Criar relatórios"],
      },
    ],
    projects: [
      {
        name: "Dashboard",
        description: "Análise de vendas",
        technologies: ["Power BI"],
      },
    ],
    evidence_policy: {
      never_invent_skill: true,
      never_invent_experience: true,
    },
  };
}

describe("Meu perfil", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(getCandidateProfile).mockResolvedValue(makeProfile());
    vi.mocked(saveCandidateProfile).mockImplementation(
      async (profile) => profile,
    );
  });

  afterEach(() => {
    cleanup();
  });

  it("carrega os dados profissionais existentes", async () => {
    render(<Profile />);

    const name = await screen.findByLabelText("Nome *");

    expect((name as HTMLInputElement).value).toBe("Pessoa de Teste");
    expect(
      (screen.getByLabelText("Competências principais") as HTMLTextAreaElement)
        .value,
    ).toBe("Power BI");

    expect(saveCandidateProfile).not.toHaveBeenCalled();
  });

  it("salva alterações e preserva as demais seções", async () => {
    const user = userEvent.setup();
    const original = makeProfile();

    render(<Profile />);

    const name = await screen.findByLabelText("Nome *");
    await user.clear(name);
    await user.type(name, "Nome Atualizado");

    const skills = screen.getByLabelText("Competências principais");
    await user.clear(skills);
    await user.type(skills, "SQL\nPower BI");

    await user.click(screen.getByLabelText("Aceito trabalho presencial"));
    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    await waitFor(() => {
      expect(saveCandidateProfile).toHaveBeenCalledTimes(1);
    });

    const submitted = vi.mocked(saveCandidateProfile).mock.calls[0][0];

    expect(submitted.candidate.name).toBe("Nome Atualizado");
    expect(submitted.skills.core).toEqual(["SQL", "Power BI"]);
    expect(submitted.candidate.work_preferences.onsite).toBe(true);
    expect(submitted.education).toEqual(original.education);
    expect(submitted.experience).toEqual(original.experience);
    expect(submitted.projects).toEqual(original.projects);
    expect(submitted.evidence_policy).toEqual(original.evidence_policy);

    expect(
      await screen.findByText(
        "Perfil salvo! As próximas análises usarão os dados atualizados.",
      ),
    ).toBeTruthy();
  });

  it("preserva os campos após falha e permite tentar novamente", async () => {
    const user = userEvent.setup();
    vi.mocked(saveCandidateProfile).mockRejectedValueOnce(
      new TypeError("Falha de conexão"),
    );

    render(<Profile />);

    const name = await screen.findByLabelText("Nome *");
    await user.clear(name);
    await user.type(name, "Nome Preservado");

    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect((name as HTMLInputElement).value).toBe("Nome Preservado");

    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    expect(
      await screen.findByText(
        "Perfil salvo! As próximas análises usarão os dados atualizados.",
      ),
    ).toBeTruthy();

    expect(saveCandidateProfile).toHaveBeenCalledTimes(2);
  });

    it("edita formação, experiência e projeto e salva os dados", async () => {
    const user = userEvent.setup();

    render(<Profile />);
    await screen.findByLabelText("Nome *");

    const degree = screen.getByLabelText("Curso ou formação");
    await user.clear(degree);
    await user.type(degree, "MBA em Análise de Dados");

    const role = screen.getByLabelText("Cargo ou atividade");
    await user.clear(role);
    await user.type(role, "Analista de Dados");

    const project = screen.getByLabelText("Nome do projeto");
    await user.clear(project);
    await user.type(project, "Dashboard de Vendas");

    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    await waitFor(() => {
      expect(saveCandidateProfile).toHaveBeenCalledTimes(1);
    });

    const submitted = vi.mocked(saveCandidateProfile).mock.calls[0][0];

    expect(submitted.education[0].degree).toBe("MBA em Análise de Dados");
    expect(submitted.experience[0].role).toBe("Analista de Dados");
    expect(submitted.projects[0].name).toBe("Dashboard de Vendas");

    expect(submitted.experience[0].responsibilities).toEqual([
      "Criar relatórios",
    ]);
    expect(submitted.evidence_policy).toEqual(makeProfile().evidence_policy);
  });

  it("adiciona uma formação e remove um projeto somente ao salvar", async () => {
    const user = userEvent.setup();

    render(<Profile />);
    await screen.findByLabelText("Nome *");

    await user.click(
      screen.getByRole("button", { name: "Adicionar formação" }),
    );

    const degrees = screen.getAllByLabelText("Curso ou formação");
    const institutions = screen.getAllByLabelText("Instituição");
    const statuses = screen.getAllByLabelText(
      "Situação — inclua o ano de conclusão",
    );

    await user.type(degrees[1], "Curso de SQL");
    await user.type(institutions[1], "Instituição de Cursos");
    await user.type(statuses[1], "Concluído em 2026");

    const projectName = screen.getByLabelText("Nome do projeto");
    const projectEntry = projectName.closest(".profile-entry");

    if (!projectEntry) {
      throw new Error("Registro do projeto não encontrado");
    }

    const removeButton = projectEntry.querySelector("button");

    if (!removeButton) {
      throw new Error("Botão de remoção não encontrado");
    }

    await user.click(removeButton);

    expect(saveCandidateProfile).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    await waitFor(() => {
      expect(saveCandidateProfile).toHaveBeenCalledTimes(1);
    });

    const submitted = vi.mocked(saveCandidateProfile).mock.calls[0][0];

    expect(submitted.education).toHaveLength(2);
    expect(submitted.education[1]).toEqual({
      degree: "Curso de SQL",
      institution: "Instituição de Cursos",
      status: "Concluído em 2026",
      start: null,
      end: null,
    });
    expect(submitted.projects).toEqual([]);
    expect(submitted.experience).toEqual(makeProfile().experience);
  });

  it("impede salvar um link com protocolo inválido", async () => {
    const user = userEvent.setup();

    render(<Profile />);
    await screen.findByLabelText("Nome *");

    const link = screen.getByLabelText("Link do portfólio");
    await user.clear(link);
    await user.type(link, "ftp://example.com");

    await user.click(
      screen.getByRole("button", { name: "Salvar meu perfil" }),
    );

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(saveCandidateProfile).not.toHaveBeenCalled();
  });
});

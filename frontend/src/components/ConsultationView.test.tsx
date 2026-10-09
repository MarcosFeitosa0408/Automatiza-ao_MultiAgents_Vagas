import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { listJobApplications, deleteJobApplication } from "../api/applications";
import { getCandidateProfile, saveCandidateProfile } from "../api/profile";
import type { JobApplicationObject } from "../types/api";
import type { MasterProfile } from "../types/profile";
import ConsultationView from "./ConsultationView";

vi.mock("../api/applications", async (importOriginal) => ({
  ...await importOriginal<typeof import("../api/applications")>(),
  listJobApplications: vi.fn(),
  deleteJobApplication: vi.fn(),
}));

vi.mock("../api/profile", () => ({
  getCandidateProfile: vi.fn(),
  saveCandidateProfile: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

const application: JobApplicationObject = {
  application_id: "consultation-test",
  job: {
    job_id: "job-test",
    title: "Analista de Dados",
    company: "Empresa de Teste",
    source: "TESTE",
    url: null,
    location: "São Paulo",
    work_model: "HYBRID",
    employment_type: "CLT",
    description: "Anúncio salvo.",
    requirements: ["SQL"],
    desirable_requirements: [],
    discovered_at: "2026-10-01T12:00:00Z",
    status: "DISCOVERED",
  },
  qualification: null,
  personalization: null,
  preparation: null,
  tracking: {
    job_id: "job-test",
    current_status: "SCREENING",
    history: [{
      status: "SCREENING",
      note: "Aguardando resposta da empresa.",
      occurred_at: "2026-10-02T12:00:00Z",
    }],
    followup_count: 0,
    last_followup_at: null,
  },
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-02T12:00:00Z",
};

const profile: MasterProfile = {
  schema_version: "1",
  candidate_id: "candidate-test",
  candidate: {
    name: "Pessoa de Teste",
    location: { city: "São Paulo", state: "SP", country: "Brasil" },
    employment_status: {
      currently_clt: false,
      actively_seeking: true,
      priority: "",
      primary_goal: "",
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
    summary: "Resumo informado pelo candidato.",
    focus: [],
  },
  skills: {
    core: ["SQL"],
    database: [],
    python: [],
    analytics: [],
    tools: [],
    automation: [],
  },
  languages: { portuguese: "Nativo", english: "Intermediário" },
  portfolio: { portfolio_url: "", github_url: "", linkedin_url: "" },
  education: [],
  experience: [],
  projects: [],
  evidence_policy: {},
};

it("permite ler o anúncio e histórico sem exibir ações de edição", async () => {
  vi.mocked(listJobApplications).mockResolvedValue([application]);
  render(<ConsultationView />);
  await screen.findByText("Analista de Dados");
  const user = userEvent.setup();
  await user.click(screen.getByText("Consultar anúncio e histórico"));
  expect(screen.getByText("Aguardando resposta da empresa.")).toBeTruthy();
  expect(screen.getByText("Anúncio salvo.")).toBeTruthy();
  expect(screen.queryByText("Editar descrição e requisitos")).toBeNull();
  expect(screen.queryByRole("button", { name: "Excluir oportunidade" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Gerar prévia do currículo" })).toBeNull();
  expect(deleteJobApplication).not.toHaveBeenCalled();
});

it("mostra o perfil com campos protegidos e sem permitir salvar", async () => {
  vi.mocked(listJobApplications).mockResolvedValue([]);
  vi.mocked(getCandidateProfile).mockResolvedValue(profile);
  render(<ConsultationView />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Meu perfil" }));
  const name = await screen.findByLabelText("Nome *") as HTMLInputElement;
  expect(name.value).toBe("Pessoa de Teste");
  expect(name.matches(":disabled")).toBe(true);
  expect(screen.queryByRole("button", { name: "Salvar meu perfil" })).toBeNull();
  expect(saveCandidateProfile).not.toHaveBeenCalled();
});

import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { JobApplicationObject } from "../../types/api";
import { correctJobDetails, updateJobDetails } from "../../api/jobDetails";
import JobDetailsEditor from "./JobDetailsEditor";
vi.mock("../../api/jobDetails", () => ({ correctJobDetails: vi.fn(), updateJobDetails: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const application: JobApplicationObject = {
  application_id: "application-test-1",
  job: {
    job_id: "job-test-1",
    title: "Analista de Dados",
    company: "Empresa de Teste",
    source: "Teste",
    url: null,
    location: "São Paulo",
    work_model: "HYBRID",
    employment_type: "CLT",
    description: "Oportunidade utilizada apenas nos testes.",
    requirements: ["SQL"],
    desirable_requirements: [],
    discovered_at: "2026-10-01T12:00:00Z",
    status: "DISCOVERED",
  },
  qualification: null,
  personalization: null,
  preparation: null,
  tracking: null,
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-01T12:00:00Z",
};


it("preserva acompanhamento e só corrige após confirmar; cancelar não salva", async () => {
  const app: JobApplicationObject = {...application, tracking:{job_id:application.job.job_id, current_status:"SCREENING", history:[], followup_count:0, last_followup_at:null}};
  const user = userEvent.setup(); const saved = vi.fn();
  vi.mocked(correctJobDetails).mockResolvedValue(app);
  render(<JobDetailsEditor application={app} onSaved={saved} />);
  await user.click(screen.getByText("Editar descrição e requisitos"));
  await user.click(screen.getByRole("button",{name:"Salvar requisitos da vaga"}));
  expect(correctJobDetails).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button",{name:"Cancelar correção"}));
  expect(correctJobDetails).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button",{name:"Salvar requisitos da vaga"}));
  vi.mocked(correctJobDetails).mockRejectedValueOnce(new Error("Falha"));
  await user.click(screen.getByRole("button",{name:"Confirmar correção do anúncio"}));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect((screen.getByLabelText("Requisitos obrigatórios — um por linha") as HTMLTextAreaElement).value).toBe("SQL");
  await user.click(screen.getByRole("button",{name:"Confirmar correção do anúncio"}));
  expect(saved).toHaveBeenCalledWith(app);
  expect(correctJobDetails).toHaveBeenLastCalledWith(app.application_id, {description:app.job.description,requirements:["SQL"],desirable_requirements:[]},app.updated_at);
  expect(updateJobDetails).not.toHaveBeenCalled();
});

it("mostra proposta de acentos sem salvar e impede um parágrafo inteiro como requisito", async () => {
  const user = userEvent.setup();
  render(<JobDetailsEditor application={{...application,job:{...application.job,description:"AgÃªncia contratando"}}} onSaved={vi.fn()} />);
  await user.click(screen.getByText("Editar descrição e requisitos"));
  await user.click(screen.getByRole("button",{name:"Conferir correção dos acentos"}));
  expect((screen.getByLabelText("Descrição da vaga") as HTMLTextAreaElement).value).toBe("AgÃªncia contratando");
  expect(updateJobDetails).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button",{name:"Aplicar correção nos campos"}));
  expect((screen.getByLabelText("Descrição da vaga") as HTMLTextAreaElement).value).toBe("Agência contratando");
  const requirements = screen.getByLabelText("Requisitos obrigatórios — um por linha");
  await user.clear(requirements);
  await user.paste("Texto longo ".repeat(30));
  await user.click(screen.getByRole("button",{name:"Salvar requisitos da vaga"}));
  expect((await screen.findByRole("alert")).textContent).toContain("Separe os requisitos");
  expect(updateJobDetails).not.toHaveBeenCalled();
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OpportunitySearch from "./OpportunitySearch";
import { searchOpportunities } from "../../api/opportunities";
import type { JobOpportunity } from "../../types/api";

vi.mock("../../api/opportunities", () => ({
  searchOpportunities: vi.fn(),
}));

const searchMock = vi.mocked(searchOpportunities);

const job: JobOpportunity = {
  job_id: "test-job-1",
  title: "Analista de Dados Júnior",
  company: "Empresa de Teste",
  source: "ADZUNA",
  url: "https://example.com/vaga",
  location: "São Paulo",
  work_model: "UNKNOWN",
  employment_type: "NAO_IDENTIFICADO",
  description: "Análise de dados com SQL.",
  requirements: [],
  desirable_requirements: [],
  discovered_at: "2026-10-01T12:00:00Z",
  status: "DISCOVERED",
};

describe("Busca de oportunidades", () => {
  beforeEach(() => {
    searchMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("envia os filtros e mostra a vaga retornada", async () => {
    searchMock.mockResolvedValue([job]);
    const user = userEvent.setup();

    render(<OpportunitySearch />);

    await user.type(
      screen.getByLabelText("Cargo ou palavras-chave"),
      "Analista de dados",
    );
    await user.type(
      screen.getByLabelText("Localização — opcional"),
      "São Paulo",
    );
    await user.click(
      screen.getByRole("button", { name: "Buscar oportunidades" }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Analista de Dados Júnior",
      }),
    ).toBeTruthy();

    expect(searchMock).toHaveBeenCalledExactlyOnceWith({
      query: "Analista de dados",
      country: "br",
      location: "São Paulo",
    });

    expect(
      screen
        .getByRole("link", { name: "Abrir anúncio da vaga" })
        .getAttribute("href"),
    ).toBe(job.url);
  });

  it("informa quando a busca não retorna vagas", async () => {
    searchMock.mockResolvedValue([]);
    const user = userEvent.setup();

    render(<OpportunitySearch />);

    await user.type(
      screen.getByLabelText("Cargo ou palavras-chave"),
      "Analista de dados",
    );
    await user.click(
      screen.getByRole("button", { name: "Buscar oportunidades" }),
    );

    expect(
      await screen.findByText(
        "Nenhuma oportunidade encontrada. Ajuste os filtros.",
      ),
    ).toBeTruthy();
  });

  it("preserva os filtros após falha e permite tentar novamente", async () => {
    searchMock.mockRejectedValueOnce(new Error("Falha de conexão"));
    searchMock.mockResolvedValueOnce([job]);
    const user = userEvent.setup();

    render(<OpportunitySearch />);

    const queryInput = screen.getByLabelText(
      "Cargo ou palavras-chave",
    ) as HTMLInputElement;

    await user.type(queryInput, "Analista de dados");
    await user.click(
      screen.getByRole("button", { name: "Buscar oportunidades" }),
    );

    expect((await screen.findByRole("alert")).textContent).toContain(
      "Não foi possível conectar ao servidor.",
    );
    expect(queryInput.value).toBe("Analista de dados");

    await user.click(
      screen.getByRole("button", { name: "Buscar oportunidades" }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Analista de Dados Júnior",
      }),
    ).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
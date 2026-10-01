import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Applications from "./Applications";
import { listJobApplications } from "../../api/applications";
import type { JobApplicationObject } from "../../types/api";

vi.mock("../../api/applications", () => ({
  listJobApplications: vi.fn(),
}));

const listMock = vi.mocked(listJobApplications);

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

describe("Listagem de candidaturas", () => {
  beforeEach(() => {
    listMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("mostra carregamento enquanto aguarda a API", async () => {
    let resolveRequest!: (value: JobApplicationObject[]) => void;

    listMock.mockImplementation(
      () =>
        new Promise<JobApplicationObject[]>((resolve) => {
          resolveRequest = resolve;
        }),
    );

    render(<Applications />);

    expect(screen.getByText("Consultando candidaturas...")).toBeTruthy();

    resolveRequest([]);

    expect(
      await screen.findByText("Nenhuma candidatura cadastrada"),
    ).toBeTruthy();
  });

  it("mostra estado vazio quando a API não possui candidaturas", async () => {
    listMock.mockResolvedValue([]);

    render(<Applications />);

    expect(
      await screen.findByText("Nenhuma candidatura cadastrada"),
    ).toBeTruthy();

    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("mostra a oportunidade retornada pela API", async () => {
    listMock.mockResolvedValue([application]);

    render(<Applications />);

    expect(await screen.findByText("Analista de Dados")).toBeTruthy();
    expect(screen.getByText("Empresa de Teste")).toBeTruthy();
    expect(screen.getByText("São Paulo")).toBeTruthy();
    expect(screen.getByText("Identificada")).toBeTruthy();
    expect(screen.getByText("Ainda não preparada")).toBeTruthy();
  });

  it("filtra por cargo, empresa e local", async () => {
    const user = userEvent.setup();
    listMock.mockResolvedValue([application]);

    render(<Applications />);

    await screen.findByText("Analista de Dados");

    const input = screen.getByRole("searchbox", {
      name: "Buscar por cargo, empresa ou local",
    });

    for (const query of ["analista", "empresa", "são paulo"]) {
      await user.clear(input);
      await user.type(input, query);

      expect(screen.getByText("Analista de Dados")).toBeTruthy();
    }

    await user.clear(input);
    await user.type(input, "sem correspondência");

    expect(
      screen.getByText("Nenhuma candidatura corresponde à sua busca."),
    ).toBeTruthy();

    expect(screen.queryByRole("table")).toBeNull();

    await user.clear(input);

    expect(screen.getByText("Analista de Dados")).toBeTruthy();
  });

  it("mostra erro e permite tentar novamente sem confundir com lista vazia", async () => {
    const user = userEvent.setup();

    listMock
      .mockRejectedValueOnce(new Error("Falha de conexão"))
      .mockResolvedValueOnce([application]);

    render(<Applications />);

    const alert = await screen.findByRole("alert");

    expect(alert.textContent).toContain(
      "Não foi possível carregar as candidaturas",
    );

    expect(
      screen.queryByText("Nenhuma candidatura cadastrada"),
    ).toBeNull();

    await user.click(
      screen.getByRole("button", { name: "Tentar novamente" }),
    );

    expect(await screen.findByText("Analista de Dados")).toBeTruthy();

    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeNull();
    });

    expect(listMock).toHaveBeenCalledTimes(2);
  });
});
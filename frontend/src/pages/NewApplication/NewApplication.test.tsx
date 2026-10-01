import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NewApplication from "./NewApplication";
import { createJobApplication } from "../../api/applications";

vi.mock("../../api/applications", () => ({
  createJobApplication: vi.fn(),
}));

const createMock = vi.mocked(createJobApplication);

async function fillRequiredFields() {
  const user = userEvent.setup();

  await user.type(screen.getByLabelText("Cargo *"), "Analista de Dados");
  await user.type(screen.getByLabelText("Empresa *"), "Empresa de Teste");
  await user.type(screen.getByLabelText("Origem da vaga *"), "Site da empresa");

  return user;
}

describe("Cadastro de oportunidade", () => {
  beforeEach(() => {
    createMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("impede cadastro sem os campos obrigatórios", async () => {
    const user = userEvent.setup();

    render(<NewApplication onViewApplications={vi.fn()} />);

    await user.click(
      screen.getByRole("button", { name: "Cadastrar oportunidade" }),
    );

    expect(createMock).not.toHaveBeenCalled();
  });

  it("envia os dados e confirma o cadastro retornado pela API", async () => {
    const onViewApplications = vi.fn();

    createMock.mockImplementation(async (request) => ({
      ...request,
      qualification: null,
      personalization: null,
      preparation: null,
      tracking: null,
      created_at: "2026-10-01T12:00:00Z",
      updated_at: "2026-10-01T12:00:00Z",
    }));

    render(
      <NewApplication onViewApplications={onViewApplications} />,
    );

    const user = await fillRequiredFields();

    await user.type(
      screen.getByLabelText("Requisitos obrigatórios"),
      "SQL{Enter}{Enter}Power BI",
    );

    await user.click(
      screen.getByRole("button", { name: "Cadastrar oportunidade" }),
    );

    expect(
      await screen.findByText("Oportunidade cadastrada!"),
    ).toBeTruthy();

    expect(createMock).toHaveBeenCalledTimes(1);

    const request = createMock.mock.calls[0][0];

    expect(request.application_id).toBeTruthy();
    expect(request.job.job_id).toBeTruthy();
    expect(request.job.title).toBe("Analista de Dados");
    expect(request.job.company).toBe("Empresa de Teste");
    expect(request.job.source).toBe("Site da empresa");
    expect(request.job.requirements).toEqual(["SQL", "Power BI"]);
    expect(request.job.status).toBe("DISCOVERED");
    expect(request.job.url).toBeNull();
    expect(request.job.work_model).toBe("UNKNOWN");

    await user.click(
      screen.getByRole("button", { name: "Ver candidaturas" }),
    );

    expect(onViewApplications).toHaveBeenCalledTimes(1);
  });

  it("mostra erro de conexão e preserva os campos preenchidos", async () => {
    createMock.mockRejectedValue(new Error("Falha de conexão"));

    render(<NewApplication onViewApplications={vi.fn()} />);

    const user = await fillRequiredFields();

    await user.click(
      screen.getByRole("button", { name: "Cadastrar oportunidade" }),
    );

    const alert = await screen.findByRole("alert");

    expect(alert.textContent).toContain(
      "Não foi possível confirmar o cadastro",
    );

    expect(
      (screen.getByLabelText("Cargo *") as HTMLInputElement).value,
    ).toBe("Analista de Dados");

    expect(screen.queryByText("Oportunidade cadastrada!")).toBeNull();

    expect(
      (
        screen.getByRole("button", {
          name: "Cadastrar oportunidade",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
  });
});
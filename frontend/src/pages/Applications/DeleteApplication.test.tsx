import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DeleteApplication from "./DeleteApplication";
import { deleteJobApplication } from "../../api/applications";

vi.mock("../../api/applications", () => ({ deleteJobApplication: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const props = { applicationId: "chosen-id", title: "Analista", company: "Empresa" };
describe("Confirmação de exclusão", () => {
  it("permite cancelar antes de chamar a API", async () => {
    const user = userEvent.setup();
    render(<DeleteApplication {...props} onDeleted={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Excluir oportunidade" }));
    expect(deleteJobApplication).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Manter oportunidade" }));
    expect(screen.queryByRole("button", { name: "Confirmar exclusão" })).toBeNull();
    expect(deleteJobApplication).not.toHaveBeenCalled();
  });
  it("preserva a vaga e informa quando a API falha", async () => {
    const user = userEvent.setup();
    const onDeleted = vi.fn();
    vi.mocked(deleteJobApplication).mockRejectedValue(new Error("offline"));
    render(<DeleteApplication {...props} onDeleted={onDeleted} />);
    await user.click(screen.getByRole("button", { name: "Excluir oportunidade" }));
    await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Não foi possível confirmar");
    expect(onDeleted).not.toHaveBeenCalled();
  });
  it("não remove da tela se a resposta não confirmar a exclusão", async () => {
    const user = userEvent.setup();
    const onDeleted = vi.fn();
    vi.mocked(deleteJobApplication).mockResolvedValue({ application_id: "chosen-id", deleted: false });
    render(<DeleteApplication {...props} onDeleted={onDeleted} />);
    await user.click(screen.getByRole("button", { name: "Excluir oportunidade" }));
    await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
    await screen.findByRole("alert");
    expect(onDeleted).not.toHaveBeenCalled();
  });
});

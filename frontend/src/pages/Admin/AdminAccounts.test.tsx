import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AdminAccounts from "./AdminAccounts";
import { listAccounts, changeAccess, deleteAccount } from "../../api/admin";
import type { ManagedAccount } from "../../api/admin";

vi.mock("../../api/admin", () => ({ listAccounts: vi.fn(), changeAccess: vi.fn(), deleteAccount: vi.fn() }));
const owner: ManagedAccount = { id: "owner", name: "Owner", email: "owner@example.invalid", role: "admin", state: "active" };
const member: ManagedAccount = { id: "member", name: "Member", email: "member@example.invalid", role: "user", state: "pending" };
afterEach(() => { cleanup(); vi.resetAllMocks(); });

async function load() {
  vi.mocked(listAccounts).mockResolvedValue([owner, member]);
  render(<AdminAccounts />);
  return within(await screen.findByRole("article", { name: `Conta ${member.email}` }));
}

describe("Controle administrativo", () => {
  it("protege a conta do administrador e só autoriza após confirmar", async () => {
    const row = await load();
    const admin = within(screen.getByRole("article", { name: `Conta ${owner.email}` }));
    expect(admin.queryByRole("button", { name: "Excluir conta" })).toBeNull();
    const user = userEvent.setup();
    await user.click(row.getByRole("button", { name: "Autorizar acesso" }));
    expect(changeAccess).not.toHaveBeenCalled();
    vi.mocked(changeAccess).mockResolvedValue({ ...member, state: "active" });
    await user.click(row.getByRole("button", { name: "Confirmar alteração de acesso" }));
    expect(changeAccess).toHaveBeenCalledWith(member.id, "authorize");
    expect(await row.findByRole("button", { name: "Bloquear acesso" })).toBeTruthy();
    expect(screen.getByRole("status").textContent).toContain("Autorizado");
  });
  it("cancelar não exclui e exclusão exige digitar o e-mail correto", async () => {
    const row = await load();
    const user = userEvent.setup();
    await user.click(row.getByRole("button", { name: "Excluir conta" }));
    expect((row.getByRole("button", { name: "Confirmar exclusão definitiva" }) as HTMLButtonElement).disabled).toBe(true);
    await user.click(row.getByRole("button", { name: "Cancelar" }));
    expect(deleteAccount).not.toHaveBeenCalled();
    await user.click(row.getByRole("button", { name: "Excluir conta" }));
    await user.type(row.getByLabelText("Digite o e-mail da conta para confirmar"), member.email);
    vi.mocked(deleteAccount).mockResolvedValue({ deleted: true, user_id: member.id });
    await user.click(row.getByRole("button", { name: "Confirmar exclusão definitiva" }));
    expect(deleteAccount).toHaveBeenCalledWith(member.id, member.email);
    expect(await screen.findByText(`Conta de ${member.email} excluída.`)).toBeTruthy();
    expect(screen.queryByRole("article", { name: `Conta ${member.email}` })).toBeNull();
    expect(screen.getByRole("article", { name: `Conta ${owner.email}` })).toBeTruthy();
  });
  it("preserva a conta quando a API falha e permite atualizar", async () => {
    const row = await load();
    const user = userEvent.setup();
    await user.click(row.getByRole("button", { name: "Autorizar acesso" }));
    vi.mocked(changeAccess).mockRejectedValue(new Error("offline"));
    await user.click(row.getByRole("button", { name: "Confirmar alteração de acesso" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Atualize");
    expect(row.getByText("Aguardando autorização")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Atualizar lista" }));
    expect(listAccounts).toHaveBeenCalledTimes(2);
    expect(await screen.findByRole("article", { name: `Conta ${member.email}` })).toBeTruthy();
  });
});

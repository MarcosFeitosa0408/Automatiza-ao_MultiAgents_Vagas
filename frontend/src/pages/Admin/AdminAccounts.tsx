import AdminMembers from "./AdminMembers";
import AdminQuestions from "./AdminQuestions";
import { useEffect, useRef, useState } from "react";
import { changeAccess, deleteAccount, listAccounts } from "../../api/admin";
import type { AccessAction, ManagedAccount } from "../../api/admin";
import { ApiError } from "../../api/client";

const labels = { pending: "Aguardando autorização", active: "Autorizado", blocked: "Bloqueado" };
const actions: Record<AccessAction, string> = { authorize: "Autorizar acesso", block: "Bloquear acesso", reactivate: "Reativar acesso" };
type Selection = { account: ManagedAccount; action: AccessAction | "delete" };

function message(error: unknown) {
  if (error instanceof ApiError) {
    const detail = (error.detail as { detail?: unknown } | null)?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Não foi possível confirmar a operação. Atualize a lista antes de tentar novamente.";
}

export default function AdminAccounts() {
  const [accounts, setAccounts] = useState<ManagedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState("");
  const [selection, setSelection] = useState<Selection | null>(null);
  const [email, setEmail] = useState("");
  const pending = useRef(false);

  useEffect(() => {
    let mounted = true;
    listAccounts().then((rows) => { if (mounted) setAccounts(rows); })
      .catch((cause) => { if (mounted) setError(message(cause)); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  async function refresh() {
    if (pending.current) return;
    pending.current = true;
    setLoading(true); setError(null); setSelection(null);
    try { setAccounts(await listAccounts()); }
    catch (cause) { setError(message(cause)); }
    finally { setLoading(false); pending.current = false; }
  }

  function select(account: ManagedAccount, action: Selection["action"]) {
    setSelection({ account, action }); setEmail(""); setError(null); setSuccess("");
  }

  async function confirm() {
    if (!selection || pending.current) return;
    const { account, action } = selection;
    pending.current = true; setBusy(true); setError(null); setSuccess("");
    try {
      if (action === "delete") {
        const result = await deleteAccount(account.id, email);
        if (!result.deleted || result.user_id !== account.id) throw new Error("Exclusão não confirmada");
        setAccounts((rows) => rows.filter((row) => row.id !== account.id));
        setSuccess(`Conta de ${account.email} excluída.`);
      } else {
        const result = await changeAccess(account.id, action);
        const expected = action === "block" ? "blocked" : "active";
        if (result.id !== account.id || result.state !== expected) throw new Error("Alteração não confirmada");
        setAccounts((rows) => rows.map((row) => row.id === account.id ? result : row));
        setSuccess(`Acesso de ${account.email}: ${labels[result.state]}.`);
      }
      setSelection(null); setEmail("");
    } catch (cause) { setError(message(cause)); }
    finally { pending.current = false; setBusy(false); }
  }

  return <main className="dashboard" aria-labelledby="admin-title">
    <section className="dashboard-panel">
      <h1 id="admin-title">Administrar acessos</h1>
      <p>Autorize novos cadastros. Bloquear encerra as sessões e preserva os dados; excluir apaga a conta, o perfil e as oportunidades salvas.</p>
      <button className="secondary-button" type="button" disabled={loading || busy} onClick={refresh}>Atualizar lista</button>
      {loading && <p role="status">Carregando contas...</p>}
      {error && <p role="alert" className="dashboard-error">{error}</p>}
      {success && <p role="status">{success}</p>}
      {!loading && accounts.length === 0 && !error && <p>Nenhuma conta encontrada.</p>}
      {!loading && accounts.map((account) => <article className="dashboard-panel" key={account.id} aria-label={`Conta ${account.email}`}>
        <h2>{account.name}</h2><p>{account.email}</p><p>{labels[account.state]}</p>
        {account.role === "admin" ? <p>Administrador — conta protegida.</p> : <>
          <button className="primary-button" type="button" disabled={busy} onClick={() => select(account, account.state === "pending" ? "authorize" : account.state === "active" ? "block" : "reactivate")}>
            {actions[account.state === "pending" ? "authorize" : account.state === "active" ? "block" : "reactivate"]}
          </button>{" "}
          <button className="secondary-button" type="button" disabled={busy} onClick={() => select(account, "delete")}>Excluir conta</button>
        </>}
        {selection?.account.id === account.id && <div role="group" aria-label={`Confirmar operação em ${account.email}`}>
          <p>{selection.action === "delete" ? "Esta exclusão é definitiva na plataforma. Backups anteriores não são apagados por este botão." : selection.action === "block" ? "Bloquear esta pessoa? As sessões serão encerradas e seus dados preservados." : "Liberar o acesso desta pessoa à plataforma?"}</p>
          {selection.action === "delete" && <>
            <label htmlFor="delete-account-email">Digite o e-mail da conta para confirmar</label>
            <input id="delete-account-email" value={email} onChange={(event) => setEmail(event.target.value)} disabled={busy} autoComplete="off" />
          </>}
          <button className="primary-button" type="button" disabled={busy || (selection.action === "delete" && email.trim().toLowerCase() !== account.email)} onClick={confirm}>
            {busy ? "Aguarde..." : selection.action === "delete" ? "Confirmar exclusão definitiva" : "Confirmar alteração de acesso"}
          </button>{" "}
          <button className="secondary-button" type="button" disabled={busy} onClick={() => setSelection(null)}>Cancelar</button>
        </div>}
      </article>)}
    </section>
    <AdminMembers />
    <AdminQuestions />
  </main>;
}

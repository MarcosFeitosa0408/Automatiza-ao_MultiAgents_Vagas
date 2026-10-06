import { useRef, useState } from "react";
import { deleteHelp, exportHelp, helpHistory, reviewHelp } from "../../api/help";
import type { HelpItem } from "../../api/help";

export default function AdminQuestions() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<HelpItem[]>([]);
  const [week, setWeek] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState<string | null>(null);
  const pending = useRef(false);

  async function load(selected?: string, page = 0) {
    const result = await helpHistory(selected || undefined, page);
    setItems(result.items); setWeek(result.week); setTotal(result.total); setOffset(page);
  }
  async function run(action: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError("");
    try { await action(); }
    catch { setError("Não foi possível concluir. Confira a conexão e tente novamente."); }
    finally { pending.current = false; setBusy(false); }
  }
  function edit(id: string, change: Partial<HelpItem>) {
    setItems(current => current.map(item => item.id === id ? { ...item, ...change } : item));
  }
  return <section className="dashboard-panel help-admin">
    <button type="button" className="secondary-button" aria-expanded={open} disabled={busy} onClick={() => {
      setOpen(!open); if (!open) void run(() => load());
    }}>🤖 Dúvidas para melhoria</button>
    {open && <div>
      <h2>Revisão semanal de dúvidas</h2>
      <p>As respostas aqui são rascunhos revisados. Exporte o histórico para preparar uma atualização da base do robô. Salvar uma resposta não publica a orientação automaticamente.</p>
      <label htmlFor="help-week">Segunda-feira da semana</label>
      <input id="help-week" type="date" value={week} disabled={busy} onChange={event => setWeek(event.target.value)} />
      <button type="button" disabled={busy} onClick={() => void run(() => load(week))}>Consultar semana</button>
      <button type="button" disabled={busy || !week} onClick={() => void run(async () => {
        const data = await exportHelp(week);
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
        const link = document.createElement("a"); link.href = url; link.download = `duvidas-${week}.json`;
        document.body.append(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      })}>Exportar semana</button>
      {error && <p role="alert">{error}</p>}
      {busy && <p role="status">Aguarde...</p>}
      <p>{total} dúvida(s) nesta semana. A exportação não inclui a identidade das contas. Revise o texto antes de compartilhar.</p>
      {!busy && !items.length && <p>Nenhuma dúvida nesta página.</p>}
      {items.map(item => <article className="help-question" key={item.id}>
        <p><strong>{item.question}</strong></p>
        <label htmlFor={`state-${item.id}`}>Estado</label>
        <select id={`state-${item.id}`} value={item.state} disabled={busy} onChange={event => edit(item.id, { state: event.target.value as HelpItem["state"] })}>
          <option value="pending">Pendente</option><option value="reviewing">Em revisão</option><option value="answered">Respondida</option>
        </select>
        <label htmlFor={`answer-${item.id}`}>Resposta revisada</label>
        <textarea id={`answer-${item.id}`} maxLength={4000} value={item.answer} disabled={busy} onChange={event => edit(item.id, { answer: event.target.value })} />
        <button type="button" disabled={busy || (item.state === "answered" && !item.answer.trim())} onClick={() => void run(async () => {
          await reviewHelp(item.id, item.state, item.answer);
          await load(week, offset);
        })}>Salvar revisão</button>
        {confirm === item.id ? <div>
          <p>Excluir esta dúvida do histórico? O limite usado pelo candidato permanece.</p>
          <button type="button" disabled={busy} onClick={() => void run(async () => { await deleteHelp(item.id); setConfirm(null); await load(week, offset); })}>Confirmar exclusão</button>
          <button type="button" disabled={busy} onClick={() => setConfirm(null)}>Cancelar</button>
        </div> : <button type="button" disabled={busy} onClick={() => setConfirm(item.id)}>Excluir dúvida</button>}
      </article>)}
      <button type="button" disabled={busy || offset === 0} onClick={() => void run(() => load(week, Math.max(0, offset - 100)))}>Página anterior</button>
      <button type="button" disabled={busy || offset + 100 >= total} onClick={() => void run(() => load(week, offset + 100))}>Próxima página</button>
    </div>}
  </section>;
}

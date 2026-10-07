import { useId, useRef, useState } from "react";
import { recordProgress } from "../../api/progress";
import { ApiError } from "../../api/client";
import type { JobApplicationObject, JobStatus } from "../../types/api";
const stages: [JobStatus,string][] = [
  ["APPLIED","Enviei minha candidatura"],["SCREENING","Estou em triagem"],["INTERVIEW","Fui chamado para entrevista"],
  ["FINAL","Cheguei à etapa final"],["OFFER","Recebi uma proposta"],["HIRED","Fui contratado"],
  ["REJECTED","Não fui selecionado"],["WITHDRAWN","Desisti desta candidatura"],["NO_RESPONSE","Ainda não recebi resposta"],["APPLICATION_FAILED","O envio falhou"],
];
const labels=Object.fromEntries(stages);
export default function ProgressPanel({application,onSaved}:{application:JobApplicationObject;onSaved:(value:JobApplicationObject)=>void}) {
  const [selected,setSelected]=useState<JobStatus>("APPLIED");
  const [note,setNote]=useState(""); const [confirm,setConfirm]=useState(false);
  const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  const pending=useRef(false);const id=useId();
  const current=application.tracking?.current_status ?? null;
  async function save() {
    if(pending.current || !confirm)return;
    pending.current=true;setBusy(true);setError("");
    try {onSaved(await recordProgress(application.application_id,selected,current,note));setConfirm(false);setNote("");}
    catch(cause) {const detail=cause instanceof ApiError ? (cause.detail as {detail?:unknown})?.detail : null;setError(typeof detail==="string"?detail:"Não foi possível confirmar o registro. Atualize a lista antes de tentar novamente.");}
    finally {pending.current=false;setBusy(false);}
  }
  return <details className="progress-panel">
    <summary>Acompanhar candidatura</summary>
    <p>Registre o que aconteceu no site da empresa ou no contato com o recrutador. Este controle não envia currículo nem candidatura.</p>
    <p>Etapa atual: {current ? labels[current] ?? current : "Ainda sem acompanhamento"}.</p>
    <label htmlFor={`${id}-stage`}>Etapa que aconteceu</label>
    <select id={`${id}-stage`} value={selected} disabled={busy || confirm} onChange={event=>setSelected(event.target.value as JobStatus)}>{stages.map(([value,label])=><option key={value} value={value} disabled={value===current}>{label}</option>)}</select>
    <label htmlFor={`${id}-note`}>Observação opcional (até 1.000 caracteres)</label>
    <textarea id={`${id}-note`} rows={3} maxLength={1000} value={note} disabled={busy || confirm} onChange={event=>setNote(event.target.value)} />
    <p>As datas do histórico indicam quando você registrou a etapa. Só marque fatos reais; é possível registrar diretamente a etapa recebida, sem inventar etapas anteriores. Registros anteriores permanecem no histórico.</p>
    {error && <p role="alert">{error}</p>}
    {confirm ? <div><p>Confirma que “{labels[selected]}” aconteceu para {application.job.title} · {application.job.company}?</p>
      <button type="button" disabled={busy} onClick={()=>void save()}>{busy?"Salvando...":"Confirmar registro"}</button>
      <button type="button" disabled={busy} onClick={()=>setConfirm(false)}>Cancelar registro</button>
    </div> : <button type="button" disabled={busy || selected===current} onClick={()=>{setError("");setConfirm(true);}}>Registrar etapa</button>}
    {application.tracking && <details><summary>Ver histórico das etapas</summary><ol>{application.tracking.history.map((event,index)=><li key={index}>{labels[event.status] ?? event.status} — registrado em {new Date(event.occurred_at).toLocaleString("pt-BR")}<p>{event.note}</p></li>)}</ol></details>}
  </details>;
}

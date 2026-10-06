import { useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { askHelp, forwardHelp, helpInfo } from "../api/help";
import type { HelpQuota, HelpReply } from "../api/help";
import { ApiError } from "../api/client";

function errorText(error: unknown) {
  const detail = error instanceof ApiError ? (error.detail as {detail?:unknown})?.detail : null;
  return typeof detail === "string" ? detail : "Não foi possível consultar a ajuda. Tente novamente.";
}

export default function HelpRobot() {
  const [open,setOpen]=useState(false);
  const [question,setQuestion]=useState("");
  const [asked,setAsked]=useState("");
  const [reply,setReply]=useState<HelpReply|null>(null);
  const [quota,setQuota]=useState<HelpQuota|null>(null);
  const [suggestions,setSuggestions]=useState<string[]>([]);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [consent,setConsent]=useState(false);
  const [sent,setSent]=useState(false);
  const requestId=useRef("");
  const pending=useRef(false);
  const id=useId();

  async function toggle() {
    setOpen(!open);
    if (!open && !quota) {
      try { const info=await helpInfo();setQuota(info);setSuggestions(info.suggestions); }
      catch(cause){setError(errorText(cause));}
    }
  }
  async function ask(text:string) {
    if(pending.current || text.trim().length<3)return;
    pending.current=true;setBusy(true);setError("");setNotice("");setReply(null);setConsent(false);setSent(false);
    try {const result=await askHelp(text.trim());setAsked(text.trim());setReply(result);setQuota(result);requestId.current=crypto.randomUUID();}
    catch(cause){setError(errorText(cause));}
    finally {pending.current=false;setBusy(false);}
  }
  async function submit(event:FormEvent){event.preventDefault();await ask(question);}
  async function forward() {
    if(pending.current || !consent || !reply || reply.known || sent)return;
    pending.current=true;setBusy(true);setError("");
    try {const result=await forwardHelp(asked,requestId.current);setQuota(result);setSent(true);setNotice(result.duplicate?"Essa dúvida já foi encaminhada. Nenhum novo envio foi contado.":"Dúvida encaminhada para melhoria. Obrigado por ajudar!");}
    catch(cause){setError(errorText(cause));}
    finally{pending.current=false;setBusy(false);}
  }
  return <section className="dashboard-panel help-robot" aria-label="Robô de dúvidas">
    <button className="secondary-button" type="button" aria-expanded={open} aria-controls={id} onClick={toggle}>
      <span aria-hidden="true">🤖</span> Tirar dúvidas da plataforma
    </button>
    {open && <div id={id}>
      <h2>Olá! Como posso orientar você?</h2>
      <p>Respondo sobre as funções da plataforma, com uma base revisada. Não consulto seu perfil, não executo ações e não sou uma conversa de assuntos gerais.</p>
      <p>Salvar, excluir ou enviar continuam sob seu controle. Não digite senhas, dados pessoais nem conteúdo do currículo.</p>
      {suggestions.length>0 && <div className="help-suggestions">{suggestions.map(text=><button type="button" className="secondary-button" disabled={busy} key={text} onClick={()=>{setQuestion(text);void ask(text);}}>{text}</button>)}</div>}
      <form onSubmit={submit}>
        <label htmlFor={`${id}-question`}>Sua dúvida sobre a plataforma</label>
        <textarea id={`${id}-question`} value={question} maxLength={600} minLength={3} required rows={3} disabled={busy} onChange={event=>{setQuestion(event.target.value);setReply(null);setError("");setNotice("");setConsent(false);setSent(false);}} />
        <button className="primary-button" disabled={busy || question.trim().length<3} type="submit">{busy?"Aguarde...":"Perguntar ao robô"}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {reply && <div className="help-reply" role="status"><p><span aria-hidden="true">🤖 </span>{reply.answer}</p></div>}
      {reply && !reply.known && !sent && <div className="help-forward">
        <p>Somente uma dúvida que você confirmar será guardada no histórico administrativo. O envio para melhoria não é um atendimento com prazo de resposta.</p>
        <label><input type="checkbox" checked={consent} disabled={busy} onChange={event=>setConsent(event.target.checked)} /> Conferi que a dúvida não contém informações pessoais ou segredos e quero encaminhá-la ao administrador.</label>
        <button type="button" className="secondary-button" onClick={forward} disabled={busy || !consent || quota?.remaining===0}>Enviar dúvida para melhoria</button>
      </div>}
      {quota && <p className="form-help">{quota.remaining===null?"Administrador: encaminhamentos sem limite semanal.":`${quota.remaining} de 3 encaminhamentos disponíveis nesta semana.`} Renovação: {new Date(quota.renews_at).toLocaleString("pt-BR",{timeZone:"America/Sao_Paulo"})}, horário de São Paulo. As respostas conhecidas e o guia continuam disponíveis.</p>}
      <button className="secondary-button" type="button" onClick={()=>setOpen(false)}>Fechar dúvidas</button>
    </div>}
  </section>;
}

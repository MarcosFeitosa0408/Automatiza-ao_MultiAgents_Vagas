import { useId, useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { generateResumePreview } from "../../api/resume";
import RobotStatus from "../../components/RobotStatus";
import { buildCoverLetter } from "./buildCoverLetter";
import type { CoverLetterDraft } from "./buildCoverLetter";
import { printCoverLetter } from "./printCoverLetter";
import "./CoverLetterPanel.css";

function describeError(cause: unknown): string {
  if (cause instanceof ApiError && cause.detail && typeof cause.detail === "object") {
    const body = cause.detail as Record<string, unknown>;
    const message = typeof body.message === "string" ? body.message : body.detail;
    if (typeof message === "string") return message.replace("gerar o currículo", "gerar a carta");
  }
  return "Não foi possível preparar a carta. Confira seu perfil e os requisitos da vaga e tente novamente.";
}

export default function CoverLetterPanel({ applicationId }: { applicationId: string }) {
  const panelId = useId();
  const [draft, setDraft] = useState<CoverLetterDraft | null>(null);
  const [body, setBody] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const pending = useRef(false);
  const documentRef = useRef<HTMLElement>(null);

  async function generate() {
    if (pending.current) return;
    pending.current = true;
    setLoading(true);
    setExpanded(true);
    setError("");
    setNotice("");
    setReviewed(false);
    try {
      const preview = await generateResumePreview(applicationId);
      const letter = buildCoverLetter(preview);
      setDraft(letter);
      setBody(letter.body);
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      pending.current = false;
      setLoading(false);
    }
  }

  async function copy() {
    if (!draft || !reviewed || !body.trim()) return;
    setNotice("");
    setError("");
    try {
      await navigator.clipboard.writeText([draft.name, ...draft.contacts, "Carta de Apresentação", body].filter(Boolean).join("\n\n"));
      setNotice("Carta copiada. Você escolhe onde e quando enviar.");
    } catch {
      setError("Não foi possível copiar automaticamente. Selecione o texto no campo da carta e copie manualmente.");
    }
  }

  function savePdf() {
    if (!draft || !reviewed || !body.trim() || !documentRef.current) return;
    setError("");
    try {
      printCoverLetter(documentRef.current, draft.name);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível abrir o PDF da carta.");
    }
  }

  return (
    <div className="cover-letter-panel">
      <button className="secondary-button" type="button" disabled={loading} aria-expanded={expanded} aria-controls={panelId} onClick={() => {
        if (draft) setExpanded(!expanded);
        else void generate();
      }}>
        {loading ? "Preparando carta..." : "Carta de Apresentação"}
      </button>
      {expanded && <section id={panelId} aria-label="Carta de Apresentação da candidatura" className="cover-letter-content" aria-busy={loading}>
        {loading && <RobotStatus working message="Preparando sua carta com os dados do perfil e da vaga…" />}
        {error && <p role="alert">{error}</p>}
        {draft && <>
          <h3>Carta para {draft.company || "a empresa cadastrada"}</h3>
          <p className="cover-letter-help">O texto usa as informações do seu perfil e as competências relacionadas à vaga. Revise e ajuste antes de usar. A carta fica nesta tela: copie ou salve em PDF antes de sair.</p>
          {draft.warnings.length > 0 && <ul className="cover-letter-warnings">{draft.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
          {draft.unsupportedRequirements.length > 0 && <p className="cover-letter-help">Requisitos sem correspondência na análise: {draft.unsupportedRequirements.join(" · ")}. Eles não foram acrescentados como qualificações na carta.</p>}
          <label htmlFor={`${panelId}-body`}>Texto da carta — você pode editar</label>
          <textarea id={`${panelId}-body`} value={body} rows={15} disabled={loading} onChange={(event) => {
            setBody(event.target.value);
            setReviewed(false);
            setNotice("");
            setError("");
          }} />
          <details>
            <summary>Ver documento para PDF</summary>
            <article className="cover-letter-document" ref={documentRef}>
              <header>
                {draft.name && <h2>{draft.name}</h2>}
                {draft.contacts.map((contact) => <p key={contact}>{contact}</p>)}
              </header>
              <h3>Carta de Apresentação</h3>
              {body.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}
            </article>
          </details>
          <label className="cover-letter-review">
            <input type="checkbox" checked={reviewed} disabled={loading} onChange={(event) => setReviewed(event.target.checked)} />
            {" "}Revisei a carta e confirmo que as informações estão corretas.
          </label>
          <div className="cover-letter-actions">
            <button className="secondary-button" type="button" disabled={loading || !reviewed || !body.trim()} onClick={() => void copy()}>Copiar carta</button>
            <button className="primary-button" type="button" disabled={loading || !reviewed || !body.trim()} onClick={savePdf}>Salvar carta em PDF</button>
          </div>
          <p className="cover-letter-help">Na janela de impressão, escolha “Salvar como PDF”, papel A4 e desative cabeçalhos e rodapés. Confira as páginas antes de salvar. A carta não é enviada à empresa automaticamente.</p>
          {notice && <p role="status">{notice}</p>}
          <div className="cover-letter-actions">
            <button className="secondary-button" type="button" disabled={loading} onClick={() => void generate()}>Gerar nova carta</button>
            <button className="secondary-button" type="button" disabled={loading} onClick={() => setExpanded(false)}>Fechar carta</button>
          </div>
          <p className="cover-letter-help">Gerar nova carta busca o perfil atualizado e substitui o texto editado nesta tela.</p>
        </>}
      </section>}
    </div>
  );
}

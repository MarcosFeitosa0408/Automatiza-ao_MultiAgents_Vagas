import RobotStatus from "../../components/RobotStatus";
import { useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { generateResumePreview, translateResumePreview } from "../../api/resume";
import type { ResumePreview, ResumeLanguage } from "../../api/resume";
import { printResume } from "./printResume";

const headings = {
  "pt-BR": {summary: "Resumo profissional", skills: "Competências", experience: "Experiência profissional", projects: "Projetos", education: "Formação", languages: "Idiomas", portuguese: "Português", english: "Inglês", current: "Atual"},
  "en-US": {summary: "Professional summary", skills: "Skills", experience: "Professional experience", projects: "Projects", education: "Education", languages: "Languages", portuguese: "Portuguese", english: "English", current: "Present"},
  es: {summary: "Resumen profesional", skills: "Competencias", experience: "Experiencia profesional", projects: "Proyectos", education: "Formación", languages: "Idiomas", portuguese: "Portugués", english: "Inglés", current: "Actualidad"},
};

type ResumePanelProps = {
  applicationId: string;
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.detail;

    if (body && typeof body === "object") {
      const data = body as Record<string, unknown>;

      if (typeof data.message === "string") return data.message;
      if (typeof data.detail === "string") return data.detail;
    }

    return "Não foi possível gerar a prévia. Confira o perfil e os requisitos da vaga.";
  }

  return "Não foi possível conectar ao servidor.";
}

export default function ResumePanel({
  applicationId,
}: ResumePanelProps) {
  const [preview, setPreview] = useState<ResumePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submitting = useRef(false);
  const documentRef = useRef<HTMLElement | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const [original, setOriginal] = useState<ResumePreview | null>(null);
  const [language, setLanguage] = useState<ResumeLanguage>("pt-BR");
  const [translating, setTranslating] = useState(false);
  const labels = headings[preview?.language ?? "pt-BR"];

  async function translate() {
    if (submitting.current || language === "pt-BR") return;
    submitting.current = true;
    setTranslating(true);
    setError(null);
    setPdfError(null);
    try {
      setPreview(await translateResumePreview(applicationId, language));
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      submitting.current = false;
      setTranslating(false);
    }
  }

  function savePdf() {
    if (!preview || !documentRef.current) return;
    setPdfError(null);
    try {
      printResume(documentRef.current, preview.name, preview.language ?? "pt-BR");
    } catch (cause) {
      setPdfError(cause instanceof Error ? cause.message : "Não foi possível salvar o PDF.");
    }
  }

  async function generate() {
    if (submitting.current) return;

    submitting.current = true;
    setLoading(true);
    setError(null);
    setPreview(null);
    setPdfError(null);

    try {
      const generated = await generateResumePreview(applicationId);
      setPreview(generated);
      setOriginal(generated);
      setLanguage("pt-BR");
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  }

  return (
    <div className="resume-panel">
      <button
        className="secondary-button"
        type="button"
        onClick={generate}
        disabled={loading || translating}
      >
        {loading ? "Gerando..." : "Gerar prévia do currículo"}
      </button>

      {loading && <RobotStatus working message="Organizando seu currículo…" />}
      {error && <p role="alert">{error}</p>}

      {preview && (
        <div>
          <RobotStatus message="Prévia gerada. Confira o conteúdo abaixo." />

          <div className="resume-translation">
            <label htmlFor={`resume-language-${applicationId}`}>Idioma do currículo</label>
            <select id={`resume-language-${applicationId}`} value={language} disabled={translating} onChange={(event) => {
              const selected = event.target.value as ResumeLanguage;
              setLanguage(selected);
              setError(null);
              if (selected === "pt-BR" && original) setPreview(original);
            }}>
              <option value="pt-BR">Português do Brasil</option>
              <option value="en-US">Inglês</option>
              <option value="es">Espanhol</option>
            </select>
            {language !== "pt-BR" && <>
              <p>Ao clicar em Traduzir currículo, os textos profissionais serão enviados ao DeepL. Os campos de nome, contato, links, empresas e datas ficam fora do envio; confira se há informações pessoais nas descrições. A tradução não altera seu perfil nem a vaga.</p>
              <button type="button" className="secondary-button" disabled={translating || language === preview.language} onClick={translate}>
                {translating ? "Traduzindo..." : "Traduzir currículo"}
              </button>
            </>}
            {translating && <RobotStatus working message="Traduzindo seu currículo…" />}
            {preview.language && <p role="status">Tradução pronta. Revise o currículo antes de salvar o PDF.</p>}
          </div>

          <details open>
            <summary>Ver currículo para {preview.job_title}</summary>

            <article className="resume-document" ref={documentRef}>
              <header>
                <h2>{preview.name}</h2>
                <p><strong>{preview.professional_title}</strong></p>
                <p>{preview.location}</p>
                <p>
                  {[preview.email, preview.phone].filter(Boolean).join(" · ")}
                </p>

                {Object.entries(preview.links).map(([name, url]) =>
                  /^https?:\/\//i.test(url) ? (
                    <p key={name}>
                      <a href={url} target="_blank" rel="noopener noreferrer">
                        {url}
                      </a>
                    </p>
                  ) : null,
                )}
              </header>

              <section>
                <h3>{labels.summary}</h3>
                <p>{preview.professional_summary}</p>
              </section>

              {preview.skills.length > 0 && (
                <section>
                  <h3>{labels.skills}</h3>
                  <p>{preview.skills.join(" · ")}</p>
                </section>
              )}

              {preview.experience.length > 0 && (
                <section>
                  <h3>{labels.experience}</h3>

                  {preview.experience.map((experience, index) => (
                    <div key={index}>
                      <p>
                        <strong>{experience.role}</strong>
                        {" — "}{experience.company}
                      </p>
                      <p>
                        {experience.start}
                        {experience.current
                          ? ` — ${labels.current}`
                          : experience.end
                            ? ` — ${experience.end}`
                            : ""}
                      </p>

                      <ul>
                        {experience.responsibilities.map((text, position) => (
                          <li key={position}>{text}</li>
                        ))}

                        {experience.achievements.map((achievement, position) => (
                          <li key={`achievement-${position}`}>
                            {achievement.description}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </section>
              )}

              {preview.projects.length > 0 && (
                <section>
                  <h3>{labels.projects}</h3>

                  {preview.projects.map((project, index) => (
                    <div key={index}>
                      <p><strong>{project.name}</strong></p>
                      <p>{project.description}</p>
                      <p>{project.technologies.join(" · ")}</p>
                    </div>
                  ))}
                </section>
              )}

              {preview.education.length > 0 && (
                <section>
                  <h3>{labels.education}</h3>

                  {preview.education.map((education, index) => (
                    <div key={index}>
                      <p><strong>{education.degree}</strong></p>
                      <p>{education.institution} · {education.status}</p>
                      {(education.start || education.end) && (
                        <p>
                          {[education.start, education.end]
                            .filter(Boolean)
                            .join(" — ")}
                        </p>
                      )}
                    </div>
                  ))}
                </section>
              )}

              <section>
                <h3>{labels.languages}</h3>
                {preview.languages.portuguese && (
                  <p>{labels.portuguese}: {preview.languages.portuguese}</p>
                )}
                {preview.languages.english && (
                  <p>{labels.english}: {preview.languages.english}</p>
                )}
              </section>
            </article>
          </details>

          <div className="resume-review">
            <h3>Revisão antes de usar</h3>

            <ul>
              {preview.warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>

            {preview.ats_keywords.length > 0 && (
              <p>
                <strong>Palavras-chave identificadas:</strong>{" "}
                {preview.ats_keywords.join(" · ")}
              </p>
            )}

            {preview.unsupported_requirements.length > 0 && (
              <p>
                <strong>Requisitos sem correspondência na análise:</strong>{" "}
                {preview.unsupported_requirements.join(" · ")}
              </p>
            )}
          </div>

          <div className="resume-export">
            <button className="primary-button" type="button" onClick={savePdf} disabled={translating || language !== (preview.language ?? "pt-BR")}>
              Salvar currículo em PDF 📄
            </button>
            <p>Na janela de impressão, escolha “Salvar como PDF”, papel A4 e desative cabeçalhos e rodapés. Confira as páginas antes de salvar.</p>
            <p>O arquivo contém somente o currículo no idioma da prévia, sem os avisos da análise. Ele não é enviado à empresa automaticamente.</p>
            {pdfError && <p role="alert">{pdfError}</p>}
          </div>

          <button type="button" disabled={translating} onClick={() => { setPreview(null); setOriginal(null); setPdfError(null); }}>
            Fechar prévia
          </button>
        </div>
      )}
    </div>
  );
}

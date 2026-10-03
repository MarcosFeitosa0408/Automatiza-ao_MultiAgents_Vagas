import { useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { generateResumePreview } from "../../api/resume";
import type { ResumePreview } from "../../api/resume";

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

  async function generate() {
    if (submitting.current) return;

    submitting.current = true;
    setLoading(true);
    setError(null);
    setPreview(null);

    try {
      setPreview(await generateResumePreview(applicationId));
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
        disabled={loading}
      >
        {loading ? "Gerando..." : "Gerar prévia do currículo"}
      </button>

      {loading && <p role="status">Organizando seu currículo...</p>}
      {error && <p role="alert">{error}</p>}

      {preview && (
        <div>
          <p role="status">Prévia gerada. Confira o conteúdo abaixo.</p>

          <details open>
            <summary>Ver currículo para {preview.job_title}</summary>

            <article className="resume-document">
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
                <h3>Resumo profissional</h3>
                <p>{preview.professional_summary}</p>
              </section>

              {preview.skills.length > 0 && (
                <section>
                  <h3>Competências</h3>
                  <p>{preview.skills.join(" · ")}</p>
                </section>
              )}

              {preview.experience.length > 0 && (
                <section>
                  <h3>Experiência profissional</h3>

                  {preview.experience.map((experience, index) => (
                    <div key={index}>
                      <p>
                        <strong>{experience.role}</strong>
                        {" — "}{experience.company}
                      </p>
                      <p>
                        {experience.start}
                        {experience.current
                          ? " — Atual"
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
                  <h3>Projetos</h3>

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
                  <h3>Formação</h3>

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
                <h3>Idiomas</h3>
                {preview.languages.portuguese && (
                  <p>Português: {preview.languages.portuguese}</p>
                )}
                {preview.languages.english && (
                  <p>Inglês: {preview.languages.english}</p>
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

          <button type="button" onClick={() => setPreview(null)}>
            Fechar prévia
          </button>
        </div>
      )}
    </div>
  );
}
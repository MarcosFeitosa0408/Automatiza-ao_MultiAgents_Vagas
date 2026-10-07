import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { createJobApplication } from "../../api/applications";
import { ApiError } from "../../api/client";
import type {
  JobApplicationCreateRequest,
  JobApplicationObject,
  JobOpportunity,
  WorkModel,
} from "../../types/api";

type NewApplicationProps = {
  onViewApplications: (applicationId?: string) => void;
  initialJob?: JobOpportunity;
};

function splitLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 422) {
      return "O backend não aceitou os dados. Confira os campos e o link da vaga.";
    }

    return `Não foi possível cadastrar a oportunidade. A API retornou erro ${error.status}.`;
  }

  return "Não foi possível confirmar o cadastro. Verifique a conexão e consulte a lista antes de tentar novamente.";
}

export default function NewApplication({
  onViewApplications,
  initialJob,
}: NewApplicationProps) {
  const [duplicate, setDuplicate] = useState<{ applicationId: string; title: string; company: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<JobApplicationObject | null>(null);

  const submitting = useRef(false);
  const ids = useRef<{ applicationId: string; jobId: string } | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting.current) {
      return;
    }

    const form = event.currentTarget;
    const data = new FormData(form);

    function read(name: string): string {
      return String(data.get(name) ?? "").trim();
    }

    const title = read("title");
    const company = read("company");
    const source = read("source");
    const url = read("url");

    setError(null);
    setDuplicate(null);

    if (!title || !company || !source) {
      setError("Preencha cargo, empresa e origem da vaga.");
      return;
    }

    if (url) {
      try {
        const parsed = new URL(url);

        if (!["http:", "https:"].includes(parsed.protocol)) {
          throw new Error("Protocolo inválido");
        }
      } catch {
        setError("Informe um link válido começando com http:// ou https://.");
        return;
      }
    }

    if (!ids.current) {
      ids.current = {
        applicationId: crypto.randomUUID(),
        jobId: initialJob?.job_id ?? crypto.randomUUID(),
      };
    }

    const request: JobApplicationCreateRequest = {
      application_id: ids.current.applicationId,
      job: {
        job_id: ids.current.jobId,
        title,
        company,
        source,
        url: url || null,
        location: read("location") || "NAO_IDENTIFICADO",
        work_model: read("work_model") as WorkModel,
        employment_type: read("employment_type") || "NAO_IDENTIFICADO",
        description: read("description"),
        requirements: splitLines(read("requirements")),
        desirable_requirements: splitLines(read("desirable_requirements")),
        discovered_at: initialJob?.discovered_at ?? new Date().toISOString(),
        status: "DISCOVERED",
      },
    };

    submitting.current = true;
    setSaving(true);

    try {
      const result = await createJobApplication(request);
      setSaved(result);
    } catch (err) {
      const detail = err instanceof ApiError ? (err.detail as { detail?: unknown })?.detail : null;
      if (err instanceof ApiError && err.status === 409 && detail && typeof detail === "object") {
        const data = detail as Record<string, unknown>;
        if (data.code === "opportunity_already_saved" && typeof data.application_id === "string" && typeof data.title === "string" && typeof data.company === "string") {
          setDuplicate({ applicationId: data.application_id, title: data.title, company: data.company });
        } else setError(errorMessage(err));
      } else setError(errorMessage(err));
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <section className="dashboard">
        <article className="dashboard-panel">
          <div className="application-success" role="status">
            <h2>Oportunidade cadastrada!</h2>
            <p>
              {saved.job.title} · {saved.job.company}
            </p>
            <p>
              O cadastro foi confirmado pela API. Nenhuma candidatura
              foi enviada à empresa.
            </p>
          </div>

          <button
            className="primary-button"
            type="button"
            onClick={() => onViewApplications()}
          >
            Ver candidaturas
          </button>
        </article>
      </section>
    );
  }

  return (
    <section className="dashboard" aria-labelledby="new-application-title">
      <div className="dashboard-intro">
        <div>
          <p className="dashboard-eyebrow">NOVA OPORTUNIDADE</p>
          <h2 id="new-application-title">Cadastrar oportunidade</h2>
          <p>
            Confira as informações do anúncio real. Este cadastro guarda
            a oportunidade na plataforma para análise e revisão humana.
          </p>
        </div>
      </div>

      <form
        className="dashboard-panel opportunity-form"
        onSubmit={handleSubmit}
        aria-busy={saving}
      >
        <p className="form-help">Campos com * são obrigatórios.</p>

        {initialJob && (
          <p className="form-help">
            Os dados da oportunidade selecionada foram preenchidos.
            Revise a descrição e informe os requisitos antes da análise.
          </p>
        )}

        {error && (
          <div className="dashboard-error" role="alert">
            {error}
          </div>
        )}

        {duplicate && <div role="status" className="application-success">
          <h3>Esta vaga já está nas suas candidaturas.</h3>
          <p>{duplicate.title} · {duplicate.company}</p>
          <p>A vaga existente foi preservada. Abra-a para editar a descrição e os requisitos. Os campos digitados aqui não foram salvos.</p>
          <button type="button" className="secondary-button" onClick={() => onViewApplications(duplicate.applicationId)}>Abrir vaga existente</button>
        </div>}

        <fieldset disabled={saving}>
          <legend className="visually-hidden">Informações da vaga</legend>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="job-title">Cargo *</label>
              <input
                id="job-title"
                name="title"
                defaultValue={initialJob?.title ?? ""}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-company">Empresa *</label>
              <input
                id="job-company"
                name="company"
                defaultValue={initialJob?.company ?? ""}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-source">Origem da vaga *</label>
              <input
                id="job-source"
                name="source"
                defaultValue={initialJob?.source ?? ""}
                placeholder="Ex.: site da empresa, LinkedIn, Gupy"
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-url">Link da vaga</label>
              <input
                id="job-url"
                name="url"
                type="url"
                defaultValue={initialJob?.url ?? ""}
                placeholder="https://..."
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-location">Local</label>
              <input
                id="job-location"
                name="location"
                defaultValue={initialJob?.location ?? ""}
                placeholder="Cidade e estado, conforme o anúncio"
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-work-model">Modalidade</label>
              <select
                id="job-work-model"
                name="work_model"
                defaultValue={initialJob?.work_model ?? "UNKNOWN"}
              >
                <option value="UNKNOWN">Não informada</option>
                <option value="REMOTE">Remoto</option>
                <option value="HYBRID">Híbrido</option>
                <option value="ONSITE">Presencial</option>
              </select>
            </div>

            <div className="form-field form-field-wide">
              <label htmlFor="job-employment-type">Tipo de contratação</label>
              <input
                id="job-employment-type"
                name="employment_type"
                defaultValue={initialJob?.employment_type ?? ""}
                placeholder="Ex.: CLT, PJ, estágio"
              />
            </div>

            <div className="form-field form-field-wide">
              <label htmlFor="job-description">Descrição da vaga</label>
              <textarea
                id="job-description"
                name="description"
                defaultValue={initialJob?.description ?? ""}
                rows={6}
                placeholder="Cole a descrição original do anúncio"
              />
            </div>

            <div className="form-field">
              <label htmlFor="job-requirements">Requisitos obrigatórios</label>
              <textarea
                id="job-requirements"
                name="requirements"
                defaultValue={initialJob?.requirements.join("\n") ?? ""}
                rows={5}
                aria-describedby="requirements-help"
              />
              <small id="requirements-help">
                Escreva um requisito por linha, conforme o anúncio.
              </small>
            </div>

            <div className="form-field">
              <label htmlFor="job-desirable">Requisitos desejáveis</label>
              <textarea
                id="job-desirable"
                name="desirable_requirements"
                defaultValue={
                  initialJob?.desirable_requirements.join("\n") ?? ""
                }
                rows={5}
                aria-describedby="desirable-help"
              />
              <small id="desirable-help">
                Escreva um requisito por linha.
              </small>
            </div>
          </div>
        </fieldset>

        <button
          className="primary-button"
          type="submit"
          disabled={saving}
        >
          {saving ? "Cadastrando..." : "Cadastrar oportunidade"}
        </button>
      </form>
    </section>
  );
}
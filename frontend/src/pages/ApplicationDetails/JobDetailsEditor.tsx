import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "../../api/client";
import { updateJobDetails } from "../../api/jobDetails";
import type { JobApplicationObject } from "../../types/api";

type JobDetailsEditorProps = {
  application: JobApplicationObject;
  onSaved: (application: JobApplicationObject) => void;
};

function splitLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function describeError(cause: unknown): string {
  if (cause instanceof ApiError) {
    if (cause.detail && typeof cause.detail === "object") {
      const body = cause.detail as Record<string, unknown>;

      if (typeof body.detail === "string") return body.detail;
      if (typeof body.message === "string") return body.message;
    }

    return "Não foi possível salvar. Confira os dados e tente novamente.";
  }

  return "Não foi possível conectar ao servidor. Os campos foram preservados.";
}

export default function JobDetailsEditor({
  application,
  onSaved,
}: JobDetailsEditorProps) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const submitting = useRef(false);
  const job = application.job;
  const prefix = `job-details-${application.application_id}`;

  if (application.tracking || application.preparation) {
    return (
      <p className="table-secondary">
        A edição do anúncio está indisponível após a preparação
        ou o início do acompanhamento.
      </p>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting.current) return;

    const data = new FormData(event.currentTarget);

    function read(name: string) {
      return String(data.get(name) ?? "").trim();
    }

    const requirements = splitLines(read("requirements"));

    setError(null);
    setSuccess(false);

    if (requirements.length === 0) {
      setError("Informe pelo menos um requisito real do anúncio.");
      return;
    }

    submitting.current = true;
    setSaving(true);

    try {
      const updated = await updateJobDetails(application.application_id, {
        description: read("description"),
        requirements,
        desirable_requirements: splitLines(
          read("desirable_requirements"),
        ),
      });

      onSaved(updated);
      setSuccess(true);
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  }

  return (
    <details className="job-details-editor">
      <summary>Editar descrição e requisitos</summary>

      <form
        onSubmit={handleSubmit}
        aria-busy={saving}
        onChange={() => {
          setSuccess(false);
          setError(null);
        }}
      >
        <p>
          Copie os requisitos do anúncio completo, um por linha.
          Não acrescente ferramentas que a empresa não solicitou.
          Ao salvar, análises anteriores serão limpas para recalcular.
        </p>

        <fieldset disabled={saving}>
          <legend>Informações do anúncio</legend>

          <label htmlFor={`${prefix}-description`}>
            Descrição da vaga
          </label>
          <textarea
            id={`${prefix}-description`}
            name="description"
            rows={6}
            defaultValue={job.description}
          />

          <label htmlFor={`${prefix}-requirements`}>
            Requisitos obrigatórios — um por linha
          </label>
          <textarea
            id={`${prefix}-requirements`}
            name="requirements"
            rows={5}
            defaultValue={job.requirements.join("\n")}
            required
          />

          <label htmlFor={`${prefix}-desirable`}>
            Requisitos desejáveis — um por linha
          </label>
          <textarea
            id={`${prefix}-desirable`}
            name="desirable_requirements"
            rows={4}
            defaultValue={job.desirable_requirements.join("\n")}
          />

          <button className="primary-button" type="submit">
            {saving ? "Salvando..." : "Salvar requisitos da vaga"}
          </button>
        </fieldset>

        {error && <p role="alert">{error}</p>}

        {success && (
          <p role="status">
            Requisitos salvos com sucesso! Agora você pode gerar
            a prévia do currículo e preparar a entrevista.
          </p>
        )}
      </form>
    </details>
  );
}
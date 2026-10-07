import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "../../api/client";
import { correctJobDetails, updateJobDetails } from "../../api/jobDetails";
import type { JobApplicationObject } from "../../types/api";

import { hasLongRequirements, repairText } from "./repairText";

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
  const formRef = useRef<HTMLFormElement | null>(null);
  const [confirmation, setConfirmation] = useState(false);
  const [accentChanges, setAccentChanges] = useState<{name: string; before: string; after: string}[]>([]);
  const [accentNotice, setAccentNotice] = useState("");
  const job = application.job;

  function checkAccents() {
    const form = formRef.current;
    if (!form) return;
    const changes = ["description", "requirements", "desirable_requirements"].flatMap((name) => {
      const field = form.elements.namedItem(name) as HTMLTextAreaElement;
      const after = repairText(field.value);
      return after !== field.value ? [{name, before: field.value, after}] : [];
    });
    setAccentChanges(changes);
    setAccentNotice(changes.length ? "Confira a proposta abaixo. Ela ainda não foi aplicada nem salva." : "Não foi encontrada uma correção segura. Se os acentos continuarem errados, copie o texto correto do anúncio original.");
    setConfirmation(false);
  }

  function applyAccents() {
    const form = formRef.current;
    if (!form) return;
    for (const change of accentChanges) {
      (form.elements.namedItem(change.name) as HTMLTextAreaElement).value = change.after;
    }
    setAccentChanges([]);
    setAccentNotice("A proposta foi aplicada somente aos campos. Revise e salve para atualizar a vaga.");
    setConfirmation(false);
  }
  const prefix = `job-details-${application.application_id}`;

  if (application.preparation) {
    return (
      <p className="table-secondary">
        A edição do anúncio está indisponível após a preparação ou aprovação.
        O conteúdo e o acompanhamento foram preservados.
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

    if (hasLongRequirements(requirements) || hasLongRequirements(splitLines(read("desirable_requirements")))) {
      setError("Separe os requisitos em itens curtos. Cole o anúncio completo em Descrição da vaga.");
      return;
    }
    if (application.tracking && !confirmation) {
      setConfirmation(true);
      return;
    }

    submitting.current = true;
    setSaving(true);

    try {
      const request = {
        description: read("description"),
        requirements,
        desirable_requirements: splitLines(
          read("desirable_requirements"),
        ),
      };
      const updated = application.tracking
        ? await correctJobDetails(application.application_id, request, application.updated_at)
        : await updateJobDetails(application.application_id, request);
      setConfirmation(false);
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
        ref={formRef}
        onSubmit={handleSubmit}
        aria-busy={saving}
        onChange={() => {
          setConfirmation(false);
          setAccentChanges([]);
          setSuccess(false);
          setError(null);
        }}
      >
        <p>
          Copie os requisitos do anúncio completo, um por linha.
          Não acrescente ferramentas que a empresa não solicitou.
          Ao salvar, análises anteriores serão limpas para recalcular.
          O acompanhamento e seu histórico serão preservados. A correção não envia candidatura.
          Para a comparação atual, informe competências por nome em linhas separadas, quando exigidas:
          por exemplo, SQL e Power BI em linhas diferentes. Não cole o anúncio inteiro nos requisitos.
        </p>

        <button type="button" className="secondary-button" disabled={saving} onClick={checkAccents}>Conferir correção dos acentos</button>
        {accentNotice && <p role="status">{accentNotice}</p>}
        {accentChanges.length > 0 && <div>
          {accentChanges.map((change) => <details key={change.name}>
            <summary>{change.name === "description" ? "Descrição" : change.name === "requirements" ? "Requisitos obrigatórios" : "Requisitos desejáveis"}: conferir antes e depois</summary>
            <p><strong>Texto atual:</strong> {change.before}</p>
            <p><strong>Proposta:</strong> {change.after}</p>
          </details>)}
          <button type="button" disabled={saving} onClick={applyAccents}>Aplicar correção nos campos</button>
          <button type="button" disabled={saving} onClick={() => {setAccentChanges([]); setAccentNotice("");}}>Descartar proposta</button>
        </div>}
        {confirmation && <div role="status">
          <p>Confirma a correção do anúncio de {job.title} — {job.company}? As análises serão recalculadas. As etapas, observações e datas do acompanhamento serão preservadas.</p>
          <button type="button" disabled={saving} onClick={() => setConfirmation(false)}>Cancelar correção</button>
        </div>}
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
            {saving ? "Salvando..." : confirmation ? "Confirmar correção do anúncio" : "Salvar requisitos da vaga"}
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
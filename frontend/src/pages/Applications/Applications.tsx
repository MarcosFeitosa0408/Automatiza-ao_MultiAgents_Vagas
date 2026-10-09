import ProgressPanel from "./ProgressPanel";
import DeleteApplication from "./DeleteApplication";
import JobDetailsEditor from "../ApplicationDetails/JobDetailsEditor";
import InterviewPanel from "./InterviewPanel";
import ResumePanel from "./ResumePanel";
import { useEffect, useState } from "react";
import { listJobApplications } from "../../api/applications";
import type {
  JobApplicationObject,
  JobStatus,
} from "../../types/api";

const statusLabels: Record<JobStatus, string> = {
  DISCOVERED: "Identificada",
  QUALIFIED: "Qualificada",
  VALIDATION_REVIEW: "Em revisão",
  APPROVED: "Aprovada",
  READY_TO_APPLY: "Pronta para candidatura",
  APPLIED: "Candidatura enviada",
  SCREENING: "Triagem",
  INTERVIEW: "Entrevista",
  FINAL: "Etapa final",
  OFFER: "Proposta",
  HIRED: "Contratado",
  REJECTED: "Rejeitada",
  WITHDRAWN: "Retirada",
  NO_RESPONSE: "Sem resposta",
  EXPIRED: "Expirada",
  APPLICATION_FAILED: "Falha na candidatura",
};

function formatDate(value: string) {
  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "Data indisponível"
    : date.toLocaleDateString("pt-BR");
}

export default function Applications({
  initialApplicationId,
  readOnly = false,
}: {
  initialApplicationId?: string;
  readOnly?: boolean;
} = {}) {
  const [selectedId, setSelectedId] = useState(initialApplicationId);
  const [applications, setApplications] =
    useState<JobApplicationObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadApplications() {
      try {
        const data = await listJobApplications();

        if (active) {
          setApplications(data);
        }
      } catch {
        if (active) {
          setError(
            "Não foi possível carregar as candidaturas. Verifique se o backend está em execução.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadApplications();

    return () => {
      active = false;
    };
  }, [reloadKey]);

  function reload() {
    setLoading(true);
    setError(null);
    setNotice(null);
    setReloadKey((value) => value + 1);
  }

  const query = search.trim().toLocaleLowerCase("pt-BR");

  const filteredApplications = applications.filter((application) => {
    if (selectedId && application.application_id !== selectedId) return false;
    const text = [
      application.job.title,
      application.job.company,
      application.job.location,
    ]
      .join(" ")
      .toLocaleLowerCase("pt-BR");

    return text.includes(query);
  });

  return (
    <section className="dashboard" aria-labelledby="applications-title">
      {selectedId && <div role="status"><p>Exibindo a vaga já cadastrada. Abra Editar descrição e requisitos para completá-la.</p><button type="button" className="secondary-button" onClick={() => setSelectedId(undefined)}>Ver todas as candidaturas</button></div>}
      <div className="dashboard-intro">
        <div>
          <p className="dashboard-eyebrow">OPORTUNIDADES</p>
          <h2 id="applications-title">Suas candidaturas</h2>
          <p>
            Acompanhe as oportunidades cadastradas e a etapa atual de
            cada processo. Uma candidatura pronta ainda não foi enviada.
          </p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={reload}
          disabled={loading}
        >
          {loading ? "Carregando..." : "Atualizar"}
        </button>
      </div>

      {notice && <p role="status">{notice}</p>}

      <article className="dashboard-panel" aria-busy={loading}>
        <div className="applications-toolbar">
          <div>
            <label className="search-label" htmlFor="application-search">
              Buscar por cargo, empresa ou local
            </label>
            <input
              id="application-search"
              className="search-input"
              type="search"
              placeholder="Digite para filtrar..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              disabled={loading || error !== null}
            />
          </div>

          {!loading && !error && (
            <span className="panel-badge" role="status">
              {filteredApplications.length} de {applications.length}
            </span>
          )}
        </div>

        {loading ? (
          <div className="application-empty" role="status">
            Consultando candidaturas...
          </div>
        ) : error ? (
          <div className="dashboard-error" role="alert">
            <p>{error}</p>
            <button
              className="secondary-button"
              type="button"
              onClick={reload}
            >
              Tentar novamente
            </button>
          </div>
        ) : applications.length === 0 ? (
          <div className="application-empty">
            <h3>Nenhuma candidatura cadastrada</h3>
            <p>
              As oportunidades aparecerão aqui quando forem cadastradas.
            </p>
          </div>
        ) : filteredApplications.length === 0 ? (
          <div className="application-empty" role="status">
            Nenhuma candidatura corresponde à sua busca.
          </div>
        ) : (
          <div
            className="applications-table-wrap"
            tabIndex={0}
            role="region"
            aria-label="Tabela de candidaturas com rolagem horizontal"
          >
            <table className="applications-table">
              <caption className="visually-hidden">
                Oportunidades cadastradas na plataforma
              </caption>
              <thead>
                <tr>
                  <th scope="col">Oportunidade</th>
                  <th scope="col">Local</th>
                  <th scope="col">Etapa</th>
                  <th scope="col">Score</th>
                  <th scope="col">Revisão humana</th>
                  <th scope="col">Atualizada em</th>
                </tr>
              </thead>
              <tbody>
                {filteredApplications.map((application) => {
                  const status =
                    application.tracking?.current_status ??
                    application.job.status;

                  const decision = application.preparation?.decision;

                  const review =
                    decision === "APPROVED_BY_HUMAN"
                      ? "Aprovada pela pessoa"
                      : decision === "REJECTED_BY_HUMAN"
                        ? "Rejeitada pela pessoa"
                        : decision === "PENDING_HUMAN_APPROVAL"
                          ? "Aguardando aprovação"
                          : "Ainda não preparada";

                  return (
                    <tr key={application.application_id}>
                      <td>
                        <strong>{application.job.title}</strong>
                        <span className="table-secondary">
                          {application.job.company}
                        </span>
                        <span className="table-secondary">
                          Cadastrada em {new Date(application.created_at).toLocaleString("pt-BR")}
                        </span>
                        {!readOnly && <>
<DeleteApplication
                          applicationId={application.application_id}
                          title={application.job.title}
                          company={application.job.company}
                          onDeleted={(id) => {
                            setApplications((current) => current.filter((item) => item.application_id !== id));
                            setNotice("Oportunidade excluída da sua conta.");
                          }}
                        />
                        <JobDetailsEditor
  application={application}
  onSaved={(updated) => {
    setApplications((current) =>
      current.map((item) =>
        item.application_id === updated.application_id
          ? updated
          : item,
      ),
    );
  }}
/>

<ProgressPanel application={application} onSaved={(updated) => {
  setApplications((current) => current.map((item) => item.application_id === updated.application_id ? updated : item));
  setNotice(updated.tracking?.current_status === "HIRED"
    ? "Contratação registrada! 🎉 Parabéns por essa conquista!"
    : updated.tracking?.current_status === "INTERVIEW"
      ? "Entrevista registrada! 🤖 Boa preparação para esse próximo passo!"
      : updated.tracking?.current_status === "REJECTED"
        ? "Resultado registrado. Vamos continuar buscando novas oportunidades. 💙"
        : "Etapa registrada. O dashboard usará este histórico ao ser aberto.");
}} />

<ResumePanel
  key={`resume-${application.application_id}-${application.updated_at}`}
  applicationId={application.application_id}
/>

<InterviewPanel
  key={`interview-${application.application_id}-${application.updated_at}`}
  applicationId={application.application_id}
/>
</>}
{readOnly && (
  <details>
    <summary>Consultar anúncio e histórico</summary>
    <p>{application.job.description}</p>
    <h3>Requisitos obrigatórios</h3>
    <ul>
      {application.job.requirements.map((value, index) => (
        <li key={index}>{value}</li>
      ))}
    </ul>
    <h3>Requisitos desejáveis</h3>
    <ul>
      {application.job.desirable_requirements.map((value, index) => (
        <li key={index}>{value}</li>
      ))}
    </ul>
    <h3>Histórico das etapas</h3>
    {application.tracking?.history.length ? (
      <ol>
        {application.tracking.history.map((event, index) => (
          <li key={index}>
            <strong>{statusLabels[event.status] ?? event.status}</strong>
            {" — "}
            {new Date(event.occurred_at).toLocaleString("pt-BR")}
            <p>{event.note}</p>
          </li>
        ))}
      </ol>
    ) : <p>Nenhuma etapa registrada.</p>}
  </details>
)}

                      </td>
                      <td>{application.job.location || "Não informado"}</td>
                      <td>
                        <span className="status-badge">
                          {statusLabels[status] ?? status}
                        </span>
                      </td>
                      <td>
                        {application.qualification?.fit_score ?? "—"}
                      </td>
                      <td>{review}</td>
                      <td>{formatDate(application.updated_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
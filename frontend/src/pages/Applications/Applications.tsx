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

export default function Applications() {
  const [applications, setApplications] =
    useState<JobApplicationObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

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
    setReloadKey((value) => value + 1);
  }

  const query = search.trim().toLocaleLowerCase("pt-BR");

  const filteredApplications = applications.filter((application) => {
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
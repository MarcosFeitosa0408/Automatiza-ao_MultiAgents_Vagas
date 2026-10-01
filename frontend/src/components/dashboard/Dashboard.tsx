import { useEffect, useState } from "react";
import { getJobApplicationMetrics } from "../../api/metrics";
import type { JobApplicationMetrics } from "../../api/metrics";

type DashboardProps = {
  onNewApplication: () => void;
};

export default function Dashboard({
  onNewApplication,
}: DashboardProps) {
  const [metrics, setMetrics] = useState<JobApplicationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const data = await getJobApplicationMetrics();

        setMetrics(data);
      } catch (err) {
        console.error("Erro ao carregar métricas:", err);
        setError("Não foi possível carregar as métricas da API.");
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  return (
    <section className="dashboard">
      <div className="dashboard-intro">
        <div>
          <p className="dashboard-eyebrow">VISÃO GERAL</p>

          <h2>Central de candidaturas</h2>

          <p>
            Acompanhe oportunidades, qualificações, candidaturas e evolução
            do processo seletivo em um único lugar.
          </p>
        </div>

<button
  className="primary-button"
  type="button"
  onClick={onNewApplication}
>
  + Nova candidatura
</button>

      </div>

      {error && (
        <div className="dashboard-error" role="alert">
          {error}
        </div>
      )}

      <div className="dashboard-metrics">
        <article className="metric-card">
          <span>Total de candidaturas</span>

          <strong>
            {loading ? "..." : metrics?.total_applications ?? 0}
          </strong>

          <small>Dados reais da API</small>
        </article>

        <article className="metric-card">
          <span>Em processo</span>

          <strong>
            {loading ? "..." : metrics?.screening_or_beyond ?? 0}
          </strong>

          <small>Screening ou além</small>
        </article>

        <article className="metric-card">
          <span>Entrevistas</span>

          <strong>
            {loading ? "..." : metrics?.interviews ?? 0}
          </strong>

          <small>Dados reais da API</small>
        </article>

        <article className="metric-card">
          <span>Contratações</span>

          <strong>
            {loading ? "..." : metrics?.hires ?? 0}
          </strong>

          <small>Dados reais da API</small>
        </article>
      </div>

      <div className="dashboard-panels">
        <article className="dashboard-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-eyebrow">PIPELINE</p>
              <h3>Funil de candidaturas</h3>
            </div>

            <span className="panel-badge">
              {loading ? "Carregando" : "Dados reais"}
            </span>
          </div>

          <div className="pipeline-placeholder">
            <span>
              {loading
                ? "Consultando dados do backend..."
                : `Screening ou além: ${metrics?.screening_or_beyond ?? 0} · Entrevistas: ${
                    metrics?.interviews ?? 0
                  } · Ofertas: ${metrics?.offers ?? 0} · Contratações: ${
                    metrics?.hires ?? 0
                  }`}
            </span>
          </div>
        </article>

        <article className="dashboard-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-eyebrow">TAXAS</p>
              <h3>Conversão da operação</h3>
            </div>
          </div>

          <div className="activity-placeholder">
            {loading ? (
              <span>Consultando métricas...</span>
            ) : (
              <span>
                Resposta: {metrics?.response_rate ?? 0}% · Entrevista:{" "}
                {metrics?.interview_rate ?? 0}% · Oferta:{" "}
                {metrics?.offer_rate ?? 0}% · Contratação:{" "}
                {metrics?.hire_rate ?? 0}%
              </span>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
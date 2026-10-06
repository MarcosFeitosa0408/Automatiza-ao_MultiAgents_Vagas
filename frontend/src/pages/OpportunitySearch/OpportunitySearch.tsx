import RobotStatus from "../../components/RobotStatus";
import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "../../api/client";
import { searchOpportunities } from "../../api/opportunities";
import type { JobOpportunity } from "../../types/api";

type OpportunitySearchProps = {
  onSelectOpportunity?: (job: JobOpportunity) => void;
};

export default function OpportunitySearch({
  onSelectOpportunity,
}: OpportunitySearchProps) {
  const [jobs, setJobs] = useState<JobOpportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submitting = useRef(false);


  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting.current) return;

    const form = event.currentTarget;
    const data = new FormData(form);
    const query = String(data.get("query") ?? "").trim();
    const country = String(data.get("country") ?? "").trim().toLowerCase();
    const location = String(data.get("location") ?? "").trim();

    if (!query || !/^[a-z]{2}$/.test(country)) {
      setError("Informe o cargo e um código de país com duas letras.");
      return;
    }

    submitting.current = true;
    setLoading(true);
    setError(null);
    setJobs([]);
    setSearched(false);

    try {
      const results = await searchOpportunities({
        query,
        country,
        location,
      });

      setJobs(results);
      setSearched(true);
    } catch (cause) {
      if (cause instanceof ApiError) {
        setError(
          cause.status === 503
            ? "A fonte de vagas ainda não está configurada no servidor."
            : cause.status === 504
              ? "A busca demorou para responder. Tente novamente."
              : "Não foi possível consultar a fonte de vagas. Tente novamente.",
        );
      } else {
        setError("Não foi possível conectar ao servidor.");
      }
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  }

  return (
    <section className="opportunity-search">
      <form onSubmit={handleSubmit} className="opportunity-search-form">
        <fieldset disabled={loading}>
          <legend>O que você procura?</legend>

          <label htmlFor="search-query">Cargo ou palavras-chave</label>
          <input
            id="search-query"
            name="query"
            placeholder="Ex.: Analista de dados"
            required
            maxLength={200}
          />

          <label htmlFor="search-country">Código do país</label>
          <input
            id="search-country"
            name="country"
            defaultValue="br"
            required
            minLength={2}
            maxLength={2}
            pattern="[A-Za-z]{2}"
            aria-describedby="search-country-help"
          />
          <small id="search-country-help">
            Ex.: br para Brasil, gb para Reino Unido.
            A disponibilidade depende da cobertura da Adzuna.
          </small>

          <label htmlFor="search-location">Localização — opcional</label>
          <input
            id="search-location"
            name="location"
            placeholder="Ex.: São Paulo"
            maxLength={200}
          />

          <button type="submit">
            {loading ? "Buscando..." : "Buscar oportunidades"}
          </button>
        </fieldset>
      </form>

      <p>
        Confira no anúncio os requisitos de residência, autorização de
        trabalho e modalidade. Encontrar uma vaga não confirma sua
        elegibilidade nem envia uma candidatura.
      </p>

      {loading && <RobotStatus working message="Buscando vagas…" />}
      {error && <p role="alert">{error}</p>}

      {searched && (
        <RobotStatus mood={jobs.length === 0 ? "retry" : "ready"} message={jobs.length === 0 ? "Nenhuma oportunidade encontrada. Ajuste os filtros." : `${jobs.length} oportunidades encontradas.`} />
      )}

      <div className="opportunity-results">
        {jobs.map((job) => (
  <article className="opportunity-result" key={job.job_id}>
    <h2>{job.title}</h2>
    <p><strong>{job.company}</strong></p>
    <p>{job.location}</p>
    <small>Fonte: {job.source}</small>

    {/* O botão fica aqui */}
    {onSelectOpportunity && (
      <button
        className="primary-button"
        type="button"
        onClick={() => onSelectOpportunity(job)}
      >
        Selecionar oportunidade
      </button>
    )}

    <details>
      <summary>Descrição da oportunidade</summary>
      <p>{job.description || "Descrição não informada."}</p>
    </details>

            {job.url && /^https?:\/\//i.test(job.url) && (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Abrir anúncio da vaga
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
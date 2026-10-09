import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  activateTrial,
  getSubscriptionStatus,
} from "../api/subscription";
import type { SubscriptionStatus } from "../api/subscription";

type Props = {
  children: ReactNode;
  consultation: ReactNode;
  onPurchase: () => void;
};

export default function SubscriptionAccess({
  children,
  consultation,
  onPurchase,
}: Props) {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const pending = useRef(false);
  const mounted = useRef(false);

  useEffect(() => {
    mounted.current = true;
    let active = true;
    let refreshing = false;

    async function refresh() {
      if (refreshing) return;
      refreshing = true;
      try {
        const result = await getSubscriptionStatus();
        if (active) {
          setStatus(result);
          setError("");
        }
      } catch {
        if (active) {
          setStatus(null);
          setError("Não foi possível conferir seu acesso. Tente novamente.");
        }
      } finally {
        refreshing = false;
      }
    }

    void refresh();
    const timer = window.setInterval(() => void refresh(), 60000);
    const handleFocus = () => void refresh();
    window.addEventListener("focus", handleFocus);

    return () => {
      active = false;
      mounted.current = false;
      window.clearInterval(timer);
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  async function startTrial() {
    if (pending.current) return;
    pending.current = true;
    setStarting(true);
    setError("");
    try {
      const result = await activateTrial();
      if (mounted.current) setStatus(result);
    } catch {
      if (mounted.current) {
        setError("Não foi possível iniciar seu teste. Tente novamente.");
      }
    } finally {
      pending.current = false;
      if (mounted.current) setStarting(false);
    }
  }

  if (!status) {
    return (
      <section className="dashboard-panel" aria-busy={!error}>
        {error
          ? <p role="alert">{error}</p>
          : <p role="status">Conferindo seu acesso...</p>}
      </section>
    );
  }

  if (status.access_allowed) {
    return (
      <>
        {status.kind === "trial" && (
          <section className="dashboard-panel">
            <p>
              Experimente grátis por 24 horas. Depois, aproveite o primeiro
              mês por R$ 19,90. Próximos meses por R$ 29,90.
            </p>
            {status.trial_ends_at !== null && (
              <p>
                Seu teste termina em{" "}
                {new Date(status.trial_ends_at * 1000).toLocaleString("pt-BR")}.
              </p>
            )}
          </section>
        )}
        {status.kind === "paid" && (
          <section className="dashboard-panel">
            <p>Seu acesso está ativo.</p>
            {status.paid_ends_at != null && (
              <p>
                Disponível até{" "}
                {new Date(status.paid_ends_at * 1000).toLocaleString("pt-BR")}.
              </p>
            )}
            <button
              type="button"
              className="secondary-button"
              onClick={onPurchase}
            >
              Renovar — R$ 29,90/mês
            </button>
          </section>
        )}
        {children}
      </>
    );
  }

  const commercial = status.kind === "trial_available"
    || status.kind === "consultation"
    || status.kind === "trial_expired"
    || status.kind === "paid_expired";
  const renewal = status.next_payment_amount === 2990;

  return (
    <>
      <section className="dashboard-panel">
        <p className="dashboard-eyebrow">MULTIAGENTS VAGAS</p>
        <h1>{status.trial_available ? "Experimente a plataforma" : "Seu acesso"}</h1>

        {status.trial_available ? (
          <p>
            Experimente grátis por 24 horas. Depois, aproveite o primeiro
            mês por R$ 19,90. Próximos meses por R$ 29,90.
          </p>
        ) : commercial ? (
          <p>
            {renewal
              ? "Seu período de acesso terminou. Renove por R$ 29,90 para continuar. Seu perfil e o histórico das candidaturas permanecem salvos."
              : "Seu teste gratuito terminou. Aproveite a oferta de lançamento para continuar. Seu perfil e o histórico das candidaturas permanecem salvos."}
          </p>
        ) : (
          <p>Esta conta não está liberada para utilizar a plataforma.</p>
        )}

        {status.kind === "consultation" && (
          <p>
            Você pode consultar seus dados e candidaturas até{" "}
            {status.consultation_ends_at === null
              ? "o término do período de consulta"
              : new Date(status.consultation_ends_at * 1000).toLocaleString("pt-BR")}.
            Para editar ou utilizar as demais funções, ative seu plano.
          </p>
        )}

        {status.trial_available && (
          <button
            type="button"
            className="primary-button"
            disabled={starting}
            onClick={() => void startTrial()}
          >
            {starting ? "Aguarde..." : "Testar grátis por 24 horas"}
          </button>
        )}

        {commercial && (
          <button
            type="button"
            className="secondary-button"
            disabled={starting}
            onClick={onPurchase}
          >
            {renewal
              ? "Renovar — R$ 29,90/mês"
              : "Ativar 1º mês — R$ 19,90"}
          </button>
        )}

        {error && <p role="alert">{error}</p>}
      </section>

      {status.kind === "consultation" && status.read_allowed && consultation}
    </>
  );
}

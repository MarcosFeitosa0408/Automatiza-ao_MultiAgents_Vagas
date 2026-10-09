import { useEffect, useRef, useState } from "react";
import { apiRequest } from "../../api/client";
import type { SubscriptionStatus } from "../../api/subscription";

type Payment = {
  id: string;
  amount: number;
  state: string;
  environment: "sandbox" | "production";
  created_at: number;
  period_start: number | null;
  period_end: number | null;
};

type Member = {
  id: string;
  name: string;
  email: string;
  role: string;
  state: string;
  subscription: SubscriptionStatus;
  payments: Payment[];
  access_history?: {
    event: "REGISTER" | "LOGIN";
    occurred_at: number;
  }[];
};

const labels: Record<string, string> = {
  admin: "Administrador",
  existing: "Conta existente — acesso preservado",
  pending: "Aguardando autorização",
  blocked: "Bloqueado",
  restricted: "Acesso restrito",
  trial_available: "Teste disponível — ainda não iniciado",
  trial: "Em teste gratuito",
  consultation: "Somente consulta",
  trial_expired: "Teste encerrado",
  paid: "Membro com pagamento confirmado",
  paid_expired: "Acesso pago encerrado",
};

const paymentLabels: Record<string, string> = {
  CREATING: "Gerando cobrança",
  WAITING: "Aguardando pagamento",
  PAID: "Pagamento confirmado",
  DECLINED: "Pagamento recusado",
  CANCELED: "Cobrança cancelada",
  EXPIRED: "Cobrança expirada",
};

function date(value: number | null | undefined) {
  return value == null ? "Não iniciado" : new Date(value * 1000).toLocaleString("pt-BR");
}

function money(value: number) {
  return (value / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export default function AdminMembers() {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const pending = useRef(false);

  useEffect(() => {
    let active = true;
    void apiRequest<{ members: Member[] }>("/admin/members")
      .then((result) => { if (active) setMembers(result.members); })
      .catch(() => { if (active) setError("Não foi possível consultar os membros."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function refresh() {
    if (pending.current) return;
    pending.current = true;
    setLoading(true);
    setError("");
    try {
      const result = await apiRequest<{ members: Member[] }>("/admin/members");
      setMembers(result.members);
    } catch {
      setError("Não foi possível consultar os membros. Tente novamente.");
    } finally {
      pending.current = false;
      setLoading(false);
    }
  }

  return (
    <section className="dashboard-panel" aria-labelledby="members-title">
      <h2 id="members-title">Membros, testes e pagamentos</h2>
      <p>
        A situação de uso e os pagamentos são separados da autorização
        administrativa. Pagamentos do Sandbox são apenas testes.
      </p>
      <button
        type="button"
        className="secondary-button"
        disabled={loading}
        onClick={() => void refresh()}
      >
        Atualizar membros
      </button>
      {loading && <p role="status">Consultando membros...</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && members.length === 0 && <p>Nenhum membro encontrado.</p>}
      {!loading && members.map((member) => (
        <article className="dashboard-panel" key={member.id}>
          <h3>{member.name}</h3>
          <p>{member.email}</p>
          <p><strong>{labels[member.subscription.kind] ?? member.subscription.kind}</strong></p>
          {member.subscription.kind === "paid" && member.payments.some(
            (payment) => payment.state === "PAID" && payment.environment === "sandbox",
          ) && (
            <p>Confira o ambiente no histórico: pagamentos Sandbox não representam receita real.</p>
          )}
          {member.subscription.trial_started_at != null && (
            <>
              <p>Início do teste: {date(member.subscription.trial_started_at)}</p>
              <p>Fim das 24 horas: {date(member.subscription.trial_ends_at)}</p>
            </>
          )}
          {member.subscription.kind === "consultation" && (
            <p>Consulta disponível até: {date(member.subscription.consultation_ends_at)}</p>
          )}
          {member.subscription.paid_ends_at != null && (
            <p>Validade do acesso pago: {date(member.subscription.paid_ends_at)}</p>
          )}
          <details>
            <summary>Histórico de cadastro e entradas</summary>
            <p>Registros disponíveis a partir da ativação deste histórico.</p>
            {member.access_history?.length ? (
              <ul>
                {member.access_history.map((entry, index) => (
                  <li key={index}>
                    {entry.event === "REGISTER" ? "Cadastro criado" : "Entrada bem-sucedida"}
                    {" — "}{date(entry.occurred_at)}
                  </li>
                ))}
              </ul>
            ) : <p>Nenhuma entrada registrada neste histórico.</p>}
          </details>
          <details>
            <summary>Histórico de pagamentos</summary>
            {member.payments.length === 0 ? (
              <p>Nenhuma cobrança registrada.</p>
            ) : (
              <ul>
                {member.payments.map((payment) => (
                  <li key={payment.id}>
                    <strong>{money(payment.amount)}</strong>
                    {" — "}{paymentLabels[payment.state] ?? payment.state}
                    {" — "}{payment.environment === "sandbox" ? "TESTE — Sandbox" : "Produção"}
                    <p>Cobrança criada em: {date(payment.created_at)}</p>
                    {payment.state === "PAID" && (
                      <p>
                        Período de acesso: {date(payment.period_start)}
                        {" até "}{date(payment.period_end)}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </details>
        </article>
      ))}
    </section>
  );
}

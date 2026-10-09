import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import QRCode from "qrcode";
import { ApiError } from "../api/client";
import { createPixPayment, getPixPayment } from "../api/payment";
import type { PixPayment } from "../api/payment";
import { getSubscriptionStatus } from "../api/subscription";

type Props = {
  onBack: () => void;
  onConfirmed: () => void;
};

function currency(amount: number) {
  return (amount / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function describeError(cause: unknown): string {
  if (cause instanceof ApiError && cause.detail && typeof cause.detail === "object") {
    const detail = (cause.detail as Record<string, unknown>).detail;
    if (typeof detail === "string") return detail;
  }
  return "Não foi possível consultar o pagamento. Tente novamente.";
}

export default function PixPaymentPage({ onBack, onConfirmed }: Props) {
  const [amount, setAmount] = useState<number | null>(null);
  const [taxId, setTaxId] = useState("");
  const [payment, setPayment] = useState<PixPayment | null>(null);
  const [qrImage, setQrImage] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [creating, setCreating] = useState(false);
  const [checking, setChecking] = useState(false);
  const pending = useRef(false);
  const checkPending = useRef(false);
  const mounted = useRef(false);
  const confirmed = useRef(false);

  useEffect(() => {
    mounted.current = true;
    let active = true;
    void getSubscriptionStatus().then((status) => {
      if (active) setAmount(status.next_payment_amount ?? 1990);
    }).catch((cause: unknown) => {
      if (active) setError(describeError(cause));
    });
    return () => {
      active = false;
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const text = payment?.qr_text;
    let active = true;
    if (text) {
      void QRCode.toDataURL(text, {
        width: 320,
        margin: 4,
        errorCorrectionLevel: "M",
        color: { dark: "#000000", light: "#ffffff" },
      }).then((url) => {
        if (active) setQrImage(url);
      }).catch(() => {
        if (active) setError("Não foi possível desenhar o QR Code. Utilize o código Pix abaixo.");
      });
    }
    return () => { active = false; };
  }, [payment?.qr_text]);

  async function checkPayment() {
    if (!payment || checkPending.current || confirmed.current) return;
    checkPending.current = true;
    setChecking(true);
    try {
      const updated = await getPixPayment(payment.id);
      if (!mounted.current) return;
      setPayment(updated);
      setError("");
      if (updated.state === "PAID") {
        confirmed.current = true;
        onConfirmed();
      } else {
        setNotice("Pagamento ainda não confirmado. A consulta continuará automaticamente.");
      }
    } catch (cause) {
      if (mounted.current) setError(describeError(cause));
    } finally {
      checkPending.current = false;
      if (mounted.current) setChecking(false);
    }
  }

  const paymentId = payment?.id;
  const paymentState = payment?.state;

  useEffect(() => {
    if (!paymentId || paymentState !== "WAITING") return;
    let active = true;
    let refreshing = false;

    async function refresh() {
      if (refreshing || checkPending.current || confirmed.current || !paymentId) return;
      refreshing = true;
      try {
        const updated = await getPixPayment(paymentId);
        if (!active) return;
        setPayment(updated);
        setError("");
        if (updated.state === "PAID" && !confirmed.current) {
          confirmed.current = true;
          onConfirmed();
        }
      } catch (cause) {
        if (active) setError(describeError(cause));
      } finally {
        refreshing = false;
      }
    }

    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [paymentId, paymentState, onConfirmed]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current || amount === null) return;
    const digits = taxId.replace(/\D/g, "");
    if (digits.length !== 11) {
      setError("Informe um CPF com 11 dígitos.");
      return;
    }
    pending.current = true;
    setCreating(true);
    setError("");
    try {
      const created = await createPixPayment(digits);
      if (mounted.current) {
        setPayment(created);
        setTaxId("");
        setNotice("");
      }
    } catch (cause) {
      if (mounted.current) setError(describeError(cause));
    } finally {
      pending.current = false;
      if (mounted.current) setCreating(false);
    }
  }

  async function copyCode() {
    if (!payment?.qr_text) return;
    try {
      await navigator.clipboard.writeText(payment.qr_text);
      if (mounted.current) setNotice("Código Pix copiado. Cole no aplicativo do seu banco.");
    } catch {
      if (mounted.current) setNotice("Selecione o código abaixo e copie manualmente.");
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "24px auto", padding: 16 }}>
      <section className="dashboard-panel">
        <p className="dashboard-eyebrow">MULTIAGENTS VAGAS</p>
        <h1>Continue sua preparação</h1>
        <p>
          Oferta de lançamento: primeiro mês por R$ 19,90.
          Próximos meses por R$ 29,90.
        </p>
        <p>
          Cada pagamento confirmado libera 30 dias de acesso.
          A renovação por Pix depende de um novo pagamento.
        </p>
        <h2>{payment ? currency(payment.amount) : amount === null ? "Consultando valor..." : currency(amount)}</h2>

        {!payment && (
          <form onSubmit={(event) => void submit(event)}>
            <label htmlFor="pix-cpf">CPF do pagador</label>
            <input
              id="pix-cpf"
              inputMode="numeric"
              autoComplete="off"
              maxLength={14}
              value={taxId}
              onChange={(event) => setTaxId(event.target.value)}
              disabled={creating}
              required
            />
            <p>
              Seu nome, e-mail e CPF serão enviados ao PagBank
              para gerar a cobrança.
            </p>
            <button
              type="submit"
              className="primary-button"
              disabled={creating || amount === null}
            >
              {creating ? "Gerando Pix..." : "Pagar com Pix"}
            </button>
          </form>
        )}

        {payment && (
          <>
            {payment.environment === "sandbox" && (
              <p role="status">
                AMBIENTE DE TESTES: este Pix não recebe dinheiro real.
              </p>
            )}
            {qrImage && payment.state === "WAITING" && (
              <div style={{ textAlign: "center", margin: "24px 0" }}>
                <img
                  src={qrImage}
                  alt="QR Code Pix da cobrança"
                  width={320}
                  height={320}
                  style={{ maxWidth: "100%", height: "auto", background: "#fff" }}
                />
              </div>
            )}
            {payment.qr_text && payment.state === "WAITING" && (
              <>
                <label htmlFor="pix-code">Pix Copia e Cola</label>
                <textarea id="pix-code" value={payment.qr_text} readOnly rows={4} />
                <button type="button" className="primary-button" onClick={() => void copyCode()}>
                  Copiar código Pix
                </button>
              </>
            )}
            <p>
              {payment.state === "WAITING"
                ? "Aguardando a confirmação do PagBank."
                : payment.state === "PAID"
                  ? "Pagamento confirmado pelo servidor."
                  : "Esta cobrança não está disponível para pagamento."}
            </p>
            {payment.state === "WAITING" && (
              <button
                type="button"
                className="secondary-button"
                disabled={checking}
                onClick={() => void checkPayment()}
              >
                {checking ? "Consultando..." : "Conferir pagamento"}
              </button>
            )}
          </>
        )}

        {notice && <p role="status">{notice}</p>}
        {error && <p role="alert">{error}</p>}
        <p>
          <button
            type="button"
            className="secondary-button"
            disabled={creating || checking}
            onClick={onBack}
          >
            Voltar
          </button>
        </p>
      </section>
    </main>
  );
}

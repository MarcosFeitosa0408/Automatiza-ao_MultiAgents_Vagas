import PasswordInput from "../../components/PasswordInput";
import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { requestPasswordRecovery, resetAccountPassword } from "../../api/auth";
import { ApiError } from "../../api/client";

type Props = { token: string | null; onBack: (message?: string) => void };

export default function PasswordRecovery({ token, onBack }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const pending = useRef(false);
  const resetting = token !== null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const password = String(data.get("password") ?? "");
    setError("");
    setNotice("");
    if (resetting && password !== String(data.get("confirmation") ?? "")) {
      setError("As senhas não coincidem.");
      return;
    }
    pending.current = true;
    setBusy(true);
    try {
      if (resetting) {
        const result = await resetAccountPassword(token, password);
        form.reset();
        onBack(result.message);
      } else {
        const result = await requestPasswordRecovery(String(data.get("email") ?? "").trim());
        setNotice(result.message);
      }
    } catch (cause) {
      const detail = cause instanceof ApiError ? (cause.detail as { detail?: unknown } | null)?.detail : null;
      setError(typeof detail === "string" ? detail : "Não foi possível concluir. Confira os campos e tente novamente.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return <main className="auth-page">
    <section className="dashboard-panel auth-card">
      <p className="dashboard-eyebrow">MULTIAGENTS VAGAS</p>
      <h1>{resetting ? "Criar nova senha" : "Recuperar minha senha"}</h1>
      <p>{resetting ? "Use uma senha de 8 a 128 caracteres. Seus dados serão preservados." : "Informe o e-mail que você usa para entrar na plataforma."}</p>
      {error && <p className="dashboard-error" role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <legend className="visually-hidden">Recuperação de senha</legend>
          {resetting ? <>
            <label htmlFor="recovery-password">Nova senha</label>
            <PasswordInput fieldLabel="nova senha" id="recovery-password" name="password" autoComplete="new-password" minLength={8} maxLength={128} required />
            <label htmlFor="recovery-confirmation">Confirmar nova senha</label>
            <PasswordInput fieldLabel="confirmação da nova senha" id="recovery-confirmation" name="confirmation" autoComplete="new-password" minLength={8} maxLength={128} required />
          </> : <>
            <label htmlFor="recovery-email">E-mail de acesso</label>
            <input id="recovery-email" name="email" type="email" autoComplete="email" maxLength={254} required />
          </>}
          <button className="primary-button" type="submit">{busy ? "Aguarde..." : resetting ? "Salvar nova senha" : "Enviar link de recuperação"}</button>
        </fieldset>
      </form>
      <button className="secondary-button" disabled={busy} type="button" onClick={() => onBack()}>Voltar ao login</button>
      <p className="form-help">A recuperação de senha não altera a autorização de acesso à plataforma.</p>
    </section>
  </main>;
}

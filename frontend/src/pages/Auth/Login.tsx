import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { loginAccount, registerAccount } from "../../api/auth";
import type { AccountSession } from "../../api/auth";
import { ApiError } from "../../api/client";

type Props = { onAuthenticated: (session: AccountSession) => void; message?: string };

export default function Login({ onAuthenticated, message }: Props) {
  const [registering, setRegistering] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = useRef(false);
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const name = String(data.get("name") ?? "").trim();
    const email = String(data.get("email") ?? "").trim();
    const password = String(data.get("password") ?? "");
    setError(null);
    if (registering && password !== String(data.get("confirmation") ?? "")) {
      setError("As senhas não coincidem.");
      return;
    }
    pending.current = true;
    setBusy(true);
    try {
      if (registering) {
        const result = await registerAccount(name, email, password);
        form.reset();
        setNotice(result.message);
        setRegistering(false);
      } else {
        const session = await loginAccount(email, password);
        form.reset();
        onAuthenticated(session);
      }
    } catch (cause) {
      if (cause instanceof ApiError) {
        const body = cause.detail as { detail?: unknown } | null;
        setError(typeof body?.detail === "string" ? body.detail : "Confira os campos. Use uma senha com 15 a 128 caracteres.");
      } else {
        setError("Não foi possível conectar ao servidor. Tente novamente.");
      }
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="dashboard-panel auth-card">
        <p className="dashboard-eyebrow">MULTIAGENTS VAGAS</p>
        <h1>{registering ? "Criar minha conta" : "Entrar na plataforma"}</h1>
        <p>Seu perfil e suas oportunidades pertencem à sua conta. Novos cadastros precisam da autorização do administrador.</p>
        {message && <p role="status">{message}</p>}
        {notice && <p role="status">{notice}</p>}
        {error && <p className="dashboard-error" role="alert">{error}</p>}
        <form onSubmit={submit} key={registering ? "register" : "login"}>
          <fieldset disabled={busy}>
            <legend className="visually-hidden">Acesso à conta</legend>
            {registering && <>
              <label htmlFor="account-name">Nome</label>
              <input id="account-name" name="name" autoComplete="name" required maxLength={100} />
            </>}
            <label htmlFor="account-email">E-mail de acesso</label>
            <input id="account-email" type="email" name="email" autoComplete="username" required maxLength={254} />
            <label htmlFor="account-password">Senha</label>
            <input id="account-password" type="password" name="password" autoComplete={registering ? "new-password" : "current-password"} required minLength={15} maxLength={128} aria-describedby="password-help" />
            <small id="password-help">Use de 15 a 128 caracteres. Uma frase longa ajuda a lembrar.</small>
            {registering && <>
              <label htmlFor="account-confirmation">Confirmar senha</label>
              <input id="account-confirmation" type="password" name="confirmation" autoComplete="new-password" required minLength={15} maxLength={128} />
            </>}
            <button className="primary-button" type="submit">{busy ? "Aguarde..." : registering ? "Solicitar acesso" : "Entrar"}</button>
          </fieldset>
        </form>
        <button className="secondary-button" type="button" disabled={busy} onClick={() => { setRegistering(!registering); setError(null); }}>
          {registering ? "Já tenho uma conta" : "Criar conta"}
        </button>
        <p className="form-help">Ao recarregar ou fechar esta aba, será necessário entrar novamente. Guarde sua senha: a recuperação por e-mail ainda não está disponível.</p>
      </section>
    </main>
  );
}

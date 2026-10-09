import PasswordInput from "../../components/PasswordInput";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { loginAccount, registerTrialAccount } from "../../api/auth";
import type { AccountSession } from "../../api/auth";
import PasswordRecovery from "./PasswordRecovery";
import { ApiError } from "../../api/client";

type Props = { onAuthenticated: (session: AccountSession) => void; message?: string };

export default function Login({ onAuthenticated, message }: Props) {
  const [recovery, setRecovery] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  useEffect(() => {
    function readRecoveryLink() {
      if (window.location.hash.startsWith("#/redefinir-senha?")) {
        const token = new URLSearchParams(window.location.hash.split("?")[1]).get("token") ?? "";
        setResetToken(token);
        setRecovery(true);
        // Guarda apenas em memória: remove o segredo da barra de endereço e do histórico atual.
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
      }
    }
    readRecoveryLink();
    window.addEventListener("hashchange", readRecoveryLink);
  return () => window.removeEventListener("hashchange", readRecoveryLink);
  }, []);

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
        const session = await registerTrialAccount(name, email, password);
        form.reset();
        onAuthenticated(session);
      } else {
        const session = await loginAccount(email, password);
        form.reset();
        onAuthenticated(session);
      }
    } catch (cause) {
      if (cause instanceof ApiError) {
        const body = cause.detail as { detail?: unknown } | null;
        setError(typeof body?.detail === "string" ? body.detail : "Confira os campos. Use uma senha com 8 a 128 caracteres.");
      } else {
        setError("Não foi possível conectar ao servidor. Tente novamente.");
      }
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  if (recovery) return <PasswordRecovery token={resetToken} onBack={(success) => {
    setResetToken(null);
    setRecovery(false);
    setRegistering(false);
    setError(null);
    setNotice(success ?? "");
  }} />;

  return (
    <main className="auth-page auth-with-robots">
      <figure className="auth-robots">
        <img src="/images/robots-globe.jpg" width="1408" height="768" alt="Pequenos robôs ao redor de um globo, ilustrando a preparação para oportunidades de trabalho." />
        <figcaption>Seu próximo passo começa aqui <span aria-hidden="true">🌎🤖</span></figcaption>
        <p>Encontre vagas alinhadas ao seu perfil, prepare seu currículo para sistemas ATS e pratique entrevistas. Organize suas candidaturas e acompanhe cada etapa, mantendo as decisões sob seu controle.</p>
      </figure>
      <section className="dashboard-panel auth-card">
        <p className="dashboard-eyebrow">MULTIAGENTS VAGAS</p>
        <h1>{registering ? "Criar minha conta" : "Entrar na plataforma"}</h1>
        <p>Crie sua conta e ative o teste gratuito de 24 horas. Primeiro mês por R$ 19,90; renovação por R$ 29,90.</p>
        <p>Seu perfil é privado e vinculado à sua conta.</p>
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
            <PasswordInput fieldLabel="senha" id="account-password" name="password" autoComplete={registering ? "new-password" : "current-password"} required minLength={8} maxLength={128} aria-describedby="password-help" />
            <small id="password-help">Use de 8 a 128 caracteres. Uma frase longa ajuda a lembrar.</small>
            {registering && <>
              <label htmlFor="account-confirmation">Confirmar senha</label>
              <PasswordInput fieldLabel="confirmação da senha" id="account-confirmation" name="confirmation" autoComplete="new-password" required minLength={8} maxLength={128} />
            </>}
            <button className="primary-button" type="submit">{busy ? "Aguarde..." : registering ? "Criar conta para testar" : "Entrar"}</button>
          </fieldset>
        </form>
        <button className="secondary-button" type="button" disabled={busy} onClick={() => { setRegistering(!registering); setError(null); }}>
          {registering ? "Já tenho uma conta" : "Criar conta"}
        </button>
        {!registering && <button className="secondary-button" type="button" disabled={busy} onClick={() => { setResetToken(null); setRecovery(true); }}>Esqueci minha senha</button>}
        <p className="form-help">Ao recarregar ou fechar esta aba, será necessário entrar novamente.</p>
      </section>
    </main>
  );
}

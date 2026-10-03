import { useEffect, useState } from "react";
import "./App.css";
import Platform from "./Platform";
import Login from "./pages/Auth/Login";
import { logoutAccount } from "./api/auth";
import type { AccountSession, AccountUser } from "./api/auth";
import { setAccessToken } from "./api/session";
import { ApiError } from "./api/client";

export default function App() {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [message, setMessage] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function expired() {
      setUser(null);
      setMessage("Sua sessão terminou. Entre novamente.");
      setError(null);
    }
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);

  function authenticated(session: AccountSession) {
    setAccessToken(session.access_token);
    setUser(session.user);
    setMessage("");
    setError(null);
  }

  async function logout() {
    setLoggingOut(true);
    setError(null);
    try {
      await logoutAccount();
      setAccessToken(null);
      setUser(null);
      setMessage("Você saiu da sua conta.");
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        setAccessToken(null);
        setUser(null);
      } else {
        setError("Não foi possível encerrar a sessão no servidor. Tente novamente.");
      }
    } finally {
      setLoggingOut(false);
    }
  }

  if (!user) return <Login onAuthenticated={authenticated} message={message} />;

  return <>
    <div className="account-bar">
      <span>Conta: {user.email}</span>
      <button type="button" className="secondary-button" onClick={logout} disabled={loggingOut}>{loggingOut ? "Saindo..." : "Sair da conta"}</button>
      {error && <p role="alert">{error}</p>}
    </div>
    <Platform key={user.id} />
  </>;
}

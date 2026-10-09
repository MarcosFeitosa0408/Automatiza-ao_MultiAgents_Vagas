import { useCallback, useEffect, useState } from "react";
import PixPaymentPage from "./components/PixPaymentPage";
import "./App.css";
import Platform from "./Platform";
import SubscriptionAccess from "./components/SubscriptionAccess";
import ConsultationView from "./components/ConsultationView";
import HelpRobot from "./components/HelpRobot";
import PlatformGuide from "./components/PlatformGuide";
import AdminAccounts from "./pages/Admin/AdminAccounts";
import Login from "./pages/Auth/Login";
import { logoutAccount } from "./api/auth";
import type { AccountSession, AccountUser } from "./api/auth";
import { setAccessToken } from "./api/session";
import { ApiError } from "./api/client";

export default function App() {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [message, setMessage] = useState("");
  const [adminOpen, setAdminOpen] = useState(false);
  const [purchaseOpen, setPurchaseOpen] = useState(false);
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
    setAdminOpen(false);
    setPurchaseOpen(false);
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

  const paymentConfirmed = useCallback(() => {
    void logoutAccount().catch(() => undefined);
    setAccessToken(null);
    setUser(null);
    setPurchaseOpen(false);
    setError(null);
    setMessage("Pagamento confirmado. Entre novamente para utilizar seu acesso.");
  }, []);

  if (!user) return <Login onAuthenticated={authenticated} message={message} />;

  return <>
    <div className="account-bar">
      <span>Bem-vindo, {user.name}! <span aria-hidden="true">🚀😊</span> Vamos dar mais um passo na sua preparação?</span>
      <span>Conta: {user.email}</span>
      {user.role === "admin" && <button className="secondary-button" type="button" onClick={() => setAdminOpen(!adminOpen)}>{adminOpen ? "Voltar à plataforma" : "Administrar acessos"}</button>}
      <button type="button" className="secondary-button" onClick={logout} disabled={loggingOut}>{loggingOut ? "Saindo..." : "Sair da conta"}</button>
      {error && <p role="alert">{error}</p>}
    </div>
    <HelpRobot key={`help-${user.id}`} />
    <PlatformGuide key={`guide-${user.id}`} />
    {user.role === "admin" ? (
      adminOpen ? <AdminAccounts /> : <Platform key={user.id} />
    ) : (
      purchaseOpen ? (
        <PixPaymentPage
          key={`payment-${user.id}`}
          onBack={() => setPurchaseOpen(false)}
          onConfirmed={paymentConfirmed}
        />
      ) : (
        <SubscriptionAccess
          key={user.id}
          consultation={<ConsultationView />}
          onPurchase={() => {
            setError(null);
            setPurchaseOpen(true);
          }}
        >
          <Platform key={user.id} />
        </SubscriptionAccess>
      )
    )}
  </>;
}

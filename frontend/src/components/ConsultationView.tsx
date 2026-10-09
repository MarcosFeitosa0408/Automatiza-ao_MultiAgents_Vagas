import { useState } from "react";
import Applications from "../pages/Applications/Applications";
import Profile from "../pages/Profile/Profile";

export default function ConsultationView() {
  const [page, setPage] = useState<"applications" | "profile">("applications");

  return (
    <main>
      <section className="dashboard-panel">
        <h2>Consultar meus dados</h2>
        <nav aria-label="Consultas disponíveis">
          <button
            type="button"
            className="secondary-button"
            aria-pressed={page === "applications"}
            onClick={() => setPage("applications")}
          >
            Minhas candidaturas
          </button>
          <button
            type="button"
            className="secondary-button"
            aria-pressed={page === "profile"}
            onClick={() => setPage("profile")}
          >
            Meu perfil
          </button>
        </nav>
      </section>

      {page === "applications"
        ? <Applications readOnly />
        : <Profile readOnly />}
    </main>
  );
}

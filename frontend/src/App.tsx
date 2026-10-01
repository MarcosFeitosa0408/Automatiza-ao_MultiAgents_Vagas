import { useEffect, useState } from "react";
import "./App.css";
import MainLayout from "./components/layout/MainLayout";
import type { NavigationPage } from "./components/layout/Sidebar";
import Dashboard from "./components/dashboard/Dashboard";
import Applications from "./pages/Applications/Applications";

function readPage(): NavigationPage {
  return window.location.hash === "#/candidaturas"
    ? "applications"
    : "dashboard";
}

function App() {
  const [page, setPage] = useState<NavigationPage>(readPage);

  useEffect(() => {
    function handleHashChange() {
      setPage(readPage());
    }

    window.addEventListener("hashchange", handleHashChange);

    return () => {
      window.removeEventListener("hashchange", handleHashChange);
    };
  }, []);

  function navigate(nextPage: NavigationPage) {
    window.location.hash =
      nextPage === "applications" ? "/candidaturas" : "/dashboard";
  }

  const isDashboard = page === "dashboard";

  return (
    <MainLayout
      title={isDashboard ? "Dashboard" : "Candidaturas"}
      subtitle={
        isDashboard
          ? "Acompanhe sua operação de candidaturas com inteligência e controle."
          : "Consulte suas oportunidades e acompanhe cada processo."
      }
      activePage={page}
      onNavigate={navigate}
    >
      {isDashboard ? <Dashboard /> : <Applications />}
    </MainLayout>
  );
}

export default App;
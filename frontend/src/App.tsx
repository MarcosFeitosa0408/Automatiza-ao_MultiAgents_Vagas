import { useEffect, useState } from "react";
import "./App.css";
import MainLayout from "./components/layout/MainLayout";
import type { NavigationPage } from "./components/layout/Sidebar";
import Dashboard from "./components/dashboard/Dashboard";
import Applications from "./pages/Applications/Applications";
import NewApplication from "./pages/NewApplication/NewApplication";

function readPage(): NavigationPage {
  switch (window.location.hash) {
    case "#/candidaturas":
      return "applications";
    case "#/nova-candidatura":
      return "new-application";
    default:
      return "dashboard";
  }
}

const pageInfo: Record<
  NavigationPage,
  { title: string; subtitle: string; hash: string }
> = {
  dashboard: {
    title: "Dashboard",
    subtitle:
      "Acompanhe sua operação de candidaturas com inteligência e controle.",
    hash: "/dashboard",
  },
  applications: {
    title: "Candidaturas",
    subtitle: "Consulte suas oportunidades e acompanhe cada processo.",
    hash: "/candidaturas",
  },
  "new-application": {
    title: "Nova candidatura",
    subtitle: "Cadastre uma oportunidade para análise e revisão humana.",
    hash: "/nova-candidatura",
  },
};

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
    window.location.hash = pageInfo[nextPage].hash;
  }

  const info = pageInfo[page];

  return (
    <MainLayout
      title={info.title}
      subtitle={info.subtitle}
      activePage={page}
      onNavigate={navigate}
    >
      {page === "dashboard" && (
        <Dashboard
          onNewApplication={() => navigate("new-application")}
        />
      )}

      {page === "applications" && <Applications />}

      {page === "new-application" && (
        <NewApplication
          onViewApplications={() => navigate("applications")}
        />
      )}
    </MainLayout>
  );
}

export default App;
import { useEffect, useState } from "react";
import "./App.css";
import MainLayout from "./components/layout/MainLayout";
import type { NavigationPage } from "./components/layout/Sidebar";
import Dashboard from "./components/dashboard/Dashboard";
import Applications from "./pages/Applications/Applications";
import NewApplication from "./pages/NewApplication/NewApplication";
import OpportunitySearch from "./pages/OpportunitySearch/OpportunitySearch";
import Profile from "./pages/Profile/Profile";
import type { JobOpportunity } from "./types/api";

function readPage(): NavigationPage {
  switch (window.location.hash) {
    case "#/candidaturas":
      return "applications";
    case "#/nova-candidatura":
      return "new-application";
    case "#/buscar-oportunidades":
      return "opportunity-search";
    case "#/meu-perfil":
      return "profile";
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
    subtitle: "Acompanhe sua operação de candidaturas com inteligência e controle.",
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
  "opportunity-search": {
    title: "Buscar oportunidades",
    subtitle: "Encontre vagas por cargo, país e localização.",
    hash: "/buscar-oportunidades",
  },
  profile: {
    title: "Meu perfil",
    subtitle: "Revise os dados profissionais usados pelos agentes.",
    hash: "/meu-perfil",
  },
};

function Platform() {
  const [page, setPage] = useState<NavigationPage>(readPage);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string | undefined>();
  const [selectedJob, setSelectedJob] = useState<JobOpportunity | null>(null);

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
    setSelectedApplicationId(undefined);
    if (nextPage === "new-application") {
      setSelectedJob(null);
    }

    window.location.hash = pageInfo[nextPage].hash;
  }

  function selectOpportunity(job: JobOpportunity) {
    setSelectedJob(job);
    window.location.hash = pageInfo["new-application"].hash;
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
        <Dashboard onNewApplication={() => navigate("new-application")} />
      )}

      {page === "applications" && <Applications initialApplicationId={selectedApplicationId} />}

      {page === "new-application" && (
        <NewApplication
          key={selectedJob?.job_id ?? "manual"}
          initialJob={selectedJob ?? undefined}
          onViewApplications={(id) => { navigate("applications"); setSelectedApplicationId(id); }}
        />
      )}

      {page === "opportunity-search" && (
        <OpportunitySearch onSelectOpportunity={selectOpportunity} />
      )}

      {page === "profile" && <Profile />}
    </MainLayout>
  );
}

export default Platform;
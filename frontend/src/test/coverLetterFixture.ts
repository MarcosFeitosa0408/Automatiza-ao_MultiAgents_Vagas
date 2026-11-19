import type { ResumePreview } from "../api/resume";

export function coverLetterFixture(): ResumePreview {
  return {
    application_id: "letter-test", job_title: "Analista de Dados", company: "Empresa Exemplo",
    name: "Pessoa de Teste", email: "pessoa@example.com", phone: "11900000000", location: "São Paulo, SP",
    professional_title: "Analista de Dados", professional_summary: "Trabalho com análise de dados e relatórios comerciais.",
    skills: ["SQL", "Power BI"],
    education: [{ degree: "Análise de Dados", institution: "Instituição Exemplo", status: "Em andamento" }],
    experience: [{ company: "Empresa Anterior", role: "Analista", employment_type: "Freelance", start: "2025-03", end: "2025-06", current: false, location: "São Paulo", work_model: "Remoto", technologies: ["SQL"], responsibilities: ["Criar relatórios de vendas"], achievements: [{ metric: "vendas", value: 15, unit: "%", approximate: true, period: "três meses", description: "Análises associadas a um crescimento aproximado de 15% nas vendas em três meses." }] }],
    projects: [{ name: "Dashboard Comercial", description: "Análise de indicadores por unidade.", technologies: ["Power BI"], authorized_for_portfolio: true }],
    languages: { portuguese: "Nativo", english: "Intermediário" },
    links: { portfolio_url: "https://example.com/portfolio" },
    ats_keywords: ["SQL"], unsupported_requirements: ["Kubernetes"], warnings: ["Aviso interno da prévia de currículo."],
  };
}

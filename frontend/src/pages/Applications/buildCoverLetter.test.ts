import { expect, it } from "vitest";
import { buildCoverLetter } from "./buildCoverLetter";
import { coverLetterFixture } from "../../test/coverLetterFixture";

it("personaliza cargo, empresa e evidências reais, sem converter vendas em lucro ou inventar resultados", () => {
  const source = coverLetterFixture();
  const before = structuredClone(source);
  const letter = buildCoverLetter(source);
  expect(letter.body).toContain("À equipe de recrutamento da Empresa Exemplo");
  expect(letter.body).toContain("oportunidade de Analista de Dados na Empresa Exemplo");
  expect(letter.body).toContain("SQL e Power BI");
  expect(letter.body).toContain(source.experience[0].achievements[0].description);
  expect(letter.body).not.toContain("lucro");
  expect(letter.body).not.toContain("Kubernetes");
  expect(letter.body).not.toContain("25%");
  expect(letter.body).not.toContain("fluente");
  expect(letter.body).toContain("situação: Em andamento");
  expect(letter.body).not.toContain("concluí");
  expect(letter.unsupportedRequirements).toEqual(["Kubernetes"]);
  expect(source).toEqual(before);
});

it("seleciona a experiência relacionada à vaga e exclui projetos não autorizados", () => {
  const source = coverLetterFixture();
  source.experience.unshift({ ...source.experience[0], role: "Motorista", company: "Transportadora", technologies: ["Direção"], responsibilities: ["Transportar cargas"], achievements: [] });
  source.projects.unshift({ name: "Projeto Confidencial", description: "Conteúdo reservado", technologies: ["SQL", "Power BI"], authorized_for_portfolio: false });
  const letter = buildCoverLetter(source);
  expect(letter.body).toContain("Atuei como Analista na Empresa Anterior");
  expect(letter.body).not.toContain("Motorista");
  expect(letter.body).toContain("Dashboard Comercial");
  expect(letter.body).not.toContain("Conteúdo reservado");
});

it("gera outra carta a partir do perfil e da empresa da outra candidatura", () => {
  const source = coverLetterFixture();
  source.name = "Outra Pessoa";
  source.job_title = "Assistente Financeiro";
  source.company = "Outra Empresa";
  source.professional_summary = "Organização de registros financeiros.";
  source.skills = ["Excel"];
  source.experience = [];
  source.projects = [];
  const letter = buildCoverLetter(source);
  expect(letter.body).toContain("Assistente Financeiro na Outra Empresa");
  expect(letter.body).toContain("destaco Excel");
  expect(letter.body).toContain("Outra Pessoa");
  expect(letter.body).not.toContain("Empresa Anterior");
  expect(letter.body).not.toContain("Power BI");
});

it("trata perfil incompleto e ausência de correspondência sem alegar qualificações da vaga", () => {
  const source = coverLetterFixture();
  source.name = "NAO_IDENTIFICADO";
  source.company = "não informado";
  source.professional_summary = "";
  source.email = "";
  source.phone = "";
  source.skills = [];
  source.education = [];
  source.links.portfolio_url = "javascript:alert('teste')";
  const letter = buildCoverLetter(source);
  expect(letter.warnings.length).toBeGreaterThan(2);
  expect(letter.body).not.toContain("SQL");
  expect(letter.body).not.toContain("Empresa Anterior");
  expect(letter.body).not.toContain("NAO_IDENTIFICADO");
  expect(letter.contacts.join(" ")).not.toContain("javascript:");
});

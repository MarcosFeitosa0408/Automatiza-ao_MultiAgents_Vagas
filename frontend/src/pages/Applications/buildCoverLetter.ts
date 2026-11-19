import type { ResumePreview } from "../../api/resume";

export type CoverLetterDraft = {
  name: string;
  company: string;
  jobTitle: string;
  contacts: string[];
  body: string;
  matchedSkills: string[];
  unsupportedRequirements: string[];
  warnings: string[];
};

function clean(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  return /^(?:n[ãa]o[_ ]identificado|n\/?a|n[ãa]o informado)$/i.test(text) ? "" : text;
}

function distinct(values: string[]): string[] {
  const seen = new Set<string>();
  return values.map(clean).filter((value) => {
    const key = value.toLocaleLowerCase("pt-BR");
    if (!value || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function sentence(text: string): string {
  return /[.!?…]$/.test(text) ? text : `${text}.`;
}

function joinItems(values: string[]): string {
  return values.length < 2 ? values.join("") : `${values.slice(0, -1).join(", ")} e ${values.at(-1)}`;
}

/** Usa os fatos da prévia privada, cuja seleção de competências já considera a vaga. */
export function buildCoverLetter(preview: ResumePreview): CoverLetterDraft {
  const name = clean(preview.name);
  const company = clean(preview.company);
  const jobTitle = clean(preview.job_title);
  const skills = distinct(preview.skills).slice(0, 6);
  const selected = new Set(skills.map((skill) => skill.toLocaleLowerCase("pt-BR")));
  const overlap = (technologies: string[]) => distinct(technologies)
    .filter((technology) => selected.has(technology.toLocaleLowerCase("pt-BR"))).length;
  const experience = preview.experience
    .filter((item) => clean(item.role) && clean(item.company) && overlap(item.technologies) > 0)
    .map((item) => ({ item, relevance: overlap(item.technologies) }))
    .sort((a, b) => b.relevance - a.relevance)[0]?.item;
  const project = preview.projects
    .filter((item) => item.authorized_for_portfolio !== false && clean(item.name) && clean(item.description) && overlap(item.technologies) > 0)
    .map((item) => ({ item, relevance: overlap(item.technologies) }))
    .sort((a, b) => b.relevance - a.relevance)[0]?.item;
  const education = preview.education.find((item) => clean(item.degree) && clean(item.institution) && clean(item.status));
  const summary = clean(preview.professional_summary);
  const paragraphs: string[] = [
    company ? `À equipe de recrutamento da ${company},` : "À equipe de recrutamento,",
    jobTitle
      ? `Apresento meu interesse na oportunidade de ${jobTitle}${company ? ` na ${company}` : ""}.`
      : "Apresento meu interesse na oportunidade cadastrada.",
  ];

  if (summary) paragraphs.push(sentence(summary));
  if (skills.length) {
    paragraphs.push(`Entre minhas competências relacionadas aos requisitos informados para esta vaga, destaco ${joinItems(skills)}.`);
  }
  if (experience) {
    const activities = distinct(experience.responsibilities).slice(0, 2);
    const result = experience.achievements.map((item) => clean(item.description)).find(Boolean);
    paragraphs.push([
      `${experience.current ? "Atuo" : "Atuei"} como ${clean(experience.role)} na ${clean(experience.company)}.`,
      activities.length ? sentence(`Entre minhas atividades, destaco: ${activities.join("; ")}`) : "",
      result ? sentence(`Nessa experiência, destaco o seguinte resultado: ${result}`) : "",
    ].filter(Boolean).join(" "));
  }
  if (project) paragraphs.push(`No projeto ${clean(project.name)}, desenvolvi o seguinte trabalho: ${sentence(clean(project.description))}`);
  if (education) paragraphs.push(`Minha formação inclui ${clean(education.degree)}, na instituição ${clean(education.institution)} (situação: ${clean(education.status)}).`);
  paragraphs.push("Coloco-me à disposição para uma conversa sobre minha trajetória e como minhas qualificações podem contribuir para as atividades da vaga. Agradeço pela atenção e pela oportunidade de apresentar meu perfil.");
  paragraphs.push(["Atenciosamente,", name].filter(Boolean).join("\n"));

  const warnings: string[] = [];
  if (!name) warnings.push("Preencha seu nome em Meu perfil e gere a carta novamente antes de usar.");
  if (!company || !jobTitle) warnings.push("Confira o cargo e a empresa no cadastro da vaga para personalizar o destinatário.");
  if (!skills.length) warnings.push("Não foram identificadas competências correspondentes aos requisitos da vaga. Confira seu perfil e os requisitos antes de usar a carta.");
  if (!summary && !experience && !project) warnings.push("Seu perfil tem poucas informações para apresentar sua trajetória. Complete o resumo, as experiências ou os projetos em Meu perfil.");
  if (!clean(preview.email) && !clean(preview.phone)) warnings.push("Inclua um contato em Meu perfil para a empresa poder retornar.");

  const portfolio = clean(preview.links.portfolio_url);
  return {
    name, company, jobTitle,
    contacts: distinct([preview.email, preview.phone, preview.location, /^https?:\/\//i.test(portfolio) ? portfolio : ""]),
    body: paragraphs.join("\n\n"),
    matchedSkills: skills,
    unsupportedRequirements: distinct(preview.unsupported_requirements),
    warnings,
  };
}

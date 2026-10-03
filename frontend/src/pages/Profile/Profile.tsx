import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "../../api/client";
import {
  getCandidateProfile,
  saveCandidateProfile,
} from "../../api/profile";
import type { MasterProfile } from "../../types/profile";
import ProfileSections from "./ProfileSections";
import { normalizeProfileSections } from "./normalizeProfileSections";

function splitLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return "O perfil mestre ainda não foi cadastrado no servidor.";
    }

    if (error.status === 422) {
      return "Confira os campos. O servidor não aceitou a estrutura do perfil.";
    }

    return "Não foi possível concluir a operação. Seus campos foram preservados.";
  }

  return "Não foi possível conectar ao servidor. Verifique se ele está funcionando.";
}

type TextFieldProps = {
  name: string;
  label: string;
  value: string;
  multiline?: boolean;
  required?: boolean;
};

function TextField({
  name,
  label,
  value,
  multiline = false,
  required = false,
}: TextFieldProps) {
  const id = `profile-${name}`;

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>

      {multiline ? (
        <textarea
          id={id}
          name={name}
          defaultValue={value}
          rows={4}
          required={required}
        />
      ) : (
        <input
          id={id}
          name={name}
          defaultValue={value}
          required={required}
        />
      )}
    </div>
  );
}

type CheckboxProps = {
  name: string;
  label: string;
  checked: boolean;
};

function Checkbox({ name, label, checked }: CheckboxProps) {
  return (
    <label className="profile-checkbox">
      <input
        type="checkbox"
        name={name}
        defaultChecked={checked}
      />
      <span>{label}</span>
    </label>
  );
}

const skillFields = [
  ["core", "Competências principais"],
  ["database", "Bancos de dados e SQL"],
  ["python", "Python e bibliotecas"],
  ["analytics", "Análise de dados e BI"],
  ["tools", "Ferramentas"],
  ["automation", "Automação"],
] as const;

export default function Profile() {
  const [profile, setProfile] = useState<MasterProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const submitting = useRef(false);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await getCandidateProfile();

        if (active) {
          setProfile(result);
        }
      } catch (cause) {
        if (active) {
          setError(describeError(cause));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!profile || submitting.current) {
      return;
    }

    const data = new FormData(event.currentTarget);

    function read(name: string): string {
      return String(data.get(name) ?? "").trim();
    }

    function checked(name: string): boolean {
      return data.has(name);
    }

    setError(null);
    setSuccess(false);

    if (!read("name") || !read("professional-title")) {
      setError("Preencha seu nome e seu título profissional.");
      return;
    }

    for (const name of ["portfolio_url", "github_url", "linkedin_url"]) {
      const value = read(name);

      if (!value) continue;

      try {
        const url = new URL(value);

        if (!["http:", "https:"].includes(url.protocol)) {
          throw new Error("Protocolo inválido");
        }
      } catch {
        setError("Informe os links começando com http:// ou https://.");
        return;
      }
    }

    // Copia o perfil completo para preservar as seções não editadas.
    const updated = normalizeProfileSections(profile);

    updated.candidate.name = read("name");
    updated.candidate.email = read("email");
    updated.candidate.phone = read("phone");
    updated.candidate.location = {
      city: read("city"),
      state: read("state"),
      country: read("country"),
    };

    updated.candidate.employment_status = {
      currently_clt: checked("currently_clt"),
      actively_seeking: checked("actively_seeking"),
      priority: read("priority"),
      primary_goal: read("primary_goal"),
    };

    updated.candidate.career_target = {
      primary_roles: splitLines(read("primary_roles")),
      secondary_roles: splitLines(read("secondary_roles")),
      seniority: splitLines(read("seniority")),
    };

    updated.candidate.work_preferences = {
      employment_type_priority: splitLines(read("employment_type_priority")),
      remote: checked("remote"),
      hybrid: checked("hybrid"),
      onsite: checked("onsite"),
      preferred_location: splitLines(read("preferred_location")),
      relocation: checked("relocation"),
    };

    updated.professional_positioning = {
      title: read("professional-title"),
      summary: read("summary"),
      focus: splitLines(read("focus")),
    };

    for (const [key] of skillFields) {
      updated.skills[key] = splitLines(read(`skills-${key}`));
    }

    updated.languages = {
      portuguese: read("portuguese"),
      english: read("english"),
    };

    updated.portfolio = {
      portfolio_url: read("portfolio_url"),
      github_url: read("github_url"),
      linkedin_url: read("linkedin_url"),
    };

    submitting.current = true;
    setSaving(true);

    try {
      const saved = await saveCandidateProfile(updated);
      setProfile(saved);
      setSuccess(true);
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  }

  if (loading) {
    return <p role="status">Carregando seu perfil...</p>;
  }

  if (!profile) {
    return (
      <section className="dashboard">
        <p role="alert">{error ?? "Não foi possível carregar o perfil."}</p>
        <button type="button" onClick={() => window.location.reload()}>
          Tentar novamente
        </button>
      </section>
    );
  }

  return (
    <section className="dashboard">
      <div className="dashboard-intro">
        <div>
          <p className="dashboard-eyebrow">MEU PERFIL</p>
          <h2>Dados profissionais</h2>
          <p>
            Informe apenas competências e experiências verdadeiras.
            Os agentes usam este perfil na análise das vagas.
          </p>
        </div>
      </div>

      <form
        className="dashboard-panel opportunity-form profile-form"
        onSubmit={handleSubmit}
        onChange={() => setSuccess(false)}
        aria-busy={saving}
      >
        {error && <p className="dashboard-error" role="alert">{error}</p>}

        {success && (
          <p role="status">
            Perfil salvo! As próximas análises usarão os dados atualizados.
          </p>
        )}

        <fieldset disabled={saving}>
          <legend>Identificação e apresentação</legend>

          <div className="form-grid">
            <TextField name="name" label="Nome *" value={profile.candidate.name} required />
            <TextField
            name="email"
            label="E-mail de contato"
            value={profile.candidate.email ?? ""}
          />
            <TextField
            name="phone"
            label="Telefone de contato"
            value={profile.candidate.phone ?? ""}
          />
            <TextField name="professional-title" label="Título profissional *" value={profile.professional_positioning.title} required />
            <TextField name="city" label="Cidade" value={profile.candidate.location.city} />
            <TextField name="state" label="Estado ou região" value={profile.candidate.location.state} />
            <TextField name="country" label="País de residência" value={profile.candidate.location.country} />
            <TextField name="summary" label="Resumo profissional" value={profile.professional_positioning.summary} multiline />
            <TextField name="focus" label="Áreas de atuação — uma por linha" value={profile.professional_positioning.focus.join("\n")} multiline />
          </div>
        </fieldset>

        <fieldset disabled={saving}>
          <legend>Objetivos e disponibilidade</legend>

          <div className="form-grid">
            <TextField name="primary_roles" label="Cargos principais — um por linha" value={profile.candidate.career_target.primary_roles.join("\n")} multiline />
            <TextField name="secondary_roles" label="Cargos adicionais — um por linha" value={profile.candidate.career_target.secondary_roles.join("\n")} multiline />
            <TextField name="seniority" label="Níveis desejados — um por linha" value={profile.candidate.career_target.seniority.join("\n")} multiline />
            <TextField name="primary_goal" label="Objetivo principal" value={profile.candidate.employment_status.primary_goal} />
            <TextField name="priority" label="Prioridade da busca" value={profile.candidate.employment_status.priority} />
            <TextField name="employment_type_priority" label="Tipos de contratação — um por linha" value={profile.candidate.work_preferences.employment_type_priority.join("\n")} multiline />
            <TextField name="preferred_location" label="Locais de interesse — um por linha" value={profile.candidate.work_preferences.preferred_location.join("\n")} multiline />
          </div>

          <div className="profile-checkboxes">
            <Checkbox name="currently_clt" label="Atualmente trabalho em regime CLT" checked={profile.candidate.employment_status.currently_clt} />
            <Checkbox name="actively_seeking" label="Estou buscando oportunidades" checked={profile.candidate.employment_status.actively_seeking} />
            <Checkbox name="remote" label="Aceito trabalho remoto" checked={profile.candidate.work_preferences.remote} />
            <Checkbox name="hybrid" label="Aceito trabalho híbrido" checked={profile.candidate.work_preferences.hybrid} />
            <Checkbox name="onsite" label="Aceito trabalho presencial" checked={profile.candidate.work_preferences.onsite} />
            <Checkbox name="relocation" label="Tenho disponibilidade para mudar de residência" checked={profile.candidate.work_preferences.relocation} />
          </div>
        </fieldset>

        <fieldset disabled={saving}>
          <legend>Competências</legend>
          <p>Escreva uma competência por linha em cada campo.</p>

          <div className="form-grid">
            {skillFields.map(([key, label]) => (
              <TextField
                key={key}
                name={`skills-${key}`}
                label={label}
                value={profile.skills[key].join("\n")}
                multiline
              />
            ))}
          </div>
        </fieldset>

        <fieldset disabled={saving}>
          <legend>Idiomas e links</legend>

          <div className="form-grid">
            <TextField name="portuguese" label="Nível de português" value={profile.languages.portuguese} />
            <TextField name="english" label="Nível de inglês" value={profile.languages.english} />
            <TextField name="portfolio_url" label="Link do portfólio" value={profile.portfolio.portfolio_url} />
            <TextField name="github_url" label="Link do GitHub" value={profile.portfolio.github_url} />
            <TextField name="linkedin_url" label="Link do LinkedIn" value={profile.portfolio.linkedin_url} />
          </div>
        </fieldset>

        <fieldset disabled={saving}>
  <legend>Histórico profissional e acadêmico</legend>

  <ProfileSections
    profile={profile}
    onChange={setProfile}
  />
</fieldset>

<p className="form-help">
  Confira suas alterações antes de salvar.
  Registros removidos serão excluídos do perfil ao clicar em
  “Salvar meu perfil”.
</p>

        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Salvando..." : "Salvar meu perfil"}
        </button>
      </form>
    </section>
  );
}
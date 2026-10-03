import type { MasterProfile } from "../../types/profile";

type SectionName = "education" | "experience" | "projects";
type Entry = Record<string, unknown>;

type Field = {
  key: string;
  label: string;
  kind?: "text" | "multiline" | "list" | "boolean";
};

type Section = {
  key: SectionName;
  title: string;
  singular: string;
  fields: Field[];
  empty: Entry;
};

const sections: Section[] = [
    {
    key: "education",
    title: "Formação",
    singular: "formação",
    fields: [
      { key: "degree", label: "Curso ou formação" },
      { key: "institution", label: "Instituição" },
      { key: "status", label: "Situação — inclua o ano de conclusão" },
      { key: "start", label: "Início da formação — AAAA-MM" },
      { key: "end", label: "Conclusão da formação — AAAA-MM" },
    ],
    empty: {
      degree: "",
      institution: "",
      status: "",
      start: null,
      end: null,
    },
  },
    {
    key: "experience",
    title: "Experiências",
    singular: "experiência",
    fields: [
      { key: "company", label: "Empresa ou organização" },
      { key: "role", label: "Cargo ou atividade" },
      { key: "employment_type", label: "Tipo de contratação" },
      { key: "start", label: "Início — por exemplo, 2025-03" },
      {
        key: "end",
        label: "Fim da experiência — AAAA-MM; deixe vazio se atual",
      },
      {
        key: "current",
        label: "Ainda exerço esta atividade",
        kind: "boolean",
      },
      { key: "location", label: "Localização" },
      { key: "work_model", label: "Modalidade de trabalho" },
      {
        key: "technologies",
        label: "Ferramentas — uma por linha",
        kind: "list",
      },
      {
        key: "responsibilities",
        label: "Atividades realizadas — uma por linha",
        kind: "list",
      },
    ],
    empty: {
      company: "",
      role: "",
      employment_type: "",
      start: "",
      end: null,
      current: false,
      location: "",
      work_model: "",
      technologies: [],
      responsibilities: [],
      achievements: [],
    },
  },
  {
    key: "projects",
    title: "Projetos",
    singular: "projeto",
    fields: [
      { key: "name", label: "Nome do projeto" },
      { key: "description", label: "Descrição", kind: "multiline" },
      { key: "technologies", label: "Ferramentas — uma por linha", kind: "list" },
      { key: "context", label: "Contexto do projeto", kind: "multiline" },
    ],
    empty: {
      name: "",
      description: "",
      technologies: [],
      context: null,
      authorized_for_portfolio: null,
    },
  },
];

function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asLines(value: unknown): string {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string").join("\n")
    : "";
}

type ProfileSectionsProps = {
  profile: MasterProfile;
  onChange: (profile: MasterProfile) => void;
};

export default function ProfileSections({
  profile,
  onChange,
}: ProfileSectionsProps) {
  function updateEntry(
    section: SectionName,
    index: number,
    field: string,
    value: unknown,
  ) {
    onChange({
      ...profile,
      [section]: profile[section].map((entry, position) =>
        position === index ? { ...entry, [field]: value } : entry,
      ),
    });
  }

  function addEntry(section: Section) {
    onChange({
      ...profile,
      [section.key]: [
        ...profile[section.key],
        structuredClone(section.empty),
      ],
    });
  }

  function removeEntry(section: SectionName, index: number) {
    onChange({
      ...profile,
      [section]: profile[section].filter((_, position) => position !== index),
    });
  }

  return (
    <>
      {sections.map((section) => (
        <fieldset key={section.key}>
          <legend>{section.title}</legend>

          {profile[section.key].length === 0 && (
            <p>Nenhum registro nesta seção.</p>
          )}

          {profile[section.key].map((entry, index) => (
            <div className="profile-entry" key={`${section.key}-${index}`}>
              <h3>{section.title} — registro {index + 1}</h3>

              <div className="form-grid">
                {section.fields.map((field) => {
                  const id = `profile-${section.key}-${index}-${field.key}`;

                  if (field.kind === "boolean") {
                    return (
                      <label className="profile-checkbox" key={field.key}>
                        <input
                          id={id}
                          type="checkbox"
                          checked={entry[field.key] === true}
                          onChange={(event) =>
                            updateEntry(
                              section.key,
                              index,
                              field.key,
                              event.target.checked,
                            )
                          }
                        />
                        <span>{field.label}</span>
                      </label>
                    );
                  }

                  const multiline =
                    field.kind === "list" || field.kind === "multiline";

                  const value =
                    field.kind === "list"
                      ? asLines(entry[field.key])
                      : asText(entry[field.key]);

                  function update(value: string) {
                    updateEntry(
                      section.key,
                      index,
                      field.key,
                      field.kind === "list" ? value.split("\n") : value,
                    );
                  }

                  return (
                    <div className="form-field" key={field.key}>
                      <label htmlFor={id}>{field.label}</label>

                      {multiline ? (
                        <textarea
                          id={id}
                          value={value}
                          rows={4}
                          onChange={(event) => update(event.target.value)}
                        />
                      ) : (
                        <input
                          id={id}
                          value={value}
                          onChange={(event) => update(event.target.value)}
                        />
                      )}
                    </div>
                  );
                })}
              </div>

              {section.key === "experience" && (
                <p className="form-help">
                  Resultados e métricas existentes serão preservados.
                  A edição deles será acrescentada separadamente.
                </p>
              )}

              <button
                type="button"
                onClick={() => removeEntry(section.key, index)}
              >
                Remover este registro
              </button>
            </div>
          ))}

          <button type="button" onClick={() => addEntry(section)}>
            Adicionar {section.singular}
          </button>
        </fieldset>
      ))}
    </>
  );
}

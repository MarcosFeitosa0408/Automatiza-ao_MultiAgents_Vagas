export interface MasterProfile {
  schema_version: string;
  candidate_id: string;

  candidate: {
    name: string;
    email?: string;
    phone?: string;
    location: {
      city: string;
      state: string;
      country: string;
    };
    employment_status: {
      currently_clt: boolean;
      actively_seeking: boolean;
      priority: string;
      primary_goal: string;
    };
    career_target: {
      primary_roles: string[];
      secondary_roles: string[];
      seniority: string[];
    };
    work_preferences: {
      employment_type_priority: string[];
      remote: boolean;
      hybrid: boolean;
      onsite: boolean;
      preferred_location: string[];
      relocation: boolean;
    };
  };

  professional_positioning: {
    title: string;
    summary: string;
    focus: string[];
  };

  skills: {
    core: string[];
    database: string[];
    python: string[];
    analytics: string[];
    tools: string[];
    automation: string[];
  };

  languages: {
    portuguese: string;
    english: string;
  };

  portfolio: {
    portfolio_url: string;
    github_url: string;
    linkedin_url: string;
  };

  // Seções preservadas integralmente durante a edição desta tela.
  education: Record<string, unknown>[];
  experience: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  evidence_policy: Record<string, unknown>;
}
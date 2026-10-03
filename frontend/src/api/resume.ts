import { apiRequest } from "./client";

export interface ResumePreview {
  application_id: string;
  job_title: string;
  company: string;
  name: string;
  email: string;
  phone: string;
  location: string;
  professional_title: string;
  professional_summary: string;
  skills: string[];
  education: {
    degree: string;
    institution: string;
    status: string;
    start?: string | null;
    end?: string | null;
  }[];
  experience: {
    company: string;
    role: string;
    employment_type: string;
    start: string;
    end?: string | null;
    current: boolean;
    location: string;
    work_model: string;
    technologies: string[];
    responsibilities: string[];
    achievements: {
      metric: string;
      value: number;
      description: string;
      unit?: string | null;
      approximate: boolean;
      period?: string | null;
    }[];
  }[];
  projects: {
    name: string;
    description: string;
    technologies: string[];
    context?: string | null;
    authorized_for_portfolio?: boolean | null;
  }[];
  languages: Record<string, string>;
  links: Record<string, string>;
  ats_keywords: string[];
  unsupported_requirements: string[];
  warnings: string[];
}

export function generateResumePreview(
  applicationId: string,
): Promise<ResumePreview> {
  return apiRequest<ResumePreview>(
    `/job-applications/${encodeURIComponent(applicationId)}/resume-preview`,
    { method: "POST" },
  );
}
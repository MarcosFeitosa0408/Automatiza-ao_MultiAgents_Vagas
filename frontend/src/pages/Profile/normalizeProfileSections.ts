import type { MasterProfile } from "../../types/profile";

const listFields = {
  education: [],
  experience: ["technologies", "responsibilities"],
  projects: ["technologies"],
} as const;

const textFields = {
  education: ["degree", "institution", "status", "start", "end"],
  experience: [
    "company",
    "role",
    "employment_type",
    "start",
    "location",
    "work_model",
  ],
  projects: ["name", "description", "context"],
} as const;

export function normalizeProfileSections(
  profile: MasterProfile,
): MasterProfile {
  const updated = structuredClone(profile);

  const sections = ["education", "experience", "projects"] as const;

  for (const section of sections) {
    updated[section] = updated[section].map((entry) => {
      const normalized = { ...entry };

      for (const field of listFields[section]) {
        const value = entry[field];

        if (Array.isArray(value)) {
          normalized[field] = value
            .filter((item): item is string => typeof item === "string")
            .map((item) => item.trim())
            .filter(Boolean);
        }
      }

      for (const field of textFields[section]) {
        const value = entry[field];

        if (typeof value === "string") {
          normalized[field] = value.trim();
        }
      }

      return normalized;
    });
  }

  return updated;
}
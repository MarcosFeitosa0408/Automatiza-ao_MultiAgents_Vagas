import { apiRequest } from "./client";
import type { JobApplicationObject } from "../types/api";

export type JobDetailsUpdateRequest = {
  description: string;
  requirements: string[];
  desirable_requirements: string[];
};

export function updateJobDetails(
  applicationId: string,
  request: JobDetailsUpdateRequest,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/job-details`,
    {
      method: "PATCH",
      body: JSON.stringify(request),
    },
  );
}
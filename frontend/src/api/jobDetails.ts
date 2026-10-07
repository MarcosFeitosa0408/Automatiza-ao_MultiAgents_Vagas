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
export function correctJobDetails(
  applicationId: string,
  request: JobDetailsUpdateRequest,
  expectedUpdatedAt: string,
): Promise<JobApplicationObject> {
  return apiRequest(`/job-applications/${encodeURIComponent(applicationId)}/correct-details`, {
    method: "PATCH",
    body: JSON.stringify({ ...request, expected_updated_at: expectedUpdatedAt, confirmed: true }),
  });
}

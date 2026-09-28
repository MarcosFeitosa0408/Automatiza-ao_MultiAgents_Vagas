import { apiRequest } from "./client";
import type {
  DeleteJobApplicationResponse,
  FollowUpCheckResponse,
  JobApplicationCreateRequest,
  JobApplicationObject,
  StoredTrackingStatusUpdateRequest,
} from "../types/api";

export function createJobApplication(
  request: JobApplicationCreateRequest,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>("/job-applications", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function listJobApplications(): Promise<JobApplicationObject[]> {
  return apiRequest<JobApplicationObject[]>("/job-applications");
}

export function getJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}`,
  );
}

export function deleteJobApplication(
  applicationId: string,
): Promise<DeleteJobApplicationResponse> {
  return apiRequest<DeleteJobApplicationResponse>(
    `/job-applications/${encodeURIComponent(applicationId)}`,
    {
      method: "DELETE",
    },
  );
}

export function qualifyJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/qualify`,
    {
      method: "POST",
    },
  );
}

export function personalizeJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/personalize`,
    {
      method: "POST",
    },
  );
}

export function prepareJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/prepare`,
    {
      method: "POST",
    },
  );
}

export function approveJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/approve`,
    {
      method: "POST",
    },
  );
}

export function rejectJobApplication(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/reject`,
    {
      method: "POST",
    },
  );
}

export function startJobApplicationTracking(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/tracking/start`,
    {
      method: "POST",
    },
  );
}

export function updateJobApplicationTracking(
  applicationId: string,
  request: StoredTrackingStatusUpdateRequest,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/tracking/status`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export function checkJobApplicationFollowUp(
  applicationId: string,
): Promise<FollowUpCheckResponse> {
  return apiRequest<FollowUpCheckResponse>(
    `/job-applications/${encodeURIComponent(applicationId)}/follow-up/check`,
    {
      method: "POST",
    },
  );
}

export function registerJobApplicationFollowUp(
  applicationId: string,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>(
    `/job-applications/${encodeURIComponent(applicationId)}/follow-up/register`,
    {
      method: "POST",
    },
  );
}
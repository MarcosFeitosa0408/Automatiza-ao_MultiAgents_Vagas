import { apiRequest } from "./client";
import type {
  ApplicationPreparation,
  JobAnalysisRequest,
  JobApplicationObject,
  PersonalizationResult,
  QualificationResult,
  TrackingStatusUpdateRequest,
} from "../types/api";

export function analyzeJob(
  request: JobAnalysisRequest,
): Promise<QualificationResult> {
  return apiRequest<QualificationResult>("/analyze-job", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function personalizeJob(
  request: JobAnalysisRequest,
): Promise<PersonalizationResult> {
  return apiRequest<PersonalizationResult>("/personalize-job", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function prepareApplication(
  request: JobAnalysisRequest,
): Promise<ApplicationPreparation> {
  return apiRequest<ApplicationPreparation>("/prepare-application", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function approveApplication(
  application: ApplicationPreparation,
): Promise<ApplicationPreparation> {
  return apiRequest<ApplicationPreparation>("/approve-application", {
    method: "POST",
    body: JSON.stringify({ application }),
  });
}

export function rejectApplication(
  application: ApplicationPreparation,
): Promise<ApplicationPreparation> {
  return apiRequest<ApplicationPreparation>("/reject-application", {
    method: "POST",
    body: JSON.stringify({ application }),
  });
}

export function updateTrackingStatus(
  request: TrackingStatusUpdateRequest,
): Promise<JobApplicationObject> {
  return apiRequest<JobApplicationObject>("/update-tracking-status", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
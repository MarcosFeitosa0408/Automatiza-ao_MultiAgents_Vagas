export type WorkModel =
  | "REMOTE"
  | "HYBRID"
  | "ONSITE"
  | "UNKNOWN";

export type JobStatus =
  | "DISCOVERED"
  | "QUALIFIED"
  | "VALIDATION_REVIEW"
  | "APPROVED"
  | "READY_TO_APPLY"
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "FINAL"
  | "OFFER"
  | "HIRED"
  | "REJECTED"
  | "WITHDRAWN"
  | "NO_RESPONSE"
  | "EXPIRED"
  | "APPLICATION_FAILED";

export type ApplicationDecision =
  | "PENDING_HUMAN_APPROVAL"
  | "APPROVED_BY_HUMAN"
  | "REJECTED_BY_HUMAN";

export interface JobOpportunity {
  job_id: string;
  title: string;
  company: string;
  source: string;
  url: string | null;
  location: string;
  work_model: WorkModel;
  employment_type: string;
  description: string;
  requirements: string[];
  desirable_requirements: string[];
  discovered_at: string;
  status: JobStatus;
}

export interface JobAnalysisRequest {
  job_id: string;
  title: string;
  company: string;
  source?: string;
  location?: string;
  work_model?: WorkModel;
  employment_type?: string;
  description?: string;
  requirements?: string[];
  desirable_requirements?: string[];
}

export interface ApplicationPreparation {
  job_id: string;
  approved_for_human_review: boolean;
  decision: ApplicationDecision;
  ready_to_apply: boolean;
  blocking_issues: string[];
  warnings: string[];
}

export interface JobApplicationCreateRequest {
  application_id: string;
  job: JobOpportunity;
}

export interface TrackingEvent {
  status: JobStatus;
  note: string;
  occurred_at: string;
}

export interface ApplicationTracking {
  job_id: string;
  current_status: JobStatus;
  history: TrackingEvent[];
  followup_count: number;
  last_followup_at: string | null;
}

export interface TrackingStatusUpdateRequest {
  tracking: ApplicationTracking;
  new_status: JobStatus;
  note?: string;
}

export interface StoredTrackingStatusUpdateRequest {
  new_status: JobStatus;
  note?: string;
}

export interface FollowUpCheckResponse {
  application_id: string;
  should_follow_up: boolean;
  followup_count: number;
  last_followup_at: string | null;
}

export interface DeleteJobApplicationResponse {
  application_id: string;
  deleted: boolean;
}

export interface QualificationBreakdown {
  technical_skills: number;
  professional_experience: number;
  responsibilities: number;
  seniority: number;
  location_work_model: number;
  ats_compatibility: number;
}

export interface QualificationResult {
  job_id: string;
  fit_score: number;
  recommendation: string;
  matched_skills: string[];
  missing_skills: string[];
  eliminatory_gaps: string[];
  breakdown: QualificationBreakdown;
  reasoning: string[];
}

export interface PersonalizationResult {
  job_id: string;
  professional_title: string;
  professional_summary: string;
  selected_skills: string[];
  selected_experiences: string[];
  selected_projects: string[];
  ats_keywords: string[];
  unsupported_requirements: string[];
  evidence_verified: boolean;
}

export interface JobApplicationObject {
  application_id: string;
  job: JobOpportunity;
  qualification: QualificationResult | null;
  personalization: PersonalizationResult | null;
  preparation: ApplicationPreparation | null;
  tracking: ApplicationTracking | null;
  created_at: string;
  updated_at: string;
}
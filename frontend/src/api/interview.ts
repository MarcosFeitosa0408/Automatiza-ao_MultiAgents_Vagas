import { apiRequest } from "./client";

export interface InterviewQuestion {
  question_id: string;
  category: string;
  question: string;
  guidance: string[];
}

export interface InterviewPlan {
  job_id: string;
  job_title: string;
  company: string;
  questions: InterviewQuestion[];
  preparation_notes: string[];
}

export function generateInterviewPlan(
  applicationId: string,
): Promise<InterviewPlan> {
  return apiRequest<InterviewPlan>(
    `/job-applications/${encodeURIComponent(applicationId)}/interview-plan`,
    { method: "POST" },
  );
}
import { apiRequest } from "./client";

export interface InterviewQuestion {
  question_id: string;
  category: string;
  question: string;
  guidance: string[];
}

export interface InterviewFeedback {
  question_id: string;
  score: number;
  criteria: { name: string; score: number; maximum: number; guidance: string }[];
  limitation: string;
}

export function evaluateInterviewAnswer(applicationId: string, questionId: string, answer: string): Promise<InterviewFeedback> {
  return apiRequest(`/job-applications/${encodeURIComponent(applicationId)}/interview-feedback`, {
    method: "POST", body: JSON.stringify({ question_id: questionId, answer }),
  });
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

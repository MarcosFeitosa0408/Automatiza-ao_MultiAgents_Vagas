import { apiRequest } from "./client";

export interface JobApplicationMetrics {
  total_applications: number;
  screening_or_beyond: number;
  interviews: number;
  finals: number;
  offers: number;
  hires: number;
  rejections: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  hire_rate: number;
}

export function getJobApplicationMetrics(): Promise<JobApplicationMetrics> {
  return apiRequest<JobApplicationMetrics>("/job-applications/metrics");
}
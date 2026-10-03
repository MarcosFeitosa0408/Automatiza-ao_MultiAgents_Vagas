import { apiRequest } from "./client";
import type { JobOpportunity } from "../types/api";

export interface OpportunitySearchRequest {
  query: string;
  country: string;
  location: string;
}

export function searchOpportunities(
  request: OpportunitySearchRequest,
): Promise<JobOpportunity[]> {
  return apiRequest<JobOpportunity[]>("/opportunities/search", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
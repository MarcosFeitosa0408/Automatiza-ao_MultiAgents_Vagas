import { apiRequest } from "./client";
import type { JobApplicationObject, JobStatus } from "../types/api";
export function recordProgress(id:string,newStatus:JobStatus,expectedStatus:JobStatus|null,note:string) {
  return apiRequest<JobApplicationObject>(`/job-applications/${encodeURIComponent(id)}/progress`,{method:"POST",body:JSON.stringify({new_status:newStatus,expected_status:expectedStatus,confirmed:true,note})});
}

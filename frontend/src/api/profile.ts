import { apiRequest } from "./client";
import type { MasterProfile } from "../types/profile";

export function getCandidateProfile(): Promise<MasterProfile> {
  return apiRequest<MasterProfile>("/profile");
}

export function saveCandidateProfile(
  profile: MasterProfile,
): Promise<MasterProfile> {
  return apiRequest<MasterProfile>("/profile", {
    method: "PUT",
    body: JSON.stringify(profile),
  });
}
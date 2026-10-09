import { apiRequest } from "./client";

export type SubscriptionStatus = {
  access_allowed: boolean;
  read_allowed: boolean;
  kind:
    | "admin"
    | "existing"
    | "pending"
    | "blocked"
    | "restricted"
    | "trial_available"
    | "trial"
    | "consultation"
    | "trial_expired"
    | "paid"
    | "paid_expired";
  trial_available: boolean;
  trial_started_at: number | null;
  trial_ends_at: number | null;
  consultation_ends_at: number | null;
  paid_ends_at?: number | null;
  next_payment_amount?: 1990 | 2990;
};

export function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return apiRequest<SubscriptionStatus>("/auth/subscription");
}

export function activateTrial(): Promise<SubscriptionStatus> {
  return apiRequest<SubscriptionStatus>("/auth/trial", {
    method: "POST",
  });
}

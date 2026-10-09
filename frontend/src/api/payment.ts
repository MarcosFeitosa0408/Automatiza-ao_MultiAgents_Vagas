import { apiRequest } from "./client";

export type PixPayment = {
  id: string;
  amount: 1990 | 2990;
  state:
    | "CREATING"
    | "WAITING"
    | "PAID"
    | "DECLINED"
    | "CANCELED"
    | "EXPIRED";
  environment: "sandbox" | "production";
  qr_text: string | null;
  period_start: number | null;
  period_end: number | null;
};

export function createPixPayment(taxId: string): Promise<PixPayment> {
  return apiRequest<PixPayment>("/auth/pix", {
    method: "POST",
    body: JSON.stringify({ tax_id: taxId }),
  });
}

export function getPixPayment(paymentId: string): Promise<PixPayment> {
  return apiRequest<PixPayment>(
    `/auth/pix/${encodeURIComponent(paymentId)}`,
  );
}

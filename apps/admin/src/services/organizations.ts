import { apiClient } from "@silveryarn/web-shared/api";
import type { Organization } from "@/types";

/** GET /organizations — admin 전용(decisions.md #59, I2). */
export async function listOrganizations(): Promise<Organization[]> {
  return apiClient.get<Organization[]>("/organizations");
}

/** POST /organizations — 시설 신규 등록. B2G 계약 결과를 운영자가 직접 입력한다. */
export async function createOrganization(name: string): Promise<Organization> {
  return apiClient.post<Organization>("/organizations", { name });
}

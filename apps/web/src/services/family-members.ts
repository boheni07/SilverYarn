import { apiClient } from "@silveryarn/web-shared/api";
import type { FamilyMember } from "@/types";

export async function listFamilyMembers(userId: string): Promise<FamilyMember[]> {
  return apiClient.get<FamilyMember[]>(`/users/${userId}/family-members`);
}

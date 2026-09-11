import { apiClient } from "@silveryarn/web-shared/api";
import type { FamilyMember } from "@/types";

/** GET /users/{userId}/family-members — admin은 `authorize_user_access`의
 * `is_admin` 우회로 2FA 없이도 조회 가능(core/auth.py). */
export async function listFamilyMembers(userId: string): Promise<FamilyMember[]> {
  return apiClient.get<FamilyMember[]>(`/users/${userId}/family-members`);
}

/** design.md §3.1 FamilyMember — schema.md `family_members` 테이블과 1:1 매핑. */
export type FamilyRole = "family" | "caregiver" | "social_worker" | "admin";

export interface FamilyMember {
  id: string;
  userId: string;
  role: FamilyRole;
  name: string;
  contact: string;
  twoFactorEnabled: boolean;
}

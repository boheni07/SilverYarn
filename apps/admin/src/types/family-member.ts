/** design.md §3.1 FamilyMember — schema.md `family_members` 테이블과 1:1 매핑.
 * apps/web과 동일 정의(공유 패키지 대상은 아직 아님 — 도메인 타입은 각 앱 스코프). */
export type FamilyRole = "family" | "caregiver" | "social_worker" | "admin";

export interface FamilyMember {
  id: string;
  userId: string;
  role: FamilyRole;
  name: string;
  contact: string;
  twoFactorEnabled: boolean;
}

export const FAMILY_ROLE_LABEL: Record<FamilyRole, string> = {
  family: "가족",
  caregiver: "돌봄 제공자",
  social_worker: "복지사",
  admin: "관리자",
};

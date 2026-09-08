/** design.md §3.1(v0.9) User — schema.md `users` 테이블과 1:1 매핑.
 * apps/web/src/types/user.ts와 동일 — 공유 패키지가 아직 없어 두 앱이 각자 들고 있다. */
export interface User {
  id: string;
  name: string;
  birthDate?: string; // ISO date
  primaryDeviceId?: string;
  createdAt: string;
  updatedAt: string;
}

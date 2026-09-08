/** design.md §3.1(v0.9) User — schema.md `users` 테이블과 1:1 매핑. */
export interface User {
  id: string;
  name: string;
  birthDate?: string; // ISO date
  primaryDeviceId?: string;
  createdAt: string;
  updatedAt: string;
}

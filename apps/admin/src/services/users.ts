import { apiClient } from "@/lib/api/client";
import type { Pagination } from "@/lib/api/client";
import type { User } from "@/types";

// Presentation(app/·components/·features/)이 lib/api를 직접 import할 수 없으므로
// (eslint import/no-restricted-paths) 이 타입은 services/를 통해서만 재노출한다.
export type { Pagination };

export async function getUser(userId: string): Promise<User> {
  return apiClient.get<User>(`/users/${userId}`, { authToken: "dev" });
}

/** GET /users?page=&page_size= — apps/admin 사용자 목록 화면(신규, 2026-09-08). */
export async function listUsers(page: number, pageSize: number): Promise<{ users: User[]; pagination: Pagination }> {
  const { data, pagination } = await apiClient.getPaginated<User>(
    `/users?page=${page}&page_size=${pageSize}`,
    { authToken: "dev" },
  );
  return { users: data, pagination };
}

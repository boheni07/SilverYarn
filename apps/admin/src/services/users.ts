import { apiClient } from "@silveryarn/web-shared/api";
import type { Pagination } from "@silveryarn/web-shared/api";
import type { User } from "@/types";

// Presentation(app/·components/·features/)이 lib/api를 직접 import할 수 없으므로
// (eslint import/no-restricted-paths) 이 타입은 services/를 통해서만 재노출한다.
export type { Pagination };

export async function getUser(userId: string): Promise<User> {
  return apiClient.get<User>(`/users/${userId}`);
}

/** GET /users?page=&page_size=&name= — apps/admin 사용자 목록 화면(신규 2026-09-08,
 * name 이름 검색 추가 2026-09-08). */
export async function listUsers(params: {
  page: number;
  pageSize: number;
  name?: string;
}): Promise<{ users: User[]; pagination: Pagination }> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  });
  if (params.name) query.set("name", params.name);

  const { data, pagination } = await apiClient.getPaginated<User>(`/users?${query}`);
  return { users: data, pagination };
}

import Link from "next/link";
import { listUsers } from "@/services/users";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/services/errors";
import type { Pagination } from "@/services/users";
import type { User } from "@/types";

const PAGE_SIZE = 20;

interface UsersPageProps {
  searchParams: Promise<{ page?: string }>;
}

/**
 * structure.md §5 화면 인벤토리 표에는 없지만(본문 설명에만 "사용자 관리" 언급),
 * apps/admin의 실질적 진입점 — GET /users(2026-09-08 신규)를 써서 관리자가 사용자
 * ID를 미리 몰라도 기기 관리·동기화 모니터링으로 들어갈 수 있게 한다.
 */
export default async function UsersPage({ searchParams }: UsersPageProps) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam ?? "1") || 1);

  let users: User[];
  let pagination: Pagination | null = null;
  let error: string | null = null;
  try {
    const result = await listUsers(page, PAGE_SIZE);
    users = result.users;
    pagination = result.pagination;
  } catch (e) {
    error = e instanceof ApiError ? e.message : "사용자 목록을 불러오지 못했습니다.";
    users = [];
  }

  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1;

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">사용자 관리</h1>
      <p className="mt-2 text-ink-muted">
        {pagination ? `전체 ${pagination.total}명 · ${page}/${totalPages}페이지` : "전체 사용자 목록입니다."}
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && users.length === 0 && (
        <p className="mt-6 text-ink-muted">등록된 사용자가 없습니다.</p>
      )}

      <ul className="mt-6 flex flex-col gap-4">
        {users.map((user) => (
          <li key={user.id}>
            <Link href={`/devices?userId=${user.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <h2 className="font-editorial text-h2 font-semibold text-ink">{user.name}</h2>
                <p className="mt-1 text-caption text-ink-muted">
                  {user.birthDate ? `생년월일 ${user.birthDate} · ` : ""}
                  가입일 {new Date(user.createdAt).toLocaleDateString("ko-KR")}
                </p>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!error && totalPages > 1 && (
        <nav className="mt-8 flex items-center justify-center gap-4">
          {page > 1 ? (
            <Link href={`/users?page=${page - 1}`} className="text-body-compact text-teal-deep underline">
              이전
            </Link>
          ) : (
            <span className="text-body-compact text-ink-faint">이전</span>
          )}
          <span className="text-caption text-ink-muted">
            {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <Link href={`/users?page=${page + 1}`} className="text-body-compact text-teal-deep underline">
              다음
            </Link>
          ) : (
            <span className="text-body-compact text-ink-faint">다음</span>
          )}
        </nav>
      )}
    </main>
  );
}

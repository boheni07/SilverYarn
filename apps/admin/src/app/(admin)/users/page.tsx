import Link from "next/link";
import { listUsers } from "@/services/users";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/services/errors";
import type { Pagination } from "@/services/users";
import type { User } from "@/types";

const PAGE_SIZE = 20;

interface UsersPageProps {
  searchParams: Promise<{ page?: string; name?: string }>;
}

/**
 * structure.md §5 화면 인벤토리 표에는 없지만(본문 설명에만 "사용자 관리" 언급),
 * apps/admin의 실질적 진입점 — GET /users(2026-09-08 신규, 이름 검색 같은 날 추가)를
 * 써서 관리자가 사용자 ID를 미리 몰라도 기기 관리·동기화 모니터링으로 들어갈 수 있게 한다.
 */
export default async function UsersPage({ searchParams }: UsersPageProps) {
  const { page: pageParam, name } = await searchParams;
  const page = Math.max(1, Number(pageParam ?? "1") || 1);

  let users: User[];
  let pagination: Pagination | null = null;
  let error: string | null = null;
  try {
    const result = await listUsers({ page, pageSize: PAGE_SIZE, name });
    users = result.users;
    pagination = result.pagination;
  } catch (e) {
    error = e instanceof ApiError ? e.message : "사용자 목록을 불러오지 못했습니다.";
    users = [];
  }

  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1;

  function pageHref(nextPage: number) {
    const query = new URLSearchParams();
    if (name) query.set("name", name);
    query.set("page", String(nextPage));
    return `/users?${query}`;
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">사용자 관리</h1>
      <p className="mt-2 text-ink-muted">
        {pagination
          ? `${name ? `"${name}" 검색 결과 ` : "전체 "}${pagination.total}명 · ${page}/${totalPages}페이지`
          : "전체 사용자 목록입니다."}
      </p>

      {/* 자바스크립트 없이도 동작하는 순수 GET 폼 — 검색은 새 페이지로 이동하는
          작업이라 클라이언트 상태가 필요 없다. 검색어를 바꾸면 1페이지부터 다시 본다
          (page 인풋을 안 넣어 자연히 리셋됨). */}
      <form action="/users" method="GET" className="mt-6 flex gap-2">
        <input
          type="text"
          name="name"
          defaultValue={name ?? ""}
          placeholder="이름으로 검색"
          className="min-h-11 flex-1 rounded-lg border border-border bg-paper px-4 text-body-compact text-ink outline-none focus-visible:border-teal-deep"
        />
        <button
          type="submit"
          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-teal-deep px-5 font-ui text-body-compact font-medium text-white"
        >
          검색
        </button>
        {name && (
          <Link
            href="/users"
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-border px-5 font-ui text-body-compact text-ink-muted"
          >
            지우기
          </Link>
        )}
      </form>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && users.length === 0 && (
        <p className="mt-6 text-ink-muted">
          {name ? `"${name}"과(와) 일치하는 사용자가 없습니다.` : "등록된 사용자가 없습니다."}
        </p>
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
            <Link href={pageHref(page - 1)} className="text-body-compact text-teal-deep underline">
              이전
            </Link>
          ) : (
            <span className="text-body-compact text-ink-faint">이전</span>
          )}
          <span className="text-caption text-ink-muted">
            {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <Link href={pageHref(page + 1)} className="text-body-compact text-teal-deep underline">
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

import { listOrganizations } from "@/services/organizations";
import { OrganizationForm } from "@/features/organizations/OrganizationForm";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/services/errors";
import type { Organization } from "@/types";

/**
 * decisions.md #59(I2, 2026-09-13 사용자 결정) — B2G 시설 테넌시 안전망의 관리
 * 화면. 시설 등록·목록만 다룬다 — 어르신을 시설에 배정하는 건 `/users` 상세
 * 화면(사용자별 "시설 배정" 폼)에서 한다.
 */
export default async function OrganizationsPage() {
  let organizations: Organization[] = [];
  let error: string | null = null;
  try {
    organizations = await listOrganizations();
  } catch (e) {
    error = e instanceof ApiError ? e.message : "시설 목록을 불러오지 못했습니다.";
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">시설 관리</h1>
      <p className="mt-2 text-ink-muted">
        B2G 시설(요양원·복지관) 단위 테넌시 안전망 — 등록된 시설 소속끼리만 어르신 데이터를 열람할 수 있습니다.
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">{error}</p>
      )}

      {!error && (
        <>
          <h2 className="mt-8 font-editorial text-h2 font-semibold text-ink">등록된 시설</h2>
          {organizations.length === 0 ? (
            <p className="mt-4 text-ink-muted">아직 등록된 시설이 없습니다.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-3">
              {organizations.map((org) => (
                <li key={org.id}>
                  <Card>
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-body-compact text-ink">{org.name}</p>
                      <span className="shrink-0 text-caption text-ink-muted">
                        등록일 {new Date(org.createdAt).toLocaleDateString("ko-KR")}
                      </span>
                    </div>
                  </Card>
                </li>
              ))}
            </ul>
          )}

          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">새 시설 등록</h2>
          <div className="mt-4">
            <OrganizationForm />
          </div>
        </>
      )}
    </main>
  );
}

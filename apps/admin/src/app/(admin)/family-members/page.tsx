import Link from "next/link";
import { getUser } from "@/services/users";
import { listFamilyMembers } from "@/services/family-members";
import { listOrganizations } from "@/services/organizations";
import { InvitationForm } from "@/features/invitations/InvitationForm";
import { AssignUserOrganizationForm } from "@/features/organizations/AssignUserOrganizationForm";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/services/errors";
import { FAMILY_ROLE_LABEL } from "@/types";
import type { FamilyMember, Organization, User } from "@/types";

interface FamilyMembersPageProps {
  searchParams: Promise<{ userId?: string }>;
}

/**
 * design.md §2.9 "가족 계정 웹 콘솔 초대" 단계 — 신규 온보딩된 어르신은 Device
 * Token만 있어 스스로 첫 가족 구성원을 연결할 수 없다(v0.28에서 별도 설계 결정
 * 대기로 남겨둔 항목). admin이 대신 초대를 만드는 경로로 확정(2026-09-11) —
 * apps/admin의 첫 쓰기 화면.
 */
export default async function FamilyMembersPage({ searchParams }: FamilyMembersPageProps) {
  const { userId } = await searchParams;

  if (!userId) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-12">
        <p className="text-ink-muted">
          사용자 ID가 필요합니다. <Link href="/users" className="text-teal-deep underline">사용자 목록으로</Link>
        </p>
      </main>
    );
  }

  let user: User | null = null;
  let members: FamilyMember[] = [];
  let organizations: Organization[] = [];
  let error: string | null = null;
  try {
    [user, members, organizations] = await Promise.all([
      getUser(userId),
      listFamilyMembers(userId),
      listOrganizations(),
    ]);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "정보를 불러오지 못했습니다.";
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">가족 구성원 관리</h1>
      <p className="mt-2 text-ink-muted">{user ? `${user.name}님의 가족·복지사 구성원입니다.` : "구성원 목록입니다."}</p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">
          {error}
        </p>
      )}

      {!error && (
        <>
          {organizations.length > 0 && (
            <>
              <h2 className="mt-8 font-editorial text-h2 font-semibold text-ink">
                시설 배정 (decisions.md #59)
              </h2>
              <div className="mt-4">
                <AssignUserOrganizationForm
                  userId={userId}
                  currentOrgId={user?.orgId}
                  organizations={organizations}
                />
              </div>
            </>
          )}

          <h2 className="mt-8 font-editorial text-h2 font-semibold text-ink">등록된 구성원</h2>
          {members.length === 0 ? (
            <p className="mt-4 text-ink-muted">아직 등록된 가족/복지사가 없습니다.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-3">
              {members.map((m) => (
                <li key={m.id}>
                  <Card>
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-body-compact text-ink">{m.name}</p>
                      <div className="flex shrink-0 gap-2">
                        {m.orgId && (
                          <span className="rounded-full bg-gold-tint px-3 py-1 text-caption font-medium text-gold-deep">
                            {organizations.find((o) => o.id === m.orgId)?.name ?? "시설 소속"}
                          </span>
                        )}
                        <span className="rounded-full bg-subtle px-3 py-1 text-caption font-medium text-ink-muted">
                          {FAMILY_ROLE_LABEL[m.role]}
                        </span>
                      </div>
                    </div>
                  </Card>
                </li>
              ))}
            </ul>
          )}

          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">새 구성원 초대</h2>
          <div className="mt-4">
            <InvitationForm userId={userId} organizations={organizations} />
          </div>
        </>
      )}
    </main>
  );
}

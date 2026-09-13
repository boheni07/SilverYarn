import Link from "next/link";
import { redirect } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { getMyMemberships } from "@/services/me";
import { getUser } from "@/services/users";
import { ApiError } from "@/services/errors";

/**
 * 로그인 세션 → 어르신 연결 홈. `GET /me`(백엔드 `AuthContext.memberships`)로
 * 로그인한 가족구성원이 연결된 어르신을 자동 해석한다 — 예전 W-02 "임시 홈"(어르신
 * 계정 ID를 직접 입력받던 화면)을 대체한다.
 *
 * - 연결된 어르신이 1명(파일럿 스코프의 지배적 케이스)이면 URL에 어르신 ID가 전혀
 *   드러나지 않고 곧장 대시보드로 이동한다.
 * - 여러 명이면 고를 수 있게 목록을 보여준다(클릭으로만 `?elder=`가 채워짐 — 직접
 *   입력하지 않는다).
 * - 0명(초대를 아직 수락하지 않은 계정)이면 `require_auth`가 403으로 알려주는 안내
 *   문구를 그대로 보여준다.
 */
export default async function HomePage() {
  let memberships;
  try {
    memberships = await getMyMemberships();
  } catch (e) {
    const message =
      e instanceof ApiError ? e.message : "연결된 어르신 정보를 불러오지 못했습니다.";
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
        <div className="text-center">
          <h1 className="font-editorial text-display font-bold text-ink">은빛실타래</h1>
        </div>
        <Card className="w-full max-w-md text-center">
          <p className="text-body-compact text-ink-muted">{message}</p>
        </Card>
      </main>
    );
  }

  if (memberships.length === 1) {
    redirect(`/dashboard?elder=${encodeURIComponent(memberships[0].userId)}`);
  }

  const elders = await Promise.all(
    memberships.map(async (m) => {
      try {
        const user = await getUser(m.userId);
        return { userId: m.userId, name: user.name };
      } catch {
        return { userId: m.userId, name: "어르신" };
      }
    }),
  );

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="font-editorial text-display font-bold text-ink">은빛실타래</h1>
        <p className="mt-2 text-body-compact text-ink-muted">연결된 어르신 계정을 선택하세요.</p>
      </div>

      <Card className="w-full max-w-md">
        <ul className="flex flex-col gap-2">
          {elders.map((elder) => (
            <li key={elder.userId}>
              <Link
                href={`/dashboard?elder=${encodeURIComponent(elder.userId)}`}
                className="flex min-h-11 items-center rounded-lg border border-border-soft bg-surface px-4 text-ink hover:bg-subtle-2"
              >
                {elder.name}
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </main>
  );
}

import Link from "next/link";
import { auth, signOut } from "@/auth";

/**
 * 로그인된 관리자 표시 + 로그아웃. 로그인 페이지에선 세션이 없어 아무것도 안 그린다.
 * 루트 레이아웃에 두어 모든 콘솔 화면 상단에 공통으로 나온다.
 */
export async function AppHeader() {
  const session = await auth();
  if (!session?.accessToken) return null;

  return (
    <header className="flex items-center justify-between border-b border-border-soft bg-surface px-4 py-2 text-caption">
      <Link href="/" className="font-editorial font-semibold text-ink">
        은빛실타래 관리자
      </Link>
      <div className="flex items-center gap-3 text-ink-muted">
        {session.user?.name && <span>{session.user.name}</span>}
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/login" });
          }}
        >
          <button type="submit" className="min-h-9 rounded-md border border-border px-3 hover:bg-subtle-2">
            로그아웃
          </button>
        </form>
      </div>
    </header>
  );
}

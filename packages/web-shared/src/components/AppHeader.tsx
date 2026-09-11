import Link from "next/link";
import { auth, signOut } from "../auth";

/**
 * 로그인된 사용자 표시 + 로그아웃 (공유 — apps/web·apps/admin). 세션이 없으면
 * 아무것도 안 그린다(로그인 페이지). 각 앱 루트 레이아웃에서 `<AppHeader brand="..." />`.
 */
export async function AppHeader({ brand }: { brand: string }) {
  const session = await auth();
  if (!session?.accessToken) return null;

  return (
    <header className="flex items-center justify-between border-b border-border-soft bg-surface px-4 py-2 text-caption">
      <Link href="/" className="font-editorial font-semibold text-ink">
        {brand}
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

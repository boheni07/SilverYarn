import { redirect } from "next/navigation";
import { auth, signIn } from "@silveryarn/web-shared/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

/**
 * Keycloak SSO 로그인 진입점(apps/web과 동일 방식, decisions #49). 관리자 콘솔의
 * 화면들은 백엔드에서 `require_roles(admin)` 등으로 다시 인가를 검사하므로 —
 * 여기서는 유효한 세션만 확인하고, admin 권한이 없으면 각 화면이 403을 받는다.
 */
export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string }>;
}) {
  const session = await auth();
  const { callbackUrl } = await searchParams;
  if (session?.accessToken && !session.error) redirect(callbackUrl ?? "/");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="font-editorial text-display font-bold text-ink">은빛실타래 관리자</h1>
        <p className="mt-2 text-body-compact text-ink-muted">운영 콘솔 — 로그인이 필요합니다</p>
      </div>
      <Card className="w-full max-w-md">
        <p className="mb-4 text-caption text-ink-muted">
          관리자 계정으로 로그인합니다. 계정·권한은 Keycloak에서 발급·부여합니다.
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("keycloak", { redirectTo: callbackUrl ?? "/" });
          }}
        >
          <Button type="submit" className="w-full">
            Keycloak으로 로그인
          </Button>
        </form>
      </Card>
    </main>
  );
}

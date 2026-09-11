import { redirect } from "next/navigation";
import { auth, signIn } from "@silveryarn/web-shared/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

/**
 * Keycloak SSO 로그인 진입점. 버튼을 누르면 Auth.js가 Keycloak 인증 페이지로
 * 리다이렉트하고, 돌아오면 httpOnly 세션 쿠키가 설정된다.
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
        <h1 className="font-editorial text-display font-bold text-ink">은빛실타래</h1>
        <p className="mt-2 text-body-compact text-ink-muted">웹 콘솔 — 로그인이 필요합니다</p>
      </div>
      <Card className="w-full max-w-md">
        <p className="mb-4 text-caption text-ink-muted">
          가족·복지사·관리자 계정으로 로그인합니다. 계정은 관리자가 Keycloak에서 발급합니다.
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

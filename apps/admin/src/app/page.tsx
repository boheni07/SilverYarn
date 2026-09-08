"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

/**
 * ⚠️ 임시 진입점 — apps/web/src/app/page.tsx와 동일한 이유: Keycloak 인증이 실제로
 * 붙기 전까지 로그인 화면 대신 이 페이지가 그 자리를 채운다.
 *
 * GET /users(2026-09-08 신규)가 생기기 전까지는 관리자가 사용자 ID를 직접 입력해야만
 * 기기 관리 화면에 들어갈 수 있었다 — 이제는 "/users"가 정식 진입점이고, ID를 이미
 * 아는 경우를 위한 직접 이동 입력은 보조 수단으로만 남겨 뒀다.
 */
export default function HomePage() {
  const router = useRouter();
  const [userId, setUserId] = useState("");

  function goTo(path: string) {
    if (!userId.trim()) return;
    router.push(`${path}?userId=${encodeURIComponent(userId.trim())}`);
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="text-center">
        <h1 className="font-editorial text-display font-bold text-ink">은빛실타래 관리자</h1>
        <p className="mt-2 text-body-compact text-ink-muted">기기·동기화 운영 관리 콘솔</p>
      </div>

      <Card className="w-full max-w-md">
        <p className="mb-4 text-caption text-ink-muted">
          ⚠️ 스캐폴딩 단계 임시 진입점입니다. 실제 인증(Keycloak) 연동 전까지 이 화면이
          로그인 화면을 대신합니다.
        </p>
        <Link href="/users">
          <Button className="w-full">사용자 목록 보기</Button>
        </Link>

        <div className="my-5 flex items-center gap-3 text-caption text-ink-faint">
          <span className="h-px flex-1 bg-border" />
          또는 ID를 이미 아는 경우
          <span className="h-px flex-1 bg-border" />
        </div>

        <label htmlFor="userId" className="mb-2 block text-body-compact font-medium text-ink">
          사용자 ID (UUID)
        </label>
        <input
          id="userId"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="예: f645b7a3-e2fc-475d-b48c-ff18815b1f9b"
          className="mb-4 min-h-11 w-full rounded-lg border border-border bg-paper px-4 text-body-compact text-ink outline-none focus-visible:border-teal-deep"
        />
        <Button variant="secondary" className="w-full" onClick={() => goTo("/devices")}>
          기기 관리로 바로 이동
        </Button>
      </Card>
    </main>
  );
}

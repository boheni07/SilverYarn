"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

/**
 * ⚠️ 임시 진입점: Keycloak 인증(core/auth.py, 백엔드 미검증 스텁)이 실제로 붙기 전까지,
 * 실제 로그인 흐름 대신 어르신 계정 ID를 직접 입력받아 화면을 연결한다. 가짜 로그인
 * 화면을 만드는 대신 이렇게 명시적으로 미완성 상태를 드러내는 쪽을 택했다 — 실 인증
 * 연동 시 이 페이지를 로그인 폼으로 교체한다.
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
        <h1 className="font-editorial text-display font-bold text-ink">은빛실타래</h1>
        <p className="mt-2 text-body-compact text-ink-muted">
          어르신 자서전 제작 및 AI 말벗돌봄 플랫폼 — 웹 콘솔
        </p>
      </div>

      <Card className="w-full max-w-md">
        <p className="mb-4 text-caption text-ink-muted">
          ⚠️ 스캐폴딩 단계 임시 진입점입니다. 실제 인증(Keycloak) 연동 전까지 어르신
          계정 ID를 직접 입력해 화면을 확인합니다.
        </p>
        <label htmlFor="userId" className="mb-2 block text-body-compact font-medium text-ink">
          어르신 계정 ID (UUID)
        </label>
        <input
          id="userId"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="예: f645b7a3-e2fc-475d-b48c-ff18815b1f9b"
          className="mb-4 min-h-11 w-full rounded-lg border border-border bg-paper px-4 text-body-compact text-ink outline-none focus-visible:border-teal-deep"
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Button onClick={() => goTo("/chapters")}>자서전 뷰어로 이동</Button>
          <Button variant="secondary" onClick={() => goTo("/photos")}>
            사진 갤러리로 이동
          </Button>
          <Button variant="secondary" onClick={() => goTo("/review")}>
            가족 감수 화면으로 이동
          </Button>
          <Button variant="secondary" onClick={() => goTo("/photo-requests")}>
            사진 요청 관리로 이동
          </Button>
        </div>
      </Card>
    </main>
  );
}

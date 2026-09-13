"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { eraseUserAction } from "./actions";

/**
 * decisions.md #56(Q5) — 정보주체 삭제요청권(PIPA) 행사. crypto-shredding +
 * Qdrant/Neo4j/MinIO 정리까지 포함한 되돌릴 수 없는 작업이라, 실수 클릭 방지를
 * 위해 2단계로 나눈다: (1) "계정 삭제" 클릭 시 확인 패널이 펼쳐짐 (2) 어르신
 * 이름을 정확히 입력 + 사유를 적어야 실행 버튼이 활성화된다.
 */
export function EraseUserButton({ userId, userName }: { userId: string; userName: string }) {
  const router = useRouter();
  const [expanded, setExpanded] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const canSubmit = confirmName === userName && reason.trim().length > 0;

  async function handleErase() {
    if (!canSubmit) return;
    setPending(true);
    setError(null);
    const result = await eraseUserAction(userId, reason.trim());
    setPending(false);
    if (result.ok) {
      setDone(true);
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  if (done) {
    return <p className="mt-3 text-caption text-ink-muted">계정이 삭제되었습니다.</p>;
  }

  if (!expanded) {
    return (
      <Button variant="danger" className="mt-3" onClick={() => setExpanded(true)}>
        계정 삭제
      </Button>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-border bg-subtle-2 p-4">
      <p className="text-caption text-ink">
        되돌릴 수 없습니다. 대화·챕터·사진 등 모든 데이터가 즉시 파기됩니다(crypto-shredding).
        계속하려면 어르신 이름 <strong>&ldquo;{userName}&rdquo;</strong>을(를) 아래에 입력하세요.
      </p>
      <input
        type="text"
        value={confirmName}
        onChange={(e) => setConfirmName(e.target.value)}
        placeholder={userName}
        className="mt-3 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
      />
      <label className="mt-3 block text-caption text-ink-muted">
        삭제 사유
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="예: 정보주체 삭제 요청(전화 접수)"
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <div className="mt-4 flex gap-2">
        <Button variant="danger" onClick={handleErase} disabled={pending || !canSubmit}>
          {pending ? "삭제 중…" : "영구 삭제 실행"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            setExpanded(false);
            setConfirmName("");
            setReason("");
            setError(null);
          }}
        >
          취소
        </Button>
      </div>
    </div>
  );
}

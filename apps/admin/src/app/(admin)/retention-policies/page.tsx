import { listRetentionPolicies } from "@/services/retention-policies";
import { RetentionPolicyForm } from "@/features/retention/RetentionPolicyForm";
import { ApiError } from "@/services/errors";
import type { RetentionPolicy } from "@/types";

/**
 * decisions.md #56(Q5, 2026-09-13 사용자 결정) — 보유기간을 하드코딩하지 않고
 * DB 설정 테이블 + admin 콘솔에서 운영자가 직접 조정. 만료된 대화 원문은
 * crypto-shredding이 아니라(그건 계정 전체 삭제 전용) redaction으로 파기된다
 * (worker.py의 시간 기반 배치 잡 — `purge_expired_conversation_chunks`).
 */
export default async function RetentionPoliciesPage() {
  let policies: RetentionPolicy[] = [];
  let error: string | null = null;
  try {
    policies = await listRetentionPolicies();
  } catch (e) {
    error = e instanceof ApiError ? e.message : "보유기간 설정을 불러오지 못했습니다.";
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">보유기간 설정</h1>
      <p className="mt-2 text-ink-muted">
        보유기간이 지난 대화 원문은 매시 30분 배치 작업이 자동으로 파기(redaction)합니다 — 구조화된
        메타데이터(시기·인물·장소 등)는 자서전 집필 참고용으로 남습니다.
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">{error}</p>
      )}

      {!error && (
        <ul className="mt-8 flex flex-col gap-4">
          {policies.map((policy) => (
            <li key={policy.id}>
              <RetentionPolicyForm policy={policy} />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

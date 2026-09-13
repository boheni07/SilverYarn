import { listPublications } from "@/services/publications";
import { PublicationRequestForm } from "@/features/publication/PublicationRequestForm";
import { resolveCurrentUserId } from "@/services/me";
import { ApiError } from "@/services/errors";
import { PUBLICATION_FORMAT_LABEL, PUBLICATION_STATUS_LABEL } from "@/types";
import type { Publication } from "@/types";

interface PublicationsPageProps {
  searchParams: Promise<{ elder?: string }>;
}

/**
 * design.md §2.6 출판/인쇄 파이프라인 — "전체 챕터 confirmed → 출판 요청 →
 * 조판(PDF/ePub) → 완료" 흐름의 웹 화면. 인쇄 발주·배송은 스코프 밖(publications
 * 모듈 docstring 참조)이라 이 화면은 요청·상태확인·다운로드까지만 다룬다.
 */
export default async function PublicationsPage({ searchParams }: PublicationsPageProps) {
  const { elder } = await searchParams;
  const userId = await resolveCurrentUserId(elder);

  let publications: Publication[] = [];
  let error: string | null = null;
  try {
    publications = await listPublications(userId);
  } catch (e) {
    error = e instanceof ApiError ? e.message : "출판 요청 목록을 불러오지 못했습니다.";
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">자서전 출판</h1>
      <p className="mt-2 text-ink-muted">완성된 자서전을 전자책(ePub) 또는 하드커버 PDF로 만들어 드립니다.</p>

      {error && (
        <p className="mt-6 rounded-lg border border-border bg-subtle-2 px-4 py-3 text-ink-muted">{error}</p>
      )}

      {!error && (
        <div className="mt-6">
          <PublicationRequestForm userId={userId} />
        </div>
      )}

      {!error && (
        <>
          <h2 className="mt-10 font-editorial text-h2 font-semibold text-ink">요청 이력</h2>
          {publications.length === 0 ? (
            <p className="mt-4 text-ink-muted">아직 출판을 요청한 적이 없습니다.</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-3">
              {publications.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between gap-4 rounded-lg border border-border-soft bg-surface p-4"
                >
                  <div>
                    <p className="text-body-compact text-ink">{PUBLICATION_FORMAT_LABEL[p.format]}</p>
                    <p className="mt-1 text-caption text-ink-muted">
                      요청일 {new Date(p.requestedAt).toLocaleDateString("ko-KR")}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span className="rounded-full bg-subtle px-3 py-1 text-caption font-medium text-ink-muted">
                      {PUBLICATION_STATUS_LABEL[p.status]}
                    </span>
                    {p.downloadUrl && (
                      <a href={p.downloadUrl} className="text-caption text-teal-deep underline">
                        다운로드
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </main>
  );
}

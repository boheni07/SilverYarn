import { apiClient } from "@silveryarn/web-shared/api";
import type { Chapter, ChapterRevision, RevisionAction } from "@/types";

export async function listChapters(userId: string): Promise<Chapter[]> {
  return apiClient.get<Chapter[]>(`/users/${userId}/chapters`);
}

export async function getChapter(chapterId: string): Promise<Chapter> {
  return apiClient.get<Chapter>(`/chapters/${chapterId}`);
}

export async function listChapterRevisions(chapterId: string): Promise<ChapterRevision[]> {
  return apiClient.get<ChapterRevision[]>(`/chapters/${chapterId}/revisions`);
}

/**
 * workflow-diagrams.md §7 감수 유스케이스. reviewerId는 원래 인증 토큰에서 서버가
 * 추출해야 하지만(core/auth.py 스텁 상태), 지금은 호출자가 family_member id를
 * 직접 넘긴다 — 백엔드 chapters.py의 동일한 임시 조치와 짝을 이룬다.
 */
export async function reviewChapter(
  chapterId: string,
  input: { action: RevisionAction; reviewComment?: string; reviewerId?: string },
): Promise<Chapter> {
  return apiClient.post<Chapter>(`/chapters/${chapterId}/review`, input);
}

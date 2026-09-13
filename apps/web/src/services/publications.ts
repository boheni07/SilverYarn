import { apiClient } from "@silveryarn/web-shared/api";
import type { Publication, PublicationFormat } from "@/types";

export async function listPublications(userId: string): Promise<Publication[]> {
  return apiClient.get<Publication[]>(`/users/${userId}/publications`);
}

/** design.md §4.2/§2.6 POST /users/{userId}/publications — 전체 챕터가 confirmed여야
 * 접수된다(서버가 검증, VALIDATION_ERROR로 거부). */
export async function requestPublication(userId: string, format: PublicationFormat): Promise<Publication> {
  return apiClient.post<Publication>(`/users/${userId}/publications`, { format });
}

/** 상태 폴링용 — 제작 중(processing)인 요청이 완성됐는지 새로고침으로 확인. */
export async function getPublication(publicationId: string): Promise<Publication> {
  return apiClient.get<Publication>(`/publications/${publicationId}`);
}

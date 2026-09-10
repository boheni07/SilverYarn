import { apiClient } from "@silveryarn/web-shared/api";
import type { PhotoRequest } from "@/types";

export async function listPhotoRequests(userId: string): Promise<PhotoRequest[]> {
  return apiClient.get<PhotoRequest[]>(`/users/${userId}/photo-requests`);
}

/** design.md §4.2 — 가족→당사자 사진 추가 요청(WU3→WF3 루프 시작점). */
export async function createPhotoRequest(input: {
  userId: string;
  requestedBy?: string;
  message?: string;
}): Promise<PhotoRequest> {
  return apiClient.post<PhotoRequest>(
    "/photo-requests",
    { userId: input.userId, requestedBy: input.requestedBy, message: input.message },
   
  );
}

/** 당사자가 "지금은 어렵다"며 요청을 닫는다 — pending 상태에서만 가능(photo_requests.py). */
export async function dismissPhotoRequest(requestId: string): Promise<PhotoRequest> {
  return apiClient.post<PhotoRequest>(`/photo-requests/${requestId}/dismiss`, undefined);
}

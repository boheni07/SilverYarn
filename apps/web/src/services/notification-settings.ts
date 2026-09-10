import { apiClient } from "@/lib/api/client";
import type { ChannelPreference, NotificationSetting } from "@/types";

/** design.md §4.2 GET /family-members/{id}/notification-settings — WF5 화면을 그리는 데 필요. */
export async function getNotificationSettings(familyMemberId: string): Promise<NotificationSetting[]> {
  return apiClient.get<NotificationSetting[]>(`/family-members/${familyMemberId}/notification-settings`);
}

/** design.md §4.2 PUT — 이 구성원의 알림 수신 설정 전체를 통째로 교체(delete→insert). */
export async function replaceNotificationSettings(
  familyMemberId: string,
  settings: ChannelPreference[],
): Promise<NotificationSetting[]> {
  return apiClient.put<NotificationSetting[]>(
    `/family-members/${familyMemberId}/notification-settings`,
    { settings },
  );
}

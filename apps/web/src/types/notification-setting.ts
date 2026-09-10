/** design.md §4.2 / schema.md `notification_settings` — WF5 알림 수신 설정.
 * PUT은 이 구성원의 설정 전체를 통째로 교체(delete→insert)한다. */

export type NotifyChannel = "sms" | "email" | "push";

export interface NotificationSetting {
  id: string;
  familyMemberId: string;
  channel: NotifyChannel;
  receivesEmotionAlerts: boolean;
  receivesChapterUpdates: boolean;
  receivesSyncIssues: boolean;
  updatedAt: string;
}

/** PUT 요청 1건 — 한 채널의 수신 항목 스위치. */
export interface ChannelPreference {
  channel: NotifyChannel;
  receivesEmotionAlerts: boolean;
  receivesChapterUpdates: boolean;
  receivesSyncIssues: boolean;
}

export const NOTIFY_CHANNELS: readonly NotifyChannel[] = ["push", "email", "sms"];

export const NOTIFY_CHANNEL_LABEL: Record<NotifyChannel, string> = {
  sms: "문자(SMS)",
  email: "이메일",
  push: "앱 푸시",
};

/** 채널당 켜고 끄는 boolean 수신 항목 키. */
export type NotifyItemKey = Exclude<keyof ChannelPreference, "channel">;

/** 수신 항목 3종. `receivesEmotionAlerts`는 CTO 검토 B1에 따라 기본 opt-out(false). */
export const NOTIFY_ITEMS = [
  { key: "receivesChapterUpdates", label: "자서전 챕터 갱신" },
  { key: "receivesSyncIssues", label: "동기화 문제" },
  { key: "receivesEmotionAlerts", label: "정서 이상 알림" },
] as const satisfies readonly { key: NotifyItemKey; label: string }[];

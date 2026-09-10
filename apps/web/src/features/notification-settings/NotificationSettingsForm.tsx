"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { saveNotificationSettings } from "./actions";
import {
  NOTIFY_CHANNELS,
  NOTIFY_CHANNEL_LABEL,
  NOTIFY_ITEMS,
} from "@/types";
import type { ChannelPreference, NotificationSetting, NotifyChannel, NotifyItemKey } from "@/types";

/**
 * design.md §4.2 PUT /family-members/{id}/notification-settings (WF5).
 * PUT은 전체 교체라, 3개 채널(push/email/sms) × 3개 항목을 한 화면에서 편집해
 * 통째로 저장한다. 기존 행이 없는 채널은 백엔드 기본값(챕터 갱신만 on)으로 시작한다.
 * ChapterReviewPanel/PhotoRequestForm과 동일하게 client component + router.refresh().
 */
export function NotificationSettingsForm({
  familyMemberId,
  initial,
}: {
  familyMemberId: string;
  initial: NotificationSetting[];
}) {
  const router = useRouter();
  const [prefs, setPrefs] = useState<Record<NotifyChannel, ChannelPreference>>(() => buildInitial(initial));
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  function toggle(channel: NotifyChannel, key: NotifyItemKey) {
    setPrefs((prev) => ({
      ...prev,
      [channel]: { ...prev[channel], [key]: !prev[channel][key] },
    }));
    setSavedAt(null);
  }

  async function handleSave() {
    setPending(true);
    setError(null);
    const result = await saveNotificationSettings(
      familyMemberId,
      NOTIFY_CHANNELS.map((c) => prefs[c]),
    );
    setPending(false);
    if (result.ok) {
      setSavedAt(new Date().toLocaleTimeString("ko-KR"));
      router.refresh();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <table className="w-full border-collapse text-body-compact">
        <thead>
          <tr className="border-b border-border">
            <th className="py-2 text-left font-medium text-ink">채널</th>
            {NOTIFY_ITEMS.map((item) => (
              <th key={item.key} className="px-2 py-2 text-center font-medium text-ink-muted">
                {item.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {NOTIFY_CHANNELS.map((channel) => (
            <tr key={channel} className="border-b border-border-soft">
              <td className="py-3 text-ink">{NOTIFY_CHANNEL_LABEL[channel]}</td>
              {NOTIFY_ITEMS.map((item) => (
                <td key={item.key} className="px-2 py-3 text-center">
                  <input
                    type="checkbox"
                    aria-label={`${NOTIFY_CHANNEL_LABEL[channel]} — ${item.label}`}
                    checked={prefs[channel][item.key]}
                    onChange={() => toggle(channel, item.key)}
                    className="h-5 w-5 accent-teal-deep"
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p className="mt-3 text-caption text-ink-muted">
        정서 이상 알림은 기본 꺼짐입니다(CTO 보안 검토 B1) — 필요할 때만 켜세요.
      </p>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}
      {savedAt && <p className="mt-3 text-caption text-ink-muted">저장됨 ({savedAt})</p>}

      <Button className="mt-4" onClick={handleSave} disabled={pending}>
        {pending ? "저장 중…" : "설정 저장"}
      </Button>
    </div>
  );
}

function buildInitial(rows: NotificationSetting[]): Record<NotifyChannel, ChannelPreference> {
  const byChannel = new Map(rows.map((r) => [r.channel, r]));
  return Object.fromEntries(
    NOTIFY_CHANNELS.map((channel) => {
      const row = byChannel.get(channel);
      return [
        channel,
        {
          channel,
          receivesEmotionAlerts: row?.receivesEmotionAlerts ?? false,
          receivesChapterUpdates: row?.receivesChapterUpdates ?? true,
          receivesSyncIssues: row?.receivesSyncIssues ?? false,
        } satisfies ChannelPreference,
      ];
    }),
  ) as Record<NotifyChannel, ChannelPreference>;
}

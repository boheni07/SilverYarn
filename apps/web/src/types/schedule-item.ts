/** design.md §3.1 ScheduleItem — schema.md `schedule_items` 매핑. */
export type ScheduleKind = "appointment" | "medication";
export type ScheduleStatus = "pending" | "confirmed" | "missed" | "declined";

export interface ScheduleItem {
  id: string;
  userId: string;
  kind: ScheduleKind;
  description?: string;
  location?: string;
  recurrence?: string;
  dueAt: string;
  status: ScheduleStatus;
  remindCount: number;
  declineReason?: string;
  nextRemindAt?: string;
  respondedAt?: string;
}

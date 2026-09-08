import type { SyncStatus } from "@/types";
import { SYNC_STATUS_LABEL } from "@/types";

const SYNC_STATUS_CLASSES: Record<SyncStatus, string> = {
  success: "bg-teal-tint text-teal-deep",
  failed: "bg-subtle text-ink",
  retrying: "bg-gold-tint text-ink",
};

export function SyncStatusBadge({ status }: { status: SyncStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-caption font-medium ${SYNC_STATUS_CLASSES[status]}`}
    >
      {SYNC_STATUS_LABEL[status]}
    </span>
  );
}

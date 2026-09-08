import type { InstallMode } from "@/types";
import { INSTALL_MODE_LABEL } from "@/types";

/** apps/web의 StatusBadge.tsx와 동일한 색상 원칙 — gold/silver는 배지 배경 전용
 * (design-tokens.md §1.1, 텍스트 대비 미달이라 텍스트 색으로는 안 씀). */
const INSTALL_MODE_CLASSES: Record<InstallMode, string> = {
  kiosk: "bg-gold-tint text-ink",
  normal: "bg-teal-tint text-teal-deep",
};

export function InstallModeBadge({ mode }: { mode: InstallMode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-caption font-medium ${INSTALL_MODE_CLASSES[mode]}`}
    >
      {INSTALL_MODE_LABEL[mode]}
    </span>
  );
}

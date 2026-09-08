import type { HTMLAttributes } from "react";

/** apps/web/src/components/ui/Card.tsx와 동일 — 공유 패키지가 아직 없어 각자 들고 있다. */
export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl border border-border-soft bg-surface p-6 shadow-sm ${className}`}
      {...props}
    />
  );
}

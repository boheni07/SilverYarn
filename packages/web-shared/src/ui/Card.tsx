import type { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl border border-border-soft bg-surface p-6 shadow-sm ${className}`}
      {...props}
    />
  );
}

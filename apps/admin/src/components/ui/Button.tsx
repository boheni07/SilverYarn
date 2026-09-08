import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

/**
 * design-tokens.md §1.1: teal(4.45:1)은 본문 크기 텍스트에 AA 미달이라 버튼 배경처럼
 * 큰 면적+굵은 글씨에는 허용되지만, 여기서는 확실한 teal-deep(6.77:1 on paper)을
 * 기본값으로 써서 어떤 배경 위에서도 대비 문제가 나지 않게 한다.
 * §4 터치 타깃: 웹은 44×44px 이상 — min-h-11(44px)로 보장.
 * (apps/web/src/components/ui/Button.tsx와 동일 — 공유 패키지가 아직 없어 각자 들고 있다.)
 */
const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-teal-deep text-white hover:bg-ink focus-visible:outline-ink",
  secondary: "bg-surface text-teal-deep border border-border hover:bg-subtle-2",
  danger: "bg-surface text-ink border border-border hover:bg-subtle-2",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center rounded-lg px-5 font-ui text-body-compact font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
}

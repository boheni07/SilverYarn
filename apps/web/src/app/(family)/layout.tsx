/**
 * (family) 라우트 그룹 — 가족·복지사 화면. design-tokens.md §4의 20px 접근성
 * 기준은 "web(user 화면)"에만 명시돼 있어, 여기는 표준 웹 크기(16px, text-body-compact)를
 * 쓴다. 대비·포커스링 등 다른 WCAG AA 기준은 동일하게 적용된다.
 */
export default function FamilyLayout({ children }: { children: React.ReactNode }) {
  return <div className="font-ui text-body-compact text-ink">{children}</div>;
}

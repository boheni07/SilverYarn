/**
 * (user) 라우트 그룹 — 자서전 당사자(어르신) 화면. design-tokens.md §4 접근성
 * 최소기준: 본문 20px(text-body 토큰) 적용 대상은 "mobile·web(user)"로 명시돼
 * 있으므로, 이 레이아웃이 그 경계를 담당한다 — (family) 그룹은 이 클래스를 쓰지 않는다.
 */
export default function UserLayout({ children }: { children: React.ReactNode }) {
  return <div className="font-ui text-body text-ink">{children}</div>;
}

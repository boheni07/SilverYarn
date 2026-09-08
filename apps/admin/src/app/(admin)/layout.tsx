/**
 * (admin) 라우트 그룹 — 운영자 화면. 고령자 대상이 아니므로 apps/web의 (family)
 * 그룹과 같은 body-compact(16px)를 쓴다 — structure.md §4.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <div className="font-ui text-body-compact text-ink">{children}</div>;
}

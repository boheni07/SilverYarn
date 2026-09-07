---
name: silveryarn-kickoff-fe-review
description: 2026-09-05 킥오프 CTO 리뷰보드에서 Frontend Architect가 낸 판정 — 조건부 착수, Blocker 4건(대비비/토큰 파이프라인/App Router 위치/a11y 기준)
metadata:
  type: project
---

2026-09-05 킥오프에서 프론트엔드 관점 판정은 **조건부 착수(Blocker 4건 선결)**였다.

핵심 수치 근거 (직접 계산, WCAG 2.x relative luminance):
- `#1E7A8C`(teal) on `#F4F2EE`(paper) = **4.45:1** → AA 본문 미달(4.5 기준, 근소 미달). 흰 배경(#FFFFFF)에서는 4.98:1로 통과.
- `#9096A0`(ink-faint) on paper = **2.66:1** → CAPTION 12.5px에 지정된 색이라 전 기준 미달.
- `#B8935A`(gold) on paper = **2.55:1**, 흰 글자 on gold = **2.85:1** → 텍스트/상태바 사용 불가.
- `#DEDACF`(border) on paper = **1.25:1** → WCAG 1.4.11(3:1) 미달, 입력 필드 경계 불가시.
- `#20242B`(ink) 13.93:1, `#5B6472` 5.35:1, `#155C6B` on white 7.57:1(AAA)은 안전.

**Why:** 고령 사용자 접근성이 제품의 핵심 차별점인데 design-tokens.md v1.0에는 대비 검증·최소 터치타깃·최소 폰트 하한이 전무했다. 또 토큰이 md 표로만 존재해 web/admin/mobile 3개 표면으로 수동 복제될 위험이 있었다.

**How to apply:** 토큰 값 변경 제안 시 반드시 BI가이드(SoR) → design-tokens.md → Style Dictionary 순으로 갱신을 요구할 것. teal은 본문 텍스트색으로 승인하지 말고 `teal-deep`(#155C6B)을 텍스트/포커스용으로 유도. gold/silver/ink-faint는 장식 전용으로 제한.
관련: [[silveryarn-fe-surfaces]]

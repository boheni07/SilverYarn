# Design Tokens

> Phase 3(Mockup) 보강 산출물 — [`Plan/은빛실타래_BI가이드_v2.html`](../../Plan/은빛실타래_BI가이드_v2.html)(v2.0)의 컬러·타이포를 코드에서 사용 가능한 토큰으로 매핑 (design-validator F-5 반영) *(v1.2: "Phase 5"로 표기돼 CLAUDE.md·design.md Pipeline References의 Phase 3 분류와 불일치하던 것을 정정, L-10)*

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-07 · **Version**: 1.2

> 원본 BI 가이드의 CSS 변수(`--teal`, `--gold` 등)와 컬러 팔레트 섹션 값을 1:1로 확인 후 작성했다. 색상 값을 바꿀 때는 반드시 BI 가이드(SoR)를 먼저 갱신할 것.

> ⚠️ **v1.1 — WCAG AA 대비 보강 (2차 design-validator M-9, CTO FE-B1)**: 원본 BI 가이드 색상 중 일부가 배경(`color-paper` `#F4F2EE`) 위 텍스트로 쓰일 때 WCAG 2.1 AA(일반 텍스트 4.5:1) 기준을 충족하지 못한다 — `color-teal`(4.45:1), `color-ink-faint`(2.66:1), `color-gold`(2.55:1) 모두 실패, `color-border`(1.25:1)는 UI 컴포넌트 최소 3:1도 미달. 색상 값 자체(BI 가이드 SoR)는 바꾸지 않고, **텍스트/인터랙션 요소에는 아래 §1.1 대체 토큰을 쓰도록 사용 규칙을 추가**하는 방식으로 해소했다.

---

## 1. Color Tokens

| Token | Role(원본 명칭) | HEX | 용도 비중 |
|---|---|---|---|
| `color-ink` | Ink — 기록의 잉크 (Text) | `#20242B` | 55%(Paper Stone과 합산) — 배경·본문 |
| `color-paper` | Paper Stone (Base) | `#F4F2EE` | 배경·본문 |
| `color-teal` | Thread Teal (Primary) — 실의 색 | `#1E7A8C` | 25% — 인터랙션·강조 |
| `color-teal-deep` | Thread Teal Deep | `#155C6B` | 호버/강조 진하게 |
| `color-teal-tint` | Thread Teal Tint | `#E4F0F2` | 배경 강조 영역 |
| `color-silver` | Silver Mist (Secondary) — 은빛 | `#8E97A6` | 12% — 보조 그래픽 |
| `color-silver-deep` | Silver Deep | `#4B5563` | 보조 다크 |
| `color-gold` | Heritage Gold (Accent) — 기억의 매듭 | `#B8935A` | 8% — 포인트 |
| `color-gold-deep` | Heritage Gold Deep | `#96723F` | 포인트 강조 |
| `color-gold-tint` | Heritage Gold Tint | `#F3E9D8` | 포인트 배경 |
| `color-surface` | Surface | `#FFFFFF` | 카드/패널 배경 |
| `color-subtle` | Subtle | `#ECE8E1` | 구분 영역 |
| `color-subtle-2` | Subtle 2 | `#F7F5F1` | 구분 영역(약) |
| `color-border` | Border | `#DEDACF` | 테두리 |
| `color-border-soft` | Border Soft | `#E9E5DC` | 테두리(약) |
| `color-ink-muted` | Ink Muted | `#5B6472` | 보조 텍스트 |
| `color-ink-faint` | Ink Faint | `#9096A0` | 캡션/타임스탬프 |

### Tailwind config 매핑 (제안)

```js
// tailwind.config.js (apps/web, apps/admin)
module.exports = {
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#20242B', muted: '#5B6472', faint: '#9096A0' },
        paper: '#F4F2EE',
        teal: { DEFAULT: '#1E7A8C', deep: '#155C6B', tint: '#E4F0F2' },
        silver: { DEFAULT: '#8E97A6', deep: '#4B5563' },
        gold: { DEFAULT: '#B8935A', deep: '#96723F', tint: '#F3E9D8' },
        border: { DEFAULT: '#DEDACF', soft: '#E9E5DC' },
      },
    },
  },
};
```

> **하드코딩 색상 금지**: 컴포넌트에서 `#1E7A8C` 같은 리터럴 직접 사용 대신 `text-teal`, `bg-paper` 등 토큰 클래스를 사용한다 (CONVENTIONS.md §3 웹 컨벤션에 종속).

### 1.1 텍스트 사용 시 WCAG AA 대비 규칙 (v1.1 신규)

`color-paper`(`#F4F2EE`) 배경 기준, WCAG 2.1 AA 대비비(일반 텍스트 4.5:1, UI 컴포넌트/굵은 대형 텍스트 3:1)를 검증한 결과다. **색상 값 자체는 BI 가이드 원본을 유지**하고, 텍스트/링크 등 대비가 중요한 용도에서만 대체 토큰을 쓴다.

| Token | `color-paper` 위 대비비 | AA(4.5:1) | 텍스트 사용 가능? | 대체 규칙 |
|---|---|---|---|---|
| `color-teal` | 4.45:1 | ❌ (근소 미달) | 큰제목(H1/DISPLAY, 24px+ 굵게)만 가능 | 본문 크기 텍스트·링크는 **`color-teal-deep`(6.77:1, ✅)** 사용 |
| `color-teal-deep` | 6.77:1 *(v1.2 정정: 이전 표기 7.57:1은 흰 배경(`color-surface`) 기준값 — CTO 목표 AAA 7:1은 surface 배경에서만 충족, paper 배경에서는 AA만 충족)* | ✅(AA) | 모든 텍스트 가능 | 링크·강조 텍스트 기본값으로 채택 |
| `color-ink-faint` | 2.66:1 | ❌ | 텍스트 불가 | **장식 전용**(아이콘, 디바이더)으로 한정. 캡션/타임스탬프 텍스트는 `color-ink-muted`(대비 ✅) 사용 |
| `color-gold` | 2.55:1 | ❌ | 텍스트 불가 | **장식 전용**(배지 배경, 아이콘, 포인트 그래픽)으로 한정 |
| `color-gold-deep` | 3.93:1 | ❌ (4.5:1 미달, 3:1 이상이라 대형 굵은 텍스트/UI 컴포넌트 테두리는 가능) | 본문 텍스트 불가 | 텍스트 강조가 필요하면 `color-teal-deep` 사용 |
| `color-silver` | 2.63:1 | ❌ | 텍스트 불가 | **장식 전용**(보조 그래픽, 구분선)으로 한정 |
| `color-border` | 1.25:1 | ❌ (3:1 미달) | 테두리 전용, 포커스 링 등 인터랙션 표시에는 미사용 | 포커스 표시 등 UI 컴포넌트 경계는 `color-teal-deep` 또는 `color-ink` 사용 |

> `color-ink`(본문 텍스트), `color-ink-muted`(보조 텍스트), `color-surface` 위 텍스트는 원본 그대로 AA를 충족하므로 변경 없음.

---

## 2. Typography Tokens

| 역할 | 서체 | 용도 |
|---|---|---|
| Editorial & Title | Noto Serif KR (본명조) | 하드커버 표지, 챕터 타이틀, 구술 원문 인용 |
| UI & Conversation | Pretendard (프리텐다드) | 대화형 UI, 알림 팝업, 버튼, 메타데이터 |

### 타입 스케일

| 레벨 | 크기 | 굵기 | 서체 |
|---|---|---|---|
| DISPLAY | 34px | 700 | Noto Serif KR |
| H1 | 26px | 700 | Noto Serif KR |
| H2 | 20px | 600 | Noto Serif KR |
| BODY | **20px** *(v1.2: 모바일·웹(user) 16px→20px 상향 — decisions.md #43, CTO FE-B4 고령자 가독성 권고 채택)* | 400 | Pretendard |
| BODY(admin) | 16px *(관리자 콘솔은 고령 사용자 대상이 아니므로 기존 크기 유지)* | 400 | Pretendard |
| CAPTION | 14px *(v1.1: 12.5px→상향, 가독성)* | 500 | Pretendard (color: `color-ink-muted` *(v1.1: `color-ink-faint`는 대비 미달로 텍스트 미사용, §1.1)*) |

### Google Fonts 연동 (웹)

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
```

> 모바일(Kotlin)은 폰트 파일을 `res/font/`에 번들링 — Pretendard는 대화형 UI 전체, Noto Serif KR은 자서전 뷰어(챕터 본문) 한정 사용.

---

## 3. Color Usage Ratio (원본 가이드 기준)

```
Ink & Paper Stone(배경·본문) 55% ── Thread Teal(인터랙션·강조) 25% ── Silver Mist(보조) 12% ── Heritage Gold(포인트) 8%
```

---

## 4. 접근성 최소기준 (v1.2 신규 — CTO FE-B4, 3차 검증 H-2)

> 고령자 대상 서비스 특성상 접근성은 부가 요소가 아니라 핵심 품질축이다. 아래 기준은 `apps/mobile`(Kotlin)·`apps/web`(user 화면)에 적용하며, `apps/admin`은 대상 사용자가 다르므로 웹 표준 최소기준(WCAG AA)만 적용한다.

| 항목 | 기준 | 근거/적용 범위 |
|---|---|---|
| 본문 텍스트 크기 | BODY 20px(sp) 이상 (mobile·web user) | decisions.md #43 |
| 시스템 폰트 확대 대응 | OS 폰트 크기 200%까지 레이아웃 깨짐 없이 대응(`sp`/`rem` 단위 사용, 고정 `px` 금지) | CTO FE-B4 |
| 터치 타깃 | 최소 56×56dp(모바일), 웹은 44×44px 이상 | Android 접근성 가이드, WCAG 2.5.5 |
| 색상 대비 | 본문 텍스트 AA(4.5:1) 이상 — §1.1 대체 토큰 규칙 적용 | WCAG 2.1 AA |
| 포커스 표시 | 키보드/포커스 이동 시 시각적 포커스 링 필수(`color-teal-deep` 또는 `color-ink` 3:1 이상 테두리) | WCAG 2.4.7 |
| 스크린리더 | 모바일 TalkBack 화이트리스트(키오스크 Device Owner 모드에서도 접근성 서비스 예외 허용), 웹 시맨틱 마크업 + `aria-label` | Android Enterprise 접근성 정책 |
| 제스처 단순성 | 복잡한 제스처(핀치줌·다중터치) 대체 수단 항상 제공 | WCAG 2.5.1 |

> ⚠️ 위 기준의 **구체 구현(컴포넌트별 QA 체크리스트, 실기기 TalkBack 테스트 절차)은 Do 단계 UI 구현 시 확정**한다. 이 절은 "최소 기준선"만 정의한다.

---

## Related Documents

- [Design](./features/silveryarn-platform.design.md) §5
- [CONVENTIONS.md](../../CONVENTIONS.md) §3 (웹 콘솔 컨벤션)
- 원본: [`Plan/은빛실타래_BI가이드_v2.html`](../../Plan/은빛실타래_BI가이드_v2.html)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | design-validator F-5 반영 — BI 가이드 컬러/타이포를 토큰화 | NUBiz AX Initiative |
| 1.1 | 2026-09-07 | 2차 design-validator M-9(CTO FE-B1) 반영 — WCAG AA 대비 미달 색상(teal/ink-faint/gold/border) 사용 규칙 추가(§1.1), CAPTION 12.5px→14px 상향, 캡션 텍스트 색상을 ink-faint→ink-muted로 정정 | NUBiz AX Initiative |
| 1.2 | 2026-09-07 | 3차 design-validator 검증 반영 — H-2: 접근성 최소기준 §4 신설(BODY 20px 상향 decisions.md #43, 터치타깃/포커스링/TalkBack 등), L-1: `teal-deep`·`silver`·`gold-deep` 대비 수치 정정(흰 배경/paper 배경 구분), M-2: 이슈ID M-7 중복을 M-9로 재부여 | NUBiz AX Initiative |

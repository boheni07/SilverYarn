# Design Tokens

> Phase 5 보강 산출물 — [`Plan/은빛실타래_BI가이드_v2.html`](../../Plan/은빛실타래_BI가이드_v2.html)(v2.0)의 컬러·타이포를 코드에서 사용 가능한 토큰으로 매핑 (design-validator F-5 반영)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-05 · **Version**: 1.0

> 원본 BI 가이드의 CSS 변수(`--teal`, `--gold` 등)와 컬러 팔레트 섹션 값을 1:1로 확인 후 작성했다. 색상 값을 바꿀 때는 반드시 BI 가이드(SoR)를 먼저 갱신할 것.

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
| BODY | 16px | 400 | Pretendard |
| CAPTION | 12.5px | 500 | Pretendard (color: `color-ink-faint`) |

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

## Related Documents

- [Design](./features/silveryarn-platform.design.md) §5
- [CONVENTIONS.md](../../CONVENTIONS.md) §3 (웹 콘솔 컨벤션)
- 원본: [`Plan/은빛실타래_BI가이드_v2.html`](../../Plan/은빛실타래_BI가이드_v2.html)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | design-validator F-5 반영 — BI 가이드 컬러/타이포를 토큰화 | NUBiz AX Initiative |

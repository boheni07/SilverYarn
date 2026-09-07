# 02-design Index

> **PDCA Phase**: Design
> **Last Updated**: 2026-09-05

---

## Document List

| Document | Status | Last Modified | Owner | Description |
|----------|--------|---------------|-------|-------------|
| [features/silveryarn-platform.design.md](./features/silveryarn-platform.design.md) | 🔄 In Progress | 2026-09-06 | NUBiz AX Initiative | 온디바이스-온프레미스 하이브리드 아키텍처, 데이터 모델, API/UI 인벤토리 (v0.3, Closed-Loop 프로세스 상세화 반영) |
| [design-tokens.md](./design-tokens.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | BI 가이드 컬러/타이포 → Tailwind 토큰 매핑 |
| [workflow-diagrams.md](./workflow-diagrams.md) | 🔄 In Progress | 2026-09-06 | NUBiz AX Initiative | 비즈니스/업무/프로세스 흐름도 Mermaid 20종 (Closed-Loop·실시간파이프라인 반영 현재판) |
| [cto-review-2026-09-05.md](./cto-review-2026-09-05.md) | ✅ Approved | 2026-09-06 | CTO팀(7개 관점) | 개발팀 착수회의 대비 아키텍처/인프라/보안/FE/백엔드·API/QA/PM 심사 — Blocker 28건, 전원 Go with Conditions |

---

## Status Legend

| Status | Meaning | Description |
|--------|---------|-------------|
| ✅ Approved | Finalized | Review complete, reference baseline |
| 🔄 In Progress | Working | Currently being written |
| 👀 In Review | Pending Review | Awaiting review |
| ⏸️ On Hold | Paused | Temporarily stopped |
| ❌ Deprecated | Obsolete | No longer valid |

---

## PDCA Status

```
Current Phase: [Design] ← You are here

┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│  Plan  │───▶│ Design │───▶│   Do   │───▶│ Check  │
│   ✅   │    │  🔄    │    │ (Impl) │    │(Analyze)│
└────────┘    └────────┘    └────────┘    └────────┘
```

---

## Folder Structure

```
02-design/
├── _INDEX.md          ← Current file
└── features/
    └── silveryarn-platform.design.md
```

---

## Related Links

| Phase | Folder | Description |
|-------|--------|-------------|
| Plan | [01-plan/](../01-plan/_INDEX.md) | Planning documents |
| Design | [02-design/](./_INDEX.md) | Design documents |

---

## Notes

- 원본 아키텍처·프로세스 상세는 `Plan/자서전_말벗돌봄_프로세스_흐름도.md` 참조 (Mermaid 20+ 다이어그램).
- 원본 UI/UX 상세 스펙은 `Plan/은빛실타래_UIUX_화면설계서.html`, 브랜드 규정은 `Plan/은빛실타래_BI가이드_v2.html` 참조.
- bkit Enterprise 기본 인프라 템플릿(AWS EKS/Terraform)은 본 프로젝트의 온프레미스 데이터 주권 원칙과 맞지 않아 그대로 적용하지 않음 — infra 설계는 별도 검토 필요.

---

## Update History

| Date | Changes |
|------|---------|
| 2026-09-05 | Index 생성, silveryarn-platform.design.md 등록 |

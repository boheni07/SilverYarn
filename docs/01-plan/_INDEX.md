# 01-plan Index

> **PDCA Phase**: Plan
> **Last Updated**: 2026-09-05

---

## Document List

| Document | Status | Last Modified | Owner | Description |
|----------|--------|---------------|-------|-------------|
| [features/silveryarn-platform.plan.md](./features/silveryarn-platform.plan.md) | 🔄 In Progress | 2026-09-05 | NUBiz AX Initiative | 은빛실타래 플랫폼 전체 기획 (Plan/ 폴더 원본 문서 편입) |
| [decisions/silveryarn-platform.decisions.md](./decisions/silveryarn-platform.decisions.md) | 🔄 In Progress | 2026-09-05 | NUBiz AX Initiative | 기획서 9장 미결 사항 확정/보류 로그 |
| [glossary.md](./glossary.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | Phase 1 용어집 |
| [schema.md](./schema.md) | ✅ Approved | 2026-09-06 | NUBiz AX Initiative | Phase 1 데이터 스키마 (v1.2, 17개 엔티티 + Neo4j 연동 필드, PostgreSQL DDL) |
| [mobile-schema.md](./mobile-schema.md) | 🔄 In Progress | 2026-09-06 | NUBiz AX Initiative | 온디바이스 SQLite 로컬 스키마 (FTS5 등 6개 테이블) |
| [naming.md](./naming.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | Phase 2 네이밍 규칙 (서버/모바일/웹/DB) |
| [structure.md](./structure.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | Phase 2 모노레포 폴더 구조 |
| [../../CONVENTIONS.md](../../CONVENTIONS.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | Phase 2 컨벤션 마스터 문서 (루트) |

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
                                               │
                                               ▼
                                         ┌────────┐
                                         │  Act   │
                                         │(Improve)│
                                         └────────┘
```

---

## Folder Structure

```
01-plan/
├── _INDEX.md          ← Current file
└── features/
    └── silveryarn-platform.plan.md
```

---

## Related Links

| Phase | Folder | Description |
|-------|--------|-------------|
| Plan | [01-plan/](./_INDEX.md) | Planning documents |
| Design | [02-design/](../02-design/_INDEX.md) | Design documents |

---

## Notes

원본 기획 산출물(기획서, 프로세스 흐름도, BI 가이드, UI/UX 화면설계서)은 프로젝트 루트 `Plan/` 폴더에 그대로 보존되며, 본 PDCA 문서는 이를 bkit 표준 형식으로 정리·링크한 것이다. 세부 내용 변경 시 원본 문서를 SoR로 우선 확인할 것.

---

## Update History

| Date | Changes |
|------|---------|
| 2026-09-05 | Index 생성, silveryarn-platform.plan.md 등록 (bkit Enterprise 레벨 정식 초기화) |

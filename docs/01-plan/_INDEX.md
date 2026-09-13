# 01-plan Index

> **PDCA Phase**: Do (Plan 산출물은 기준선으로 확정, decisions.md만 계속 갱신 중)
> **Last Updated**: 2026-09-13

---

## Document List

| Document | Status | Last Modified | Owner | Description |
|----------|--------|---------------|-------|-------------|
| [features/silveryarn-platform.plan.md](./features/silveryarn-platform.plan.md) | ✅ Approved | 2026-09-07 (v0.4) | NUBiz AX Initiative | 은빛실타래 플랫폼 전체 기획 (Plan/ 폴더 원본 문서 편입) |
| [decisions/silveryarn-platform.decisions.md](./decisions/silveryarn-platform.decisions.md) | 🔄 In Progress | 2026-09-13 (v0.25) | NUBiz AX Initiative | 기획서 9장 미결 사항 확정/보류 로그 — 법무·인프라·경영 미결 14건(#52~#65) 전부 확정+구현 완료 |
| [glossary.md](./glossary.md) | ✅ Approved | 2026-09-13 (v1.2) | NUBiz AX Initiative | 프로젝트 용어집 |
| [schema.md](./schema.md) | ✅ Approved | 2026-09-13 (v1.17) | NUBiz AX Initiative | 데이터 스키마 (도메인 19개 + 부속 4개 테이블, PostgreSQL DDL) |
| [mobile-schema.md](./mobile-schema.md) | ✅ Approved | 2026-09-13 (v0.11) | NUBiz AX Initiative | 온디바이스 SQLite 로컬 스키마 (FTS5 등) |
| [erd.md](./erd.md) | ✅ Approved | 2026-09-13 (v1.4) | NUBiz AX Initiative | 데이터 모델링 & ERD — 도메인별 3분할 + 온디바이스 매핑 + Qdrant/Neo4j 연계 (흑백 Mermaid) |
| [naming.md](./naming.md) | ✅ Approved | 2026-09-05 | NUBiz AX Initiative | 네이밍 규칙 (서버/모바일/웹/DB) |
| [structure.md](./structure.md) | ✅ Approved | 2026-09-08 (v1.27) | NUBiz AX Initiative | 모노레포 폴더 구조 |
| [../../CONVENTIONS.md](../../CONVENTIONS.md) | ✅ Approved | 2026-09-07 (v1.5) | NUBiz AX Initiative | 컨벤션 마스터 문서 (루트) |

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
Plan(✅) → Design(✅) → Do(🔄 현재) → Check(🔄 2회 완료) → Report(✅ 1회) → Act(・)
```

Plan 단계 산출물(schema/erd/glossary/naming/structure)은 확정 기준선이지만, **Do 단계 구현이 스키마·용어를 계속 확장**하고 있어(마이그레이션 0001~0012) 이 폴더 문서들도 실제로는 살아있는 문서다. `decisions.md`만 별도로 "🔄 In Progress" — 신규 논의가 생길 때마다 계속 늘어난다.

---

## Folder Structure

```
01-plan/
├── _INDEX.md          ← Current file
├── glossary.md
├── schema.md
├── mobile-schema.md
├── erd.md
├── naming.md
├── structure.md
├── features/
│   └── silveryarn-platform.plan.md
└── decisions/
    └── silveryarn-platform.decisions.md
```

---

## Related Links

| Phase | Folder | Description |
|-------|--------|-------------|
| Plan | [01-plan/](./_INDEX.md) | Planning documents |
| Design | [02-design/](../02-design/_INDEX.md) | Design documents |
| Check | [03-check/](../03-check/blocked-decisions-tracker.md) | Gap analyses, decision tracker |
| Report | [04-report/](../04-report/features/silveryarn-platform.report.md) | Do 사이클 보고서 |

---

## Notes

원본 기획 산출물(기획서, 프로세스 흐름도, BI 가이드, UI/UX 화면설계서)은 프로젝트 루트 `Plan/` 폴더에 그대로 보존되며, 본 PDCA 문서는 이를 bkit 표준 형식으로 정리·링크한 것이다. 세부 내용 변경 시 원본 문서를 SoR로 우선 확인할 것. **코드가 존재하는 현재는 코드가 최우선 SoR**(CLAUDE.md 원칙)이며, 이 폴더 문서는 코드와 다르면 갱신 대상이다.

---

## Update History

| Date | Changes |
|------|---------|
| 2026-09-05 | Index 생성, silveryarn-platform.plan.md 등록 (bkit Enterprise 레벨 정식 초기화) |
| 2026-09-07 | 3차 design-validator 검증 M-4 반영 — 문서 목록에 mobile-schema/erd/naming/structure/CONVENTIONS 누락분 등록, 전 문서 Last Modified·버전 최신화, Folder Structure 블록에 실제 파일 목록 반영 |
| 2026-09-13 | **문서 최신화 점검** — PDCA 현재 단계를 "Design"에서 "Do"로 정정. 전 문서 버전·최종수정일 실제 값으로 갱신(schema v1.4→v1.17, erd v1.2→v1.4, glossary v1.1→v1.2, decisions v0.7→v0.25, structure v1.3→v1.27, mobile-schema v0.3→v0.11) — 이 표가 오랫동안 2026-09-07 시점 값에 멈춰 있던 드리프트 정정 | NUBiz AX Initiative |

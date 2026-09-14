# 02-design Index

> **PDCA Phase**: Do (Design 산출물은 기준선으로 계속 갱신 중)
> **Last Updated**: 2026-09-13

---

## Document List

| Document | Status | Last Modified | Owner | Description |
|----------|--------|---------------|-------|-------------|
| [features/silveryarn-platform.design.md](./features/silveryarn-platform.design.md) | 🔄 In Progress | 2026-09-14 (v0.59) | NUBiz AX Initiative | 온디바이스-온프레미스 하이브리드 아키텍처, 데이터 모델, API/UI 인벤토리 — Do 단계 구현과 지속 동기화 |
| [sync-contract.md](./sync-contract.md) | ✅ Approved | 2026-09-13 (v0.8) | NUBiz AX Initiative | 온디바이스↔서버 동기화 계약 — 비동기 처리, 엔티티별 충돌정책, Presigned URL, 증분 다운로드 |
| [design-tokens.md](./design-tokens.md) | ✅ Approved | 2026-09-07 (v1.2) | NUBiz AX Initiative | BI 가이드 컬러/타이포 → Tailwind 토큰 매핑, WCAG AA 대비 규칙, 접근성 최소기준 |
| [workflow-diagrams.md](./workflow-diagrams.md) | 🔄 In Progress | 2026-09-13 (v0.7) | NUBiz AX Initiative | 비즈니스/업무/프로세스 흐름도 Mermaid 21종 (흑백 고대비판) |
| [data-classification-policy.md](./data-classification-policy.md) | ✅ Approved | 2026-09-13 (v0.1, 신규) | NUBiz AX Initiative | PII/메타데이터 4단계 분류 + 외부 통신 경계 정책 (decisions.md #58/I1 후속) |
| [screen-definitions.md](./screen-definitions.md) | 🔄 In Progress | 2026-09-14 (v0.4) | NUBiz AX Initiative | 사용자 화면(UI/UX) 기준 화면정의서 — 모바일앱(대화 전용 UI + 사진 추가하기, 5개)·웹(사용자·가족, 12개)·웹(관리자, 8개) 총 25개 화면 전수, 전체/영역별 화면 흐름도 포함 |
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
Plan(✅) → Design(✅ 기준선 확정, Do와 병행 갱신) → Do(🔄 현재) → Check(🔄 2회 완료) → Report(✅ 1회) → Act(・)

법무·인프라·경영 미결 14건(Q1~Q6·I1~I5·경영3) — 전부 구현 완료 (2026-09-13, PR #32~#39)
남은 후속: 온디바이스 SLM 실기기 벤치마크(#27/#9/#31, 프로토콜+하니스 준비완료)
```

---

## Folder Structure

```
02-design/
├── _INDEX.md          ← Current file
├── design-tokens.md
├── workflow-diagrams.md
├── sync-contract.md
├── data-classification-policy.md
├── screen-definitions.md
├── cto-review-2026-09-05.md
└── features/
    └── silveryarn-platform.design.md
```

---

## Related Links

| Phase | Folder | Description |
|-------|--------|-------------|
| Plan | [01-plan/](../01-plan/_INDEX.md) | Planning documents |
| Design | [02-design/](./_INDEX.md) | Design documents |
| Check | [03-check/](../03-check/blocked-decisions-tracker.md) | Gap analyses, decision tracker |
| Report | [04-report/](../04-report/features/silveryarn-platform.report.md) | Do 사이클 보고서 |

---

## Notes

- 원본 아키텍처·프로세스 상세는 `Plan/자서전_말벗돌봄_프로세스_흐름도.md` 참조 (Mermaid 20+ 다이어그램).
- 원본 UI/UX 상세 스펙은 `Plan/은빛실타래_UIUX_화면설계서.html`, 브랜드 규정은 `Plan/은빛실타래_BI가이드_v2.html` 참조.
- bkit Enterprise 기본 인프라 템플릿(AWS EKS/Terraform)은 본 프로젝트의 온프레미스 데이터 주권 원칙과 맞지 않아 그대로 적용하지 않음 — 실제 인프라는 `infra/docker-compose.yml`(온프레미스 자체 GPU/베어메탈 전제)로 확정.
- Do 단계 진입 후에도 이 폴더의 문서들은 "완료된 기준선"이 아니라 **코드 구현과 함께 계속 갱신되는 살아있는 문서**다 — 신규 모듈·엔드포인트·화면 추가 시 design.md §3/§4.2/§5.1/§7/§9/§11을 먼저 갱신할 것(SoR 원칙 2).

---

## Update History

| Date | Changes |
|------|---------|
| 2026-09-05 | Index 생성, silveryarn-platform.design.md 등록 |
| 2026-09-07 | 3차 design-validator 검증 M-4 반영 — design-tokens/workflow-diagrams 버전 표기 추가, sync-contract.md 신규 등록, Folder Structure 블록 실제 파일 목록 반영 |
| 2026-09-13 | **문서 최신화 점검** — PDCA 현재 단계를 "Design"에서 "Do"로 정정(2026-09-08부터 실제로는 Do 단계였으나 이 표만 갱신 누락). 전 문서 버전·최종수정일을 실제 값으로 갱신(design.md v0.6→v0.52, workflow-diagrams v0.4→v0.5, sync-contract v0.1→v0.7 반영 누락 정정). 신규 `data-classification-policy.md` 등록(decisions.md #58/I1 후속). PDCA Status 블록에 법무·인프라·경영 미결 14건 완료 현황 반영 | NUBiz AX Initiative |
| 2026-09-13 | 신규 `screen-definitions.md` 등록 — 사용자 화면(UI/UX)만을 기준으로 모바일앱·웹(사용자·가족)·웹(관리자) 27개 화면을 실제 구현 코드 기준 전수 정의(사용자 요청). 첫 절에 전체 화면 흐름도, 영역별로 별도 흐름도 포함 |
| 2026-09-13 | `screen-definitions.md` v0.2 — 모바일 UI 패러다임 전환(하단 4탭 제거, 은실이 대화 화면 통합) 반영, Part A 7개→4개 화면, 전체 27→24개 |
| 2026-09-13 | **문서 정합성 전수점검(사용자 요청)** — 이 표의 스테일 버전 참조 정정(design.md v0.52→v0.56, workflow-diagrams v0.6→v0.7, sync-contract v0.7→v0.8). design.md·workflow-diagrams.md·sync-contract.md·blocked-decisions-tracker.md·glossary.md에 남아있던 페르소나 구 명칭 "은빛이"를 "은실이"로 정정(decisions.md #66), workflow-diagrams.md §19 "표시명 미정" 표기 정정 |
| 2026-09-13 | **웹 실 인증 세션 연결(사용자 결정)** — design.md v0.57→v0.58(`GET /me` §4.2 신규 행), screen-definitions.md v0.2→v0.3(W-02를 임시 홈에서 세션 자동 연결 홈으로 재정의, W-09/W-10 구성원 선택 단계 제거 반영, A-02 배지 정정) | NUBiz AX Initiative |
| 2026-09-14 | **모바일 "사진 추가하기"(M-05) 신규(사용자 요청)** — design.md v0.58→v0.59(§5.1/§11.1), screen-definitions.md v0.3→v0.4(Part A 4개→5개, 전체 24→25개). mobile-schema.md v0.12(device_state.user_id 신규)는 `docs/01-plan/_INDEX.md`에서 관리 | NUBiz AX Initiative |

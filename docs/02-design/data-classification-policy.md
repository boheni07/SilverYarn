# 데이터 분류 및 외부 통신 경계 정책 (Data Classification & Egress Boundary Policy)

> **Summary**: "Zero External Data Egress" 원칙(기획서 3.1 원칙2, decisions.md #58/I1)에서 말하는 "PII 수준"과 "메타데이터 수준"의 경계를 컬럼 단위로 명문화한다.
>
> **Project**: 은빛실타래 (SilverYarn)
> **Version**: 0.1 (신규)
> **Author**: NUBiz AX(AI Transformation) Initiative
> **Date**: 2026-09-13
> **Status**: Draft
> **관련 결정**: [decisions.md #58(I1)](../01-plan/decisions/silveryarn-platform.decisions.md) — 이 문서가 그 "후속 작업"란이 요구한 명문화 산출물이다.

---

## 왜 이 문서가 필요한가

`blocked-decisions-tracker.md`의 I1 항목은 "PII·원본 데이터만 외부 유출을 절대 금지하고, 메타데이터 수준 외부 통신은 허용"으로 확정됐지만(2026-09-12 사용자 결정), **"PII 수준"과 "메타데이터 수준"을 가르는 구체 기준이 없으면 다음 기능을 추가할 때마다 해석 분쟁이 생긴다** — 예: "사용자 이름은 메타데이터인가?", "정서 점수는 PII인가?", "에러 로그에 찍힌 스택트레이스는?". 이 문서는 schema.md의 실제 컬럼을 4단계로 분류해 그 경계를 고정한다.

**분류가 바뀌면(신규 컬럼 추가 등) 이 문서를 먼저 갱신한 뒤 구현한다** — CLAUDE.md SoR 원칙에 따라 코드가 최종 근거이지만, 새 컬럼을 어느 등급으로 다룰지의 *의도*는 여기 먼저 기록한다.

---

## 1. 4단계 분류

| 등급 | 정의 | 외부 반출 | 저장 방식 |
|---|---|---|---|
| **Tier 1 — PII 원본데이터** | 구술 원문·음성·사진 등 재식별 가능성이 극도로 높은 자유형식 콘텐츠 | **절대 금지**(예외 없음) | 애플리케이션 레벨 필드 암호화(§7.3) 또는 오브젝트 자체 격리(MinIO) |
| **Tier 2 — 개인정보(구조화)** | 이름·연락처·생년월일 등 특정 개인을 식별하는 구조화 필드 | 금지(단, 국외이전 동의 예외 — §3) | 일부 암호화(연락처·생년월일), 일부 평문(이름 — 부분검색 UX, decisions.md #45 2차) |
| **Tier 3 — 구조화 메타데이터** | 개인 식별력이 낮은 태깅·통계·타임스탬프·상태값 | 원칙적으로 내부 전용, 필요 시 익명화 후 제한적 허용 | 평문 저장 |
| **Tier 4 — 비개인정보(인프라)** | 빌드 도구·폰트·SDK·에러/메트릭 텔레메트리 등 사람이 아닌 시스템에 대한 통신 | **허용** | 해당 없음(전송 데이터 자체가 개인정보 아님) |

---

## 2. Tier 1 — PII 원본데이터 (절대 외부 반출 금지)

| 컬럼/자원 | 테이블 | 암호화 | 비고 |
|---|---|---|---|
| `body_text` | `chapters` | ✅ (decisions.md #45 1차) | 자서전 챕터 본문 |
| `body_text_snapshot` | `chapter_revisions` | ✅ | 감수 이력 스냅샷 |
| `transcript_on_device` | `conversation_chunks` | ✅ | 온디바이스 1차 전사 |
| `transcript_server` | `conversation_chunks` | ✅ | 서버 고정밀 재전사 |
| `assistant_response` | `conversation_chunks` | ✅ | AI 응답 텍스트(대화 복원에 필요, CTO 검토 H-2) |
| 원본 음성(`raw_audio_ref`가 가리키는 MinIO 객체) | (Object Storage) | 격리(오브젝트 자체) | **업로드 성공 즉시 단말에서 삭제**(decisions.md #30) — "최근 5일 캐시"(#9)는 미동기화 상태의 보존기간만 다룸 |
| 사진 원본(`storage_ref`가 가리키는 MinIO 객체) | `photos` | 격리 | presigned URL(15분 만료)로만 접근 |
| Qdrant 임베딩 벡터 | (Qdrant) | payload 최소화 | CTO 검토 B4 "최고위험"(embedding inversion) — payload에 원문 미저장, `user_id`만(§7.3) |
| Neo4j 그래프 노드 속성 | (Neo4j) | 최소화 | 인물명·장소 등 구조화 추출값만, 원문 텍스트 미저장 |

**파기 수단**: crypto-shredding(`user_encryption_keys` 삭제) + `UserErasureService`가 Qdrant/Neo4j/MinIO를 정리(decisions.md #56, Q5). 시간 기반 보유기간은 `conversation_chunks` 원문에만 적용(`retention_policies`).

---

## 3. Tier 2 — 개인정보(구조화)

| 컬럼 | 테이블 | 암호화 | 비고 |
|---|---|---|---|
| `contact` | `family_members`, `invitations` | ✅ (blind index 동반) | decisions.md #45 2차 |
| `birth_date` | `users` | ✅ | DATE→VARCHAR 암호문 전환 |
| `name` | `users`, `family_members` | ❌ 평문 | 부분검색 UX 필요 + CTO 검토상 최고위험 아님으로 판단(decisions.md #45 2차) |

**국외이전 예외**: FCM(구글, 미국 서버)로 전송되는 **기기 푸시 토큰**은 Tier 2급 식별자이지만, `international_transfer` 전용 동의(decisions.md #57, Q6, 기본 미동의)를 받은 경우에 한해 예외적으로 허용한다 — 이 문서의 "Tier 2는 외부 반출 금지" 원칙의 유일한 예외이며, 반드시 동의 로그(`consent_logs`)와 함께여야 한다.

---

## 4. Tier 3 — 구조화 메타데이터 (내부 전용 원칙)

| 컬럼/범주 | 테이블 | 비고 |
|---|---|---|
| `meta_period`/`meta_people`/`meta_place`/`meta_emotion`/`meta_prosody` | `conversation_chunks` | 회고 파이프라인 태깅용. `meta_people`은 인물명을 담을 수 있어 Tier 2에 가깝지만, RAG 필터링 목적상 구조화 메타데이터로 취급하고 외부 반출은 하지 않는다 |
| `recall_status`/`placement_status`/`quality_flag` | `photos` | 상태값, 개인 식별력 없음 |
| `retention_until`/`purged_at` | `conversation_chunks` | 시각 값, 원문 없이는 개인 식별 불가(decisions.md #56) |
| `org_id` | `users`/`family_members`/`invitations` | 시설 소속 UUID, 그 자체로는 재식별 불가(decisions.md #59) |
| `access_logs`(actor_kind/subject/method/path/status_code) | (부속) | 접속기록 감사로그(제8조) — 내부 전용, 절대 외부 SaaS로 전송하지 않음(§5 Tier 4 예외 참조: self-hosted 관측스택은 "외부"가 아님) |

**에러/로그 텔레메트리 특칙**: `core/logging.py`/`core/observability.py`가 남기는 JSON 로그·에러 캡처는 Tier 1(대화 원문 등)을 포함하면 안 된다 — 로거 호출부에서 PII 필드를 직접 로깅하지 않는 것이 원칙(예: `logger.info("chunk_id=%s", chunk.id)`는 되지만 `logger.info(chunk.transcript_on_device)`는 안 됨). GlitchTip·Prometheus·Loki는 self-hosted라 Tier 4 인프라로 분류되지만, **거기 담기는 내용물이 실수로 Tier 1을 포함하면 그 자체가 위반**이다.

---

## 5. Tier 4 — 비개인정보 (외부 통신 허용)

decisions.md #58(I1)이 명시적으로 허용한 "메타데이터 수준" 외부 통신 목록:

| 통신 대상 | 목적 | 개인정보 포함 여부 |
|---|---|---|
| npm/pip 패키지 레지스트리 | 빌드 의존성 다운로드 | 없음 |
| Google Fonts CDN | 웹 콘솔 웹폰트 | 없음(정적 자산) |
| Firebase Cloud Messaging(FCM, 구글 미국 서버) | 푸시 알림 발송 | **기기 토큰만**(Tier 2 예외, §3 참조) — 알림 본문에 Tier 1/2 내용을 담지 않는다 |
| GitHub(소스코드 저장소, CI) | 버전 관리·CI/CD | 없음(코드에 PII 하드코딩 금지, CONVENTIONS.md §4) |
| 온프레미스 vLLM/BGE-M3 | LLM 추론·임베딩 | **해당 없음 — 이건 외부 통신이 아니다.** 원안이 외부 GPT-4o/Claude로 제안됐던 것을 Zero External Data Egress 원칙 위반으로 판단해 온프레미스로 대체(decisions.md #26) |
| self-hosted GlitchTip/Prometheus/Grafana/Loki | 에러 추적·메트릭·로그 | **해당 없음 — 이것도 외부 통신이 아니다.** SaaS APM(Sentry 등)은 I1 원칙상 채택 불가(decisions.md #61, I4) — 반드시 자체 인프라 |
| self-hosted Keycloak | 인증 | 해당 없음 |

> **완전 에어갭은 채택하지 않는다**(decisions.md #58) — 위 목록의 통신은 서비스 운영에 필수이며, 전부 "PII/원본 데이터가 담기지 않는" 통신이라는 조건으로 허용된다.

---

## 6. 신규 컬럼/기능 추가 시 체크리스트

새 컬럼을 추가하거나 새로운 외부 연동을 검토할 때 다음 순서로 판단한다:

1. **원문 자유텍스트(음성 전사·챕터 본문류)인가?** → Tier 1. 암호화 필수, 외부 반출 절대 금지.
2. **특정 개인을 직접 식별하는 구조화 필드(이름·연락처·생년월일급)인가?** → Tier 2. 암호화 검토(부분검색 필요성과 트레이드오프), 외부 반출 금지(국외이전 동의 등 명시적 예외 없이는).
3. **위 둘의 파생값이거나 태깅·상태·시각 값인가?** → Tier 3. 평문 저장 가능하나 내부 전용이 원칙.
4. **사람이 아니라 시스템(빌드·폰트·SDK·자체 인프라)에 대한 통신인가?** → Tier 4. 허용하되, 그 통신에 실수로 Tier 1~2가 섞여 들어가지 않는지 별도 확인.

애매하면(예: "정서 점수는 Tier 2인가 3인가?") 기본값은 **더 엄격한 등급**을 적용하고, `decisions.md`에 판단 근거를 기록한다.

---

## Related Documents

- Decisions: [silveryarn-platform.decisions.md #58(I1), #45, #56, #57, #61](../01-plan/decisions/silveryarn-platform.decisions.md)
- Design: [silveryarn-platform.design.md §7.3(PII 암호화)·§7.5(관측 스택)·§7.6(보유기간·삭제)](./features/silveryarn-platform.design.md)
- Schema: [schema.md](../01-plan/schema.md)
- Tracker: [blocked-decisions-tracker.md I1](../03-check/blocked-decisions-tracker.md)
- Conventions: [CONVENTIONS.md §4](../../CONVENTIONS.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-09-13 | 신규 작성 — decisions.md #58(I1) 후속 작업으로 지목됐던 "PII 수준 경계 명문화"를 4단계 분류 체계로 정리. schema.md 실제 컬럼과 1:1 매핑 | NUBiz AX Initiative |

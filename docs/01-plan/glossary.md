# silveryarn-platform 용어집 (Glossary)

> **Phase 1 산출물**: 프로젝트 전반에서 사용하는 용어를 통일하기 위한 문서
>
> **Project**: 은빛실타래 (SilverYarn)
> **Date**: 2026-09-05
> **Version**: 1.0
> **Source**: `Plan/어르신_자서전_말벗돌봄_기획서.md`, `Plan/자서전_말벗돌봄_프로세스_흐름도.md`, [decisions.md](./decisions/silveryarn-platform.decisions.md)

---

## Business Terms (내부 고유 용어)

| 용어 | English | 정의 | Global Standard Mapping |
|------|---------|------|--------------------------|
| 어르신 / 당사자 | Senior / User | 구술의 주체가 되는 1차 사용자 | `User` |
| 가족 | Family Member | 자서전을 감수·열람하는 2차 사용자 | `FamilyMember` (role: family) |
| 복지사 / 요양보호사 | Social Worker / Caregiver | 돌봄 연계가 필요한 2차 사용자 | `FamilyMember` (role: caregiver, social_worker) |
| 자서전 | Autobiography | 어르신 구술을 기반으로 생성되는 인생 기록물 전체 | - |
| 챕터 | Chapter | 자서전을 유년기/청년기/중장년기/현재로 나눈 단위 | `Chapter` |
| 구술 | Oral Narration | 어르신이 음성으로 말하는 인생 이야기 | - |
| 구술 청크 | Conversation Chunk | RAG 인덱싱을 위해 분할된 구술 텍스트 단위 | `ConversationChunk` |
| 작가 모드 | Author Mode | 연대기적 구술 발굴 및 문학적 초안 생성 운영 모드 | Interview Mode |
| 말벗돌봄 모드 | Companion Care Mode | 초개인화 공감 대화·고독감 해소 운영 모드 | Companion Chat Mode |
| 비서 모드 | Assistant Mode | 인지 기능 보조·일정/건강 관리 운영 모드 | Personal Assistant Mode |
| 미회고 사진 큐 | Unrecalled Photo Queue | 아직 대화로 다루지 않은 신규 사진 목록 | Pending Queue |
| 회고 | Recall / Reminiscence | 사진 등을 매개로 과거 기억을 구술하는 행위 | Reminiscence |
| 설치모드 | Install Mode | 단말 사양에 따라 자동 분기되는 앱 설치 방식 | Deployment Mode |
| 키오스크 모드 | Kiosk Mode | 저사양·재활용 단말 대상 단일 앱 잠금 설치 (확정: Device Owner Mode) | `COSU` (Corporate-Owned Single-Use) |
| 일반 앱 모드 | Normal App Mode | 고사양 개인 단말 대상 일반 설치 | Standard Install |
| 온디바이스 | On-Device | 스마트폰 자체에서 수행되는 오프라인 처리 | Edge / On-Device Processing |
| 온프레미스 | On-Premise | 자체 GPU 서버·DB에서 수행되는 처리 (외부 클라우드 아님) | On-Premise Infrastructure |
| 배치 동기화 | Batch Sync | 등록 Wi-Fi 접속 시 자동 수행되는 업/다운로드 | Batch Synchronization |
| 정서 모니터링 | Emotion Monitoring | 발화 톤·부정어 빈도 분석 기반 정서 상태 추적 | Sentiment Monitoring |
| 정서 알림 | Emotion Alert | 정서 점수 임계치 초과 시 가족·복지사에게 발송되는 알림 | `EmotionAlert` |
| 동의(옵트인) | Consent (Opt-in) | 외부 연계·개인정보 수집에 대한 사용자/보호자 명시적 동의 | `ConsentLog` |
| 은빛이 | Eunbit-i | 말벗돌봄 모드(CareAgent)의 페르소나 이름 (화면설계서 확정 표시명) | CareAgent persona name |
| 챕터 감수 이력 | Chapter Revision | 챕터의 승인/반려/코멘트 이력 (v1.1 신규) | `ChapterRevision` |
| 사진 추가 요청 | Photo Request | 가족이 당사자에게 사진 업로드를 요청하는 흐름 (v1.1 신규) | `PhotoRequest` |
| 출판 요청 | Publication | 인쇄용 PDF/ePub 조판·출판 요청 (v1.1 신규) | `Publication` |
| 지식 그래프 | Knowledge Graph | 인물·연도·사건·감정 엔티티 간 관계·타임라인을 저장하는 그래프 DB(Neo4j) | Neo4j Knowledge Graph |
| 갭 분석 에이전트 | Critic Agent | 서사 완성도를 Fact/Emotion/Relation/Reflection 4축으로 채점해 심층질문을 생성하는 서버 평가 에이전트 | Critic/Evaluator Agent |
| 경량화 패키징 엔진 | Compaction Engine | 서버의 정제 지식을 온디바이스 규격(SQLite FTS5, 압축 프롬프트)으로 변환하는 서버 모듈 | - |
| 무신경망 검색 | Zero-Neural RAG | 임베딩 모델 없이 SQLite FTS5(BM25) 키워드 검색만으로 수행하는 온디바이스 회상 검색 방식 (Phase 1 기본값) | - |

---

## Global Standards (업계 표준 용어)

| 용어 | 정의 | Reference |
|------|------|-----------|
| VAD | Voice Activity Detection — 음성 구간 검출 | - |
| STT | Speech-to-Text — 음성→텍스트 변환 | - |
| SLM | Small Language Model — 온디바이스 구동 가능한 경량 언어모델(1~3B급) | - |
| TTS | Text-to-Speech — 텍스트→음성 변환 | - |
| RAG | Retrieval-Augmented Generation — 검색 증강 생성 | - |
| BM25 / Dense Retrieval | 키워드 기반 / 임베딩 기반 검색, 본 프로젝트는 하이브리드(BM25+Dense) 채택 | - |
| PII | Personally Identifiable Information — 개인식별정보 | - |
| DPA | Data Processing Agreement — 데이터처리계약 | - |
| COSU | Corporate-Owned Single-Use — 단일 목적 잠금 단말 운영 모드 (Android Device Owner Mode 기반) | Android Enterprise |
| UUID | Universal Unique Identifier | RFC 4122 |
| AES-256 / TLS 1.3 | 저장 데이터 암호화 / 전송구간 암호화 표준 | - |
| 2FA | Two-Factor Authentication — 2단계 인증 | - |

---

## Mapping Table (비즈니스 ↔ 데이터 엔티티)

| 비즈니스 용어 | 데이터 엔티티 (schema.md 참조) |
|---|---|
| 어르신/당사자 | `users` |
| 가족/복지사 | `family_members` |
| 기기(재활용/개인) | `devices` |
| 자서전 챕터 | `chapters` |
| 사진 | `photos` |
| 구술 청크 | `conversation_chunks` |
| 회고 질문 큐 | `questions` |
| 일정/복약 | `schedule_items` |
| 정서 알림 | `emotion_alerts` |
| 동기화 이력 | `sync_sessions` |
| 동의 로그 | `consent_logs` |
| 챕터 감수 이력 | `chapter_revisions` |
| 사진 추가 요청 | `photo_requests` |
| 일별 정서 점수 | `emotion_scores` |
| 알림 수신 설정 | `notification_settings` |
| 가족 초대 | `invitations` |
| 출판 요청 | `publications` |

---

## Term Usage Rules

1. 코드에서는 **영문 표기**를 사용한다 (`Chapter`, `Device`, `EmotionAlert`).
2. UI/문서에서는 **한국어 용어**를 사용한다 (챕터, 기기, 정서 알림).
3. API 응답 필드명은 **snake_case 영문**을 우선한다 (`emotion_alert`, `recall_status`).
4. "어르신"과 "당사자"는 동일 대상(1차 사용자, `users` 테이블)을 가리키는 동의어로 취급한다.
5. "가족", "복지사", "요양보호사"는 모두 `family_members` 테이블의 서로 다른 `role` 값으로 표현한다.
6. DB enum 값은 항상 영문(예: `childhood`)으로 정의하고, 한글 표시명은 [schema.md §7](./schema.md#7-enum-표시명-매핑-한글-ui--영문-db-값) 매핑 테이블을 통해서만 노출한다 — enum 리터럴에 한글을 직접 사용하지 않는다.
7. API 서버 응답(wire format)의 필드명은 **snake_case**로 통일한다(decisions.md #20) — 프론트엔드(TS/Kotlin)에서 수신 후 각 스택의 네이밍 컨벤션으로 변환한다.

---

## Related Documents

- Schema: [schema.md](./schema.md)
- Plan: [silveryarn-platform.plan.md](./features/silveryarn-platform.plan.md)
- Design: [silveryarn-platform.design.md](../02-design/features/silveryarn-platform.design.md)
- Decisions: [silveryarn-platform.decisions.md](./decisions/silveryarn-platform.decisions.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | Phase 1 — 원본 기획서·프로세스흐름도 기반 용어집 초안 작성 | NUBiz AX Initiative |

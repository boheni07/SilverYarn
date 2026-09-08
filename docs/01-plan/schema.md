# Schema Definition

> Phase 1 Deliverable: silveryarn-platform 데이터 구조 정의

**Project**: 은빛실타래 (SilverYarn)
**Date**: 2026-09-07
**Version**: 1.6 (Do 단계 — photos 모듈 완성, status 컬럼 신규)
**Source**: Design 문서 §3 Data Model 초안 + UI/UX 화면설계서 필드 단위 대조 결과 반영
**용어 정의**: [glossary.md](./glossary.md) 참조

> **v1.1 변경 요약** (design-validator 리포트 2026-09-05 반영): `chapters`에 제목/순번/반려상태 추가, `chapter_revisions`·`emotion_scores`·`notification_settings`·`invitations`·`photo_requests`·`publications` 6개 엔티티 신설, `photos`/`devices`/`schedule_items`/`questions`/`users`/`conversation_chunks` 필드 보강, enum 값을 영문으로 통일(한글 표시명은 별도 매핑). 상세 변경 사유는 각 절의 "v1.1" 주석 참조.
>
> **v1.2 변경 요약** (사용자 제안 "Closed-Loop Architecture" 보고서 반영, 2026-09-06): `conversation_chunks`에 `graph_node_ref` 추가 — Neo4j 지식그래프 노드 참조([decisions.md #29](./decisions/silveryarn-platform.decisions.md)).
>
> **v1.3 변경 요약** (2차 design-validator 검증 반영, 2026-09-07): ① `conversation_chunks`에 `session_id`·`turn_id`·`mode`·`assistant_response` 4컬럼 추가 — AI 응답 텍스트가 서버에 영구 미보존되던 공백 해소, 온디바이스 `conversations` 테이블과 완전 매핑([decisions.md #34](./decisions/silveryarn-platform.decisions.md)). ② `devices`에 `slm_model_version`·`prompt_pack_version` 추가 — 키오스크 잠금 단말의 원격 프롬프트팩 갱신 추적([decisions.md #35](./decisions/silveryarn-platform.decisions.md)). ③ `users.primary_device_id` FK에 `ON DELETE SET NULL` 명시.
>
> **v1.4 변경 요약** (3차 design-validator 검증 H-1 반영, 2026-09-07): decisions.md #34에서 `assistant_response`를 PII 암호화 대상으로 이미 확정했으나 §5 PII 컬럼 목록에는 반영되지 않았던 누락을 정정 — 목록에 `assistant_response` 추가.
>
> **v1.5 변경 요약** (Do 단계, 2026-09-08): apps/admin "전체 기기 통합 모니터링" 화면용 `idx_sync_started_at ON sync_sessions(started_at DESC)` 인덱스 신규 — 기기로 필터하지 않는 전역 정렬 쿼리는 기존 `idx_sync_device(device_id, started_at DESC)`를 못 쓰기 때문(선두 컬럼 불일치).
>
> **v1.6 변경 요약** (Do 단계 — photos 모듈 완성, 2026-09-08): `photos`에 `status` 컬럼 신규(`pending_upload`/`uploaded`, 기본값 `pending_upload`) — [sync-contract.md §4](../02-design/sync-contract.md#4-사진-업로드--presigned-url-흐름-be-b2)의 "3단계 확인 콜백이 없으면 `photos` 행은 `status=pending_upload`로 남고" 문장이 이미 전제하고 있던 컬럼인데 §3.6 속성 표에는 빠져 있던 걸 실제 구현 중 발견 — 문서가 이미 확정해 둔 흐름을 코드로 옮기며 정정했다.

---

## 1. Terminology Definition

용어 정의는 [glossary.md](./glossary.md)에서 통합 관리한다.

---

## 2. Entity List

| Entity | Description | Key Attributes |
|--------|-------------|-----------------|
| `users` | 어르신 본인 (1차 사용자) | id, name, birth_date, primary_device_id |
| `family_members` | 가족·복지사·관리자 (2차 사용자) | id, user_id, role, contact |
| `devices` | 단말 사양·설치모드 레지스트리 | id, display_id, model_name, ram_gb, android_version, install_mode |
| `chapters` | 자서전 챕터 | id, chapter_no, title, period, body_text, status |
| `chapter_revisions` **(신규 v1.1)** | 챕터 감수 이력(승인/반려/코멘트) | id, chapter_id, version, reviewer_id, action |
| `photos` | 업로드 사진·회고 상태·인라인 배치 | id, uploader_type, recall_status, caption, placement_status |
| `photo_requests` **(신규 v1.1)** | 가족→당사자 사진 추가 요청 | id, requested_by, message, status |
| `conversation_chunks` | 구술/회고 청크 (RAG 인덱싱 단위) | id, transcript_on_device, transcript_server, assistant_response, mode, meta |
| `questions` | 미중복 회고 질문 큐 | id, text, type, linked_chapter_id |
| `schedule_items` | 일정·복약 항목 (비서 모드) | id, kind, location, due_at, recurrence |
| `emotion_alerts` | 정서 모니터링 임계치 초과 알림 | id, score, triggered_at, closed_at |
| `emotion_scores` **(신규 v1.1)** | 일별 정서 점수 시계열 (알림과 무관한 상시 기록) | id, recorded_date, score, note |
| `sync_sessions` | Wi-Fi 배치 동기화 이력 | id, direction, status, checksum |
| `consent_logs` | 개인정보 수집·외부연계 동의 이력 | id, consent_type, granted_by, granted_at |
| `notification_settings` **(신규 v1.1)** | 가족 알림 수신 채널·항목 설정 | id, family_member_id, channel, receives_* |
| `invitations` **(신규 v1.1)** | 가족 구성원 초대 링크 | id, token, role, status |
| `publications` **(신규 v1.1)** | 인쇄용 PDF/ePub 출판 요청·상태 | id, format, status, storage_ref |

> **범위 밖 (스코프 아웃, decisions.md #18)**: 구독·결제(Subscription/Payment) 도메인은 본 스키마에 포함하지 않는다. PG사·요금제가 결정되지 않은 상태로 엔티티를 설계하면 임의 결정이 되므로, 경영진 결정 이후 별도 Phase에서 추가한다.

---

## 3. Entity Details

### 3.1 users (어르신 본인)

**Description**: 구술의 주체가 되는 1차 사용자. 모든 데이터의 소유 주체.

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| name | varchar(100) | Y | 이름 (PII — 암호화 대상) |
| birth_date | date | N | 생년월일 (PII) — *v1.1: 온보딩 화면(M1) 요구사항에 맞춰 `birth_year`(연도만)에서 변경. 챕터 시기 매핑에는 연도만 추출해 사용* |
| primary_device_id | UUID | N | FK → devices.id |
| created_at | timestamptz | Y | 생성 시각 |
| updated_at | timestamptz | Y | 수정 시각 |

---

### 3.2 family_members (가족·복지사·관리자)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| role | enum(`family`,`caregiver`,`social_worker`,`admin`) | Y | 역할 |
| name | varchar(100) | Y | 이름 (PII) |
| contact | varchar(100) | Y | 연락처 (PII) |
| two_factor_enabled | boolean | Y | 2FA 활성화 여부 |
| created_at | timestamptz | Y | 생성 시각 |

**Relationships**: 1:N → `notification_settings`, `invitations.invited_by`, `emotion_alerts.acknowledged_by`, `consent_logs.granted_by`, `chapter_revisions.reviewer_id`, `photo_requests.requested_by`

---

### 3.3 devices (기기 레지스트리 — 기획서 3.7절)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK (내부 식별자) |
| display_id | varchar(20) | Y | 사람이 읽는 표시용 ID (예: `MB-1042`) — *v1.1 신규, WA6 검색·WA3 컬럼 요구 반영* — UNIQUE |
| model_name | varchar(50) | N | 기기 모델명 (예: "Galaxy S10") — *v1.1 신규, 부록A 기기 매핑 검증용* |
| user_id | UUID | Y | FK → users.id |
| ram_gb | numeric(4,1) | Y | RAM 용량(GB) — 판별 기준값 |
| android_version | varchar(20) | Y | Android OS 버전 — 판별 기준값 |
| install_mode | enum(`kiosk`,`normal`) | Y | 설치 시 1회 결정, 고정 (decisions.md #5) |
| ai_tops | numeric(5,1) | N | NPU 성능(TOPS) — 보조 지표 |
| slm_model_version | varchar(50) | N | 탑재된 온디바이스 SLM 버전 — v1.3 신규, 2차 검증 M-3 반영(CTO Enterprise B4) |
| prompt_pack_version | varchar(50) | N | 동기화로 갱신되는 페르소나/프롬프트 팩 버전 — v1.3 신규 |
| installed_at | timestamptz | Y | 설치 일시 |
| last_sync_at | timestamptz | N | 마지막 동기화 완료 시각 |

**판별 로직 (확정)**: `ram_gb < 6 OR android_version <= '11'` → `install_mode = 'kiosk'`, 그 외 `'normal'` (decisions.md #5).

**Wi-Fi 등록 정보 관련 (decisions.md #22)**: 등록 Wi-Fi(SSID 등)는 **온디바이스 로컬 전용 저장**이며 서버로 전송·보관하지 않는다. 따라서 본 테이블에 SSID/BSSID 컬럼을 두지 않는다 — 모바일 로컬 스토리지(Room)에서만 관리.

---

### 3.4 chapters (자서전 챕터)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| chapter_no | smallint | Y | 자서전 내 순번 (표시·정렬용) — *v1.1 신규* |
| title | varchar(200) | Y | 챕터 제목 (예: "스물다섯의 고개") — *v1.1 신규, WU2/WU1 화면 요구 반영* |
| period | enum(`childhood`,`youth`,`adulthood`,`present`) | Y | 시기 귀속 — *v1.1: 한글 리터럴(`유년기` 등)에서 영문으로 변경, glossary "코드는 영문" 규칙 준수. 표시명 매핑은 §7 참조* |
| body_text | text | Y | 문어체 정제본 (PII — 암호화 대상), 사진 인라인 마커 포함 |
| status | enum(`draft`,`in_review`,`rejected`,`confirmed`) | Y | *v1.1: `rejected`(반려) 상태 추가 — WF2 "수정 요청" 반려 루프 반영* |
| version | integer | Y | 현재 버전 번호 |
| updated_at | timestamptz | Y | 마지막 갱신 시각 |

**Relationships**: 1:N → `photos`, `conversation_chunks`, `chapter_revisions`, `questions`(linked_chapter_id)

---

### 3.5 chapter_revisions (챕터 감수 이력) — 신규 v1.1

**Description**: 기획서 3.3 "편집 원고 이력" 요구 및 WF2 반려/수정요청 루프를 위한 버전·코멘트 이력. `chapters.version`은 현재 버전만 담으므로 과거 이력과 감수 코멘트는 별도 테이블로 분리한다.

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| chapter_id | UUID | Y | FK → chapters.id |
| version | integer | Y | 해당 시점의 버전 번호 |
| body_text_snapshot | text | Y | 해당 버전의 본문 스냅샷 (PII — 암호화 대상) |
| reviewer_id | UUID | N | FK → family_members.id (가족 감수자) |
| review_comment | text | N | 반려/수정요청 코멘트 |
| action | enum(`approved`,`rejected`) | Y | 감수 결과 |
| created_at | timestamptz | Y | 생성 시각 |

---

### 3.6 photos (사진)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| uploader_type | enum(`family`,`self`) | Y | 업로더 유형 |
| status | enum(`pending_upload`,`uploaded`) | Y | *v1.6 신규* — Presigned URL 발급 직후 `pending_upload`, `POST /photos/{id}/complete` 확인 콜백 후 `uploaded`(기본값 `pending_upload`, sync-contract.md §4) |
| storage_ref | varchar(500) | Y | MinIO Object Storage 경로 |
| caption | varchar(300) | N | 사진 설명 — *v1.1 신규, WF3/WU2 화면 요구 반영* |
| year_tag | smallint | N | 예상 챕터 매핑용 연도 태그 |
| recall_status | enum(`pending`,`completed`) | Y | 미회고 큐 상태 (기본값 `pending`) |
| placement_status | enum(`proposed`,`confirmed`) | Y | *v1.1 신규* — AI 자동 삽입은 항상 `proposed`, 가족이 웹콘솔에서 확정 시 `confirmed` (decisions.md #11) |
| inline_position | varchar(50) | N | 챕터 본문 내 삽입 위치 앵커 — *v1.1 신규* |
| linked_chunk_id | UUID | N | FK → conversation_chunks.id |
| linked_chapter_id | UUID | N | FK → chapters.id |
| quality_flag | enum(`ok`,`blurry`,`inappropriate`,`unreviewed`) | Y | 서버 1차 자동 품질 체크 (기본값 `unreviewed`) |
| width | smallint | N | 원본 가로 픽셀 — *v1.1 신규* |
| height | smallint | N | 원본 세로 픽셀 — *v1.1 신규* |
| file_size_kb | integer | N | 압축 후 파일 크기(KB) — *v1.1 신규, decisions.md #10 압축정책 검증용* |
| mime_type | varchar(20) | N | 예: `image/jpeg` — *v1.1 신규* |
| uploaded_at | timestamptz | Y | 업로드 일시 |

---

### 3.7 photo_requests (사진 추가 요청) — 신규 v1.1

**Description**: 가족이 당사자에게 "사진을 더 올려달라"고 요청하는 흐름 (WU3 → WF3 알림 생성).

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id (요청 대상 당사자) |
| requested_by | UUID | N | FK → family_members.id |
| message | varchar(300) | N | 요청 메시지 |
| status | enum(`pending`,`fulfilled`,`dismissed`) | Y | 기본값 `pending` |
| created_at | timestamptz | Y | 생성 시각 |
| fulfilled_at | timestamptz | N | 사진 업로드로 충족된 시각 |

---

### 3.8 conversation_chunks (구술/회고 청크)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| raw_audio_ref | varchar(500) | Y | MinIO 원본 음성 경로 |
| transcript_on_device | text | Y | 온디바이스 1차 전사 (PII) |
| transcript_server | text | N | 서버 고정밀 재전사본 (PII) |
| meta_period | varchar(20) | N | 시기 메타 |
| meta_people | text[] | N | 인물(가족관계) 메타 — *v1.1: `varchar(200)` 스칼라에서 배열로 변경. RAG 인물 필터링(기획서 5.2)이 다중 인물을 전제하므로* |
| meta_place | varchar(100) | N | 장소 메타 |
| meta_emotion | varchar(50) | N | 감정 메타(기쁨/슬픔/도전 등) |
| meta_prosody | jsonb | N | 어조·억양 메타데이터 — *v1.1 신규, 기획서 5.1 "어조·억양 메타데이터 보관" 반영. 구체 스키마는 정서분석 모듈 설계 시 확정* |
| linked_photo_id | UUID | N | FK → photos.id |
| embedding_id | varchar(100) | N | Qdrant Vector DB 포인트 참조 |
| graph_node_ref | varchar(100) | N | Neo4j 지식그래프 노드 참조(인물·사건·감정 관계 추적) — v1.2 신규, decisions.md #29 |
| session_id | varchar(100) | N | 온디바이스 대화 세션 식별자 — v1.3 신규, mobile-schema.md `conversations.session_id`와 매핑 |
| turn_id | integer | N | 세션 내 턴 순번 — v1.3 신규 |
| mode | enum(`author`,`care`,`assist`) | N | 발생 모드(작가/말벗돌봄/비서) — v1.3 신규 |
| assistant_response | text | N | 온디바이스 SLM 응답 텍스트 (PII — 암호화 대상) — v1.3 신규, 2차 검증 H-2 반영. Critic Agent 대화품질 회고분석·대화 복원에 필요 |
| created_at | timestamptz | Y | 생성 시각 |

---

### 3.9 questions (회고 질문 큐)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| linked_chapter_id | UUID | N | FK → chapters.id — *v1.1 신규, M3 연대기 탭별 질문 필터링(period 기준) 반영* |
| text | text | Y | 질문 내용 |
| type | enum(`new_topic`,`follow_up`) | Y | 신규 주제 / 꼬리질문 |
| answered | boolean | Y | 기본값 false |
| created_at | timestamptz | Y | 생성 시각 |

---

### 3.10 schedule_items (일정·복약 — 비서 모드)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| kind | enum(`appointment`,`medication`) | Y | 일정 종류 |
| description | varchar(300) | N | 목적/약품명 |
| location | varchar(200) | N | 장소 — *v1.1 신규, M5 "상세(장소·목적)" 반영* |
| recurrence | varchar(50) | N | 반복 주기(예: `daily`,`weekly`,`none`) — *v1.1 신규, 복약 반복 요구 반영* |
| due_at | timestamptz | Y | 예정 시각 |
| status | enum(`pending`,`confirmed`,`missed`,`declined`) | Y | 기본값 `pending` |
| remind_count | smallint | Y | 재알림 발송 횟수, 기본값 0 — *v1.1 신규, M5 "3회 초과" 반영* |
| next_remind_at | timestamptz | N | 다음 재알림 예정 시각 — *v1.1 신규* |
| decline_reason | varchar(300) | N | 거부 사유 — *v1.1 신규, 흐름도 5.4 "거부 로그 + 사유" 반영* |
| responded_at | timestamptz | N | 응답 시각 |

---

### 3.11 emotion_alerts (정서 모니터링 임계치 초과 알림)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| score | numeric(5,2) | Y | 알림 발생 시점 정서 점수 |
| triggered_at | timestamptz | Y | 알림 발생 시각 |
| acknowledged_by | UUID | N | FK → family_members.id |
| acknowledged_at | timestamptz | N | 확인 응답 시각 |
| closed_at | timestamptz | N | 케이스 종료 시각 |

> **알림 발송 기준(언제, 누구에게)은 여전히 법무·윤리 검토 대기 중**(decisions.md #12). 본 엔티티는 검토 결과와 무관하게 재사용 가능하도록 설계했다.

---

### 3.12 emotion_scores (일별 정서 점수 시계열) — 신규 v1.1

**Description**: WF4·WF1 화면의 "7일/30일 추이 차트", "특이사항 메모"는 임계치 초과 여부와 무관하게 **매일 기록되는 시계열**이 필요하다. `emotion_alerts`는 임계치 초과 시에만 생성되므로 이 요구를 충족하지 못해 별도 엔티티로 분리했다.

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| recorded_date | date | Y | 점수 기록 일자 (1일 1행) |
| score | numeric(5,2) | Y | 일별 정서 점수 |
| note | varchar(300) | N | 특이사항 메모 (WF4 화면) |
| created_at | timestamptz | Y | 생성 시각 |

**Relationships**: N:1 → `users`. UNIQUE(`user_id`, `recorded_date`).

---

### 3.13 sync_sessions (Wi-Fi 배치 동기화 이력)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| device_id | UUID | Y | FK → devices.id |
| direction | enum(`upload`,`download`) | Y | 방향 |
| status | enum(`success`,`failed`,`retrying`) | Y | 상태 |
| checksum | varchar(128) | Y | 무결성 검증용 체크섬 |
| retry_count | smallint | Y | 기본값 0 |
| started_at | timestamptz | Y | 시작 시각 |
| finished_at | timestamptz | N | 종료 시각 |

---

### 3.14 consent_logs (동의 이력)

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| consent_type | enum(`data_collection`,`external_tts_optin`,`external_llm_optin`) | Y | 동의 유형 |
| granted | boolean | Y | 동의(true)/철회(false) |
| granted_by | UUID | N | FK → family_members.id |
| granted_at | timestamptz | Y | 동의/철회 시각 |

---

### 3.15 notification_settings (가족 알림 수신 설정) — 신규 v1.1

**Description**: WF5 화면의 "수신 대상 선택" 요구를 충족하되, **알림을 발송할지 말지의 임계치 로직(§3.11 주석 참조)은 이 테이블 범위 밖**이다. 여기서는 "이미 발생한 알림을 누가, 어떤 채널로 받을지"만 다룬다 — decisions.md #12(법무검토 대기)와 충돌하지 않도록 범위를 의도적으로 제한.

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| family_member_id | UUID | Y | FK → family_members.id |
| channel | enum(`sms`,`email`,`push`) | Y | 수신 채널 |
| receives_emotion_alerts | boolean | Y | 정서 알림 수신 여부, 기본값 true |
| receives_chapter_updates | boolean | Y | 챕터 갱신 알림 수신 여부, 기본값 true |
| receives_sync_issues | boolean | Y | 동기화 이상 알림 수신 여부, 기본값 false |
| updated_at | timestamptz | Y | 수정 시각 |

---

### 3.16 invitations (가족 구성원 초대) — 신규 v1.1

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id (초대 대상 시니어 계정) |
| invited_by | UUID | N | FK → family_members.id |
| contact | varchar(100) | Y | 초대받는 사람의 이메일/전화 |
| role | family_role | Y | 부여될 역할 |
| token | varchar(100) | Y | 초대 링크 토큰 (UNIQUE) |
| status | enum(`pending`,`accepted`,`expired`) | Y | 기본값 `pending` |
| created_at | timestamptz | Y | 생성 시각 |
| expires_at | timestamptz | Y | 만료 시각 |

---

### 3.17 publications (인쇄/출판 요청) — 신규 v1.1

**Description**: 기획서 3.3(MinIO "완성 PDF/ePub")·6장(자동 조판)·흐름도 2.4(Publish→Print) 요구를 위한 엔티티. 배송/주문 관리 등 물류 세부사항은 Phase 3 이후 별도 확정.

**Attributes**:
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Y | PK |
| user_id | UUID | Y | FK → users.id |
| format | enum(`hardcover_pdf`,`epub`) | Y | 출판 형식 |
| status | enum(`requested`,`processing`,`ready`,`delivered`) | Y | 기본값 `requested` |
| storage_ref | varchar(500) | N | 완성본 MinIO 경로 |
| requested_at | timestamptz | Y | 요청 시각 |
| completed_at | timestamptz | N | 완료 시각 |

---

## 4. Entity Relationship Diagram

> **정식 시각화 ERD**는 [`erd.md`](./erd.md)에서 관리한다 — 전체 관계 개요 + 도메인별(사용자/자서전/운영) Mermaid erDiagram, 속성·카디널리티·참조무결성 정책까지 포함한 완전판. 아래는 요약용 ASCII 스케치다.

```
[users] 1───N [family_members] ──1───N [notification_settings]
   │                  │
   │                  ├──N [invitations] (invited_by)
   │                  ├──N [chapter_revisions] (reviewer_id)
   │                  ├──N [emotion_alerts] (acknowledged_by)
   │                  ├──N [consent_logs] (granted_by)
   │                  └──N [photo_requests] (requested_by)
   │
   ├──1───N [devices] ──1───N [sync_sessions]
   ├──1───N [chapters] ──1───N [chapter_revisions]
   │             │
   │             ├──1───N [photos] ──0..1── [conversation_chunks]
   │             └──1───N [questions]
   │
   ├──1───N [photo_requests]
   ├──1───N [conversation_chunks]
   ├──1───N [schedule_items]
   ├──1───N [emotion_alerts]
   ├──1───N [emotion_scores]
   ├──1───N [consent_logs]
   ├──1───N [invitations]
   └──1───N [publications]
```

---

## 5. PostgreSQL DDL

> PII 컬럼(`name`, `contact`, `body_text`, `body_text_snapshot`, `transcript_*`, `birth_date`, **`assistant_response`**)은 애플리케이션 레벨 암호화 또는 `pgcrypto` 적용을 Do 단계에서 최종 결정한다. *(v1.4: `assistant_response`는 decisions.md #34에서 영구보존 확정 시 암호화 대상 포함이 함께 결정됐으나 이 목록에 누락돼 있던 것을 3차 검증 H-1로 정정)*

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  birth_date DATE,
  primary_device_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE family_role AS ENUM ('family', 'caregiver', 'social_worker', 'admin');
CREATE TABLE family_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role family_role NOT NULL,
  name VARCHAR(100) NOT NULL,
  contact VARCHAR(100) NOT NULL,
  two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE install_mode AS ENUM ('kiosk', 'normal');
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_id VARCHAR(20) NOT NULL UNIQUE,
  model_name VARCHAR(50),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ram_gb NUMERIC(4,1) NOT NULL,
  android_version VARCHAR(20) NOT NULL,
  install_mode install_mode NOT NULL,
  ai_tops NUMERIC(5,1),
  slm_model_version VARCHAR(50),
  prompt_pack_version VARCHAR(50),
  installed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_sync_at TIMESTAMPTZ
);

ALTER TABLE users
  ADD CONSTRAINT fk_users_primary_device
  FOREIGN KEY (primary_device_id) REFERENCES devices(id) ON DELETE SET NULL;

CREATE TYPE chapter_period AS ENUM ('childhood', 'youth', 'adulthood', 'present');
CREATE TYPE chapter_status AS ENUM ('draft', 'in_review', 'rejected', 'confirmed');
CREATE TABLE chapters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  chapter_no SMALLINT NOT NULL,
  title VARCHAR(200) NOT NULL,
  period chapter_period NOT NULL,
  body_text TEXT NOT NULL,
  status chapter_status NOT NULL DEFAULT 'draft',
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, chapter_no)
);

CREATE TYPE revision_action AS ENUM ('approved', 'rejected');
CREATE TABLE chapter_revisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  body_text_snapshot TEXT NOT NULL,
  reviewer_id UUID REFERENCES family_members(id),
  review_comment TEXT,
  action revision_action NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE uploader_type AS ENUM ('family', 'self');
CREATE TYPE photo_upload_status AS ENUM ('pending_upload', 'uploaded');  -- v1.6 신규
CREATE TYPE recall_status AS ENUM ('pending', 'completed');
CREATE TYPE placement_status AS ENUM ('proposed', 'confirmed');
CREATE TYPE quality_flag AS ENUM ('ok', 'blurry', 'inappropriate', 'unreviewed');
CREATE TABLE photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  uploader_type uploader_type NOT NULL,
  status photo_upload_status NOT NULL DEFAULT 'pending_upload',  -- v1.6 신규
  storage_ref VARCHAR(500) NOT NULL,
  caption VARCHAR(300),
  year_tag SMALLINT,
  recall_status recall_status NOT NULL DEFAULT 'pending',
  placement_status placement_status NOT NULL DEFAULT 'proposed',
  inline_position VARCHAR(50),
  linked_chunk_id UUID,
  linked_chapter_id UUID REFERENCES chapters(id),
  quality_flag quality_flag NOT NULL DEFAULT 'unreviewed',
  width SMALLINT,
  height SMALLINT,
  file_size_kb INTEGER,
  mime_type VARCHAR(20),
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE photo_request_status AS ENUM ('pending', 'fulfilled', 'dismissed');
CREATE TABLE photo_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  requested_by UUID REFERENCES family_members(id),
  message VARCHAR(300),
  status photo_request_status NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  fulfilled_at TIMESTAMPTZ
);

CREATE TYPE conversation_mode AS ENUM ('author', 'care', 'assist');
CREATE TABLE conversation_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  raw_audio_ref VARCHAR(500) NOT NULL,
  transcript_on_device TEXT NOT NULL,
  transcript_server TEXT,
  meta_period VARCHAR(20),
  meta_people TEXT[],
  meta_place VARCHAR(100),
  meta_emotion VARCHAR(50),
  meta_prosody JSONB,
  linked_photo_id UUID REFERENCES photos(id),
  embedding_id VARCHAR(100),
  graph_node_ref VARCHAR(100),
  session_id VARCHAR(100),
  turn_id INTEGER,
  mode conversation_mode,
  assistant_response TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE photos
  ADD CONSTRAINT fk_photos_linked_chunk
  FOREIGN KEY (linked_chunk_id) REFERENCES conversation_chunks(id);

CREATE TYPE question_type AS ENUM ('new_topic', 'follow_up');
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  linked_chapter_id UUID REFERENCES chapters(id),
  text TEXT NOT NULL,
  type question_type NOT NULL,
  answered BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE schedule_kind AS ENUM ('appointment', 'medication');
CREATE TYPE schedule_status AS ENUM ('pending', 'confirmed', 'missed', 'declined');
CREATE TABLE schedule_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind schedule_kind NOT NULL,
  description VARCHAR(300),
  location VARCHAR(200),
  recurrence VARCHAR(50),
  due_at TIMESTAMPTZ NOT NULL,
  status schedule_status NOT NULL DEFAULT 'pending',
  remind_count SMALLINT NOT NULL DEFAULT 0,
  next_remind_at TIMESTAMPTZ,
  decline_reason VARCHAR(300),
  responded_at TIMESTAMPTZ
);

CREATE TABLE emotion_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  score NUMERIC(5,2) NOT NULL,
  triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  acknowledged_by UUID REFERENCES family_members(id),
  acknowledged_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ
);

CREATE TABLE emotion_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recorded_date DATE NOT NULL,
  score NUMERIC(5,2) NOT NULL,
  note VARCHAR(300),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, recorded_date)
);

CREATE TYPE sync_direction AS ENUM ('upload', 'download');
CREATE TYPE sync_status AS ENUM ('success', 'failed', 'retrying');
CREATE TABLE sync_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  direction sync_direction NOT NULL,
  status sync_status NOT NULL,
  checksum VARCHAR(128) NOT NULL,
  retry_count SMALLINT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE TYPE consent_type AS ENUM ('data_collection', 'external_tts_optin', 'external_llm_optin');
CREATE TABLE consent_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  consent_type consent_type NOT NULL,
  granted BOOLEAN NOT NULL,
  granted_by UUID REFERENCES family_members(id),
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE notify_channel AS ENUM ('sms', 'email', 'push');
CREATE TABLE notification_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_member_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
  channel notify_channel NOT NULL,
  receives_emotion_alerts BOOLEAN NOT NULL DEFAULT true,
  receives_chapter_updates BOOLEAN NOT NULL DEFAULT true,
  receives_sync_issues BOOLEAN NOT NULL DEFAULT false,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'expired');
CREATE TABLE invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  invited_by UUID REFERENCES family_members(id),
  contact VARCHAR(100) NOT NULL,
  role family_role NOT NULL,
  token VARCHAR(100) NOT NULL UNIQUE,
  status invitation_status NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TYPE publication_format AS ENUM ('hardcover_pdf', 'epub');
CREATE TYPE publication_status AS ENUM ('requested', 'processing', 'ready', 'delivered');
CREATE TABLE publications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  format publication_format NOT NULL,
  status publication_status NOT NULL DEFAULT 'requested',
  storage_ref VARCHAR(500),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- 조회 성능을 위한 기본 인덱스
CREATE INDEX idx_chapters_user ON chapters(user_id);
CREATE INDEX idx_photos_user_recall ON photos(user_id, recall_status);
CREATE INDEX idx_chunks_user ON conversation_chunks(user_id);
CREATE INDEX idx_schedule_user_due ON schedule_items(user_id, due_at);
CREATE INDEX idx_sync_device ON sync_sessions(device_id, started_at DESC);
CREATE INDEX idx_sync_started_at ON sync_sessions(started_at DESC);  -- v1.5 신규 — 전체 기기 통합 모니터링(기기로 필터 없이 전역 정렬)용
CREATE INDEX idx_emotion_scores_user_date ON emotion_scores(user_id, recorded_date DESC);
CREATE INDEX idx_devices_display_id ON devices(display_id);
```

---

## 6. Validation Checklist

- [x] 모든 핵심 엔티티 정의됨 (17개 — v1.0의 11개 + design-validator 반영 6개 신규)
- [x] 용어가 명확하고 일관됨 → [glossary.md](./glossary.md) §7 enum 표시명 매핑 추가
- [x] 엔티티 관계가 명확함 → §4 ERD
- [x] UI/UX 화면설계서 필드 단위 대조 완료 (design-validator 리포트 B-1~B-13 전건 반영)
- [ ] 인덱스·제약조건 최종 보강 — Do 단계 실사용 쿼리 패턴 확정 후
- [x] 온디바이스 SQLite 스키마 매핑 문서화 → [mobile-schema.md](./mobile-schema.md)
- [x] 시각화 ERD 작성 → [erd.md](./erd.md)

---

## 7. Enum 표시명 매핑 (한글 UI ↔ 영문 DB 값)

> glossary.md "코드에서는 영문 표기 사용" 원칙에 따라 DB enum은 영문으로 통일했다 (decisions.md #21). UI 표시는 아래 매핑을 사용한다.

| Enum | DB 값 | 한글 표시명 |
|---|---|---|
| `chapter_period` | `childhood` | 유년기 |
| | `youth` | 청년기 |
| | `adulthood` | 중장년기 |
| | `present` | 현재 |
| `chapter_status` | `draft` / `in_review` / `rejected` / `confirmed` | 초안 / 감수중 / 반려 / 확정 |
| `conversation_mode` | `author` / `care` / `assist` | 자서전 작가 모드 / 말벗돌봄 모드 / 비서 모드 |

---

## 8. Next Steps

- Do 단계 착수 시 PII 컬럼 암호화 방식(pgcrypto vs 애플리케이션 레벨) 최종 결정
- `meta_prosody` JSONB 상세 스키마는 정서분석 모듈 설계 시 확정
- 구독/결제 도메인은 경영진 결정(decisions.md #18) 이후 별도 스키마 추가

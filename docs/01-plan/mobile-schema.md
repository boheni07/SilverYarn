# Mobile Local Schema (온디바이스 SQLite)

> **Summary**: 모바일 앱(Room/SQLite)의 로컬 저장소 스키마 초안 — 서버 [`schema.md`](./schema.md)의 서브셋·캐시 역할
>
> **Project**: 은빛실타래 (SilverYarn)
> **Date**: 2026-09-06
> **Version**: 0.1 (사용자 제안 "저사양 실시간 대화 프로세스" 보고서 반영, [decisions.md #33](./decisions/silveryarn-platform.decisions.md))
> **Status**: Draft — Do 단계에서 Room Entity로 구현 시 최종 확정

> 서버 `schema.md`가 SoR(전체 마스터 데이터)이며, 본 문서는 온디바이스가 오프라인 동작을 위해 로컬에 보관하는 **서브셋**을 정의한다. 컬럼명은 서버와의 동기화 페이로드 매핑을 쉽게 하기 위해 서버 필드명을 최대한 따른다.

---

## 1. 설계 원칙

- **오프라인 우선**: 여기 정의된 테이블만으로 3대 운영 모드가 완결 동작해야 한다 ([plan.md §3.1 FR-01](./features/silveryarn-platform.plan.md)).
- **Zero-Neural RAG (Phase 1 기본)**: 임베딩 벡터 테이블 없이 FTS5 키워드 검색만 사용한다 ([decisions.md #32](./decisions/silveryarn-platform.decisions.md)). 경량 VectorDB는 Phase 2+ 고사양 단말 한정 검토.
- **보존 정책**: 대화 원본 오디오는 서버 업로드 성공(200 OK) 즉시 삭제([decisions.md #30](./decisions/silveryarn-platform.decisions.md)), 텍스트/메타데이터는 최근 5일 롤링 윈도우 유지(잠정, [decisions.md #9](./decisions/silveryarn-platform.decisions.md)).
- **Wi-Fi 등록정보 로컬 전용**: SSID 등은 서버로 전송하지 않는다([decisions.md #22](./decisions/silveryarn-platform.decisions.md)).

---

## 2. 테이블 정의

### 2.1 `conversations` (구술/대화 턴 로컬 버퍼)

서버 `conversation_chunks`(schema.md §3.8)의 로컬 버퍼. 동기화 성공 시 `sync_status='SYNCED'`로 갱신 후, 원본 오디오만 삭제(#30)하고 행 자체는 5일 윈도우 동안 유지(오프라인 재생·문맥 참조용).

| Column | Type | Description |
|---|---|---|
| id | TEXT (UUID, PK) | 로컬 생성 ID — 서버 업로드 시 `conversation_chunks.id`로 그대로 사용(멱등성 키) |
| session_id | TEXT | 대화 세션 식별자 |
| turn_id | INTEGER | 세션 내 턴 순번 |
| mode | TEXT | `author` \| `care` \| `assist` — 발생 모드 |
| user_query | TEXT | 온디바이스 STT 텍스트 (서버 `transcript_on_device`에 대응) |
| assistant_response | TEXT | 온디바이스 SLM 응답 텍스트 |
| audio_path | TEXT NULL | 로컬 Opus 파일 경로 — 업로드 성공 시 NULL로 초기화(#30) |
| linked_chapter_id | TEXT NULL | FTS5 검색으로 참조된 챕터 ID (인지자극 로그용) |
| response_latency_ms | INTEGER NULL | 발화종료→첫음성 소요시간(ms) — §2.12 성능 모니터링용 |
| sync_status | TEXT | `PENDING` \| `UPLOADING` \| `SYNCED` \| `FAILED` |
| created_at | INTEGER (epoch ms) | 생성 시각 |

### 2.2 `autobiography_fts` (자서전 로컬 검색 인덱스 — FTS5 가상테이블)

서버 `chapters`(schema.md §3.4)의 요약본을 다운로드해 구성하는 **Zero-Neural RAG**의 핵심 테이블. 사용자 제안 원안의 스키마를 그대로 채택.

```sql
CREATE VIRTUAL TABLE autobiography_fts USING fts5(
    chapter_id UNINDEXED,
    period_era UNINDEXED,
    content,
    keywords,
    tokenize = 'unicode61'
);
```

- 조회 예시: `SELECT chapter_id, content FROM autobiography_fts WHERE autobiography_fts MATCH '비 OR 영암' ORDER BY bm25(autobiography_fts) LIMIT 1;`
- 갱신: 서버 `GET /api/v1/sync/download` 응답의 `chapter_updates`(design.md §4.3)로 Upsert

### 2.3 `questions_cache` (회고 질문 큐 로컬 캐시)

서버 `questions`(schema.md §3.9) 서브셋. `GET /sync/download`의 `priority_questions`로 갱신.

| Column | Type | Description |
|---|---|---|
| id | TEXT (PK) | 서버 `questions.id` |
| linked_chapter_id | TEXT NULL | |
| text | TEXT | |
| type | TEXT | `new_topic` \| `follow_up` |
| answered | INTEGER (bool) | |
| priority | INTEGER | 정렬 순위 — 미회고 사진 큐가 있으면 그보다 후순위 |

### 2.4 `unrecalled_photos` (미회고 사진 큐 로컬 캐시)

서버 `photos`(schema.md §3.6) 중 `recall_status='pending'` 서브셋. 대화 세션 시작 시 최우선 제시 대상 (기획서 4.4절).

| Column | Type | Description |
|---|---|---|
| id | TEXT (PK) | 서버 `photos.id` |
| storage_ref_local | TEXT | 로컬 캐시 이미지 경로 |
| caption | TEXT NULL | |
| year_tag | INTEGER NULL | |

### 2.5 `schedule_cache` (일정·복약 로컬 캐시)

서버 `schedule_items`(schema.md §3.10) 서브셋 + 온디바이스 자체 생성분(오프라인 등록 후 다음 동기화 시 서버 반영).

| Column | Type | Description |
|---|---|---|
| id | TEXT (PK) | |
| kind | TEXT | `appointment` \| `medication` |
| description | TEXT NULL | |
| location | TEXT NULL | |
| due_at | INTEGER (epoch ms) | |
| status | TEXT | `pending` \| `confirmed` \| `missed` \| `declined` |
| remind_count | INTEGER | |
| origin | TEXT | `server` \| `local` — 로컬 생성분은 동기화 전까지 `local` |

### 2.6 `device_state` (기기 상태 — 단일 행)

설치 시 1회 결정되는 값(§9.3) + 로컬 전용 네트워크 정보(#22).

| Column | Type | Description |
|---|---|---|
| install_mode | TEXT | `kiosk` \| `normal` — 설치 시 고정, 서버 `devices.install_mode`와 동기화(조회용) |
| registered_wifi_ssid | TEXT NULL | **로컬 전용, 서버 미전송** ([decisions.md #22](./decisions/silveryarn-platform.decisions.md)) |
| slm_model_version | TEXT NULL | 탑재된 온디바이스 SLM 버전 — design.md §2.10 프롬프트팩과 매핑 |
| prompt_pack_version | TEXT NULL | 동기화로 갱신되는 페르소나/프롬프트 팩 버전 |
| last_sync_at | INTEGER NULL | |

---

## 3. Retention & Cleanup Job

| 트리거 | 동작 |
|---|---|
| `conversations` 업로드 200 OK 수신 | 해당 행 `audio_path` 파일 삭제, `sync_status='SYNCED'` (#30) |
| 매일 자정 배치 | `created_at`이 5일(잠정, #9) 이전인 `conversations` 행 삭제 |
| `sync/download` 수신 | `autobiography_fts`/`questions_cache`/`unrecalled_photos`/`schedule_cache` Upsert |

---

## Related Documents
- 서버 스키마(SoR): [schema.md](./schema.md)
- Design §2.11 Closed-Loop, §2.12 실시간 파이프라인: [silveryarn-platform.design.md](../02-design/features/silveryarn-platform.design.md)
- Decisions: [silveryarn-platform.decisions.md](./decisions/silveryarn-platform.decisions.md) (#9, #22, #30, #31, #32, #33)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-09-06 | 사용자 제안 반영 초안 — `autobiography_fts` 등 6개 로컬 테이블 정의 | NUBiz AX Initiative |

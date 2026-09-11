# Sync Contract — 온디바이스 ↔ 서버 동기화 계약

> Phase 4 보강 산출물 — 3차 design-validator 검증 H-3, CTO Enterprise B1/백엔드 BE-B1/BE-B2/BE-B4 반영. `workflow-diagrams.md` §3(시퀀스)·§17(충돌 플로우차트)·§20(미결 영향)에서 각주로 예고된 계약 산출물의 본문이다.

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-11 · **Version**: 0.7

> 이 문서는 `docs/02-design/features/silveryarn-platform.design.md` §4(API Specification)를 동기화 도메인에 한해 상세화한다. 충돌하면 design.md가 아니라 **이 문서가 동기화 관련 SoR**이며, design.md §4.2/§6.1은 이 문서의 요약만 담는다(design.md v0.6에서 갱신 예정).

---

## 1. 왜 필요한가

기존 design.md §6.1은 "로컬-서버 버전 충돌 → 서버 마스터 데이터 우선 적용(Server-Wins)"이라는 **단일 규칙**만 정의했다. CTO Enterprise B1이 지적한 대로, 이를 모든 엔티티에 무차별 적용하면 **단말에서만 생성되는 데이터(예: 로컬 전용 응답 소요시간, 완료 표시)가 다음 동기화에서 서버 값으로 덮여 유실**된다. 아래 §3에서 엔티티별로 충돌정책을 분리한다.

---

## 2. 비동기 처리 계약 (BE-B1)

원본 음성·사진은 업로드 자체가 수 초~수십 초 걸릴 수 있고, 서버측 재전사(Whisper Large-v3)·지식화(Neo4j/Qdrant)·윤문(vLLM)까지는 더 오래 걸린다. 업로드 요청이 이 전체를 동기 대기하지 않도록 **작업 큐 패턴**을 채택한다.

### 2.1 업로드 요청

```
POST /api/v1/sync/upload
Content-Type: multipart/form-data (오디오 Opus 파일 + 1차 전사 JSON + 메타데이터)
Auth: Device Token
```

**응답 — 즉시 202 Accepted** (동기 처리 아님):

```json
// 202 Accepted
{
  "data": {
    "session_id": "sync_20260907_0231-uuid",
    "job_id": "job_upload-uuid",
    "status": "queued"
  }
}
```

### 2.2 작업 상태 조회 (신규 엔드포인트)

```
GET /api/v1/sync/sessions/{session_id}
Auth: Device Token
```

```json
{
  "data": {
    "session_id": "sync_20260907_0231-uuid",
    "status": "processing",   // queued | processing | completed | failed | partial
    "progress": {
      "transcription": "done",
      "knowledge_extraction": "processing",
      "chapter_generation": "pending"
    },
    "failed_items": []
  }
}
```

- 모바일은 `WorkManager` 주기 폴링(30초 간격, 최대 10분) 또는 다음 Wi-Fi 접속 시 재확인.
- `status=failed`/`partial`일 때 `failed_items`에 실패한 청크 ID 목록과 사유 코드 반환 — 클라이언트는 해당 원본만 재전송(전량 재업로드 금지).
- `sync_sessions` 테이블(schema.md)의 `status` 컬럼과 1:1 매핑.

### 2.3 멱등성 (신규 v0.5, CTO Enterprise B1)

네트워크 불안정으로 `POST /sync/upload`가 재전송되거나 arq 잡이 재시도돼도 **한 대화 턴은 정확히 한 번만** 적재된다. 별도 ULID 컬럼을 두지 않고 온디바이스가 이미 보내는 `(session_id, turn_id)`(대화 세션 식별자·턴 번호, schema.md v1.3)를 멱등성 키로 쓴다 — 클라이언트 계약 변경 없음.

| 계층 | 방어 | 대상 |
|---|---|---|
| 1. arq 잡 id | `_job_id = "upload:{user_id}:{session_id}:{turn_id}"` 고정 — 폴링 창(30초×10분) 안의 재전송은 같은 잡을 중복 enqueue하지 못한다 | 잡이 아직 큐/실행 중일 때 |
| 2. 파이프라인 사전 확인 | `UploadPipelineService`가 처리 전에 `conversation_chunks`에 같은 `(user_id, session_id, turn_id)` 행이 있으면 STT·임베딩·**챕터 윤문(save_draft가 version을 올리며 본문을 덧붙임)**을 건너뛰고 기존 청크 반환 | 잡이 이미 완료돼 큐에서 빠진 뒤의 재전송 |
| 3. DB 제약 | 부분 유니크 인덱스 `uq_conversation_chunks_turn (user_id, session_id, turn_id) WHERE session_id IS NOT NULL AND turn_id IS NOT NULL`(마이그레이션 0004) — 동시 실행되던 두 잡의 경쟁 상황을 IntegrityError로 차단, repository가 기존 행으로 회복 | 진짜 동시성 |

- `session_id`/`turn_id`가 둘 다 없는 비대화형/레거시 업로드는 멱등 보장 밖(부분 인덱스에서 제외) — 해당 경로가 생기면 별도 키 정의 필요.

---

## 3. 엔티티별 충돌정책 (Server-Wins 전면적용 폐기)

| 엔티티 | 정책 | 사유 |
|---|---|---|
| `conversation_chunks` | **Append-Only, 충돌 없음** | 매 발화가 새 행으로 생성되므로 갱신 충돌 자체가 발생하지 않음 |
| `chapters` (본문·귀속) | **Server-Wins** | 서버 vLLM 윤문·가족 감수를 거친 버전이 항상 최신 정본 |
| `chapter_revisions` | **Server-Only(쓰기 자체가 서버 전용)** | §7 감수 워크플로우에서만 생성, 온디바이스는 쓰기 권한 없음 |
| `schedule_items.completed_at` 등 **로컬 완료 표시** | **Device-Wins(필드 단위 병합)** | 어르신이 단말에서 "복약 완료"를 눌렀는데 서버 값으로 덮이면 실제 수행 여부가 유실됨. `due_at`/`description` 등 콘텐츠 필드는 Server-Wins, `completed_at`/`skipped_reason`만 Device-Wins로 필드 단위 분리. **구현(v0.5)**: 배치 sync 병합 로직 대신 전용 엔드포인트 `POST /schedule-items/{id}/respond`(status/decline_reason)로 실현 — 단말이 응답을 직접 push하고, `GET /sync/download`는 `status=pending`만 내려주므로(§5) 응답된 항목은 자연히 재하달에서 빠진다. 사실상 필드 병합과 동치이며 배치 파이프라인에 별도 병합 코드가 없다 |
| `conversations.response_latency_ms` (로컬 전용 성능 로그) | **Device-Only(서버에 대응 컬럼 없음, 업로드 시 `conversation_chunks` 메타에 병합 저장)** | §2.12 SLM 벤치마크(#27) 데이터 수집 경로 확보 — L-8 정정 |
| `device_state` | **Device-Wins(서버는 참고용 스냅샷만 수신)** | 단말 자체 상태이므로 서버가 권위를 가질 이유가 없음 |
| `photos` (배치·설명 텍스트) | **Server-Wins, 단 `placement_status=proposed`는 가족 확정 전까지 계속 제안 상태 유지** | AI 제안은 항상 초안(decisions.md #11) |

> **일반 원칙**: "누가 마지막에 썼는지"가 아니라 **"어느 쪽이 그 필드의 권위 있는 생성처인지"**로 정책을 정한다. 신규 엔티티 추가 시 이 표에 행을 먼저 추가한 뒤 구현한다.

---

## 4. 사진 업로드 — Presigned URL 흐름 (BE-B2)

원본 파일을 API 서버를 경유해 업로드하면 서버 대역폭·메모리를 불필요하게 소모한다. MinIO(S3 호환) Presigned URL로 클라이언트가 오브젝트 스토리지에 직접 업로드한다.

```
1) POST /api/v1/photos/upload-url
   Auth: 2FA + Role(family) 또는 Device Token
   Request: {
     "user_id": "...-uuid",       // 이 사진이 속할 어르신 계정 — v0.2에서 보강.
                                    // POST /devices 등 이 프로젝트 다른 엔드포인트와
                                    // 동일하게 소유자 ID를 요청 본문에 명시한다
                                    // (photos.user_id NOT NULL이라 서버가 반드시
                                    // 알아야 하는데 원래 예시엔 빠져 있었다)
     "uploader_type": "family",   // "family" | "self" — v0.2에서 보강
     "content_type": "image/jpeg",
     "file_size": 482913
   }
   Response 200:
   {
     "data": {
       "photo_id": "p_...-uuid",
       "upload_url": "https://minio.internal/silveryarn-photos/...(서명된 PUT URL, 15분 만료)",
       "expires_at": "2026-09-07T02:46:00+09:00"
     }
   }

2) 클라이언트가 upload_url로 파일 직접 PUT (MinIO, API 서버 미경유)

3) POST /api/v1/photos/{photo_id}/complete
   Response 200: { "data": { "photo_id": "p_...-uuid", "status": "uploaded" } }
```

- 3단계 확인 콜백이 없으면 `photos` 행은 `status=pending_upload`로 남고, 24시간 후 배치 작업이 정리(orphan cleanup). **구현(v0.4)**: `worker.py`의 arq cron job(`cleanup_orphan_photos`, 매시 정각)이 `PhotoService.cleanup_orphan_pending_uploads()`를 호출 — `uploaded_at`(생성 시각) 기준 24시간 지난 `pending_upload` 행을 찾아 MinIO 오브젝트 삭제(best-effort — 대부분은 presigned URL을 아예 안 써서 객체가 없는 게 정상 케이스라 `NoSuchKey`는 무시) 후 DB 행 삭제.
- 클라이언트 측 리사이즈(장변 1600px)·JPEG 80% 압축은 1단계 이전에 온디바이스에서 수행(decisions.md #10).

---

## 5. 증분 다운로드 (BE-B4)

```
GET /api/v1/sync/download?device_id={device_id}&since={sync_version}
Auth: Device Token
```

- `device_id`는 **필수**(v0.3 신규) — 원문엔 `since`만 있었으나 실제 구현 중 발견: Device Token 자체가 아직 특정 기기를 검증하지 못하는 스텁이라(core/auth.py) 호출 주체(어느 사용자 것을 내려줄지)를 식별할 방법이 없었다. `POST /sync/upload`가 body의 `device_id`로 device→user_id 신뢰 사슬을 쓰는 것과 동일한 이유로 쿼리 파라미터에 추가 — 서버가 이 `device_id`로 `devices` 테이블을 조회해 `user_id`를 얻는다.
- `since` 미지정 시 전체 스냅샷(최초 동기화).
- `since` 지정 시 해당 `sync_version` 이후 변경분만 반환 — design.md §4.3 예시의 `sync_version` 필드가 이 파라미터의 응답값과 대응. 서버가 발급한 `sync_version` 형식(`sync_YYYYMMDD_HHMMSS`)만 해석하며, 형식이 안 맞거나 없으면 전체 스냅샷으로 안전하게 폴백한다.
- 서버는 엔티티별로 워터마크 방식이 다르다(v0.3 구현 중 확정):
  - `chapter_updates`(chapters): 실제 `updated_at` 컬럼 기준 — 원문이 명시한 원칙 그대로.
  - `priority_questions`(questions): `updated_at` 컬럼이 없어(schema.md §3.9 — 답변 여부만 바뀌는 단순 큐) `created_at`을 근사 워터마크로 쓴다. `since` 이후 새로 생긴 **미답변** 질문만 반환. design.md §4.3 예시엔 없지만 실제로는 `linked_chapter_id`도 함께 내려준다(questions_cache의 연대기 탭별 필터링, mobile-schema.md §2.3).
  - `schedule_items`: 역시 `updated_at`이 없다(schema.md §3.10). `since`와 무관하게 **아직 응답 안 한(status=pending) 항목 전체**를 매번 반환 — 응답된 항목은 자연히 빠지므로 그 자체로 멱등적인 diff 역할을 한다.
  - `chapter_updates`의 `summary`/`keywords`는 design.md §2.11 4단계 Compaction Engine이 채운다(`chapters.compaction_summary`/`compaction_keywords`, 마이그레이션 0007). 업로드 파이프라인이 챕터 저장 직후 vLLM으로 요약을 생성한다(best-effort). 아직 요약 안 된 챕터(신규, 또는 vLLM 미가동)는 `summary`에 `body_text` 앞 200자를, `keywords`에 빈 배열을 임시로 담는다.
- `persona_snapshot`(신규 v0.7) — design.md §2.11 4단계 "단기 압축 기억(Short-term Compressed Persona)" JSON. 요약이 있는 모든 챕터의 (요약, 키워드)를 가로질러 vLLM이 만든 이 어르신의 배경지식(`{"summary": "...", "keywords": [...]}`, `users.persona_summary`/`persona_keywords`, 마이그레이션 0008) — 말벗돌봄 모드(CareAgent "은빛이")가 다음 대화를 시작할 때 참고한다. `since`와 무관하게 매번 최신값 전체를 내려준다(`chapter_updates`처럼 diff가 아니라 schedule_items와 같은 "현재값 전체" 방식 — 그래야 온디바이스가 항상 최신 배경지식을 갖는다). 요약된 챕터가 하나도 없으면 `null`. ⚠️ 정서 상태·심리 평가는 포함하지 않는다(decisions.md #25).

---

## 6. 표준 에러 코드 추가분

design.md §4.1의 표준 에러 코드에 아래 2종을 추가한다 (L-12):

| 코드 | HTTP | 상황 |
|---|---|---|
| `RATE_LIMITED` | 429 | 단말이 짧은 시간에 과다한 동기화 요청을 보낼 때 |
| `PAYLOAD_TOO_LARGE` | 413 | 단건 업로드가 서버 허용 크기(음성/사진) 초과 |

---

## Related Documents

- Design §4(API), §6.1(동기화 실패·충돌): [silveryarn-platform.design.md](./features/silveryarn-platform.design.md)
- Workflow: [workflow-diagrams.md](./workflow-diagrams.md) §3, §17, §20
- Schema: [schema.md](../01-plan/schema.md) `sync_sessions`, `photos`, `schedule_items`
- Decisions: [silveryarn-platform.decisions.md](../01-plan/decisions/silveryarn-platform.decisions.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-09-07 | 3차 design-validator 검증 H-3 반영 — 신규 작성. 비동기 업로드 계약(§2), 엔티티별 충돌정책(§3, Server-Wins 전면적용 폐기), Presigned URL 업로드(§4), 증분 다운로드(§5), 에러코드 추가(§6) | NUBiz AX Initiative |
| 0.2 | 2026-09-08 | photos 모듈 실제 구현 중 발견 — §4 1단계 요청 예시에 `user_id`/`uploader_type` 보강(photos.user_id NOT NULL이라 서버가 반드시 알아야 하는데 원래 예시엔 빠져 있었음, schema.md v1.6과 함께) | NUBiz AX Initiative |
| 0.3 | 2026-09-08 | `GET /sync/download` 실제 구현 중 발견 — §5에 `device_id` 필수 쿼리 파라미터 신규(호출 주체 식별 수단이 원문에 없었음), 엔티티별 워터마크 방식이 실제로는 다르다는 것을 명시(chapters=updated_at, questions=created_at 근사, schedule_items=pending 상태 전체), chapter_updates의 summary/keywords가 Compaction Engine 미구현으로 body_text 원문/빈 배열 대체임을 문서화 | NUBiz AX Initiative |
| 0.4 | 2026-09-08 | photos orphan cleanup 배치 실제 구현 — §4에 구현 상세 반영(`worker.py`의 arq cron job, 매시 정각 실행, MinIO 삭제는 best-effort). 실 Postgres+MinIO로 3가지 케이스(오브젝트 있는 채로 방치/오브젝트 없이 방치/최근 생성) 검증 | NUBiz AX Initiative |
| 0.5 | 2026-09-09 | §2.3 신설 — 업로드 멱등성 3계층(arq `_job_id` / 파이프라인 사전 확인 / 부분 유니크 인덱스 `uq_conversation_chunks_turn`), CTO B1 미해소분 반영. 멱등성 키는 별도 ULID 컬럼이 아니라 기존 `(session_id, turn_id)`. §3 `schedule_items` 행에 "필드 병합 = `/schedule-items/{id}/respond` 엔드포인트로 실현(배치 병합 코드 없음)" 명시. 마이그레이션 `0004` | NUBiz AX Initiative |
| 0.7 | 2026-09-11 | §5 — `persona_snapshot` 신규(design §2.11 4단계 "단기 압축 기억"). 요약된 챕터 전체를 가로지른 vLLM 요약(`users.persona_summary`/`persona_keywords`, 마이그레이션 0008), `chapter_updates`와 달리 diff가 아니라 매번 최신값 전체 반환. 정서·심리 평가 제외(decisions #25) | NUBiz AX Initiative |
| 0.6 | 2026-09-10 | §5 — `chapter_updates`의 `summary`/`keywords`가 이제 Compaction Engine(design §2.11 4단계, `chapters.compaction_*`, 마이그레이션 0007)이 채운 값. 업로드 파이프라인이 챕터 저장 직후 vLLM으로 요약 생성(best-effort). 요약 없는 챕터는 `body_text` 앞 200자 임시 대체(이전엔 원문 전체) | NUBiz AX Initiative |

# Naming Rules

> Phase 2 Deliverable — 상세 네이밍 규칙 (요약은 [`CONVENTIONS.md`](../../CONVENTIONS.md) §1~3 참조)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-05 · **Version**: 1.0

---

## 1. 공통 원칙

- 도메인 엔티티명(Chapter, Photo, Device 등)은 [`schema.md`](./schema.md)의 영문 표기를 모든 스택에서 동일하게 사용한다 (서버 클래스명, Kotlin 데이터클래스명, TS 타입명 모두 `Chapter`).
- 비즈니스 용어는 [`glossary.md`](./glossary.md)를 따른다.
- 약어는 업계 표준만 허용한다: `STT`, `TTS`, `SLM`, `VAD`, `RAG`, `PII`, `DPA` — 프로젝트 임의 약어 생성 금지.

---

## 2. 서버 (Python)

| 대상 | 규칙 | 예시 |
|---|---|---|
| 패키지/모듈 파일 | snake_case | `chapter_service.py`, `sync_gateway.py` |
| 클래스 | PascalCase | `ChapterService`, `PhotoQualityChecker` |
| 함수/메서드 | snake_case, 동사로 시작 | `get_chapter_by_id()`, `mark_photo_recalled()` |
| 변수 | snake_case | `raw_audio_ref`, `install_mode` |
| 상수 | UPPER_SNAKE_CASE | `KIOSK_RAM_THRESHOLD_GB = 6` |
| Pydantic 요청 DTO | `{Entity}{Action}Request` | `ChapterUpdateRequest` |
| Pydantic 응답 DTO | `{Entity}Response` | `ChapterResponse`, `PhotoResponse` |
| Enum 클래스 | PascalCase, 값은 schema.md의 enum 값과 동일 | `class InstallMode(str, Enum): kiosk="kiosk"; normal="normal"` |
| FastAPI 라우터 파일 | snake_case, 복수형 리소스명 | `chapters.py`, `photos.py`, `sync_sessions.py` |
| 테스트 파일 | `test_{모듈명}.py` | `test_chapter_service.py` |

---

## 3. 모바일 (Kotlin)

| 대상 | 규칙 | 예시 |
|---|---|---|
| 패키지 | 소문자 역도메인 | `com.silveryarn.mobile.ondevice.stt` |
| 클래스 | PascalCase | `OnDeviceSttEngine`, `SyncWorker` |
| Composable 함수 | PascalCase 명사형 | `ChapterInterviewScreen`, `PhotoRecallCard` |
| 일반 함수 | camelCase 동사형 | `startListening()`, `enqueueUnrecalledPhoto()` |
| 변수/프로퍼티 | camelCase | `unrecalledPhotoQueue`, `installMode` |
| 상수 | UPPER_SNAKE_CASE (companion object) | `RAM_THRESHOLD_GB`, `SYNC_RETRY_MAX` |
| Room Entity | `{Entity}Entity` | `ChapterEntity`, `PhotoEntity` |
| DAO 인터페이스 | `{Entity}Dao` | `ChapterDao` |
| 리소스 ID | snake_case | `ic_microphone`, `btn_add_photo` |

---

## 4. 웹 콘솔 (TypeScript/Next.js)

| 대상 | 규칙 | 예시 |
|---|---|---|
| 컴포넌트 파일 | PascalCase.tsx | `ChapterReviewPanel.tsx`, `EmotionAlertList.tsx` |
| 유틸 파일 | camelCase.ts | `formatSyncStatus.ts` |
| 폴더 | kebab-case | `chapter-review/`, `emotion-monitoring/` |
| 함수/변수 | camelCase | `getChapterById()`, `syncStatus` |
| 상수 | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE_MB` |
| 타입/인터페이스 | PascalCase, schema.md 엔티티와 1:1 | `Chapter`, `EmotionAlert`, `SyncSession` |
| API 라우트(BFF, 필요 시) | kebab-case 경로 | `/api/chapters/[id]/review` |
| Zustand 스토어 | `use{Domain}Store` | `useChapterReviewStore` |

---

## 5. DB (PostgreSQL) — schema.md와 동일 기준 재확인

| 대상 | 규칙 | 예시 |
|---|---|---|
| 테이블명 | snake_case, 복수형 | `chapters`, `emotion_alerts` |
| 컬럼명 | snake_case | `body_text`, `recall_status` |
| Enum 타입 | snake_case, 접미사 없음 | `install_mode`, `chapter_status` |
| 인덱스 | `idx_{table}_{column(s)}` | `idx_photos_user_recall` |
| 외래키 제약 | `fk_{table}_{ref}` | `fk_photos_linked_chunk` |
| 마이그레이션 파일(Alembic) | `{revision}_{설명_snake_case}.py` | `0007_add_consent_logs.py` |

---

## Related Documents

- [CONVENTIONS.md](../../CONVENTIONS.md)
- [structure.md](./structure.md)
- [schema.md](./schema.md)
- [glossary.md](./glossary.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | Phase 2 초안 | NUBiz AX Initiative |

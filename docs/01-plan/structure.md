# Folder Structure Rules

> Phase 2 Deliverable — 모노레포 전체 구조 (Design 문서 §11.1을 실행 가능한 수준으로 구체화)

**Project**: 은빛실타래 (SilverYarn) · **Date**: 2026-09-05 · **Version**: 1.0

---

## 1. 모노레포 최상위 구조

```
silveryarn/
├── apps/
│   ├── mobile/               # Kotlin, Android 네이티브 (온디바이스)
│   ├── web/                   # Next.js — 자서전 사용자·가족 웹 콘솔
│   └── admin/                  # Next.js — 관리자 콘솔
├── services/
│   ├── gateway/                 # API Gateway / 오케스트레이터 (FastAPI)
│   ├── author-engine/           # 자서전 작가 모드
│   ├── care-engine/             # 말벗돌봄 모드
│   ├── schedule-engine/         # 비서 모드 (일정/복약)
│   ├── sync-gateway/            # Wi-Fi 배치 동기화 처리
│   ├── rag-core/                # LLM·임베딩·Vector DB 오케스트레이션
│   └── shared/                  # 공통 유틸·Alembic 마이그레이션만 — *v1.1: 도메인 엔티티는 여기 두지 않는다.
│       │                          각 서비스의 domain/은 services/{engine}/domain/에 서비스별로 둔다
│       │                          (design-validator F-2, design.md §9.1과 정합)*
│       └── infrastructure/
│           └── migrations/       # Alembic 마이그레이션
├── packages/                   # 서버 서비스 간 공유 코드 (Python 패키지)
│   └── py-common/               # 공통 domain 엔티티, 유틸
├── infra/                      # 온프레미스 K8s/베어메탈 GPU 클러스터 (AWS 템플릿 미적용)
│   ├── k8s/
│   │   ├── base/
│   │   └── overlays/
│   └── docker-compose.yml       # 로컬 개발용
├── docs/                        # PDCA 문서 (01-plan ~ 04-report)
├── Plan/                        # 원본 기획 산출물 (보존, 수정 시 확인 필요)
├── CLAUDE.md
├── CONVENTIONS.md
└── .env.example
```

---

## 2. 서버 서비스 내부 구조 (Python/FastAPI, 서비스당 동일 패턴)

```
services/{engine}/
├── api/                # Presentation — FastAPI 라우터, Pydantic DTO
│   └── v1/
│       └── {resource}.py
├── application/        # Application — 유스케이스, 서비스 클래스
│   └── {resource}_service.py
├── domain/             # Domain — 순수 엔티티, 비즈니스 규칙 (schema.md 매핑)
│   └── {resource}.py
├── infrastructure/     # Infrastructure — SQLAlchemy repo, Qdrant/MinIO/vLLM client
│   └── {resource}_repository.py
├── tests/
│   └── test_{resource}_service.py
└── main.py             # FastAPI app entrypoint
```

> 예: `services/author-engine/api/v1/chapters.py`, `services/author-engine/domain/chapter.py`

---

## 3. 모바일 내부 구조 (Kotlin)

```
apps/mobile/src/main/java/com/silveryarn/mobile/
├── presentation/        # Jetpack Compose 화면 — 온보딩, 홈, 작가/말벗돌봄/비서 모드 UI
│   ├── onboarding/
│   ├── author/
│   ├── care/
│   ├── assistant/
│   └── settings/
├── ondevice/             # VAD·STT·SLM·TTS, 온디바이스 의도분류 라우터
│   ├── stt/
│   ├── slm/
│   └── tts/
├── local/                # Room(SQLite), 경량 VectorDB
│   ├── db/
│   └── vectorstore/
├── installmode/          # 설치모드 자동분기 (Device Owner Mode 프로비저닝) — decisions.md #5,#6
└── sync/                 # Wi-Fi 배치 동기화 워커 (WorkManager)
```

---

## 4. 웹 콘솔 내부 구조 (Next.js, `apps/web`·`apps/admin` 공통 패턴)

```
apps/web/src/
├── presentation/
│   ├── components/       # UI 컴포넌트
│   ├── hooks/             # useChapterReview 등
│   └── app/                # Next.js App Router 페이지
│       ├── (family)/        # 가족 대시보드, 원고 감수 등
│       └── (user)/           # 자서전 사용자 화면
├── application/
│   └── services/            # API 서비스 래퍼
├── domain/
│   └── types/                # schema.md 엔티티와 1:1 매핑되는 TS 타입
└── infrastructure/
    └── lib/api/                # 서버 API 클라이언트
```

> `apps/admin`은 동일 패턴에 `(admin)/` 라우트 그룹만 다르게 구성 (사용자 관리, Wi-Fi 동기화 모니터링, 기기 관리 등 — UI/UX 화면설계서 "웹·관리자" 절 참조).

---

## 5. 화면 인벤토리 ↔ 폴더 매핑 (참고)

| UI/UX 화면설계서 화면 | 매핑 경로 |
|---|---|
| 온보딩·초기설정 (모바일) | `apps/mobile/.../presentation/onboarding/` |
| 자서전 작가모드 인터뷰 (모바일) | `apps/mobile/.../presentation/author/` |
| 자서전 뷰어·챕터 읽기 (웹) | `apps/web/.../app/(user)/chapters/` |
| 원고 감수·대조 편집 (웹·가족) | `apps/web/.../app/(family)/review/` |
| Wi-Fi 동기화 모니터링 (웹·관리자) | `apps/admin/.../app/(admin)/sync-monitor/` |
| 기기 관리 (웹·관리자, 신규) | `apps/admin/.../app/(admin)/devices/` |

---

## 6. Dependency Rules (모든 스택 공통)

> **v1.1 정정** (design-validator F-1): 아래 다이어그램과 표가 서로 다른 규칙을 말하던 문제를 해소 — "Application이 Infrastructure의 인터페이스(포트)에는 의존하되 구체 구현체를 직접 import하지 않는다"는 의존성 역전 원칙으로 통일했다.

```
Presentation ──→ Application ──→ Domain ←── Infrastructure

규칙: 안쪽 레이어는 바깥 레이어에 의존하지 않는다.
      Domain은 외부 의존성 없이 완전히 독립적이다 (순수 엔티티·규칙만).
      Infrastructure는 Domain이 정의한 인터페이스(Repository 등)를 구현하고,
      Application은 그 인터페이스를 통해서만 Infrastructure 기능을 사용한다
      (의존성 역전 — 구체 클래스가 아닌 Domain의 추상 인터페이스에 의존).
```

| From | Can Import | Cannot Import |
|------|-----------|----------------|
| Presentation | Application, Domain | Infrastructure 직접 |
| Application | Domain (항상), Infrastructure는 **Domain이 정의한 인터페이스 경유만** | Infrastructure 구체 구현 클래스 직접 import, Presentation |
| Domain | (없음, 독립) | 모든 외부 레이어 |
| Infrastructure | Domain만 (인터페이스 구현 목적) | Application, Presentation |

---

## Related Documents

- [CONVENTIONS.md](../../CONVENTIONS.md)
- [naming.md](./naming.md)
- Design §9 Clean Architecture: [silveryarn-platform.design.md](../02-design/features/silveryarn-platform.design.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-09-05 | Phase 2 초안 | NUBiz AX Initiative |

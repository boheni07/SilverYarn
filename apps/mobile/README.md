# apps/mobile — 온디바이스 앱 (Kotlin/Android)

Android 네이티브(Kotlin), Device Owner Mode(COSU)로 키오스크 구현. `docs/01-plan/structure.md §3`이
폴더 구조의 SoR, `CONVENTIONS.md §2`가 네이밍·모듈 구조의 SoR이다.

## ⚠️ 환경 제약 — 로컬 개발 환경에는 여전히 Android SDK/Gradle이 없다

`services/backend`·`apps/web`·`apps/admin`은 실제 DB/브라우저로 e2e 검증했지만,
이 세션이 도는 로컬 환경에는 **Android SDK·Gradle이 설치돼 있지 않다**(IntelliJ IDEA가
번들한 JBR(JDK 21)은 있어 `ktlint` CLI 자체는 로컬에서 직접 돌릴 수 있게 됐지만,
AGP 빌드에 필요한 Android SDK는 없다). 그래서:

- **`ktlintCheck`/`test`/`assembleDebug`는 GitHub Actions CI(`mobile` job,
  `.github/workflows/ci.yml`)에서 실제로 실행·검증됐다** — 첫 CI 실행에서 ktlint
  파싱 실패(`sync/SyncApi.kt`의 KDoc 안 `/*` 시퀀스가 Kotlin의 중첩 블록 주석
  규칙과 충돌해 파일 끝까지 주석이 안 닫힌 문제), ktlint 포맷팅 위반 다수,
  XML 주석 안의 `--`(XML 스펙 위반으로 리소스 컴파일 실패) 등 실제 버그를
  여러 건 잡아 전부 수정했다(git log 참조). 지금은 `ktlint`/`test`/`assembleDebug`
  3단계 모두 CI에서 그린이다 — Room/Moshi/KSP codegen과 Compose 컴파일, APK
  어셈블까지 실제로 검증된 상태다.
- Gradle Wrapper의 `gradle-wrapper.jar`(바이너리)는 여전히 로컬에서 만들지
  못했다 — CI는 `./gradlew` 대신 `gradle/actions/setup-gradle`이 설치하는
  시스템 `gradle`을 직접 부른다. `./gradlew`로 로컬 실행하려면 Android
  Studio에서 프로젝트를 한 번 열어 Wrapper를 자동 생성해야 한다.
- 의존성 버전(Kotlin 2.0.20/AGP 8.5.2/Compose BOM 2024.09.03 등)은 CI에서
  실제로 서로 호환됨을 확인했다(2026-09-08 기준 CI 러너의 Android SDK/AGP로).
- CI가 못 잡는 것: 실기기/에뮬레이터 실행, UI 동작, Device Owner Mode(COSU)
  실제 프로비저닝 — 이건 실기기·MDM 인프라가 있어야 검증 가능하다.

## 왜 이런 구조인가

- 모듈 5분할(`presentation/`·`ondevice/`·`local/`·`installmode/`·`sync/`)은
  CONVENTIONS.md §2.2 = design.md §9.1 Clean Architecture 매핑 그대로다.
- 패키지 루트는 `com.silveryarn.mobile`(CONVENTIONS.md §2.1 예시와 동일).
- `local/db/`는 mobile-schema.md의 6개 테이블을 그대로 옮겼다 — 5개는 Room
  `@Entity`, `autobiography_fts`만 FTS5라(Room에 FTS5 전용 어노테이션이 없음)
  `AppDatabase`의 `RoomDatabase.Callback.onCreate`에서 raw SQL로 만든다
  (`AutobiographyFts.kt` 파일 상단 주석 참조).
- `installmode/InstallModeResolver`는 decisions.md #5를 그대로 옮겼다 —
  services/backend의 `determine_install_mode()`와 반드시 같은 값을 유지해야
  한다는 걸 코드 주석에 명시(서버가 최종 SoR).
- `ondevice/{stt,slm,tts}`는 인터페이스만 뒀다 — CONVENTIONS.md §2.2.1 표가
  STT/SLM/TTS 전부 "후보"(실기기 벤치마크 대기, decisions.md #27)라고 명시해
  구체 구현을 고르지 않았다. 유일한 예외는 `AndroidNativeTtsEngine` — "Android
  네이티브 TTS"는 추가 의존성 없이 바로 결정 가능한 후보라 구현까지 했다.
- `sync/SyncApi`는 services/backend의 실제 엔드포인트(`POST /devices`,
  `POST /sync/upload`, `GET /sync/sessions/{id}`, `GET /sync/download`)와
  1:1로 맞췄다 — apps/web/admin의 `lib/api/client.ts`와 같은 목적이지만,
  Moshi는 전역 snake_case 변환기가 없어 필드마다 `@Json(name=)`을 명시하는
  Kotlin 관용 방식을 썼다(RetrofitClient.kt 주석 참조).

## 스캐폴딩 중 발견한 문서 갭 — mobile-schema.md 정정

`device_state` 테이블에 `device_id`를 저장할 컬럼이 없었다 — `POST /devices`로
등록한 뒤 `POST /sync/upload` 등 이후 모든 호출이 device_id를 보내야 하는데,
그 값을 저장할 곳이 스키마에 없으면 등록 직후부터 막힌다. mobile-schema.md
서두가 "Room Entity로 구현 시 최종 확정" 상태라고 명시해 둔 그대로, 이번
구현 중 `device_id` 컬럼을 추가했다(v0.4).

## 로컬 개발 준비 (Android Studio 필요)

```bash
# Android Studio에서 apps/mobile/ 열기 — Gradle Wrapper 자동 생성됨
cp local.properties.example local.properties
# local.properties에 API_BASE_URL=http://127.0.0.1:8000 확인(sdk.dir은 Studio가 채움)

./gradlew ktlintCheck
./gradlew test
./gradlew assembleDebug
```

## 아직 안 된 것 (의도적 범위 제한)

- **로컬(Android Studio) 실행·디버깅 검증** — CI(`ktlint`/`test`/`assembleDebug`)는
  그린이지만, 실제 에뮬레이터/실기기에서 앱을 띄워 본 적은 없다. 위 "환경 제약" 참조.
- **Wi-Fi 등록·자동 동기화 트리거** — `sync/SyncWorker`는 실행 단위(대기 중인
  대화 업로드)만 정의, 등록 SSID 접속 감지→enqueue 로직은 없음.
- **Device Token 발급·저장** — erd.md §11 `device_credentials`가 결정 대기 상태라
  `core/auth.py`의 `require_device_token`도 서버 쪽까지 같이 스텁이다.
- **원본 음성 업로드 계약** — `POST /sync/upload`가 아직 `raw_audio_ref`를 문자열로
  받는 것으로 단순화돼 있어(services/backend README), 실제 파일 업로드(Presigned
  URL 등)가 확정되면 `SyncWorker`를 다시 손봐야 한다.
- **STT/SLM 엔진 실 구현** — 인터페이스만 있고, 실기기 벤치마크(decisions.md #27)
  결과가 나와야 구현체를 고를 수 있다.
- **Device Owner Mode 실제 프로비저닝** — 리시버·정책 XML 선언까지만, zero-touch/QR
  자동 등록은 실기기·MDM 인프라가 있어야 검증 가능.
- **정서 모니터링(emotion) 관련 UI** — Phase 1 피처플래그 OFF(decisions.md #25).
- **경량 VectorDB(local/vectorstore/)** — Phase 2+ 고사양 단말 한정(decisions.md #32).

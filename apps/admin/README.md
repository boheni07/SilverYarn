# apps/admin — 운영 관리 콘솔

Next.js(App Router) + TypeScript + Tailwind CSS v4. apps/web과 같은 스택·컨벤션이며
`docs/01-plan/structure.md §4`가 폴더 구조의 SoR이다.

## 왜 이런 구조인가

- `(admin)/` 라우트 그룹을 쓴다 — structure.md §5 화면 인벤토리가 지정한
  `sync-monitor/`, `devices/`, 그리고 실질적 진입점인 `users/`(§5 표에는 없지만
  본문에 언급된 "사용자 관리"에 해당, 아래 참조).
- apps/web과 완전히 동일한 계층 규율(`lib/api`→`services`→`app`/`components`/`features`,
  ESLint `import/no-restricted-paths`)과 디자인 토큰(`globals.css`)을 쓴다.
  `packages/design-tokens/`(structure.md v1.3 제안) 같은 공유 패키지는 아직
  스캐폴딩 전이라, 지금은 apps/web과 apps/admin이 `lib/api`·`types`·일부 `components/ui`
  파일을 각자 복사해 들고 있다 — 중복이 실제로 아플 때(3번째 앱이 생기거나 토큰이
  자주 바뀌기 시작할 때) 공유 패키지로 추출하는 게 낫다고 판단했다.
- 관리자 화면도 고령자 대상이 아니므로 apps/web의 `(family)` 그룹처럼
  `text-body-compact`(16px)를 기본으로 쓴다.

## 로컬 개발 준비

```bash
cd apps/admin
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL — apps/web과 동일하게 127.0.0.1 사용

# services/backend가 127.0.0.1:8000에서 떠 있어야 함
npm run dev
```

## 검증

```bash
npm run lint
npm run type-check
npm run build
```

### 실제 브라우저·실 백엔드로 엔드투엔드 검증 완료 (2026-09-08)

`services/backend`(uvicorn, 실 Postgres) + `next dev`를 동시에 띄우고 실제 기기를
`POST /devices`로 등록한 뒤 claude-in-chrome 브라우저 자동화로 확인했다:

- `/devices?userId=...` — 실 API에서 기기 목록(설치모드 배지 포함) 렌더링
- 기기 카드 **링크를 실제로 클릭**해 `/sync-monitor?deviceId=...`로 정상 이동
- `/sync-monitor?deviceId=...` — 실 동기화 이력 3건(성공/실패/재시도중)을 최신순으로 렌더링
- (같은 날 후속) `/` 홈에서 **"사용자 목록 보기" 링크를 실제로 클릭**해 `/users`로 이동
  → 실 사용자 4명(테스트 3 + 기존 1)이 최신 가입순으로 렌더링 → **사용자 카드를 실제로
  클릭**해 `/devices?userId=...`로 이동, 그 사용자의 기기 목록까지 확인 — 홈 → 사용자
  목록 → 기기 관리로 이어지는 전체 진입 경로를 클릭만으로 완주했다.
- (같은 날 또 후속) 기기 2대에 동기화 이력 4건(성공 2·실패 1·재시도중 1)을 심어 두고
  홈에서 **"전체 기기 통합 모니터링" 링크를 실제로 클릭**해 `/sync-monitor`(deviceId
  없음)로 이동 → 두 기기의 세션 4건 모두 최신순으로 렌더링 → **"실패" 필터 링크를
  실제로 클릭**해 1건으로 좁혀지는 것 확인 → **개별 세션의 "기기 XXXXXXXX" 링크를
  실제로 클릭**해 그 기기 단독 이력(2건)으로 드릴다운 — 전체 모니터링 ↔ 기기별
  모니터링이 같은 화면·같은 백엔드 엔드포인트로 왕복되는 것까지 클릭으로 확인했다.
- (같은 날 또 후속) `MB-3001`/`MB-3002` 표시명을 가진 기기 2대에 동기화 이력을 심고
  `/sync-monitor`(전체 모드)를 열어 세션 행에 **UUID 대신 `MB-3001`/`MB-3002`가
  실제로 렌더링**되는 것 확인 — curl로 `GET /sync/sessions` 응답의 `device_display_id`
  필드가 정확한 값을 담고 있는 것도 먼저 확인했다.

## 스캐폴딩 중 발견한 것 — 관리자 조회용 백엔드 엔드포인트 신설

기존 `GET /sync/sessions/{id}`는 **기기 자신이 자기 업로드 상태를 폴링하는 용도**라
`require_device_token`(Device Token) 인증이 걸려 있었다 — 관리자 콘솔이 이 엔드포인트를
그대로 가져다 쓰면 "관리자가 기기인 척 인증한다"는 의미론적으로 틀린 설계가 된다.
CLAUDE.md가 인가모델을 착수 전 5대 법적 리스크 중 하나로 명시한 만큼, 기존 엔드포인트의
인증 경계를 조용히 바꾸는 대신 **새 엔드포인트를 추가**했다:

- `GET /sync/sessions?device_id=...` (신규, `require_auth` — `devices.py`의
  `list_user_devices`와 동일한 "Admin — TODO: role 체크 강화" 패턴) — 기기 하나의
  최근 동기화 이력을 관리자가 조회.
- 기존 `GET /sync/sessions/{id}`(Device Token 인증, 기기 자신의 폴링용)는 그대로 뒀다.
- `services/backend/tests/modules/sync/test_sync_service.py` 신규 — 이전엔
  `SyncService` 유닛 테스트가 전혀 없었다(업로드 파이프라인 테스트만 존재).

### `GET /sync/sessions`를 페이지네이션+"전체 기기 통합 모니터링"으로 확장 (2026-09-08)

`device_id`를 **선택**으로 바꿨다 — 주면 기존처럼 기기 하나, 생략하면 전체 기기의
동기화 이력을 최신순으로 아우른다(둘 다 같은 엔드포인트, 응답도 이제 `PaginatedResponse`).
`status` 쿼리 파라미터로 성공/실패/재시도중만 골라볼 수도 있다. `SyncSessionRepository`의
`list_by_device()`/`list_all()` 두 메서드를 `list_all(offset, limit, device_id=None,
status=None)` 하나로 합쳤다 — 기기 필터가 있으면 기존 `idx_sync_device(device_id,
started_at DESC)`를, 없으면(전체 통합 모니터링) `idx_sync_started_at(started_at DESC)`
**신규 인덱스**(schema.md v1.5, `migrations/versions/0001_initial_schema.py`에 추가하고
이미 적용된 로컬 DB에는 `CREATE INDEX`를 직접 실행해 맞춰 뒀다)를 쓴다 — device_id가
선두 컬럼인 기존 인덱스로는 기기 무관 정렬을 못 타기 때문.

### `GET /users` 전체 사용자 목록 엔드포인트 추가 (2026-09-08)

`require_auth`(Admin — TODO: role 체크 강화, 위와 동일 패턴), `?page=1&page_size=20`
쿼리 파라미터로 페이지네이션한다. design.md §4.1이 표준 응답 포맷으로 문서화해 뒀던
`{ data, pagination }` 봉투(`shared/schemas.py`의 `PaginatedResponse`)를 실제로 쓰는
첫 엔드포인트다 — 그 전까지는 정의만 되고 어디서도 안 쓰이고 있었다. 정렬은
`created_at DESC`(최근 가입자 우선); `users` 테이블에 이 정렬 전용 인덱스는 아직 없어
Seq Scan을 감수한다(사용자 수 자체가 온프레미스 배포 특성상 크지 않을 것으로 가정 —
실사용 규모가 커지면 재검토). `tests/modules/users/test_user_service.py`에 페이지네이션
경계값(page<1, page_size 범위 밖, 빈 목록)까지 포함해 5 테스트 추가.

### `(admin)/users` 사용자 목록 화면 추가 (2026-09-08)

위 엔드포인트를 실제로 쓰는 화면 — `GET /users`가 반환하는 `{ data, pagination }` 봉투
전체가 필요해 `lib/api/client.ts`에 `apiClient.getPaginated()`를 새로 추가했다(기존
`get()`은 `data`만 반환하고 `pagination`은 버렸다). 이 화면이 이제 apps/admin의
실질적 진입점 — 홈(`/`)의 1차 CTA가 됐고, ID를 직접 입력하는 기존 폼은 "ID를 이미
아는 경우"용 보조 수단으로 내려갔다. `User` 타입에 `createdAt`/`updatedAt`이 실제
`UserResponse`에는 있었지만 design.md §3.1엔 누락돼 있던 걸 함께 발견·보강했다
(Device/SyncSession과 같은 패턴, apps/web의 타입 사본도 함께 갱신).

### `(admin)/sync-monitor` 전체 기기 통합 모니터링으로 확장 (2026-09-08)

같은 화면·같은 라우트(`/sync-monitor`)가 URL의 `deviceId` 유무로 두 모드를 겸한다 —
있으면 기존 "이 기기의 이력"(devices 화면에서 진입), 없으면 "전체 기기 통합
모니터링"(신규, 홈의 2차 CTA로 진입). 상태 필터(전체/성공/실패/재시도중) 배지형 링크,
페이지 넘김을 추가했고, 전체 모드에서는 각 세션 행에 기기 ID(줄임 표시)를 보여주고
클릭하면 그 기기 단독 이력으로 드릴다운한다. `services/sync.ts`의 `listDeviceSyncSessions`
(기기 필수)를 `listSyncSessions`(device_id/status 모두 선택)로 일반화했다.

### 전체 기기 통합 모니터링에 기기 표시명(displayId) 노출 (2026-09-08)

세션 행이 `deviceId`(UUID 앞 8자) 대신 `MB-1042` 같은 표시명을 보여준다. sync 모듈은
devices 테이블을 직접 조인하지 않는다는 원칙(structure.md §2)을 지키면서 N+1도
피하려고, `DeviceRepository.list_by_ids()`(IN 쿼리 한 번) + `DeviceService.get_display_ids()`
를 신설해 `sync/api/v1/sync.py`의 `list_sessions` 라우터가 devices 모듈을
`deps.py`(`get_device_service`, 이미 upload 엔드포인트가 쓰던 것)로만 호출한다 —
그 페이지에 실제로 등장하는 (많아야 page_size개) 기기 ID들만 한 번에 조회한다.
`SyncSessionResponse.device_display_id`는 기기가 삭제됐으면(FK CASCADE) `null` —
프론트는 그 경우 기존 UUID 줄임 표시로 자연스럽게 폴백한다.
`tests/modules/devices/test_device_service.py` 신규(3 테스트).

## 아직 안 된 것 (의도적 범위 제한)

- **실제 로그인 없음** — apps/web과 동일 이유(Keycloak 붙기 전 임시 진입점).
- **사용자 목록에 검색/필터 없음** — `/users`는 페이지 넘김만 있고 이름 검색은 없다.
  사용자 수가 많아지면 필요해질 기능.
- `apps/web`과 동일하게 인증·PII 암호화·RBAC는 전부 스텁 상태(`core/auth.py`).

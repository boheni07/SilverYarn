# apps/admin — 운영 관리 콘솔

Next.js(App Router) + TypeScript + Tailwind CSS v4. apps/web과 같은 스택·컨벤션이며
`docs/01-plan/structure.md §4`가 폴더 구조의 SoR이다.

## 왜 이런 구조인가

- `(admin)/` 라우트 그룹 하나만 쓴다 — structure.md §5 화면 인벤토리가 지정한
  `sync-monitor/`, `devices/` 두 화면.
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
- `SyncSessionRepository.list_by_device()`는 `idx_sync_device(device_id, started_at DESC)`
  인덱스를 그대로 활용(schema.md §6) — 별도 인덱스 불필요.
- `services/backend/tests/modules/sync/test_sync_service.py` 신규(5 테스트) — 이전엔
  `SyncService` 유닛 테스트가 전혀 없었다(업로드 파이프라인 테스트만 존재).

### `GET /users` 전체 사용자 목록 엔드포인트 추가 (2026-09-08)

`require_auth`(Admin — TODO: role 체크 강화, 위와 동일 패턴), `?page=1&page_size=20`
쿼리 파라미터로 페이지네이션한다. design.md §4.1이 표준 응답 포맷으로 문서화해 뒀던
`{ data, pagination }` 봉투(`shared/schemas.py`의 `PaginatedResponse`)를 실제로 쓰는
첫 엔드포인트다 — 그 전까지는 정의만 되고 어디서도 안 쓰이고 있었다. 정렬은
`created_at DESC`(최근 가입자 우선); `users` 테이블에 이 정렬 전용 인덱스는 아직 없어
Seq Scan을 감수한다(사용자 수 자체가 온프레미스 배포 특성상 크지 않을 것으로 가정 —
실사용 규모가 커지면 재검토). `tests/modules/users/test_user_service.py`에 페이지네이션
경계값(page<1, page_size 범위 밖, 빈 목록)까지 포함해 5 테스트 추가.

apps/admin 프론트엔드는 아직 이 엔드포인트를 안 쓴다 — 아래 "아직 안 된 것"의 첫 항목
그대로, 사용자 검색/목록 **화면**은 별도 작업이다(엔드포인트만 우선 요청받아 추가).

## 아직 안 된 것 (의도적 범위 제한)

- **실제 로그인 없음** — apps/web과 동일 이유(Keycloak 붙기 전 임시 진입점).
- **"전체 사용자 목록" 화면이 없음** — `GET /users`(list) 엔드포인트는 이제 있지만
  (바로 위 항목), apps/admin에 이걸 쓰는 화면은 아직 없다. 지금은 여전히 관리자가
  사용자 ID를 직접 입력해야 기기 관리 화면에 들어간다 — 검색/목록 UI는 후속 작업.
- **"전체 기기 통합 모니터링"이 없음** — 기기를 하나씩 알아야 동기화 이력을 볼 수 있다.
  "여러 기기를 한 화면에서 훑어보기"는 페이지네이션·필터 UI가 더 필요해 후속 작업.
- **사용자 관리 화면 없음** — structure.md §5 화면 인벤토리 표에는 `sync-monitor`/`devices`
  두 개만 명시돼 있다(본문 설명엔 "사용자 관리"도 언급되지만 표에 경로가 없음). 목록
  엔드포인트는 이제 있으니(위 "전체 사용자 목록" 항목) 화면만 만들면 되는 상태.
- `apps/web`과 동일하게 인증·PII 암호화·RBAC는 전부 스텁 상태(`core/auth.py`).

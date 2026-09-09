# apps/web — 웹 콘솔 (자서전 사용자·가족)

Next.js(App Router) + TypeScript + Tailwind CSS v4. `docs/01-plan/structure.md §4`가 폴더 구조의 SoR이다.

## 왜 이런 구조인가

- `(user)/`, `(family)/` 라우트 그룹으로 사용자·가족 화면을 분리한다 — 폴더의 괄호는 URL 세그먼트를 만들지 않으므로 각 그룹 루트에 동시에 `page.tsx`를 둘 수 없다(경로 충돌).
- `types/`(Domain)는 `design.md §3.1` TS 인터페이스를 그대로 포팅한 것이 SoR — 서버 DTO가 아니라 여기서 타입을 시작한다.
- `lib/api/`(Infrastructure, snake_case↔camelCase 변환 + fetch 클라이언트)와 `services/`(Application, 화면이 실제로 호출하는 API 래퍼)를 분리하고, ESLint `import/no-restricted-paths`(`eslint.config.mjs`)로 `app/`·`components/`·`features/`가 `lib/api`를 직접 import하지 못하게 강제한다 — CONVENTIONS.md §3.2 계층 규율.
- Pretendard는 Google Fonts에 없다(design-tokens.md 원본 스니펫이 틀렸음) — `pretendard` npm 패키지로 자체 호스팅. Noto Serif KR만 `next/font/google` 사용.
- Next.js 16 / React 19.2는 학습 데이터보다 최신이라 `AGENTS.md`가 코드 작성 전 `node_modules/next/dist/docs/` 확인을 강제한다.

## 로컬 개발 준비

```bash
cd apps/web
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL — localhost 말고 127.0.0.1 사용(아래 참조)

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

`services/backend`(uvicorn, 실 Postgres 연결) + `next dev`를 동시에 띄우고 claude-in-chrome 브라우저 자동화로 실제 버튼을 클릭해 확인했다:

- `/chapters?userId=...` — Server Component가 실 API에서 챕터 목록·본문을 가져와 렌더링
- `/review?userId=...` — 원고 감수 화면에서 **승인/반려 버튼을 실제로 클릭**해 `chapter_revisions` 행 생성과 `chapters.status` 전이(→ `confirmed` / → `rejected`)를 Postgres에서 직접 확인

이 과정에서 실제 인프라·실제 브라우저로만 드러나는 버그 3건을 발견해 수정했다(상세는 `docs/01-plan/structure.md` v1.12 변경 이력):

1. **CORS 미설정** — `services/backend`에 `CORSMiddleware`가 없어 Server Component fetch(Node 프로세스, CORS 미적용이라 그동안 정상 동작해 문제를 가려왔다)와 달리 `"use client"` 컴포넌트의 브라우저발 fetch만 `TypeError: Failed to fetch`로 조용히 실패했다. `services/backend`에 미들웨어 추가로 해결.
2. **`localhost`의 IPv6/IPv4 충돌** — 이 머신에 이미 떠 있던 무관한 프로젝트의 Kong 게이트웨이가 `localhost`(→`::1`)의 8000번 포트를 선점하고 있어 API 요청이 엉뚱한 서비스로 갔다. `NEXT_PUBLIC_API_URL`을 `127.0.0.1` 명시로 고정해 해결 — 이후 이 프로젝트에서는 `localhost` 대신 항상 `127.0.0.1`을 쓴다.
3. **반려된 챕터가 감수 목록에서 사라짐** — `(family)/review` 페이지가 `draft`/`in_review` 상태만 필터링해, 반려(`rejected`, schema.md #status v1.1) 직후 가족이 반려 사실을 다시 볼 수 없었다. `rejected`도 필터에 포함하도록 수정.
4. **`.env.example`이 커밋 안 되는 `.gitignore`** — create-next-app 기본 `.gitignore`가 `.env*`로 값 파일과 템플릿 파일을 구분 없이 전부 막아, 이 저장소의 관례(루트 `.env.example`처럼 템플릿은 커밋)와 어긋났다. `.env`/`.env.local`/`.env.*.local`만 막도록 좁혔다.

### `(user)/photos` 사진 갤러리 화면 신규 — 실 MinIO로 업로드까지 검증 (2026-09-08)

design.md §5.1 "사진·타임라인 갤러리" 화면 구현 — sync-contract.md §4 Presigned URL
3단계 흐름을 실제로 소비하는 첫 화면이다(그동안 backend curl·모바일 스캐폴딩으로만
검증됐다). `PhotoUploadForm`(client component)이 파일 선택 → `POST
/photos/upload-url` → **브라우저가 MinIO에 직접 PUT**(우리 백엔드 미경유) →
`POST /photos/{id}/complete` 3단계를 그대로 수행한다.

사진을 실제로 "보여주는" 문제도 새로 풀었다 — `storage_ref`는 내부 MinIO 오브젝트
키일 뿐 브라우저가 바로 못 연다. 버킷을 public-read로 열지 않고(가족 사진은 PII에
준하는 민감 데이터), `GET /users/{userId}/photos` 응답에 `view_url`(짧게 만료되는
presigned GET URL, `uploaded` 상태일 때만 존재)을 새로 추가해 해결했다
(`PhotoService.get_view_url`). `next/image`는 `unoptimized`로 렌더 — presigned
URL은 배포마다 도메인이 달라 `next.config`의 `remotePatterns`에 고정 등록할 수
없다.

실 백엔드(uvicorn)+실 MinIO+`next dev`를 함께 띄우고 claude-in-chrome으로 실제
파일을 업로드해 확인: 테스트 JPEG 업로드 → 3단계 API 호출 모두 성공 → 갤러리에
**실제 이미지가 렌더링**됨을 스크린샷으로 확인 → Postgres에서 `status=uploaded`
직접 확인. 지원하지 않는 파일 형식(.txt) 선택 시 클라이언트 측 검증이 서버 왕복
없이 바로 에러를 보여주고 기존 갤러리 내용은 그대로 유지되는 것도 확인.

### `(family)/photo-requests` 사진 요청 화면 신규 — 요청→확인→닫기 실제 검증 (2026-09-08)

photo_requests API(생성/조회/닫기)는 백엔드에 이미 완성돼 있었으나 소비하는
화면이 web·admin 어디에도 없었다. `PhotoRequestForm`(가족이 요청 생성,
`(family)/photo-requests`)과 `PendingPhotoRequestBanner`(당사자가 대기 중인
요청을 보고 닫기, `(user)/photos` 상단에 노출)를 신규 — 충족(fulfilled)은
이 화면들이 만드는 게 아니라 사진을 실제로 올리면(`PhotoUploadForm`) 서버가
자동 처리하므로(photo_request_service.py) 두 화면 다 "충족 처리" 버튼은 없다.
`Photo`/`PhotoRequest` 타입(design.md §3.1)에 `createdAt`/`fulfilledAt` 등
누락 필드 보강.

실 백엔드+`next dev`+claude-in-chrome으로 검증: 가족 계정으로 요청 2건 생성 →
어르신 화면(`/photos`)에 배너로 뜨는지 확인 → 하나를 "닫기" → 배너에서
사라지고 Postgres에서 `status=dismissed`로 바뀐 것, 나머지 하나는 `pending`
그대로인 것 확인.

⚠️ 이 검증 중 애플리케이션과 무관한 로컬 도구 문제 하나 발견: `npm run build`
직후 `.next`를 지우지 않고 바로 `npm run dev`(Turbopack)를 띄우면 `/`를 뺀
모든 라우트가 404를 낸다 — production build 산출물과 dev 캐시가 같은 `.next`
디렉터리를 다른 형식으로 써서 충돌하는 것으로 보인다. `rm -rf .next` 후
`npm run dev`로 재기동하면 정상화된다. 코드 버그 아님, 로컬 검증 시 항상
build→dev 순서로 실행했다면 `.next`부터 지울 것.

## 아직 안 된 것 (의도적 범위 제한)

- **실제 로그인 없음** — 루트 `page.tsx`는 Keycloak SSO(decisions.md #17) 붙기 전까지 쓰는 임시 개발용 진입점(userId 텍스트 입력)이다. 절대 실제 로그인 대체물이 아니다.
- 화면은 `(user)/chapters`(자서전 뷰어)·`(user)/photos`(사진 갤러리)·`(family)/review`(원고 감수)·`(family)/photo-requests`(사진 요청) 4개만 구현 — architecture 증명 목적. 나머지 화면(온보딩, 사진 인라인 편집 등)은 요청 시 추가.
- 사진 **삭제·캡션 편집** UI 없음 — 백엔드에도 아직 해당 엔드포인트가 없다(업로드/조회만 구현).
- AI 자동 인라인 사진 삽입 제안(`photos.placement_status=proposed` → 챕터 본문 편입) 화면 없음 — 백엔드 자체가 아직 미구현(services/backend/README.md 참조).
- 반려 후 작가 엔진 재생성 루프(workflow-diagrams.md §7)는 백엔드 미구현 — 현재 UI는 반려 상태 표시까지만 하고 재작성 트리거는 없다.

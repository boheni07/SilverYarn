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

## 아직 안 된 것 (의도적 범위 제한)

- **실제 로그인 없음** — 루트 `page.tsx`는 Keycloak SSO(decisions.md #17) 붙기 전까지 쓰는 임시 개발용 진입점(userId 텍스트 입력)이다. 절대 실제 로그인 대체물이 아니다.
- 화면은 `(user)/chapters`(자서전 뷰어)와 `(family)/review`(원고 감수) 2개만 구현 — architecture 증명 목적. 나머지 화면(온보딩, 사진 인라인 편집 등)은 요청 시 추가.
- 반려 후 작가 엔진 재생성 루프(workflow-diagrams.md §7)는 백엔드 미구현 — 현재 UI는 반려 상태 표시까지만 하고 재작성 트리거는 없다.
- `apps/admin`은 미착수 — 동일 패턴에 `(admin)/` 라우트 그룹만 다르게 구성될 예정(structure.md §4).

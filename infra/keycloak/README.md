# Keycloak (로컬 개발 전용)

`decisions.md #17`에서 확정한 Keycloak SSO의 **로컬 개발용** realm.
`docker compose up keycloak` 하면 `import/silveryarn-realm.json`을 `--import-realm`으로
자동 임포트한다 (같은 이름 realm이 이미 있으면 스킵 — 재임포트하려면 컨테이너를
`docker compose rm -sf keycloak` 후 재기동).

- 접속: http://localhost:9678 (admin / admin — **로컬 전용**)
- 발급자: `http://localhost:9678/realms/silveryarn` → `services/backend`의 `AUTH_ISSUER_URL`

## realm 구성 (`import/silveryarn-realm.json`)

| 요소 | 용도 |
|---|---|
| client `silveryarn-web` (public, direct grants) | SPA + e2e 패스워드 그랜트 |
| client `silveryarn-backend` (confidential) | 토큰 `aud` 대상 (리소스 서버) |
| `silveryarn-web` 매퍼 `backend-audience` | 액세스 토큰 `aud`에 `silveryarn-backend` 추가 |
| `silveryarn-web` 매퍼 `dev-amr` (**dev 전용 hardcoded**) | `amr: ["pwd","mfa"]` 주입 — 2FA 경로 e2e용. 운영 realm에는 넣지 않는다 |
| `sslRequired: none` | 로컬 http |

**유저는 realm export에 없다** (비밀번호 해시가 REST export에 빠지므로).
`services/backend/scripts/e2e_keycloak_check.py`가 admin REST로 `family1`/`worker1`/
`unlinked1`을 idempotent하게 프로비저닝한다.

## realm JSON 재생성

1. `docker compose rm -sf keycloak && docker compose up -d keycloak` (빈 상태)
2. `kcadm.sh`로 realm/client/매퍼 구성 (위 표대로)
3. admin REST `POST /admin/realms/silveryarn/partial-export?exportClients=true`
4. `id`/`secret`/`registrationAccessToken`·매퍼 `id` 제거 후 `import/silveryarn-realm.json`에 저장

## 온프레미스 배포

이 realm은 로컬 전용이다. 온프레미스는 별도 realm 관리(HA, 실 IdP 연동, 2FA 인증흐름,
`AUTH_2FA_AMR_VALUES` 실제 매핑) — infra-architect 상담 대기.

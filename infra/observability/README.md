# 관측 스택 (로컬 개발 전용)

`decisions.md #61`(2026-09-12 사용자 결정, I4)에서 확정한 self-hosted 관측 스택.
Sentry SaaS·다른 SaaS APM은 I1(PII 외부유출 금지) 원칙상 사용 불가해 전부
self-hosted다.

```
services/backend(호스트 프로세스, 포트 9677)
  ├─ /metrics ──────────► prometheus (스크레이프, host.docker.internal:9677)
  ├─ logs/app.jsonl ────► alloy(파일 tail) ──► loki
  └─ sentry-sdk(에러) ──► glitchtip-web
                                          prometheus·loki ──► grafana(:9680)
```

백엔드는 모듈러 모놀리스 단일 배포 단위(decisions.md #44)라 아직 컨테이너화되지
않고 이 호스트에서 직접 uvicorn으로 돈다 — 그래서 Prometheus는 `host.docker.internal`로
스크레이프하고, 로그는 push가 아니라 파일 공유(바인드마운트) 방식을 쓴다.

## 기동

```bash
cd infra
docker compose up -d glitchtip-db glitchtip-redis glitchtip-web glitchtip-bootstrap prometheus loki alloy grafana
```

`glitchtip-bootstrap`이 `glitchtip-web`의 헬스체크(`/_health/`, 마이그레이션 완료
후에만 healthy)를 기다렸다가 자동으로 계정·조직·프로젝트·DSN을 만든다 — Keycloak
realm과 달리 GlitchTip엔 가져오기 기능이 없어 `glitchtip-bootstrap.py`(Django ORM
스크립트)로 동등한 효과를 낸다. **딱 한 가지만 수동**: 아래 로그에서 DSN을 복사해
`.env.local`에 넣는 것.

```bash
docker compose logs glitchtip-bootstrap
# [glitchtip-bootstrap] DSN: http://<key>@localhost:9679/1
```

```bash
# services/backend/.env.local 또는 루트 .env.local
OBS_GLITCHTIP_DSN=http://<key>@localhost:9679/1
```

get_or_create라 재실행해도 안전하고, 한 번 만든 키는 `glitchtip_db_data` 볼륨에
남아 재부팅해도 그대로다(볼륨을 지우면 DSN도 새로 발급됨).

## 접속

| 서비스 | 주소 | 계정 |
|---|---|---|
| Grafana | http://localhost:9680 | admin / silveryarn_local_dev |
| GlitchTip | http://localhost:9679 | dev@silveryarn.local / silveryarn_local_dev (부트스트랩이 생성) |
| Prometheus | 호스트 포트 없음 — Grafana 데이터소스로만 조회 | — |
| Loki | 호스트 포트 없음 — Grafana 데이터소스로만 조회 | — |

Prometheus·Loki를 호스트에 노출하지 않은 이유: 9670-9680 범위에 남은 슬롯이
9679·9680 둘뿐이라(`docker-port-range-constraint`) GlitchTip·Grafana에 배정했다.
둘 다 사람이 볼 필요가 있을 땐 Grafana를 거치면 된다.

## 왜 Promtail이 아니라 Alloy인가

Promtail은 2026-03-02부로 EOL(공식 후속: Grafana Alloy) — 신규 구축이라 처음부터
Alloy로 시작했다. `config.alloy`가 `services/backend/logs/*.jsonl`을 tail해
Loki로 보낸다.

## 로그 포맷

`core/logging.py`가 stdout과 `OBS_LOG_FILE`(기본 `logs/app.jsonl`, 서비스 재시작
시 이어쓰기)에 동일한 JSON 한 줄씩을 남긴다. 이전에는 "구조화 로그"라고 docstring에
써놓고 실제로는 일반 텍스트를 썼던 코드·문서 드리프트가 있었다(SoR 원칙 위반) —
이번에 실제 JSON으로 바로잡았다.

## 온프레미스 배포

이 구성은 로컬 전용이다(SECRET_KEY·DB 비밀번호 하드코딩, 단일 인스턴스, 백업 없음).
온프레미스는 별도 시크릿 관리·고가용성·백업 정책 필요 — infra-architect 상담 대기.
백엔드가 컨테이너화되면(현재는 decisions.md #44로 미착수) Prometheus 스크레이프
대상도 `host.docker.internal`이 아니라 서비스명으로 바뀐다.

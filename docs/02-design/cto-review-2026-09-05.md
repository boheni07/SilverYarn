# CTO팀 설계 검토 — 은빛실타래(silveryarn-platform)

> **Summary**: 개발팀 착수회의를 앞두고 5개 전문가 관점(아키텍처·인프라·보안·프론트엔드·PM)에서 진행한 "이 설계로 착수해도 되는가" 심사 전문
>
> **Date**: 2026-09-05
> **참여 관점**: Enterprise Architect, Infrastructure Architect, Security Architect, Frontend Architect, Product Manager, Backend/API(bkend-expert), QA Strategist — **총 7개 관점 완료**
> **오케스트레이터**: `bkit:cto-lead` 최종 종합 단계에서 API 사용량 한도로 중단되어, 7개 개별 전문가 리뷰를 순차 실행하고 종합은 본 문서에서 수기 정리함.

---

## 종합 판정 요약

| 관점 | 판정 | 핵심 |
|---|---|---|
| Enterprise Architect | Go with Conditions | 동기화 계약·SLM 모델·서비스 분해·이중두뇌 설계 4대 Blocker |
| Infrastructure Architect | Go with Conditions (인프라 미정이 착수 자체는 막지 않음) | docker-compose 부재가 유일한 진짜 착수 Blocker(1.5주) |
| Security Architect | 조건부 — 법적 Blocker 6건 (가장 중대) | 동의·보유기간·인가모델·암호화가 "Do 단계 이연 불가"급 |
| Frontend Architect | 조건부 착수 (Blocker 4건 선결 필요) | 컬러 토큰 WCAG AA 미달, Next.js 폴더구조 오류 |
| Product Manager | Go — 진짜 착수 차단은 예산 1건뿐 | 법무검토(#12)는 Phase 2 사안이라 착수 안 막음 (단, 보안 관점은 이견) |
| Backend/API (bkend-expert) | Go with Conditions | BaaS 대신 자체 FastAPI 선택은 타당함을 재확인. 단, 비동기 job 계약·파일업로드 방식·엔티티 소유권 매핑 3건 선결 필요 |
| QA Strategist | Go with Conditions | 정량적 Pass/Fail 기준·고령화자 음성데이터셋·장애주입 실기기랩 3건 — 모두 코드와 무관한 1~2주 조달작업 |

**관점 간 핵심 이견**: PM은 정서 모니터링 법무검토(#12)가 Phase 2 사안이라 Phase 1 착수를 막지 않는다고 판단했으나, Security는 `emotion_scores` "기록" 자체(알림과 무관)가 Phase 1 온보딩·동의 설계와 맞물려 더 이르게 문제화된다고 판단함 — 이 이견은 해소하지 않고 경영진 판단에 맡김(§8 참조).

---

## 1. Enterprise Architect — 아키텍처 전략 심사

### 강점
- 미결 정책이 착수를 막지 않도록 스코프를 쪼갠 규율: decisions.md #19가 정서 알림을 "누가·어느 채널로 받을지(즉시 구현)"와 "언제 보낼지(법무 대기)"로 분리
- 매크로 아키텍처 선택은 제약조건상 유일함: 오프라인 시니어 환경 + Zero External Data Egress + 가족 협업을 동시에 만족하는 조합은 하이브리드뿐이며 design §2.0이 대안 탈락 근거를 문서화
- 화면↔스키마 역추적 완료: 17개 엔티티가 UI/UX 화면설계서 필드 단위로 대조되어 "화면은 있는데 테이블이 없는" 착수 실패 요인 제거

### Blocker

**B1. 동기화 계약(Sync Contract) 부재 → 실제 데이터 영구 소실 경로 존재**
기획서 3.5 "최근 5일만 로컬 보관"과 미동기화분 보존 규칙의 관계가 어느 문서에도 없음. 30일 미접속 단말은 6~30일차 구술이 삭제되고 서버에도 없어 복구 불가. design §6.1의 Server-Wins가 엔티티 무차별 적용이라 단말 전용 생성 데이터(`schedule_items`, `conversation_chunks`, 당사자 업로드 사진)가 서버 사본에 덮여 사라짐.
→ 액션: `docs/02-design/sync-contract.md` 작성 — 미동기화 보존창 예외, 엔티티별 충돌정책(server-authoritative vs device-origin append-only), ULID 멱등성 키, 재개가능 청크 업로드, 저장공간 압박 시 열화정책. (3~4일 설계 + 1일 리뷰)

**B2. 온디바이스 SLM 모델 미선정 — 모바일 크리티컬 패스 전체 대기**
모델이 정해져야 런타임(llama.cpp/MLC/MediaPipe/ONNX-RT)·메모리예산·토크나이저·프롬프트포맷·양자화 손실 허용선이 정해짐. 부록A RAM 6GB 임계값도 현재는 추정치.
→ 액션: 모바일 리드가 후보 2~3종(Kanana-2 등)을 실기기 3대(S10급/A35급/S24급)에서 STT+SLM+TTS 동시상주 벤치마크(첫토큰지연·메모리피크·배터리·한국어 노년층 STT WER). (2주, 착수와 병렬 불가)

**B3. 6개 마이크로서비스 분해에 근거 없음, 비동기 파이프라인 기반 스택 누락**
6개 서비스가 데이터 소유권을 나누지 않음(단일 PostgreSQL·단일 Alembic 체인 → 스키마 변경 시 6개 동시배포). care/schedule-engine은 Phase 2/3 기능인데 Phase 1부터 스캐폴딩 유지비 발생. 도메인 엔티티 소유권 모순(design §9.1 서비스별 vs structure.md 공유 커널). 작업 큐·Redis가 확정 스택에 없음 — sync→rag-core→author-engine 파이프라인에 트랜잭션/보상 없어 부분 실패 시 고아 벡터 발생 가능.
→ 액션: Phase 1을 모듈러 모놀리스 2프로세스(api / worker)로 재정의. 분리 근거는 도메인이 아닌 런타임 특성(요청응답 vs GPU배치). 폴더는 `services/{engine}/` 유지, import-linter로 CI 차단, PostgreSQL은 스키마 네임스페이스로 분리. 큐는 Redis+Arq/Celery, outbox 패턴. (결정회의 반나절 + ADR 1일)

**B4. 이중 두뇌(온디바이스 SLM vs 서버 LLM) — 문제 정의조차 안 됨**
흐름도 2.3은 서버 CareAgent가 실시간 LLM 응답을 만든다고 되어 있으나 offline-first 원칙상 대화는 전부 온디바이스이고, API 엔드포인트 목록에 실시간 대화 엔드포인트가 없음 — 서버가 직접 말을 거는 경로 존재 여부 자체가 미정. 페르소나 3종 중 2종 표시명 미정, 프롬프트/페르소나 배포 경로(동기화 다운로드 항목)도 미정 → 키오스크 단말 페르소나 변경이 APK 재배포로만 가능(Device Owner 잠금 단말에서 최악의 배포 채널).
→ 액션: 서버 실시간 대화 경로 존부 결정(권고: Phase 1엔 없음, 서버는 챕터생성 전용), 단일정체성 "은빛이"+3톤 레지스터로 통일(권고), 프롬프트팩을 버전드로 정의해 동기화 항목에 추가, `devices`에 `slm_model_version`·`prompt_pack_version` 컬럼 추가. (2일)

### Concern (병행 가능)
- 3스택 계약 자동화 부재 — OpenAPI를 유일 생성원으로 codegen 파이프라인 구축 (2주차까지)
- 동기화 썬더링 허드 + GPU 메모리 예산 — admission control, 4모델 동거 VRAM 예산표 필요 (3주차까지)
- 알림 발송 경로(SMS/이메일)가 Zero Egress 원칙과 미해결 충돌 (Phase 1 온보딩 착수 전)
- 장기 오프라인 시 품질 열화 사다리 미정의 (4주차)
- 공유 커널(`packages/py-common`) 경계 규칙 부재 (B3과 동시)
- 관측·에러추적 스택 미정, Sentry SaaS는 Zero Egress상 사용 불가 → 자체호스팅 GlitchTip 등 (6주차)
- 인프라 설계 미착수 — Phase 1은 docker-compose로 진행 가능, GPU 토폴로지는 조기 확정 필요 (6주차)

### 한 줄 총평
Go with conditions — 제품 정의와 데이터 모델은 착수 가능하나 "어떻게 분산·동기화·보호할지" 3개 실행축이 비어있음. B1~B4를 닫는 데 약 2주(B2 벤치마크가 임계경로), 그 기간 모바일 UI 셸·웹 스캐폴딩·스키마 마이그레이션은 병행 착수 최적. **6개 마이크로서비스로 첫 커밋을 찍는 것만은 오늘 막아야 함.**

---

## 2. Infrastructure Architect — 인프라 준비도 심사

### 강점
- 오프라인 우선 설계가 온프레미스 단일사이트 최대 약점(가용성)을 구조적으로 흡수 — 가용성 목표를 99.9%가 아닌 99%(월 7시간 다운 허용)로 정직하게 설정 가능
- 서버 워크로드가 대화형이 아니라 Wi-Fi 트리거 배치 큐 — GPU 소수 대수를 높은 활용률로 운영 가능
- 확정 스택 전체가 자체호스팅 가능 OSS이고 의존성 역전이 이미 규정됨 — LLM/STT/임베딩 클라이언트를 스텁으로 교체 가능한 구조

### Blocker

**B1. 로컬 개발환경 미정의** — `infra/` 디렉토리 자체가 리포지토리에 없음(전체가 문서 22개뿐)
→ `infra/docker-compose.dev.yml`(postgres/qdrant/minio/keycloak) + LLM/STT/임베딩 **스텁 3종**(OpenAI 호환 인터페이스) 작성. CONVENTIONS.md §4에 `STT_`·`EMBEDDING_` 접두사 누락분 추가. Qdrant 컬렉션 스펙(1024-dim/cosine) 확정. (1~1.5주)

**B2. "Zero External Data Egress" 사정거리 미정의** — 완전 에어갭이면 인프라 공수 2배, 최소해석이면 GitHub Actions 등 그대로 사용
→ 경영·보안 합동 결정 1회: "PII·원본음성·임베딩의 아웃바운드 전송만 금지, 빌드타임 인바운드는 검증된 미러 경유 허용" 권고. (1주)

**B3. 원본 구술 음성의 보유·파기 기간 미정** — 동의 취득 시 보유기간 고지 의무(개인정보보호법), 스토리지 사이징이 10배 이상 갈림(WAV 무기한 14GB/인·년 vs Opus 1.3GB/인·년)
→ 법무 검토(보유기간·파기트리거) + schema에 `retention_until`·`purged_at` 추가. (2~3주, 온보딩·동의 모듈 착수 전 완료 필수)

**B4. 예산·상면·전력 승인 미착수** — GPU 조달 리드타임 8~16주 + 랙·OS·드라이버 2~4주 = 총 12~24주. 2×A100 PCIe 노드만으로 1.5~2kW, 일반 사무실 서버랙 한계 초과
→ 하드웨어 트랙을 앱 트랙과 분리, 별도 승인 D-day 지정. IDC 상면/전용 전산실 확보 여부 즉시 확인.

> 판정: 서버 앱 코드는 B1 완료 시점(약 1.5주 뒤) 착수 가능. 인프라 미정 자체는 착수를 막지 않음.

### 리소스 산정 스트로우맨 (팀 반박·확정용 가정, 파일럿 200명 기준)
| 컴포넌트 | 사양 | 근거 |
|---|---|---|
| GPU 노드 | A100 80GB×2 (대체: L40S×2, H100×1) | LLM 32B AWQ 4bit ~20GB + Whisper large-v3 ~4GB + BGE-M3 2.3GB + TTS 3GB 동시 상주 |
| GPU 처리량 | 실사용 1 GPU-시간/일 미만 | STT 0.7~1.1 GPU-h/일 + LLM ~20분/일 — 파일럿은 1장으로도 성립 가능 |
| Qdrant | 8vCPU/64GB/1TB | 100만 벡터(200명×5,000) — 2,000명·3년이면 3,000만 벡터, int8 양자화 필요 |
| PostgreSQL | 8vCPU/32GB + replica | 용량보다 HA·PITR이 사양 근거 |
| MinIO | 가용 ~24TB | WAV 기준 200명 2.8TB/년 — Opus 전환 시 1/10 (B3 결정에 종속) |
| 네트워크 | 대칭 200Mbps+, 고정IP, DMZ | 귀가시간대 버스트 집중 고려 |
| 성능 SLO(제안) | 동기화→챕터반영 P95 30분, 감수 재생성 P95 60초 | "동시접속자" 프레이밍 자체가 부적절(대화형 동시성 ≈0) |

### Concern (병행 가능)
- 인터넷 노출 경계(DMZ, mTLS 디바이스 인증서) 설계 부재 (4주)
- "A100" 조달 리스크 — L40S/H100/RTX 6000 Ada 대체안 병기 (2주)
- 컨테이너 레지스트리·패키지 미러(Harbor+Nexus) 부재 (6주)
- 배포 전략 — K8s는 무상태만, Postgres/MinIO/Qdrant/vLLM은 K8s 밖 전용 노드 권장 (6주)
- GPU 스케줄링 — MIG 비권장(Phase 1), GPU0=vLLM 전용/GPU1=STT+임베딩+TTS (6주)
- CI/CD·GitOps 부재 (8주)
- 관측 스택 전무 — 계측은 1주차부터, 풀스택은 8주 (Prometheus+Grafana+Loki+DCGM+GlitchTip)
- 백업·DR — MinIO가 원본이자 백업타깃인 순환 SPOF, 3-2-1 원칙 필요 (8주)
- 시크릿 관리 — 착수 즉시 SOPS+age, 운영 진입 전 Vault/OpenBao+ESO (하드웨어 도착 후)
- 가용성 목표·야간 온콜 주체 미정 — 월99%/RTO4h/RPO1h 제안 (4주)

### 한 줄 총평
인프라 미정은 Do 착수를 막지 않음 — 막는 것은 docker-compose+스텁 3종(1.5주)뿐. 진짜 위험은 착수 지연이 아니라 3~6개월짜리 하드웨어 조달과 개인정보 보유기간 결정을 지금 시작하지 않아 Phase 1 완료가 무기한 밀리는 것.

---

## 3. Security Architect — 보안·법무 심사 (가장 중대)

### 강점
- 데이터 등급에 맞는 아키텍처 기본값 — Zero External Data Egress·전면 온프레미스·오프라인 우선을 원칙으로 선언, 클라우드/BaaS 템플릿 명시적 거부
- 법적 미결 사항을 코드로 밀어넣지 않은 절제 — decisions.md #12를 격리, #19에서 범위를 쪼갬
- 착수 전 보안 리뷰가 가능한 수준의 설계 상세 — RBAC 매트릭스, 백업정책, 동기화 멱등성, 설치모드 확정 수치까지 문서화

### Blocker (법적+기술)

**B1. 정서 데이터는 "알림"이 아니라 "기록" 시점부터 이미 위법 소지**
발화톤·부정어휘 기반 정신건강 상태 추정은 개인정보보호법 제23조 '건강에 관한 정보'(민감정보) 해당 가능성. 민감정보는 별도 동의 필수인데 `consent_logs.consent_type`에 해당 유형 없음 — 동의 근거 없이 민감정보 생성·축적 파이프라인이 이미 Phase 1 설계에 켜져 있음. 부수 결함: `notification_settings.receives_emotion_alerts` 기본값이 opt-out(true) — 방향이 반대.
→ Phase 1 코드에서 정서 파이프라인 전면 OFF(`emotion_scores` write, `meta_emotion`/`meta_prosody` 산출·저장 피처플래그). decisions.md #12 범위를 "알림기준"에서 "정서데이터 생성·보관·제공 전반"으로 재정의. (개발 2일 / 법무 회신 2~3주)

**B2. 대리동의의 법적 근거 공백**
`consent_logs.granted_by`가 `family_members.id`만 참조 — 가족 대리동의가 스키마상 기본 경로이고 어르신 본인 동의를 기록할 컬럼조차 없음. 판단능력 있는 성인에 대한 가족 대리동의를 인정하는 명시 조문 없음(법무 확인 필요). RBAC 매트릭스·API 목록에 정보주체(어르신) 행/엔드포인트가 0개.
→ 본인 동의 필수 범위 법무 확정, `consent_logs`에 actor 구분(self/proxy/legal_guardian) 추가, RBAC에 `data_subject` 행 신설, 본인 권리행사 경로 설계. (법무 3주 / 반영 1주)

**B3. 보유기간·파기정책이 전 문서에 없음**
보유기간 없이는 적법한 동의서 작성 자체가 불가능(법 제15조②). 삭제 대상이 PostgreSQL/MinIO/Qdrant/단말 Room DB/로컬 스냅샷 5곳에 흩어져 있는데 `ON DELETE CASCADE`(Postgres 한정)뿐 — 사용자 삭제 시 MinIO 원본음성·Qdrant 벡터는 그대로 남음.
→ 법무(항목별 보유기간, crypto-shredding 인정여부) + 5개 저장소 통합 삭제 오케스트레이션 설계. (법무 2주 / 설계 1주)

**B4. PII 암호화 방식 미결 = 스키마 결정, Do 단계 이연 불가**
- 권고: pgcrypto 비권장(키 유출 위험, 인덱스 불가) → **3계층**: ①전 저장소 볼륨암호화(LUKS) ②초민감 자유텍스트(`body_text`, `transcript_*`)는 애플리케이션 레벨 필드암호화+사용자별 DEK(KEK는 온프레미스 Vault) ③`contact`는 암호문+blind index(HMAC-SHA256, 동등검색만)
- **Qdrant가 최고위험**: BGE-M3 임베딩은 embedding inversion으로 원문 복원 가능 → 벡터 자체가 PII. payload에 원문 절대 저장 금지, 네트워크 격리 필수
- MinIO 원본음성: SSE-KMS(KES+Vault) 사용자별 키
→ (1~1.5주)

**B5. 인증/인가/테넌시/감사모델 구조적 공백**
`family_members`에 `keycloak_sub` 없음(RBAC 강제 불가), Device Token 발급·회전·폐기 절차·컬럼 없음(분실·도난 단말 차단 불가), 조직/시설 엔티티 없음(B2G 시설간 열람차단 불가), 다수 엔드포인트가 소유권 검증 규칙 미명시(IDOR, OWASP A01), 접속기록(감사로그) 엔티티 없음(안전성 확보조치 기준 제8조).
→ `organizations`, `family_members.keycloak_sub`, `device_credentials`, `access_logs` 신설, 모든 엔드포인트에 인가 술어 명시 의무화. (1주)

**B6. Zero External Data Egress가 설계 내부와 이미 충돌**
`notification_settings.channel`(sms/email/push)이 곧 FCM/문자대행사/메일릴레이 경유 — 민감정보 제3자 처리위탁+국외이전(제28조의8) 소지. design-tokens.md의 Google Fonts CDN도 접속자 IP 전송. Next.js 텔레메트리, Android Crashlytics 등 잠재 누출 다수.
→ egress 3등급 분류(절대금지/허용+통제/즉시제거), 법무(위탁계약·국외이전 고지), 폰트 self-host. (정책 3일 / 법무 2주)

### Concern (병행 가능)
- 온디바이스 저장 암호화(SQLCipher+Keystore) 미명시, 원격 lock/wipe 미설계 — Phase 1 모바일 첫 스프린트에 포함
- 재활용 단말(키오스크 판정기준=EOL 단말)이 가장 민감한 데이터를 가장 취약한 OS에 저장 — 단말 수명주기 SOP, 키오스크 탈출 침투테스트 필요
- egress 강제 인프라(default-deny+allowlist 프록시) 구축 — 실데이터 업로드 전
- RBAC 실질 결함 4건: 정서정보 보호강도 역전, admin의 콘텐츠 읽기·감수 권한(최소권한 위반), 테넌시 경계 부재, 가족 전원 무조건 전체열람(노인학대 다수가 가족에 의해 발생하는 점 고려 필요)
- 업로드 경로 기본방어 — 사진 EXIF(GPS) 제거 의무화, CSP/HSTS/CSRF, 토큰 해시저장 등
- 거버넌스 산출물(DPIA·처리방침·CPO 지정·위탁계약) 부재 — B2G 제안서 제출 전
- 자살·학대 징후 인지 시 대응 프로토콜 부재(역방향 리스크) — Phase 2 착수 전 검토

### 법무 검토 요청 항목 (원문 6건)
1. 정서 점수가 제23조 민감정보에 해당하는가? 알림 없이 기록만 해도 별도동의 필요한가?
2. 성년후견 미개시 어르신에 대한 가족 대리동의가 유효한가? 본인동의 필수범위는?
3. 가족·복지사 열람은 제17조 제3자제공인가, 제26조 위탁범위 내 이용인가?
4. 정서점수 산출·통보 기능이 의료기기법 규제대상이 될 위험이 있는가?
5. 원본음성/전사/벡터/사진/백업 각각의 보유기간·파기방법은? crypto-shredding이 적법한 파기로 인정되는가?
6. FCM/SMS/이메일 알림, Google Fonts CDN이 국외이전 고지·동의 대상인가?

### 한 줄 총평
아키텍처 방향은 이 데이터 등급에 맞게 옳게 잡혔으나, 동의·보유기간·정보주체 권리·암호화·인가모델이라는 다섯 뼈대가 모두 "Do 단계 이연"으로 비어 있어 지금 코드를 시작하면 되돌릴 수 없는 스키마와 위법한 데이터가 함께 쌓임 — Blocker 6건은 대부분 문서작업(1~2주)+법무회신 대기(2~3주)이므로, **정서 파이프라인을 끈 채 온디바이스 오프라인 코어부터 병행 착수**하는 것이 현실적 해법.

---

## 4. Frontend Architect — UI/접근성 심사

### 강점
- BI 가이드 → 토큰 매핑 값 단위 100% 일치 (17개 HEX, 타입스케일 5단계)
- 화면 인벤토리가 실제로 닫혀있음 — 23개 화면ID 전부 존재, 스코프아웃(WU4)도 취소선 명시
- 화면별 요소 테이블이 이벤트 수준까지 상세, 화면 간 데이터 연계(`spec-related`)가 전 화면에 붙어 라우팅/상태 설계 바로 착수 가능

### Blocker

**FE-B1. 컬러 토큰이 WCAG AA 미통과** (고령자 제품에서 치명)
| 조합 | 실측 대비비 | 판정 |
|---|---:|---|
| ink #20242B / paper | 13.93:1 | AAA 안전 |
| ink-muted #5B6472 / paper | 5.35:1 | AA만 통과 |
| ink-faint #9096A0 / paper (CAPTION 지정색) | **2.66:1** | **실패** |
| teal #1E7A8C / paper | **4.45:1** | **실패**(0.05차) |
| teal-deep #155C6B / white | 7.57:1 | **AAA 통과 — 권장 텍스트색** |
| gold #B8935A / paper | **2.55:1** | **실패** — 텍스트·아이콘 전면 금지 |
| silver #8E97A6 / paper | **2.63:1** | **실패** |
| border #DEDACF / paper | **1.25:1** | **실패**(비텍스트 기준도 미달) — 입력필드·카드 경계 사실상 비가시 |

→ 기능색/장식색 분리 재정의(`text-primary`, `text-secondary`, `text-link=teal-deep`), gold/silver/ink-faint는 비정보 장식 전용 명시, CI에 대비비 검증 추가, BI가이드(SoR) 선갱신 후 토큰 반영. (2~3일)

**FE-B2. 디자인 토큰의 3플랫폼 배포 메커니즘 부재**
`design-tokens.md`는 마크다운 표+제안 스니펫뿐, `packages/`엔 `py-common`만 존재해 공유 UI/토큰 패키지 없음 — web/admin/mobile에 동일 HEX 3벌 수기복제 예정. spacing·radius·shadow 등 BI가이드에 실재하는 축이 design-tokens.md에서 누락.
→ `packages/design-tokens/`(tokens.json 단일 SoR) 신설, Style Dictionary로 CSS/TS/Kotlin 3산출물 빌드, 누락 축(spacing/radius/elevation/breakpoints/motion) 추가. (3일)

**FE-B3. Next.js App Router가 인식 불가 경로에 위치**
structure.md/CONVENTIONS.md가 `apps/web/src/presentation/app/`에 App Router를 두는데, Next.js는 `app/` 또는 `src/app/`만 인식 — **동작하지 않는 구조**. Clean Architecture 4계층을 App Router(서버컴포넌트가 데이터접근 직접 수행) 위에 얹는 것도 모델과 충돌.
→ `apps/web/src/{app,components,features,services,lib/api,types}` 구조로 확정, 계층규율은 폴더가 아닌 ESLint `import/no-restricted-paths`로 강제. OpenAPI→`openapi-typescript` codegen을 CI 고정, TS 수기사본(4번째 스키마 복제) 제거. (1일 + codegen 1일)

**FE-B4. 접근성 기준 수치 0건**
CONVENTIONS.md·design-tokens.md 전문에 최소폰트하한·터치타깃·포커스링·대비등급 기술 0건. CAPTION 12.5px는 고령자 본문 권장 18px의 70%. 키오스크 특유 리스크: Device Owner Mode가 TalkBack 등 시스템 접근성 설정 접근을 차단하면 그 자체가 접근성 침해. Compose 시스템폰트 200% 스케일 미검증.
→ "접근성 최소기준" 표(하단) 채택 → design-tokens.md §4 신설, Device Owner 화이트리스트에 TalkBack/글꼴크기/확대 허용 여부 보안팀과 합의. (1일 + Compose 스파이크 1일)

### 접근성 최소 기준 제안 (WCAG 2.2 AA 필수, 텍스트만 AAA 7:1 목표)
| # | 항목 | 기준값 |
|---|---|---|
| 1 | 본문 최소크기 | 모바일 20sp / 웹(user) 20px / 웹(family·admin) 16px |
| 2 | 최소 폰트 하한 | 14px/14sp 미만 금지 (CAPTION 12.5px 폐기) |
| 3 | 터치 타깃 | 모바일 ≥56×56dp / 웹 ≥48×48px |
| 5 | 텍스트 대비 | 본문 ≥7:1 목표, 절대하한 4.5:1 |
| 6 | 비텍스트 대비 | 아이콘·경계 ≥3:1 |
| 8 | 시스템 폰트 스케일 | 200%까지 레이아웃 무손실 |
| 12 | 키오스크 접근성 예외 | Device Owner 화이트리스트에 TalkBack·글꼴크기·확대 허용 |

### Concern (병행 가능)
- apps/web 이중청중 문제 — 당사자 웹은 WU2(자서전뷰어) 단독으로 축소 권고, WU1/WU3/WU5는 M1 마일스톤 제외
- 오프라인 UI 상태 설계 부재 — 동기화 상태 5단계 확장(정상/대기/진행중/실패/오래됨) + 절대일수 문구
- Compose 메모리 예산·상태관리 미정 — UI+이미지캐시 ≤150MB 등 예산 배정, 저사양 실기기 확보해 베이스라인 측정
- 빈상태·로딩·에러·폼유효성 스펙 0건 — `docs/02-design/ui-states.md` 컴포넌트 유형별 상태매트릭스로 보완
- admin/web 공유 컴포넌트 계획 없음 — `packages/ui/` 프리미티브 추가

### 한 줄 총평
화면 인벤토리·요소 스펙은 착수 가능한 수준이지만, 브랜드 팔레트가 본문·캡션·경계선 전 계층에서 WCAG AA를 통과하지 못하고, 토큰 배포 메커니즘이 없으며, App Router가 인식 못하는 경로에 배치돼 있어 — 착수 전 5영업일을 들여 Blocker 4건을 정리하지 않으면 고령자 접근성이라는 제품의 존재이유를 코드 레벨에서 되돌릴 수 없게 됨.

---

## 5. Product Manager — 스코프·일정 준비도 심사

### 강점
- 기술 의사결정 밀도가 이례적으로 높음 — decisions.md 23건 중 17건 확정
- 상류 산출물이 코드 직전까지 완비 — schema v1.1, CONVENTIONS, design-tokens, design §2.4~2.10까지, design-validator 1회 검증으로 문서간 모순 23건 이미 제거
- 아키텍처 리스크가 정직하게 문서화 — plan §5 위험표, design §2.0 옵션비교로 "왜 하이브리드인가"를 방어 가능

### Blocker

**B1. Phase 1 예산·인력 미승인** — A100 GPU 조달 리드타임(통상 8~16주)이 승인일에 종속, 오늘 승인해도 실장비 검증은 3~6개월 뒤
→ 경영진에 Phase 1 한정 최소 예산 승인만 요청(Phase 2~3 보류 유지): 인력 고정(모바일2/백엔드2/웹1/PM·QA1, 12주), GPU 발주 승인, 파일럿 운영비. (필요시점 2026-09-12)

**B2. 온디바이스 SLM 모델 미선정** — Session 4(모바일 오프라인 코어) 전체가 미선정 모델 위에 세워짐
→ 후보 3종 고정 후 2주 스파이크(경계기기 3종에서 TTFT·tok/s·RAM peak·한국어 회고대화 50턴 품질 측정). **예산 승인 없이도 착수 가능** — 킥오프 당일 시작 권고. (스파이크 09-08 착수, 확정 09-19)

**B3. Phase 1 경계가 어느 문서에도 없음** — plan §2.1 In Scope 8개가 3개 Phase 전체를 뭉뚱그림, §11.2만 Phase 구분하나 이건 Design 문서
→ Phase 1/2/3 스코프 재정리표(하단)를 킥오프 당일 승인 후 plan §2.1 대체 게재. (즉시)

> 참고: B3은 킥오프에서 즉시 해소 가능, B2는 예산 없이 착수 가능. **실질적으로 킥오프를 멈추는 것은 B1 하나뿐.**

### 미결 의사결정 착수영향 판정표
| # | 항목 | Phase 1 착수 차단? | 근거 |
|---|---|---|---|
| #14/#2 | 예산·인력 | **착수 차단** | 인력배분 불가 + GPU 리드타임. Phase 1 한정 승인으로 해제 가능 |
| (신규) | SLM 모델 선정 | **부분 차단** | Session 3(서버)는 무관, Session 4(모바일)만 차단 |
| #12 | 정서모니터링 법적기준 | **미차단** (PM 판단) | Phase 2(구현순서6) 사안. 단, Security는 이견 — 본 문서 서두 참조 |
| #23/#18 | 결제 PG사 | 미차단(단, 숨은결정 1건) | "Phase 1 파일럿 전액무료" 결정이 어느 문서에도 없음 — 즉시 명문화 필요 |
| #9 | 최근5일 캐시 | 미차단 | 설정값으로 외부화하면 코드변경 없이 조정 가능 |
| #13 | 외부TTS | 미차단 | Phase 3 유예 확정, Phase 1과 무관 |
| #5 미세조정 | 설치모드 임계값 | 미차단 | 수치 이미 확정, 실기기 벤치마크만 잔여 |

### Phase 1/2/3 스코프 재정리 제안 (plan §2.1 대체)
| 영역 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| 온디바이스 대화 | 작가 모드만 | 말벗돌봄 추가 | 비서 모드 추가 |
| 서버 엔진 | author-engine, sync-gateway, rag-core, gateway | care-engine | schedule-engine, 출판엔진 |
| 정서 모니터링 | ❌ (스키마만 생성) | emotion_scores 기록, 알림은 #12 완료 시만 | 에스컬레이션 고도화 |
| 출판 | ❌ | ❌ | PDF/ePub 조판 |
| 결제 | ❌ (파일럿 전액무료) | ❌ | PG 연동(#23 결정 후) |

### Concern (병행 가능)
- NFR에 숫자 없음 — "오프라인 100% 가능"은 테스트 불가, Do 착수 첫주 QA리드가 수치화
- FR 8개 전부 인수기준·유저스토리 없음, FR-01은 3모드를 한줄로 묶어 Phase분할 불가 → FR-01a/b/c 분리 권고
- 파일럿 대상자 확보 경로 없음 — 복지관 MOU·동의절차 통상 4~8주, 코드보다 리드타임 길어 즉시 착수 필요
- plan §9 Next Steps 6·7·8번 담당자·기한 공백
- 에이전트 표시명 미정(AuthorAgent/ScheduleAgent)

### 측정 가능한 Phase 1 완료기준 제안 (발췌)
- EC-1 오프라인 시나리오 30/30 통과, TTS 첫음성 p95≤3.0초
- EC-6 (핵심) 생성 챕터 사실오류 ≤5%, 환각 0건
- PC-2 (생사지표) 4주 지속률 ≥60%(6/10명)

### 검증되지 않은 최대 제품 가정
- 가정A: "어르신이 몇 달간 스스로 반복해서 말한다" → Wizard-of-Oz 실험(코드 0줄, 2주) 제안
- 가정B: "1~3B 4bit SLM이 한국어 회고를 지탱할 만큼 좋다" → SLM 스파이크와 통합 검증, 미달 시 폴백설계(FR-01 재정의) 필요

### 한 줄 총평
Scope·Requirements는 경계선이 없는 것이 문제 — 킥오프 당일 Phase 표만 승인하면 해결. 미결 7건 중 Phase 1을 실제로 막는 것은 예산 1건(부분적으로 SLM 1건)뿐이며, 법무검토(#12)는 착수를 막지 않음(단, Security 관점 이견 있음). **진짜 위험은 기술이 아니라 "어르신이 계속 말할 것인가"를 검증하지 않은 채 12주를 태우는 것.**

---

## 6. Backend/API (bkend-expert) — 백엔드·API 설계 심사

### ① 자체호스팅 FastAPI 선택의 타당성 — 검증 결과: 타당함
- Zero External Data Egress 원칙상 멀티테넌트 BaaS는 구조적으로 PII가 제3자 인프라에 상주 → 원칙과 충돌
- GPU 상주 추론(vLLM/Whisper/BGE-M3)은 범용 BaaS의 서버리스 모델로 수용 불가
- Keycloak SSO + 온디바이스-서버 하이브리드 동기화는 BaaS 내장 Auth와 무관한 자체 인가체계 필요
- **결론**: bkend.ai 같은 BaaS 적용 대상이 아니며, 자체호스팅 FastAPI는 데이터주권 요구상 유일하게 타당한 선택

### 강점
- 서버 내부 무변환 파이프라인 — wire format을 DB와 동일 snake_case로 통일(#20)해 SQLAlchemy→Pydantic→JSON 변환계층 불필요, 캐이싱 버그 원천 차단
- 표준 응답 포맷·에러코드 선확정(design §4.1) — FastAPI 공통 exception_handler 하나로 즉시 통일 구현 가능
- Clean Architecture 의존 규칙이 이론이 아니라 import-linter/CI 룰로 바로 전환 가능한 수준까지 구체화

### Blocker

**BE-B1. 장시간 작업(STT 재전사·LLM 챕터생성)의 비동기 계약 완전 부재**
`POST /sync/upload` 응답 형태 미정, 실제 처리는 수십초~수분 소요가 자명한데 job 상태 조회 API가 없음. `sync_sessions` 테이블은 있으나 이를 조회하는 GET 엔드포인트가 목록에 없어 모바일이 동기화 진행상황을 확인할 방법이 없음.
→ `202 Accepted + job_id` 패턴 도입, `GET /sync/sessions/{id}` 상태조회 API 추가. (2~3일)

**BE-B2. 파일 업로드 전송 계약 미정**
음성·사진이 JSON envelope 안에서 어떻게 전달되는지 불명 — multipart 프록시 업로드 vs MinIO Presigned URL 직결 여부 없음. 5일치 배치 음성(수백MB 추정)을 FastAPI 프록시로 받으면 타임아웃·메모리 부하 위험.
→ Presigned URL 직결 방식 채택 권고: `POST /files/presigned-url → PUT MinIO → POST /sync/upload {refs}` 3단계. (1~2일)

**BE-B3. 17개 엔티티 ↔ 6개 서비스 도메인 모델 소유권 매핑 표 부재**
`users`/`family_members`/`devices`처럼 여러 서비스가 참조하는 공유 엔티티를 `py-common`에 둘지 서비스별 중복 정의할지 규칙 없음 — 첫 SQLAlchemy 모델을 쓰는 순간 개발자마다 다르게 결정해 스키마 드리프트 확실.
→ 공유 엔티티 vs 서비스 전용 엔티티 목록을 표로 확정. (반나절)

**BE-B4. `GET /sync/download`의 증분 계약 없음**
매번 전량 다운로드인지 `last_sync_at`/cursor 기반 증분인지 미정 — 저사양 단말·제한대역폭에서 전량 다운로드는 오프라인 우선 원칙과 충돌.
→ `since` 파라미터 + 서버측 변경분 추적 전략 명시. (BE-B1과 함께 1~2일)

### Concern (병행 가능)
- OpenAPI 미작성 — 요청/응답 바디·페이지네이션·정렬필터 스펙 0건, 2주차까지 확정 필요
- 엔드포인트 완전성 부족 — `consent_logs`/`questions`/`schedule_items`/`devices` POST 등이 §4.2 목록에 없음
- 웹 콘솔 POST 계열(사진업로드·초대) Idempotency 키 부재 — 재시도 시 중복생성 위험
- 표준 에러코드에 429(Rate Limit)·413(Payload Too Large) 없음
- Alembic 단일체인+6서비스 배포 룰 — Enterprise B3(모듈러 모놀리스화)와 연동해 정리

### 한 줄 총평
Go with conditions — 데이터모델·컨벤션은 완성도 높아 골격은 오늘 만들 수 있으나, API Specification이 "엔드포인트 이름 목록"에 머물러 이 프로젝트 핵심 난이도(비동기 처리, 파일업로드)의 계약이 없음. BE-B1·B2·B4를 1주 내 확정 후 라우터 착수 권고 — Enterprise B3·B1과 사실상 동일 타임라인이라 별도 지연 요인 아님.

---

## 7. QA Strategist — 테스트 전략 준비도 심사

### 강점
- Test Scope 표(§8.1)가 6개 시나리오축(오프라인/동기화/사진회고/설치모드/정서/출판)을 선제 식별
- 동기화 실패·충돌 처리(§6.1)·Diff 멱등성(§2.8) 문서화로 최소 검증 기준선 존재
- 설치모드 경계기기 5개 모델이 부록A에 실명·RAM·OS버전까지 구체 명시 — 실기기 랩 조달 리스트 즉시 추출 가능

### Blocker

**QA-B1. 테스트 정량 기준(Pass/Fail 임계값) 전무**
§8.1은 "무엇을 테스트할지"만 있고 "얼마나 되면 통과인지"가 없음. §6.1 재시도 최대 N회조차 N 미정. PM의 EC-1~9(제품 완료기준)와는 레이어가 다른, 개별 테스트케이스 단위 수치가 없음.
→ QA리드가 시나리오별 정량기준표 작성 (1주, 코드와 무관하게 즉시 가능)

**QA-B2. 고령 화자 음성인식 정확도가 Test Scope에서 통째로 누락**
Enterprise B2의 SLM 벤치마크는 성능(TTFT/메모리)만 보는 것이고, "어르신 발화(방언·틀니 발음·저속발화·배경소음)를 얼마나 정확히 알아듣는가"는 별개 축인데 데이터셋도 계획도 없음.
→ 고령 화자 음성 코퍼스 확보를 SLM 스파이크와 동시 착수

**QA-B3. 네트워크 장애주입·실기기 랩의 조달 주체·일정 부재**
"실기기/에뮬레이터 수동 QA", "네트워크 장애 주입"이 도구명 없는 명사로만 존재 — Infra의 docker-compose(서버 로컬환경)와는 다른 레이어인 QA 전용 인프라(Toxiproxy/tc netem 등 + 저사양 실기기 3~5대)가 미배정.
→ 인프라 트랙(1.5주)에 QA 요구사항으로 포함

### Concern (병행 가능)
- 다중세션 E2E 상태영속성(사진회고가 며칠에 걸침) 세부설계 필요
- Diff 멱등성 fuzz/property 테스트 계획 없음
- CI 자동화(API/UI액션) vs 수동 QA(실기기 배터리·메모리·오프라인) 경계 불명확
- 정서 모니터링 알림 정확도 검증용 골든데이터셋 없음(법무 승인과 별개 이슈)
- 저장공간 압박 시 열화(5일 캐시 풀 상태) 테스트 케이스 없음
- 테스트용 PII 데이터 거버넌스(실데이터 vs 합성데이터) 미정

### 한 줄 총평
Go with conditions — Test Scope와 실기기 매트릭스라는 뼈대는 있어 QA 계획 수립은 지금 시작 가능하나, 정량기준·음성데이터셋·장애주입랩 3건이 없으면 Check 단계에서 "얼마나 되어야 통과인가"를 판단할 근거가 없음. 모두 코드 착수를 막을 필요 없는 1~2주 문서/조달 작업.

---

## 8. 종합 (7개 관점 교차 정리)

관점별 세부는 위 1~7절 참조. PPT 발표자료(`은빛실타래_개발착수회의_kickoff.pptx`) 8부에 요약 반영됨.

### 종합 Blocker 우선순위
1. **Phase 1 예산·인력 승인** (경영진) — 유일한 진짜 착수 차단 요소
2. **보안/법적 5대 공백** (동의·보유기간·인가모델·암호화·Zero Egress 내부충돌) — 법무 회신 2~3주 걸리므로 즉시 착수 필요
3. **온디바이스 SLM 모델 미선정** — 예산 무관하게 즉시 착수 가능한 2주 스파이크 (QA-B2 음성데이터셋과 동시 진행)
4. **동기화 계약 부재** — 데이터 영구소실 경로, sync-gateway 착수 전 필수 (BE-B1/B2/B4와 함께 설계)
5. **6개 마이크로서비스 근거 부재** — 모듈러 모놀리스로 재정의 권고 (BE-B3 엔티티 소유권 매핑과 연동)
6. **컬러 토큰 WCAG 미달 + Next.js 폴더구조 오류** — 프론트엔드 착수 전 2~3일
7. **로컬 개발환경(docker-compose) 부재** — 1~1.5주 (QA-B3 장애주입 인프라 포함해 확장)
8. **API 비동기/파일업로드/증분동기화 계약 부재** (BE-B1,B2,B4) — 라우터 착수 전 1주
9. **테스트 정량기준·고령화자 음성데이터셋 부재** (QA-B1,B2) — 1~2주, 병행 가능

### 권고
경영진의 Phase 1 한정 예산 승인과 병행하여, **정서 모니터링 파이프라인을 피처플래그로 OFF한 상태로** 온디바이스 오프라인 코어·웹 콘솔 스캐폴딩·SLM 벤치마크(+고령화자 음성데이터셋 확보)·동기화 계약 설계(+비동기 API 계약)를 즉시 병행 착수하는 것을 권고함. 7개 관점 전원이 "Go with Conditions"로 수렴했고, No-go를 시사한 관점은 없음.

---

## Related Documents
- Plan: [silveryarn-platform.plan.md](../01-plan/features/silveryarn-platform.plan.md)
- Design: [silveryarn-platform.design.md](./features/silveryarn-platform.design.md)
- Decisions: [silveryarn-platform.decisions.md](../01-plan/decisions/silveryarn-platform.decisions.md)
- 발표자료: [presentations/은빛실타래_개발착수회의_kickoff.pptx](../presentations/은빛실타래_개발착수회의_kickoff.pptx)

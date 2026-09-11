# silveryarn-platform 의사결정 로그

> **Summary**: 기획서(`Plan/어르신_자서전_말벗돌봄_기획서.md`) 9장 "다음 논의가 필요한 사항"에 대한 확정/보류 기록
>
> **Project**: 은빛실타래 (SilverYarn)
> **Date**: 2026-09-05
> **Status**: 일부 확정 / 일부 보류(경영진·법무 승인 대기)

---

## 범례

| 상태 | 의미 |
|---|---|
| ✅ 확정 | 이번 세션에서 결정, Plan/Design 문서에 반영 완료 |
| 🕒 보류 | 사용자 확인 결과 의도적으로 보류 (사유 명시) |
| ⚖️ 별도 검토 필요 | AI가 임의로 결정할 사안이 아니며, 법무/윤리/경영 검토가 필요 |

---

## 1. 비즈니스/전략 결정 (사용자 확인 완료)

| # | 항목 | 결정 | 근거/비고 | 상태 |
|---|------|------|-----------|:---:|
| 1 | 타겟 채널 우선순위 (B2C vs B2G) | **병행 추진** — Phase 1부터 B2C(가족 결제)와 B2G(지자체·복지관 파일럿)를 동시에 검토 | 리소스 분산 리스크가 있으므로 Phase 1 기능 범위(§2.1 In Scope)는 채널 구분 없이 공통 핵심 기능에 집중하고, 채널별 온보딩/과금 방식만 후속 분리 설계 | ✅ 확정 |
| 2 | Phase 1~3 착수 일정·예산·투입 인력 | **아직 미확정 — 보류** | 경영진 승인 대기. Plan 문서 §4(Success Criteria)·§9(Next Steps)는 "일정/예산 미정" 전제로 작성됨. 실제 착수 전 별도 컨펌 필요 | 🕒 보류 |
| 3 | 외부 고품질 TTS 연계(기획서 3.4절) | **지금은 보류 — 온프레미스 자체 파인튜닝 TTS만 사용** | Phase 1~2는 온프레미스 TTS로 진행하고, 외부 연계는 원안대로 Phase 3 파일럿 검토 대상으로만 유지. 법무·보안팀 DPA 검토는 Phase 3 착수 시점에 개시 | ✅ 확정 (원안 유지) |
| 4 | '기억의 서재' 프로젝트와의 관계 | **완전히 별개 프로젝트로 확정** (기획서 명시 내용 재확인) | 온디바이스 SLM 모델 선정·브랜드 포지셔닝의 중복 여부 재점검은 더 이상 본 프로젝트의 선결 조건이 아님 — 향후 필요 시 별도 트랙에서 논의 | ✅ 확정 |

---

## 2. 기술 결정 (기존 문서 근거 기반으로 확정 — 이번 세션에서 결정)

| # | 항목 | 결정 | 근거 | 상태 |
|---|------|------|------|:---:|
| 5 | 설치모드(키오스크/일반) 판별 임계값 | **기획서 부록A 검토안을 정식 채택**: RAM 6GB 미만 **또는** Android 11(API 30) 이하 → 키오스크 모드. 둘 중 하나라도 미달 시 보수적으로 키오스크 판정 | 부록A에서 RAM 단일 기준의 한계(S10/노트10 사례)를 이미 실증적으로 검토했고, 극민감 개인정보를 다루는 서비스 특성상 보수적 판정이 타당함. 실기기 벤치마크(9장 잔여 항목)는 이 임계값의 미세조정용으로 후속 진행 | ✅ 확정 |
| 6 | 키오스크 모드 구현 방식 | **Android Device Owner Mode(COSU) 채택** — Screen Pinning 미채택 | Screen Pinning은 사용자가 뒤로가기+최근앱 길게 누르기로 스스로 해제 가능해 "다른 앱 접근 차단"이라는 요구(기획서 3.7절)를 완전히 만족하지 못함. Device Owner Mode는 OS 레벨에서 잠금을 강제하고 재활용 단말의 공장초기화 후 최초 계정 설정 시점에 자동 프로비저닝(zero-touch/QR)이 가능해 재활용 단말 배포 워크플로우에 적합 | ✅ 확정 |
| 7 | 모바일 플랫폼 | **Android 전용(1차), 네이티브(Kotlin)** | Device Owner API는 Android 전용 개념이며, 부록A의 실제 매핑 기기(갤럭시 S9~S25 시리즈)가 전부 Android. 온디바이스 SLM·STT·TTS 동시 구동 성능도 네이티브 접근이 유리 | ✅ 확정 |
| 8 | Wi-Fi 동기화 트리거 정책 | 등록된 Wi-Fi(자택 등)에 한정, **접속 감지 즉시 백그라운드 자동 트리거**(특정 시간대 예약 방식 미채택). 데이터 사용량 제한은 두지 않음(Wi-Fi 전용이라 셀룰러 과금 이슈 없음) | 기획서 3.5절 "동기화 트리거: 등록된 Wi-Fi 접속이 감지되면 사용자 조작 없이 백그라운드에서 자동 수행" 원칙을 그대로 구체화 | ✅ 확정 |
| 9 | 로컬 보관 "최근 5일" 기준 | **1차 기본값으로 유지**, 최종 확정 아님 — Phase 1 실기기(특히 저사양 키오스크 단말) 저장용량 벤치마크 후 조정 여지를 열어둠 | 기획서 원안의 잠정 수치이며, 부록A 대상 저사양 기기(2~4GB RAM급)의 실제 가용 저장공간 실측 전까지는 확정하지 않는 것이 안전 | 🕒 보류 (기본값 유지, 벤치마크 후 재확정) |
| 10 | 당사자 모바일 사진 업로드 UX | **카메라 즉시촬영 + 기존 갤러리 선택 모두 지원**(택일 아님). 업로드 전 클라이언트 측 리사이즈(장변 최대 1600px)·JPEG 80% 압축 적용 | 저사양 단말의 저장용량·전송량 제약(기획서 9장 문제의식)을 동시에 만족시키는 가장 단순한 절충안 | ✅ 확정 |
| 11 | 사진 인라인 편입 정책 | AI가 삽입한 위치는 항상 **"제안(초안)" 상태**이며 가족이 웹 콘솔(§2.4)에서 최종 확정 전까지 자유롭게 위치·설명을 재조정 가능. 부적절·흐릿한 사진은 서버 측 1차 자동 품질 체크(블러 감지 등)로 걸러 가족 확인 대기열에 별도 표시 | 기획서 4.4절 "가족이 위치·설명을 조정할 수 있다"는 원칙을 구체적 워크플로우로 확정 | ✅ 확정 |

---

## 2.1 추가 기술 결정 (design-validator 검증 반영, 2026-09-05)

> `design-validator` 에이전트 검증에서 발견된 문서 간 불일치(A-1, A-4)와 스코프 공백(B-4)을 해소하기 위해 추가로 확정한 항목.

| # | 항목 | 결정 | 근거 | 상태 |
|---|------|------|------|:---:|
| 15 | 서버 백엔드 프레임워크 | **Python 3.11+ / FastAPI 확정** | CONVENTIONS.md가 이미 FastAPI 전제로 작성돼 있었으나 CLAUDE.md·design.md에는 "미정"으로 남아있던 불일치(design-validator A-1)를 해소. 온프레미스 배포 용이성, 비동기 I/O, 팀 컨벤션과의 정합성 | ✅ 확정 |
| 16 | 웹 콘솔 프레임워크 | **Next.js(App Router)+TypeScript+Tailwind 확정** (재등재) | Phase 2에서 CONVENTIONS.md §0.1로 이미 결정했으나 본 로그에 누락돼 있던 것(design-validator C-2)을 정식 등재 | ✅ 확정 |
| 17 | 인증(SSO) | **Keycloak SSO 확정** | 원본 `Plan/자서전_말벗돌봄_프로세스_흐름도.md` §4.1이 이미 Keycloak을 전제로 게이트웨이 인증을 설계해뒀음(design-validator A-4) — 신규 문서를 원본과 일치시킴 | ✅ 확정 |
| 18 | 구독·결제 도메인 | **Phase 1 스코프에서 제외** — 엔티티·API·화면 설계 모두 보류 | PG사·요금제는 경영/법무 결정 사항이며 AI가 임의로 설계하면 실제와 어긋날 위험이 큼(design-validator B-4). 화면설계서의 "구독·결제 관리" 화면은 Phase 2 이후 별도 스코프로 명시 분리 | ✅ 확정(스코프 아웃) — 실제 결제 설계는 ⚖️ 별도 검토 |
| 19 | 정서 알림 수신 설정 범위 | 가족의 **알림 수신 채널·항목 선택**(notification_settings)은 지금 구현하되, **알림 발송 임계치 로직 자체**는 #12(법무·윤리 검토)가 끝날 때까지 보류 | design-validator B-10이 지적한 "WF5 화면이 미확정 정책(임계치)을 선행 요구"하는 충돌을 "누가·어디로 받을지"와 "언제 보낼지"로 범위를 분리해 해소 | ✅ 확정 |
| 20 | API 응답 필드 케이싱 | 서버 wire format은 **snake_case로 통일**, 클라이언트(TS/Kotlin)에서 각자 컨벤션으로 변환 | glossary.md 규칙과 CONVENTIONS.md 서버 규칙(snake_case)을 API 경계에서도 일관 적용(design-validator D-3) | ✅ 확정 |
| 21 | DB enum 값 표기 | **영문으로 통일**(예: `childhood`), 한글은 표시명 매핑([schema.md §7](../schema.md#7-enum-표시명-매핑-한글-ui--영문-db-값))으로만 노출 | `chapter_period`에 한글 리터럴을 직접 쓰면 glossary "코드는 영문" 원칙과 상충(design-validator D-2) | ✅ 확정 |
| 22 | Wi-Fi 등록 정보 저장 위치 | 등록 Wi-Fi(SSID 등)는 **온디바이스 로컬 전용**, 서버 미전송·미저장 | 어느 문서에도 저장 위치가 명시돼 있지 않아 구현 시 임의 판단 위험이 있었음(design-validator B-7). 서버가 자택 네트워크 식별정보를 보관할 이유가 없어 로컬 전용으로 확정 | ✅ 확정 |

---

## 2.2 추가 기술 결정 (CTO팀 검토 반영, 2026-09-05)

> *(v0.7 정정: 아래 표는 "결정" 칸에 근거가 함께 기술돼 있어 §1과 같은 5열(#|항목|결정|근거|상태) 헤더로는 셀 개수가 맞지 않던 것을 4열로 정정 — 내용 변경 없음, 3차 검증 M-1)*

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 24 | Phase 1 파일럿 과금 여부 | **전액 무료로 확정** — 결제 도메인이 스코프 아웃(#18)된 상태에서 유료 전제 온보딩은 성립하지 않음 (CTO팀 PM 리뷰 지적사항 반영) | ✅ 확정 |
| 25 | 정서 모니터링 파이프라인 Phase 1 활성화 여부 | **비활성화(피처플래그 OFF)로 확정** — `emotion_scores` 기록 자체가 민감정보 소지 가능성이 있어(CTO팀 보안 리뷰 B1), 법무 검토(#12) 완료 전까지 코드 경로를 꺼둔다. 스키마(DDL)는 만들되 write 경로는 Phase 2 법무 승인 후 활성화 | ✅ 확정 (보수적 기본값) |

---

## 2.3 추가 기술 결정 (Closed-Loop/실시간파이프라인 반영, 2026-09-06)

> *(v0.7 정정: §2.2와 동일 사유로 4열 헤더로 정정 — 3차 검증 M-1)*

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 26 | 챕터 윤문·Gap분석용 LLM (사용자 제안 "Closed-Loop Architecture" 보고서 검토) | **외부 GPT-4o/Claude 미채택, 온프레미스 vLLM(자체 호스팅)으로 확정** — 원안은 서버측 고급 생성 단계에 외부 LLM API를 제안했으나, 어르신 구술 원문(가족사·건강 등 극민감 정보)이 외부로 전송되는 것은 원칙2(전면 온프레미스, 기획서 3.1) 및 #15(FastAPI/vLLM 확정)와 정면 충돌 — 파이프라인 구조(전사→지식추출→윤문→Gap분석)는 그대로 채택하되 모델만 자체 호스팅으로 대체 | ✅ 확정 (원칙 재확인) |
| 27 | 온디바이스 SLM 벤치마크 후보 추가 | Qwen2.5-0.5B를 Kanana-2 등과 함께 **벤치마크 후보군에 추가**. 최종 선정은 여전히 보류 — 실기기 벤치마크(9장, CTO팀 Enterprise B2/PM B2) 결과로 확정 | 🕒 후보 추가, 최종선정 보류 유지 |
| 28 | Vector DB 재확인 | 제안된 Milvus는 미채택, **Qdrant self-hosted 확정 유지**(기획서 3.3, 5.2, decisions 없음—원안 그대로) | ✅ 확정 유지 (변경 없음) |
| 29 | 지식 그래프(Knowledge Graph) 도입 | **Neo4j 채택 확정** — 구술에서 추출한 인물(Person)·연도(Time)·사건(Event)·감정(Emotion) 엔티티 간 인과관계·타임라인을 그래프로 저장. Qdrant(벡터 유사도 검색)와 상호보완 — Qdrant는 "의미가 비슷한 청크 찾기", Neo4j는 "이 사람과 이 사건이 어떻게 연결되는지 추적하기"에 사용. 온프레미스 자체 호스팅(Zero External Data Egress 원칙 적용 동일) | ✅ 확정 (신규 인프라 컴포넌트) |
| 30 | 온디바이스 원본 음성 파일 삭제 시점 | **서버 업로드 성공 응답(200 OK) 수신 즉시 로컬 원본 오디오 삭제**로 확정 — 기존 "최근 5일 캐시" 원칙(#9, 잠정)과 상충하지 않음: 5일 캐시는 "미동기화 상태에서 얼마나 버틸지"를 다루고, 본 결정은 "동기화 성공 후 즉시 공간 회수"를 다룸. 전사 텍스트·메타데이터는 기존 5일 원칙 유지 | ✅ 확정 (저장공간 최적화, #9와 별개 축) |
| 31 | 말벗돌봄 실시간 대화 파이프라인 최적화 기법 (사용자 제안 "저사양 실시간 대화 프로세스" 보고서 검토) | **구조적 기법 채택 확정**: ① VAD 묵음판정 800ms 윈도우 ② 문장 단위 SLM 스트리밍→TTS 파이프라이닝(전체 응답 완성 대기 없이 첫 문장 즉시 합성) ③ 로컬 대화 로그에 참조 챕터ID·응답소요시간 기록(§2.12). 단, **구체 라이브러리(Sherpa-ONNX 등)와 정확한 지연시간·메모리 수치(RAM ~850MB, 첫음성 0.8~1.2초 등)는 제안자의 목표 추정치이며 실기기 벤치마크(#27) 전까지 미검증 상태**로 표기 | ✅ 기법 확정 / 🕒 수치는 벤치마크 검증 대기 |
| 32 | 온디바이스 로컬 RAG 방식 (Phase 1 기본값) | **SQLite FTS5(BM25 키워드 검색) 단독을 Phase 1 기본값으로 확정** — 임베딩 모델 상주 시 RAM 100~200MB 추가 소요되어 저사양(RAM 4GB급) 단말에서 부담. 경량 Vector Store(임베딩 기반 의미검색)는 **고사양(일반 모드) 단말 한정 Phase 2+ 검토 대상으로 격하** — design §2.1/CONVENTIONS §2.2.1의 "경량 VectorDB" 언급은 이 결정으로 대체됨 | ✅ 확정 (Phase 1 범위) |
| 33 | 온디바이스 로컬 스키마 문서화 | `autobiography_fts` 등 온디바이스 SQLite 스키마 초안을 [`mobile-schema.md`](../mobile-schema.md)로 신규 문서화 — schema.md §6 체크리스트의 "온디바이스 SQLite 스키마 매핑" 항목 완료 | ✅ 확정 (문서화 완료) |

---

## 2.4 추가 기술 결정 (2차 design-validator 검증 반영, 2026-09-07)

| # | 항목 | 결정 | 근거 | 상태 |
|---|------|------|------|:---:|
| 34 | 온디바이스 AI 응답 텍스트의 서버 영구보존 여부 | **보존함으로 확정** — `conversation_chunks`에 `session_id`·`turn_id`·`mode`·`assistant_response` 4컬럼 신설(schema.md v1.3), 온디바이스 `conversations` 테이블과 완전 매핑 | 2차 검증 H-2 — 서버 저장처가 없으면 Critic Agent(§2.11)의 대화품질 회고분석·대화 복원이 근본적으로 불가능. PII 암호화 대상 목록에 `assistant_response` 포함 | ✅ 확정 |
| 35 | 기기별 SLM/프롬프트팩 버전 서버 추적 | **`devices`에 `slm_model_version`·`prompt_pack_version` 컬럼 추가 확정**(schema.md v1.3) | 2차 검증 M-3(CTO Enterprise B4) — Device Owner Mode로 잠긴 키오스크 단말은 앱 재배포가 사실상 불가능해, 어느 단말이 구버전 프롬프트팩을 쓰고 있는지 서버가 추적하지 못하면 원격 갱신 여부를 판단할 수 없음 | ✅ 확정 |

---

## 2.5 추가 기술 결정 (3차 design-validator 검증 반영, 2026-09-07)

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 43 | 모바일·웹(사용자) 본문 텍스트 크기 | **BODY 16px → 20px 상향 확정** — CTO FE-B4 권고("고령자 가독성 최우선, 20sp 이상")를 사용자가 채택. `apps/admin`(관리자 콘솔)은 대상 사용자가 다르므로 기존 16px 유지. design-tokens.md §2·§4에 반영 | ✅ 확정 |

---

## 2.6 추가 기술 결정 (Do 단계 착수 — 모듈러 모놀리스 스캐폴딩, 2026-09-07)

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 44 | 서버 첫 커밋 배포 단위 | **`services/backend/`(Python 패키지명 `core_service`) 단일 배포 단위로 확정** — structure.md가 이미 명시한 "Design §11.1 기준, 아직 스캐폴딩 전" 제안(services/author-engine, care-engine, schedule-engine, sync-gateway, rag-core 개별 마이크로서비스)은 **논리적 모듈 경계**로만 유지하고, 물리적 배포는 CTO Enterprise B3 권고에 따라 `api`(FastAPI) + `worker`(비동기 잡 처리, sync-contract.md §2) 2프로세스 모듈러 모놀리스로 시작한다. 각 도메인 모듈(`modules/{users,devices,author,care,schedule,sync}/`)은 내부적으로 api/application/domain/infrastructure 4계층을 유지해 향후 특정 모듈만 별도 서비스로 분리(예: GPU 부하가 큰 rag-core)할 때 리팩터링 비용을 최소화한다 | ✅ 확정 |

---

## 2.7 추가 기술 결정 (Do 단계 — PII 필드 암호화 1차, 2026-09-09)

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 45 | PII 자유텍스트 컬럼 암호화 방식 | **애플리케이션 레벨 필드 암호화 + 사용자별 DEK로 확정** (CTO 검토 [B4](../../02-design/cto-review-2026-09-05.md) 권고 ②·③ 채택, schema.md §5가 "Do 단계 최종 결정"으로 남겨둔 항목). `pgcrypto`는 **미채택**(키 유출 위험·인덱스 불가, B4 명시). **1차 대상(코드 반영 완료)**: `chapters.body_text`, `chapter_revisions.body_text_snapshot`, `conversation_chunks.transcript_on_device`/`transcript_server`/`assistant_response` 5개 컬럼. **알고리즘**: Fernet(AES-128-CBC+HMAC-SHA256), 토큰 접두사 `pii.v1.`로 평문/암호문 구분(마이그레이션 안전장치). **키 계층**: 사용자별 DEK를 `user_encryption_keys` 테이블에 KEK로 랩핑 저장, KEK는 환경변수 `PII_KEK`(MultiFernet 회전 대비) — **온프레미스 Vault 이전 전까지 임시**이며 `core/crypto.py`의 `PiiCrypto` 생성 지점만 교체하면 됨. **crypto-shredding**: 사용자 파기 시 `user_encryption_keys` 행 삭제로 해당 사용자 PII 자유텍스트 전부 복호화 불가 → B3 파기정책의 파기 수단 후보(법무 확인 대기). **범위**: `users.name`(부분일치 검색 재설계 선행)·`contact`(blind index)·`birth_date`(컬럼 타입 변경)는 2차 라운드로 분리 | ✅ 확정 (구현: `services/backend`, 마이그레이션 `0002`) |

> **2차 라운드 결과 (2026-09-09, v0.15)**: `contact`(암호문+blind index)·`birth_date`(앱 레이어 암호화) 적용. **`name`은 평문 유지로 확정** — 부분검색 UX 손실 대비 민감도가 낮고 CTO B4도 최고위험으로 보지 않음. **3차(남음)**: `PII_KEK`의 Vault 이전, `key_version` 기반 KEK 회전 절차, blind index 키 정식 분리(현재 KEK 첫 키에서 유도).

---

## 2.8 추가 기술 결정 (Do 단계 — 실 인증 구현, 2026-09-09)

| # | 항목 | 결정(근거 포함) | 상태 |
|---|------|------|:---:|
| 47 | 인증·인가 실구현 방식 + erd.md §11 스키마 추가 범위 | **Keycloak JWKS RS256 검증 + 사용자별 DEK식이 아닌 토큰 기반 RBAC로 확정.** `core/auth.py` 스텁(하드코딩 `roles=["family"]`)을 실 검증으로 교체([cto-review B5](../../02-design/cto-review-2026-09-05.md), 원본 프로세스흐름도 §4.1). erd.md §11 5개 중 **3개 반영**: ① `family_members.keycloak_sub`(VARCHAR, **비유일 인덱스** — erd의 "UK" 제안과 달리 한 사람이 여러 어르신을 담당하면 같은 sub로 여러 행이 생기므로), ② `device_credentials`(Device Token을 SHA-256 해시로만 보관, `POST /devices` 응답에 평문 1회 발급 — B5(b)), ③ `access_logs`(HTTP 미들웨어 best-effort 적재 — 제8조·B5(e)). **보류**: `organizations`(B2G 시설 테넌시 — 운영모델 확정 필요), `*.retention_until`(B3 법무 대기). **2FA**: 토큰 `amr` claim으로 판정(`AUTH_2FA_AMR_VALUES` 설정, Keycloak 인증흐름 의존). **IDOR/소유권**: `authorize_user_access()` 헬퍼로 핵심 엔드포인트(chapters·photos·consent·schedule·conversation-chunks·users·devices·sync)에 우선 적용, 나머지(family_members·invitations·photo_requests)는 인증만 유지하고 인가 확대는 후속. **환경변수**: `AUTH_AUDIENCE`·`AUTH_JWKS_URL`·`AUTH_2FA_AMR_VALUES` 추가(CONVENTIONS.md §4). `AUTH_ISSUER_URL` 미설정 시 `require_family` 첫 호출에서 RuntimeError(fail closed) | ✅ 확정 (구현: `services/backend`, 마이그레이션 `0003`) |
| 49 | 웹 콘솔(apps/web·apps/admin) Keycloak 로그인 연동 방식 | **Auth.js(NextAuth v5) + Keycloak provider로 확정**(사용자 결정). `silveryarn-web`은 public client → auth code flow + PKCE(client secret 없음, `token_endpoint_auth_method: "none"`). Auth.js가 로그인 리다이렉트·토큰 교환·**리프레시**·httpOnly 세션 쿠키를 처리하고, 액세스 토큰은 `session.accessToken`으로 노출된다. `lib/api/client.ts`에 `import "server-only"` — 이 모듈은 서버(Server Component·Server Action·Route Handler)에서만 실행되고 `auth()`로 토큰을 읽어 백엔드 `Authorization: Bearer`로 실어 보낸다(토큰이 브라우저 번들에 안 들어감). 클라이언트 컴포넌트의 폼 제출은 **Server Action**을 거친다. Next.js 16의 `middleware.ts`→`proxy.ts` rename 반영. **apps/web(3000)·apps/admin(3001) 둘 다 같은 `silveryarn-web` 클라이언트 사용** — realm `redirectUris`에 `localhost:3000/*`·`localhost:3001/*`. admin은 GET 전용이라 Server Action 불필요(client.ts server-only만). admin 화면은 백엔드가 `require_roles(admin)`으로 재검사(프론트는 유효 세션만 확인). **로컬 실 flow 브라우저 검증**(양쪽 앱: Keycloak 로그인 → 세션 → 실 Bearer로 백엔드 조회/PUT → 반영). env: `AUTH_SECRET`·`AUTH_KEYCLOAK_ID`·`AUTH_KEYCLOAK_ISSUER`·`AUTH_URL`(각 앱 `.env.local`, gitignore) | ✅ 확정 (구현: `apps/web`·`apps/admin`) |

> **후속 과제**: Device Token 회전 UI·주기, social_worker의 "동의 시 챕터 조회"(design.md §7.1) 동의 게이팅, `organizations` 테넌시(B2G 착수 시). 웹 콘솔 로그인(#49)은 apps/web·apps/admin 둘 다 완료.

| 50 | apps/web·apps/admin 공유 코드 추출 방식 | **npm workspaces + `packages/web-shared`로 확정**(사용자 결정). 루트 `package.json`에 `workspaces: ["apps/web","apps/admin","packages/*"]`. `@silveryarn/web-shared`가 **Keycloak 인증**(`auth.ts`·`proxy`·`auth-route` — PR #19에서 두 앱에 cp됐던 보안 코드), **API 클라이언트**(`api/`, server-only + `auth()` 토큰 주입), **UI 프리미티브**(`ui/` Button·Card), **AppHeader**(`brand` prop)를 노출. TS 소스를 그대로 export하고 각 앱 `next.config.ts` `transpilePackages`로 트랜스파일(Turbopack은 자동이지만 명시). `types/*`는 앱별 유지(design.md §3.1 SoR 미러, 향후 OpenAPI codegen). Next 16 `src/proxy.ts`·`app/api/auth/[...nextauth]/route.ts`는 앱 루트에 얇은 재노출 shim. eslint 계층 경계는 `import/no-restricted-paths`(파일 경로) → `no-restricted-imports`(패키지명 `@silveryarn/web-shared/api`)로 전환. CI는 워크스페이스 루트에서 `npm ci` 1회. **트리거**: admin README가 명시한 "인증 코드가 두 앱에 복붙돼 동기화 부담" 조건에 도달 | ✅ 확정 (구현: 루트·`packages/web-shared`) |
| 51 | 첫 가족 구성원 연결 경로 (§2.9, v0.28에서 보류) | **admin 중개 경로로 확정**(사용자 결정 — 웹 콘솔/admin 경로 vs device-token 부트스트랩 엔드포인트 두 안 중 선택). 갓 온보딩한 어르신 기기(Device Token)는 `POST /invitations`(family 권한 필요) 호출 권한이 없어 스스로 첫 가족을 연결할 수 없던 문제. admin이 대신 `POST /invitations`를 호출해 초대 링크를 만들고(운영자가 가족에게 전달), 가족은 apps/web `/invitations/[token]`에서 로그인 후 수락한다. **인가모델 변경 없음** — 기존 `authorize_user_access`의 `is_admin` 전역 우회를 그대로 재사용, device-token 부트스트랩 안(Device Token에 "가족 권한 부여" 능력을 새로 주는 안)은 채택하지 않음. apps/admin의 첫 쓰기 화면(Server Action) | ✅ 확정 (구현: `apps/admin`·`apps/web`) |

---

## 3. 별도 검토가 필요한 항목 (AI가 임의 결정하지 않음)

| # | 항목 | 사유 | 상태 |
|---|------|------|:---:|
| 12 | 정서 모니터링 알림의 법적/윤리적 기준 (누구에게, 어떤 임계치로 통보할지) | 어르신 본인 동의 없이 제3자(가족·복지사)에게 정신건강 관련 정보가 전달될 수 있는 사안으로, 개인정보보호법·의료법 등 법적 책임이 따름. AI가 임의로 기준을 정하면 실제 서비스에서 법적 리스크가 발생할 수 있어 **반드시 법무·윤리 검토를 거쳐야 함** | ⚖️ 별도 검토 필요 |
| 13 | 외부 TTS 연계의 구체 대상 서비스·비용·DPA 체결 | 계약·비용 문제로 경영진/법무 결정 사항 (§1의 결정에 따라 Phase 3 착수 시점으로 유예) | ⚖️ 별도 검토 필요 (Phase 3 시점) |
| 14 | Phase 1~3 착수 일정·예산·인력 | 경영진 승인 사항 (§1 참조) | ⚖️ 별도 검토 필요 |
| 23 | 구독·결제 PG사·요금제 | #18에서 Phase 1 스코프 아웃은 확정했으나, 실제 결제 도메인 설계 자체는 B2C/B2G 과금 방식이 정해져야 가능 (경영/법무 결정 사항) | ⚖️ 별도 검토 필요 |
| 46 | 가족 대리동의의 법적 근거 + 정보주체(어르신) 권리행사 모델 | CTO 검토 [B2](../../02-design/cto-review-2026-09-05.md) — 성년후견 미개시 어르신에 대한 가족 대리동의 유효성·본인동의 필수범위가 법무 확정 대기. **Do 단계 임시 구현(2026-09-09)**: `consent_logs.granted_by` 유무로 `actor`(self/proxy)를 파생만 하고, CTO 권고인 명시적 enum(self/proxy/**legal_guardian**)·`data_subject` RBAC 행은 도입하지 않음 — `legal_guardian`을 코드가 임의 정의하면 안 되므로. 법무 회신 후 스키마 컬럼(`actor` enum)·RBAC 반영 | ⚖️ 별도 검토 필요 (임시 구현 존재) |
| 48 | 복지사(social_worker)의 어르신 데이터 열람 근거 | CTO 검토 B2 — "가족·복지사 열람이 제17조 제3자제공인가, 제26조 위탁범위 내 이용인가". 이걸 표현할 consent 유형(`third_party_access` 등)·범위가 법무 확정 대기. **Do 단계 임시 구현(2026-09-09, 0.16)**: `READ_ELDER_DATA_ROLES`에서 social_worker 제외해 **fail-closed**(챕터·사진·대화·일정 조회 차단, 정서 알림·본인 알림설정은 유지). 법무 확정 후 전용 consent 유형 신설 + 그 동의 상태를 게이트로 복지사 재포함 | ⚖️ 별도 검토 필요 (fail-closed 구현) |

> 12번 항목에 대해 초안 성격의 시작점을 제안할 수는 있으나(예: 1차 알림은 가족에게만, 복지사는 가족 동의 시에만, 무응답 시 단계적 에스컬레이션), **이를 정식 기준으로 채택하는 것은 법무·윤리 검토 이후에만 가능**하다.

---

## 4. 원본 Plan/ 문서 자체의 오류 — 사용자 지시로 수정 완료 (2026-09-05)

> `design-validator` 검증에서 원본 산출물 자체의 내부 오류가 발견되어 최초에는 "문서관리팀 확인 필요"로 수정을 보류했으나, 사용자가 명시적으로 "보류한 것도 모두 수정"을 지시하여 원본을 직접 정정했다. 변경 이력은 각 파일의 편집 이력으로 남으며, 아래는 정정 요약이다.
>
> **번호 체계 안내**: 아래 표의 번호(36~42)는 원래 #24~#30이었으나, §2.2의 CTO팀 검토 결정 항목과 번호가 중복되는 버그가 있어 2차 design-validator 검증 시 발견 후 2026-09-07 재부여했다. 이 표를 가리키는 외부 참조는 없는 것을 확인했다.

| # | 위치 | 문제 → 조치 |
|---|------|------|
| 36 | `Plan/은빛실타래_UIUX_화면설계서.html` L276, `Plan/자서전_말벗돌봄_프로세스_흐름도.md` L7 | 기준 문서 버전 표기가 기획서 v0.3/v0.4를 참조 중이었음 → **기획서 v0.5로 정정** |
| 37 | `Plan/은빛실타래_UIUX_화면설계서.html` L1263 | "WA6(관리자·외부연계 동의 현황)" 참조 — 실제 WA6는 "기기 관리" 화면 → **전용 화면이 없다는 사실을 명시하고 WA6 오참조 제거** (신규 화면 설계는 별도 필요, 임의로 만들어내지 않음) |
| 38 | L842 | "M2 홈 또는 M6 자서전 탭에서 진입" — M6은 '설정' 화면 → **M3(자서전 탭)로 정정** |
| 39 | L1530 | "M1·M7 로컬 캐시로 배포" — 같은 문서 L1532의 "M3/M4에서 우선 제시"와 불일치 → **M3·M4로 정정** |
| 40 | L1127 | "M6 로컬 캐시로도 배포" → **M3·M4로 정정** (동일 사유) |
| 41 | L1362, L1583, L1956 | 정서 모니터링 절 번호를 "2.3절"/"4.4절"로 혼용 — 실제는 프로세스흐름도 §4.3 → **"프로세스흐름도 4.3절"로 통일 정정** |
| 42 | L967 | "4.2 자서전 제작 라이프사이클과 연동" — 실제 라이프사이클은 §5.2(§4.2는 Wi-Fi 동기화 절) → **"프로세스흐름도 5.2"로 정정**, L1042의 기존 올바른 인용과 통일 |

**후속 확인 권장**: 원본 문서 소유자(NUBiz AX Initiative 기획팀)가 위 정정 내용을 검토·승인할 것을 권장한다 — Claude가 design-validator 리포트에 근거해 기계적으로 정정했으나 최종 검수는 사람이 하는 것이 안전하다.

---

## Related Documents

- Plan: [silveryarn-platform.plan.md](../features/silveryarn-platform.plan.md)
- Design: [silveryarn-platform.design.md](../../02-design/features/silveryarn-platform.design.md)
- CTO팀 검토: [cto-review-2026-09-05.md](../../02-design/cto-review-2026-09-05.md) — #24, #25, #34, #35, #43 결정의 근거
- ERD: [erd.md](../erd.md), Mobile Schema: [mobile-schema.md](../mobile-schema.md)
- 원본 기획서 9장: [`Plan/어르신_자서전_말벗돌봄_기획서.md`](../../../Plan/어르신_자서전_말벗돌봄_기획서.md#9-다음-논의가-필요한-사항)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.22 | 2026-09-11 | Do 단계 — #51 첫 가족 구성원 연결 경로(**사용자 결정: admin 중개 경로**, §2.9 v0.28에서 보류). apps/admin `(admin)/family-members`(첫 쓰기 화면, `POST /invitations` 호출) + apps/web `/invitations/[token]`(초대 수락). 인가모델 변경 없음 — 기존 `is_admin` 전역 우회 재사용. 모바일 변경 없음. design.md v0.42 | NUBiz AX Initiative |
| 0.21 | 2026-09-11 | Do 단계 — #50 apps/web·apps/admin 공유 코드 추출(**사용자 결정: npm workspaces + `packages/web-shared`**). 루트 package.json 워크스페이스, Keycloak 인증·API 클라이언트·UI 프리미티브를 `@silveryarn/web-shared`로. eslint 계층 경계를 `no-restricted-imports`로 전환. CI 워크스페이스 루트 설치. structure.md v1.36 | NUBiz AX Initiative |
| 0.20 | 2026-09-11 | Do 단계 — #49를 apps/admin에도 이식(같은 Auth.js 방식). admin은 GET 전용이라 Server Action 불필요. realm `silveryarn-web` `redirectUris`에 `localhost:3001/*` 추가(admin은 3001에서 뜸). 양쪽 앱 브라우저 flow 검증(admin은 `require_roles(admin)` 통과 확인). design.md v0.35·structure.md v1.34 | NUBiz AX Initiative |
| 0.19 | 2026-09-11 | Do 단계 — #49 웹 콘솔 Keycloak 로그인 연동(**사용자 결정: Auth.js/NextAuth v5**). public client + auth code flow + PKCE, `lib/api/client.ts` server-only + Server Action 경로, Next 16 `proxy.ts`. 로컬 실 flow 검증 완료. design.md v0.34·structure.md v1.33 | NUBiz AX Initiative |
| 0.1 | 2026-09-05 | 기획서 9장 11개 항목 처리(로그 행 기준 14개, 일부 이중 기재), 3개는 법무·경영 검토 필요로 분류 | NUBiz AX Initiative (사용자 확인 반영) |
| 0.2 | 2026-09-05 | design-validator 검증 반영 — #15~#22 기술 결정 추가(FastAPI, Next.js 재등재, Keycloak, 구독결제 스코프아웃, 알림설정 범위분리, API 케이싱, enum 영문화, Wi-Fi 로컬전용), #23 후속 검토 항목 추가 | NUBiz AX Initiative |
| 0.3 | 2026-09-05 | CTO팀 5개 관점 검토(cto-review-2026-09-05.md) 반영 — #24(Phase 1 무료 확정), #25(정서 파이프라인 Phase 1 OFF 확정) 추가 | NUBiz AX Initiative |
| 0.4 | 2026-09-06 | 사용자 제안 "Closed-Loop Architecture" 보고서 검토 반영 — #26(외부LLM 미채택, 온프레미스 유지), #27(Qwen2.5-0.5B 후보 추가), #28(Qdrant 유지 재확인), #29(Neo4j 지식그래프 신규 채택), #30(음성파일 즉시삭제 정책) 추가 | NUBiz AX Initiative (사용자 확인 반영) |
| 0.5 | 2026-09-06 | 사용자 제안 "저사양 실시간 대화 프로세스" 보고서 반영 — #31(VAD/스트리밍 최적화 기법, 수치는 검증대기), #32(FTS5 단독 RAG Phase 1 기본값 확정), #33(mobile-schema.md 문서화) 추가 | NUBiz AX Initiative (사용자 제안 반영) |
| 0.6 | 2026-09-07 | 2차 design-validator 검증 반영 — #34(conversation_chunks 서버 영구보존 확정), #35(devices SLM/프롬프트팩 버전 추적) 추가. **번호 중복 버그 수정**: §3에 있던 #24~#33을 §2.2/§2.3/§2.4로 재배치(카테고리 정정), §4의 원본 문서 오류 로그를 #24~#30에서 #36~#42로 재번호(§2.2와의 충돌 해소) | NUBiz AX Initiative |
| 0.7 | 2026-09-07 | 3차 design-validator 검증 반영 — §2.5 신설, #43(본문 텍스트 20px 상향, CTO FE-B4) 추가. M-1: §2.2/§2.3 표 헤더가 5열인데 실제 셀은 4열이던 렌더링 버그 정정(4열 헤더로 통일, 내용 변경 없음) | NUBiz AX Initiative |
| 0.8 | 2026-09-07 | Do 단계 착수 — §2.6 신설, #44(서버 첫 커밋을 `services/backend/` 모듈러 모놀리스 단일 배포 단위로 확정, CTO Enterprise B3) 추가 | NUBiz AX Initiative |
| 0.9 | 2026-09-09 | Do 단계 — §2.7 신설, #45(PII 자유텍스트 5개 컬럼 암호화 방식 확정: 애플리케이션 레벨 필드 암호화 + 사용자별 DEK, `PII_KEK` 임시, CTO B4) 추가. schema.md v1.7·CONVENTIONS.md §4(`PII_` 접두사)·design.md §7.3 동반 갱신 | NUBiz AX Initiative |
| 0.10 | 2026-09-09 | Do 단계 — consent 모듈 구현. §3에 #46(가족 대리동의 법적 근거 — CTO B2, `actor` 임시 파생 구현만) 추가. design.md v0.18(§2.9·§3.1·§4.2) 동반 갱신 | NUBiz AX Initiative |
| 0.11 | 2026-09-09 | Do 단계 — 실 인증 구현. §2.8 신설, #47(Keycloak JWKS 검증 + erd.md §11 스키마 3종 반영: keycloak_sub·device_credentials·access_logs; organizations·retention은 보류) 추가. schema.md v1.8·erd.md §11·CONVENTIONS.md §4·design.md §7.4 동반 갱신 | NUBiz AX Initiative |
| 0.12 | 2026-09-09 | Do 단계 — 동기화 계약 잔여분(멱등성·questions 조회·schedule 필드병합). 별도 ULID 컬럼 없이 기존 `(session_id, turn_id)`를 멱등성 키로 채택(sync-contract.md §2.3, schema.md v1.9). 새 결정 항목은 없음 — 기존 계약(CTO B1)의 구현 마감 | NUBiz AX Initiative |
| 0.18 | 2026-09-09 | Do 단계 — 로컬 Keycloak realm 확정. `infra/docker-compose.yml`에 keycloak(port 9678) + `infra/keycloak/import/silveryarn-realm.json`(client `silveryarn-web`/`silveryarn-backend`, audience·**dev 전용 hardcoded amr** 매퍼). 새 결정 항목 없음 — decisions #17 확정의 로컬 개발 구현. 실 인프라 e2e로 인증·PII·멱등성 전부 검증(README.md), 무인증 401 버그 수정 | NUBiz AX Initiative |
| 0.17 | 2026-09-09 | Do 단계 — 모바일 온보딩 화면 흐름 구현. **Navigation Compose·ViewModel 프레임워크 미도입 확정**(사용자 결정) — 선형 온보딩엔 상태 호이스팅(sealed `OnboardingStep` + `when`)으로 충분, 화면이 늘면 재검토. design.md v0.25·mobile-schema.md v0.7 | NUBiz AX Initiative |
| 0.16 | 2026-09-09 | Do 단계 — social_worker 어르신 데이터 조회 **fail-closed** 확정(사용자 결정). RBAC §7.1의 복지사 "동의 시" 열람을 표현할 전용 consent 유형은 만들지 않고, 제3자제공 법무 판단(CTO B2, #12 관련)까지 조회 자체를 차단한다. `core/auth.py` `READ_ELDER_DATA_ROLES`에서 social_worker 제외. design.md v0.24 | NUBiz AX Initiative |
| 0.15 | 2026-09-09 | Do 단계 — PII 2차 확정·구현. `contact`(family_members·invitations) = 사용자별 DEK 암호문 + `contact_bidx`(HMAC-SHA256, 동등검색). `birth_date` = 앱 레이어 암호화(DATE→VARCHAR). **`name`은 평문 유지** — 사용자 결정(부분검색 UX·낮은 민감도). blind index 키는 `PII_KEK` 첫 키에서 유도(임시). schema.md v1.11·design.md v0.23·마이그레이션 0006 | NUBiz AX Initiative |
| 0.14 | 2026-09-09 | Do 단계 — `notifications` 모듈. CTO 검토 B1 부수결함 수정: `notification_settings.receives_emotion_alerts` 기본값 opt-out(true)→opt-in(false). `(family_member_id, channel)` UNIQUE 신설. schema.md v1.10·design.md v0.22·마이그레이션 0005. 새 결정 항목 없음 | NUBiz AX Initiative |
| 0.13 | 2026-09-09 | Do 단계 — 인가 확대(family-members·invitations·photo-requests). #47의 "나머지 엔드포인트" 후속. `POST /invitations/{token}/accept`가 수락자 토큰 `sub`를 `family_members.keycloak_sub`에 연결하도록 수정(계정 연결 갭). social_worker "동의 시 챕터 조회"(RBAC §7.1)는 전용 consent 유형 enum 결정이 필요해 #46 관련 항목으로 유예. design.md v0.21 | NUBiz AX Initiative |

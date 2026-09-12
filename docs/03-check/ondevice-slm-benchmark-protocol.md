# 온디바이스 SLM 실기기 벤치마크 프로토콜

> **작성일**: 2026-09-12 · **Status**: 실행 대기(실기기 미확보) · **작성 배경**: 사용자 요청 —
> `docs/03-check/blocked-decisions-tracker.md` "⏳ 선행조건 대기" 항목 중 결정이 아니라
> 실측이 먼저인 3건(온디바이스 SLM 선정·로컬 캐시 기준·실시간 파이프라인 수치)을
> 실행 가능한 절차로 구체화했다.
>
> **관련 결정**: [decisions #27](../01-plan/decisions/silveryarn-platform.decisions.md)(SLM 모델 선정),
> [#31](../01-plan/decisions/silveryarn-platform.decisions.md)(실시간 파이프라인 목표 수치),
> [#9](../01-plan/decisions/silveryarn-platform.decisions.md)(로컬 5일 캐시 기준)
>
> **하니스 코드**: `apps/mobile/app/src/main/java/com/silveryarn/mobile/benchmark/`
> (순수 로직은 `app/src/test`로 유닛테스트 검증됨) +
> `app/src/androidTest/java/.../RealDeviceBenchmarkTest.kt`(실행 진입점)
>
> ⚠️ **이 문서와 하니스 코드는 측정 준비물이지 측정 결과가 아니다.** 이 리포지토리를
> 작업한 환경에는 물리 안드로이드 기기·Android SDK/NDK·adb가 전혀 없어(`apps/mobile/
> README.md` "환경 제약") 실제 벤치마크를 실행할 수 없었다 — §1을 채운 뒤 실기기에서
> 직접 실행해야 한다.

---

## 0. 왜 필요한가

`SlmEngine`/`SttEngine`(`apps/mobile/.../ondevice/`)은 아직 순수 인터페이스뿐이고 실
구현체가 없다. Kanana-2·Qwen2.5-0.5B(둘 다 4bit 양자화) 중 무엇을 최종 채택할지,
"최근 5일" 로컬 캐시 기준이 저사양 단말에서 실제로 버틸 용량인지, 실시간 대화
파이프라인의 목표 수치(메모리 ~850MB, 첫 응답 0.8~1.2초)가 현실적인지 — 세 질문
전부 문서·회의로 답할 수 없고 실기기에 실제로 올려봐야 한다.

---

## 1. 준비물

### 1.1 실기기 3종

CLAUDE.md의 설치모드 임계값(RAM<6GB 또는 Android≤11 → 키오스크)을 기준으로 세
등급을 나눈다. 아래는 각 등급을 대표할 만한 예시일 뿐 — 실제 조달은 손에 넣기
쉬운 기종으로 대체해도 된다. 중요한 건 "이 프로젝트의 저사양 임계값 근처"를
실제로 포함하는 것이다.

| 등급 | 예시 기종 | 왜 이 등급인가 |
|---|---|---|
| 저사양("S10급") | Galaxy S10 / S10e, RAM 6~8GB, Android 12 업그레이드 상한 기종도 포함 | **키오스크 모드 판정 경계**(RAM<6GB 또는 Android≤11)에 실제로 걸리거나 근접한 기기 — 가장 중요한 등급 |
| 중간("A35급") | Galaxy A35, RAM 6~8GB, 중급 SoC | 저가 신규 구매 단말 대표 |
| 고사양("S24급") | Galaxy S24, RAM 8GB+, 최신 SoC | 3종 동시 상주(STT+SLM+TTS) 여유가 있는지 상한선 확인 |

### 1.2 SLM 후보 모델 파일

- **Kanana-2**(카카오, 경량 버전) — 4bit 양자화(GGUF 등) 배포본 확보
- **Qwen2.5-0.5B** — 4bit 양자화 배포본 확보(Alibaba 공식 또는 커뮤니티 양자화)

### 1.3 추론 런타임 선정 (이 문서 범위 밖 — 별도 결정 필요)

아래 중 하나를 골라 `SlmEngine`을 구현해야 한다(이번 세션엔 미포함):

| 후보 | 장점 | 확인 필요 |
|---|---|---|
| llama.cpp (Android JNI) | GGUF 생태계, 커뮤니티 큼 | NDK 크로스컴파일, 4bit 양자화 지원 확인 |
| MLC-LLM | 모바일 GPU(Vulkan/OpenCL) 가속 | Kanana-2 컴파일 지원 여부 |
| ONNX Runtime Mobile | 안드로이드 공식 지원 안정적 | 두 모델 다 ONNX 변환 필요 |

STT는 CONVENTIONS.md가 이미 "Sherpa-ONNX 등 후보"로 지목해뒀다 — 위와 별개로
Sherpa-ONNX Android 배포본 + 한국어 모델(예: 자체 파인튜닝 또는 공개 한국어 STT
모델) 확보가 필요하다.

### 1.4 코드 연동

1. `SttEngine`/`SlmEngine` 실 구현체를 만들어 `RealDeviceBenchmarkTest.kt`의
   `UnimplementedSttEngine()`/`UnimplementedSlmEngine()` 자리를 교체한다.
2. TTS는 이미 실 구현체(`AndroidNativeTtsEngine`, OS 내장 TTS)가 있어 그대로 쓴다.

---

## 2. 테스트 픽스처

`apps/mobile/app/src/androidTest/assets/benchmark_fixtures/`에 16kHz mono PCM
(헤더 없는 raw, `.pcm` 확장자) 오디오 샘플을 넣는다.

| 항목 | 권장값 |
|---|---|
| 샘플 수 | 최소 5~10개 |
| 길이 | 각 5~20초 (실제 어르신 발화 길이 분포를 반영) |
| 화자 | **실제 노년층 발화 속도·억양·조사 생략 등을 반영**해야 함 — 일반 성우 낭독은 STT 난이도를 과소평가한다 |
| 내용 | 회고/일상 대화 혼합(작가 모드·말벗 모드 둘 다 대표하도록) |

파일이 하나도 없으면 `RealDeviceBenchmarkTest`는 실패가 아니라 **스킵**된다(JUnit
`Assume` — "준비 안 됨"과 "돌았는데 기준 미달"을 구분하기 위해 의도적으로 나눔).

⚠️ 실제 오디오 파일은 리포지토리에 커밋하지 않는다(`.gitignore` 처리됨) — 개인정보
소지 가능성과 무관하게 바이너리 픽스처는 별도 사설 저장소에서 받아온다.

---

## 3. 측정 절차

1. 위 1.4의 실 구현체로 교체, 2의 픽스처 배치.
2. `RealDeviceBenchmarkTest.kt` 상단의 `slmCandidateName`을 이번 실행 후보 이름으로 바꾼다(예: `"kanana-2-4bit"`).
3. 기기를 USB 디버깅으로 연결하고 실행:
   ```bash
   cd apps/mobile
   ./gradlew connectedAndroidTest --tests "com.silveryarn.mobile.benchmark.RealDeviceBenchmarkTest"
   ```
4. **다른 모든 백그라운드 앱을 종료**하고 화면 밝기·절전모드를 고정한 상태로 실행 —
   그렇지 않으면 메모리·배터리 측정값이 다른 프로세스에 오염된다.
5. 기기별 · 후보별로 반복(3기기 × 2후보 = 최소 6회 세션).
6. 결과 파일 회수:
   ```bash
   adb pull /sdcard/Android/data/com.silveryarn.mobile/files/benchmark ./benchmark-results/<기기명>
   ```

---

## 4. 측정 항목과 목표치

`TurnMetrics`/`SessionSummary`(`BenchmarkModels.kt`)가 매 턴·매 세션 자동 집계한다.

| 지표 | decisions.md #31 목표치 | 코드 위치 |
|---|---|---|
| 첫 응답 지연(VAD 종료 → TTS 첫 오디오) | 0.8~1.2초 | `TurnMetrics.totalTurnLatencyMs`, 세션 `totalLatencyP50Ms`/`P95Ms` |
| 메모리(3엔진 동시 상주) | ~850MB | `TurnMetrics.memoryUsedMb`, 세션 `peakMemoryMb` |
| 발열 조절(throttling) | 발생하지 않아야 함 | `SessionSummary.thermalThrottled`(`PowerManager.THERMAL_STATUS_MODERATE` 이상 감지 시 true) |
| 배터리 소모 | 별도 기준 없음 — 참고 수치로 기록 | `SessionSummary.batteryDrainPercent` |

**주의**: 정수 % 배터리 측정은 짧은 세션(턴 10개 이하)에서는 변화가 안 잡힐 수
있다. 배터리 소모율이 필요하면 턴을 반복해 최소 30분~1시간 세션으로 다시 재보라.

**품질(WER 등 STT 정확도, 응답 자연스러움)은 이 하니스의 범위 밖이다** — 리소스·
지연시간만 자동 측정하고, 답변 품질은 벤치마크 세션 중 사람이 직접 듣고 별도로
평가해야 한다(라벨링된 정답 코퍼스가 없어 자동화 불가).

---

## 5. 측정값 검증

하니스가 뽑은 숫자를 그대로 믿기 전에 한 번은 OS 표준 도구와 대조한다:

- 메모리: `adb shell dumpsys meminfo com.silveryarn.mobile`의 TOTAL PSS와
  `DeviceProfiler.snapshotMemoryMb()` 값 비교
- 배터리: `adb shell dumpsys battery`의 level과 비교
- 발열: Android 9 이하 기기는 `PowerManager.getCurrentThermalStatus()` API 자체가
  없어(`DeviceProfiler`가 -1 반환) 기기 표면 온도를 적외선 온도계 등으로 직접 재야 한다

---

## 6. 결과 취합 · 판정

각 세션의 `summary.csv` 한 줄씩을 모아 기기×후보 비교표를 만든다
(`CsvReportWriter.SUMMARY_HEADER` 컬럼 그대로 스프레드시트에 붙여넣기).

**최종 선정 기준(제안 — 실제 채택은 이 실측 결과를 보고 다시 확정)**:
1. 저사양("S10급") 기기에서 발열 조절이 발생하지 **않는** 후보만 남긴다.
2. 남은 후보 중 `totalLatencyP95Ms`가 목표치(1.2초)에 더 가까운 쪽을 우선한다.
3. 동률이면 답변 품질(§4 "품질" 참고 — 사람이 직접 청취 평가)로 최종 결정.

결과가 나오면 `decisions.md #27`에 정식 기재하고, 이 문서와
`blocked-decisions-tracker.md`의 해당 행을 "완료"로 갱신한다.

---

## 7. 부록 — 로컬 "최근 5일" 캐시 실측 (decisions #9)

SLM 벤치마크와 별개로, 저사양 기기의 실제 저장 공간에 mobile-schema.md 6개
테이블(특히 `conversations`의 Opus 오디오·`autobiography_fts`)이 5일치 누적됐을 때
얼마나 차지하는지 실측이 필요하다.

1. 저사양 기기에 앱 설치, 실제 사용 패턴과 비슷하게(하루 대화 10~20턴) 5일간 축적.
2. `adb shell du -sh /data/data/com.silveryarn.mobile/` 로 앱 전체 데이터 크기 확인.
3. `conversations` 테이블의 `audio_path`(성공 업로드 후 null로 비워짐, mobile-schema.md
   §3 retention 정책)가 실제로 정리되고 있는지도 같이 확인 — 정리가 안 되면 5일치가
   아니라 무한정 누적되는 버그일 수 있다.
4. 저사양 기기의 여유 저장공간 대비 이 크기가 안전한 비율인지 판단해 5일 기준을
   유지할지 조정할지 결정.

---

## Related Documents

- [blocked-decisions-tracker.md](./blocked-decisions-tracker.md) — "⏳ 선행조건 대기" 표
- [decisions.md](../01-plan/decisions/silveryarn-platform.decisions.md) #9·#27·#31
- [mobile-schema.md](../01-plan/mobile-schema.md) §3 (retention 정책)
- 하니스 코드: `apps/mobile/app/src/main/java/com/silveryarn/mobile/benchmark/`

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-09-12 | 최초 작성 — 측정 하니스 코드와 함께 신규(사용자 요청, 실측 3건 중 벤치마크 프로토콜+하니스로 선행 준비) | NUBiz AX Initiative |

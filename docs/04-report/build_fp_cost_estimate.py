# -*- coding: utf-8 -*-
"""
은빛실타래(SilverYarn) FP(Function Point) 산정 내역서 + SW개발비 산정 워크북 생성 스크립트.

방법론: IFPUG(International Function Point Users Group) CPM 표준 —
한국소프트웨어산업진흥원/한국소프트웨어산업협회가 공표하는 '소프트웨어사업 대가산정 가이드'
(소프트웨어산업 진흥법 제19조, SW사업대가기준)이 채택하고 있는 방식과 동일하다.

산정 절차:
  1) 데이터기능(ILF/EIF) + 트랜잭션기능(EI/EO/EQ) 식별
  2) 기능별 DET(Data Element Type)/RET(Record Element Type) 또는 FTR(File Type Referenced) 산정
  3) IFPUG 복잡도 매트릭스로 Low/Average/High 판정 → 가중치 부여
  4) 미조정 기능점수(UFP) = 전 기능 가중치 합
  5) 보정계수(VAF) = 0.65 + (14개 일반시스템특성 총점 × 0.01)
  6) 조정 기능점수(AFP) = UFP × VAF
  7) SW개발비 = AFP × FP당단가 × (1+이윤율) [+ 직접경비]

⚠️ FP당 단가는 한국소프트웨어산업협회가 매년 실측 공표하는 값으로, 이 스크립트는
   사용자 요청에 따라 "예시값 + 별도 셀 분리" 방식을 채택한다 — SW개발비산정 시트의
   [FP당 단가] 셀 하나만 최신 공표자료로 교체하면 전체 금액이 자동 재계산된다.
"""

import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

# ────────────────────────────────────────────────────────────────────────────
# 공통 스타일
# ────────────────────────────────────────────────────────────────────────────

TITLE_FONT = Font(name="맑은 고딕", size=16, bold=True, color="FFFFFF")
TITLE_FILL = PatternFill("solid", fgColor="1F3864")
H1_FONT = Font(name="맑은 고딕", size=12, bold=True, color="FFFFFF")
H1_FILL = PatternFill("solid", fgColor="2E5395")
HEADER_FONT = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
SUB_FONT = Font(name="맑은 고딕", size=10, bold=True)
SUB_FILL = PatternFill("solid", fgColor="D9E2F3")
NOTE_FONT = Font(name="맑은 고딕", size=9, italic=True, color="7F7F7F")
BODY_FONT = Font(name="맑은 고딕", size=10)
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
INPUT_FONT = Font(name="맑은 고딕", size=10, bold=True, color="BF8F00")
RESULT_FILL = PatternFill("solid", fgColor="E2EFDA")
RESULT_FONT = Font(name="맑은 고딕", size=11, bold=True, color="375623")
THIN = Side(style="thin", color="B7B7B7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
CENTER_NOWRAP = Alignment(horizontal="center", vertical="center")

TODAY = datetime.date(2026, 9, 13)


def style_header_row(ws: Worksheet, row: int, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = BORDER


def style_data_rows(ws: Worksheet, start_row: int, end_row: int, ncols: int, wrap_cols=None) -> None:
    wrap_cols = wrap_cols or set()
    for r in range(start_row, end_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = WRAP if c in wrap_cols else CENTER_NOWRAP


def set_col_widths(ws: Worksheet, widths: dict) -> None:
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w


def sheet_title(ws: Worksheet, text: str, ncols: int, row: int = 1) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = TITLE_FONT
    cell.fill = TITLE_FILL
    cell.alignment = CENTER
    ws.row_dimensions[row].height = 28


# ────────────────────────────────────────────────────────────────────────────
# IFPUG 복잡도 판정 (표준 CPM 매트릭스 — 연도와 무관한 고정 상수)
# ────────────────────────────────────────────────────────────────────────────

def ilf_eif_complexity(det: int, ret: int) -> str:
    if ret <= 1:
        return "Low" if det <= 50 else "Average"
    if ret <= 5:
        if det <= 19:
            return "Low"
        return "Average" if det <= 50 else "High"
    if det <= 19:
        return "Average"
    return "High"


ILF_WEIGHT = {"Low": 7, "Average": 10, "High": 15}
EIF_WEIGHT = {"Low": 5, "Average": 7, "High": 10}


def ei_complexity(det: int, ftr: int) -> str:
    if ftr <= 1:
        if det <= 4:
            return "Low"
        return "Low" if det <= 15 else "Average"
    if ftr == 2:
        if det <= 4:
            return "Low"
        return "Average" if det <= 15 else "High"
    if det <= 4:
        return "Average"
    return "High"


EI_WEIGHT = {"Low": 3, "Average": 4, "High": 6}


def eo_eq_complexity(det: int, ftr: int) -> str:
    if ftr <= 1:
        if det <= 5:
            return "Low"
        return "Low" if det <= 19 else "Average"
    if ftr <= 3:
        if det <= 5:
            return "Low"
        return "Average" if det <= 19 else "High"
    if det <= 5:
        return "Average"
    return "High"


EO_WEIGHT = {"Low": 4, "Average": 5, "High": 7}
EQ_WEIGHT = {"Low": 3, "Average": 4, "High": 6}


# ────────────────────────────────────────────────────────────────────────────
# 데이터: 서버 ILF (내부논리파일) — schema.md v1.17 도메인 19개 + 비RDB 저장소 3개
# ────────────────────────────────────────────────────────────────────────────
# (한글명, 대응 테이블/저장소, DET, RET, 설명)

ILF_SERVER = [
    ("어르신(당사자) 정보", "users", 7, 1,
     "자서전·말벗돌봄 서비스의 1차 사용자(어르신) 기본정보 — 이름·생년월일·소속기기·시설(B2G)·"
     "단기압축기억(persona) 스냅샷. schema.md §3.1."),
    ("가족·복지사 구성원 정보", "family_members", 7, 1,
     "어르신에 연결된 2차 사용자(가족/요양보호사/복지사/관리자) — 역할·연락처·2FA 여부·소속시설. "
     "schema.md §3.2."),
    ("기기(단말) 레지스트리", "devices", 12, 1,
     "설치된 스마트폰의 사양(RAM·OS·NPU)·설치모드(키오스크/일반)·탑재 SLM/프롬프트팩 버전을 "
     "관리하는 기기 마스터. schema.md §3.3."),
    ("자서전 챕터", "chapters", 12, 2,
     "유년기~현재로 구분된 자서전 본문 — 초안/감수중/반려/확정 상태, 버전, Compaction Engine이 "
     "생성한 요약·키워드. RET=2(본문 그룹 + 압축요약 그룹). schema.md §3.4."),
    ("챕터 감수 이력", "chapter_revisions", 7, 1,
     "챕터 승인/반려 시점의 본문 스냅샷과 감수자·코멘트 이력. schema.md §3.5."),
    ("사진", "photos", 19, 2,
     "업로드된 사진의 저장위치·회고상태·자서전 삽입위치·품질검수 결과. 상태값에 따라 노출되는 "
     "속성군이 달라 RET=2. schema.md §3.6."),
    ("사진 추가 요청", "photo_requests", 7, 1,
     "가족이 당사자에게 신규 사진 업로드를 요청하는 흐름의 상태 관리. schema.md §3.7."),
    ("구술 대화 청크", "conversation_chunks", 20, 2,
     "RAG 인덱싱 단위의 구술 전사·AI 응답·시기/인물/장소 메타데이터. 보유기간 만료/파기 시각 포함. "
     "메타데이터 그룹이 조건부로 채워져 RET=2. schema.md §3.8, decisions.md #56."),
    ("회고 질문 큐", "questions", 6, 1,
     "Critic Agent가 서사 완성도 갭을 분석해 생성한 심층 회고 질문 목록. schema.md §3.9."),
    ("일정·복약 항목", "schedule_items", 12, 2,
     "병원예약/복약 일정, 확인·거절·재알림 상태. 항목 종류(kind)에 따라 필드 의미가 달라 "
     "RET=2. schema.md §3.10."),
    ("정서 알림", "emotion_alerts", 6, 1,
     "정서 점수 임계치 초과 시 생성되는 알림·확인·종료 이력(Phase 1 피처플래그 OFF). schema.md §3.11."),
    ("일별 정서 점수", "emotion_scores", 5, 1,
     "발화 톤 분석 기반 일별 정서 점수 시계열(Phase 1 피처플래그 OFF). schema.md §3.12."),
    ("동기화 이력", "sync_sessions", 8, 1,
     "Wi-Fi 배치 동기화(업/다운로드)의 상태·체크섬·재시도 이력. schema.md §3.13."),
    ("동의 이력", "consent_logs", 7, 1,
     "개인정보 수집·외부TTS·외부LLM·제3자제공·국외이전 5종 동의/철회 이력(append-only). "
     "schema.md §3.14."),
    ("알림 수신 설정", "notification_settings", 6, 1,
     "가족 구성원별 SMS/이메일/푸시 채널 및 수신 항목 설정. schema.md §3.15."),
    ("가족 구성원 초대", "invitations", 9, 1,
     "admin 중개 초대 토큰·역할·소속시설·수락상태 관리. schema.md §3.16."),
    ("출판 요청", "publications", 5, 1,
     "완성 자서전의 인쇄용 PDF/ePub 조판·출판 요청 상태(Phase 3 예정). schema.md §3.17."),
    ("B2G 시설", "organizations", 3, 1,
     "요양원·복지관 등 B2G 시설 — 시설 테넌시 안전망의 기준 엔티티. schema.md §3.20, "
     "decisions.md #59."),
    ("보유기간 정책", "retention_policies", 4, 1,
     "카테고리별 데이터 보유일수를 admin이 조정하는 설정 — 하드코딩 대신 DB 설정 테이블. "
     "schema.md §3.21, decisions.md #56."),
    ("임베딩 벡터 저장소", "Qdrant(conversation_chunks 컬렉션)", 3, 1,
     "구술 청크의 BGE-M3 임베딩 벡터 — 하이브리드(BM25+Dense) 검색의 색인 저장소. "
     "원문 미저장(payload=user_id만, CTO 검토 B4)."),
    ("지식그래프 저장소", "Neo4j(Person/ConversationChunk 노드)", 6, 1,
     "인물·사건·시기·장소 엔티티와 '언급됨' 관계를 저장하는 지식그래프 — 회고 대화 맥락 추적."),
    ("미디어 원본 저장소", "MinIO(오브젝트 스토리지)", 4, 1,
     "구술 원본 음성(.opus)·사진 원본·출판물 PDF/ePub의 바이너리 객체 저장소(presigned URL 접근)."),
]

EIF_SERVER = [
    ("외부 인증 디렉터리", "Keycloak Realm(사용자·역할)", 5, 1,
     "웹 콘솔 사용자의 SSO 계정·역할·2FA 여부를 관리하는 외부 시스템 — 본 애플리케이션은 "
     "JWKS로 토큰만 검증하고 데이터는 유지보수하지 않는다(EIF)."),
]

# ────────────────────────────────────────────────────────────────────────────
# 데이터: 서버 트랜잭션 기능 — 실행 중인 백엔드 openapi.json 46개 엔드포인트 전수 대조
# ────────────────────────────────────────────────────────────────────────────
# (구분, Method, Path, 한글기능명, 설명, DET, FTR)

TX_SERVER = [
    ("EQ", "GET", "/chapters/{id}", "챕터 단건 조회", "챕터 본문·상태·버전을 단건 조회한다.", 9, 1),
    ("EI", "POST", "/chapters/{id}/review", "챕터 감수 승인/반려",
     "가족이 챕터를 승인/반려하고 감수 이력을 생성한다. 승인 시 Compaction 재확인 안전망을 "
     "동반 트리거한다(chapters+chapter_revisions).", 8, 2),
    ("EQ", "GET", "/chapters/{id}/revisions", "챕터 감수 이력 조회", "특정 챕터의 승인/반려 이력을 조회한다.", 6, 1),
    ("EQ", "GET", "/conversation-chunks/{id}", "구술 청크 단건 조회", "구술 청크 1건을 복호화하여 조회한다.", 14, 1),
    ("EI", "POST", "/devices", "기기 신규 등록",
     "설치 시점 1회 기기를 등록하고 Device Token을 발급한다(부트스트랩, 인증 없음).", 10, 1),
    ("EQ", "GET", "/family-members/{id}/notification-settings", "알림 수신 설정 조회",
     "구성원의 채널별 알림 수신 설정을 조회한다.", 5, 1),
    ("EI", "PUT", "/family-members/{id}/notification-settings", "알림 수신 설정 변경",
     "구성원의 알림 수신 설정 전체를 교체(delete→insert)한다.", 5, 1),
    ("EI", "POST", "/invitations", "가족 구성원 초대 생성",
     "admin/가족이 신규 구성원 초대 토큰을 발급한다(연락처·역할·소속시설 지정).", 6, 2),
    ("EQ", "GET", "/invitations/{token}", "초대 토큰 조회", "토큰 자체가 접근권한이라 무인증으로 초대 정보를 조회한다.", 6, 1),
    ("EI", "POST", "/invitations/{token}/accept", "초대 수락",
     "초대받은 사용자가 로그인 후 수락 — 신규 계정과 초대 토큰을 연결한다.", 4, 2),
    ("EQ", "GET", "/organizations", "시설 목록 조회", "B2G 시설(요양원·복지관) 전체 목록을 조회한다.", 3, 1),
    ("EI", "POST", "/organizations", "시설 신규 등록", "B2G 시설을 신규 등록한다(admin).", 3, 1),
    ("EQ", "GET", "/organizations/{id}", "시설 단건 조회", "시설 1건의 상세를 조회한다.", 3, 1),
    ("EI", "POST", "/photo-requests", "사진 추가 요청 생성", "가족이 당사자에게 사진 업로드를 요청한다.", 5, 2),
    ("EI", "POST", "/photo-requests/{id}/dismiss", "사진 추가 요청 닫기", "충족되지 않은 사진 요청을 닫는다.", 2, 1),
    ("EI", "POST", "/photos/upload-url", "사진 업로드 URL 발급",
     "MinIO Presigned URL을 발급하고 pending_upload 상태의 사진 행을 생성한다.", 6, 1),
    ("EI", "POST", "/photos/{id}/complete", "사진 업로드 완료 확인", "업로드 완료 콜백을 받아 사진 상태를 uploaded로 전환한다.", 3, 1),
    ("EQ", "GET", "/retention-policies", "보유기간 정책 목록 조회", "카테고리별 보유일수 설정 목록을 조회한다(admin).", 4, 1),
    ("EI", "PUT", "/retention-policies/{category}", "보유기간 정책 변경",
     "카테고리별 보유일수를 admin이 직접 조정한다.", 3, 1),
    ("EQ", "GET", "/schedule-items/{id}", "일정 단건 조회", "일정/복약 항목 1건을 조회한다.", 9, 1),
    ("EI", "POST", "/schedule-items/{id}/next-reminder", "일정 재알림 예약",
     "가족이 '나중에 알림'을 눌러 재알림 시각을 갱신한다.", 2, 1),
    ("EI", "POST", "/schedule-items/{id}/respond", "일정 응답 처리", "어르신/가족이 일정을 확인·거절한다.", 3, 1),
    ("EO", "GET", "/sync/download", "증분 다운로드(자서전·질문·일정·페르소나)",
     "챕터 요약·우선순위 질문·일정·단기압축기억을 증분(since 기준)으로 계산해 내려보낸다 — "
     "4개 ILF를 가로지르는 파생 데이터 조합.", 16, 4),
    ("EQ", "GET", "/sync/sessions", "동기화 이력 목록 조회(관리자)", "전체/기기별 동기화 이력을 페이지네이션 조회한다.", 8, 2),
    ("EQ", "GET", "/sync/sessions/{id}", "업로드 작업 상태 조회", "비동기 업로드 1건의 처리 상태를 조회한다.", 4, 1),
    ("EI", "POST", "/sync/upload", "구술 발화·사진 업로드(비동기)",
     "원본 음성·1차 전사·신규 사진을 접수해 202로 응답하고, 지식화 파이프라인(전사 보정→"
     "임베딩→챕터 갱신→질문 생성→페르소나 갱신)을 비동기로 구동한다 — 5개 데이터저장소에 "
     "걸친 가장 복잡한 트랜잭션.", 12, 5),
    ("EI", "POST", "/users", "어르신 계정 생성", "온보딩 시 1차 사용자 계정을 생성한다(부트스트랩).", 3, 1),
    ("EQ", "GET", "/users", "사용자 목록 조회", "전체 사용자를 페이지네이션·이름검색으로 조회한다(admin).", 7, 1),
    ("EQ", "GET", "/users/{id}", "사용자 단건 조회", "사용자 1건의 상세를 조회한다.", 7, 1),
    ("EQ", "GET", "/users/{id}/chapters", "사용자별 챕터 목록 조회", "특정 어르신의 챕터 전체를 조회한다.", 9, 1),
    ("EI", "POST", "/users/{id}/consent-logs", "동의 기록 생성", "개인정보 수집 등 5종 동의/철회 1건을 기록한다.", 4, 1),
    ("EQ", "GET", "/users/{id}/consent-logs", "동의 이력 조회", "사용자의 전체 동의 이력을 조회한다.", 6, 1),
    ("EO", "GET", "/users/{id}/consent-state", "유형별 현재 동의 상태 산출",
     "동의 유형별 최신 행을 계산해 '현재 동의 상태'를 파생한다 — 온보딩 게이트·RBAC 조건 판정용.", 5, 1),
    ("EQ", "GET", "/users/{id}/conversation-chunks", "사용자별 구술 청크 목록 조회", "특정 어르신의 구술 청크를 조회한다.", 14, 1),
    ("EO", "GET", "/users/{id}/conversation-chunks/count", "특정 시각 이후 청크 개수 산출",
     "PII를 복호화하지 않고 COUNT만 계산 — 가족 대시보드 '오늘 대화' 통계.", 3, 1),
    ("EO", "GET", "/users/{id}/conversation-chunks/search", "구술 청크 키워드 검색",
     "전량 복호화 후 애플리케이션 레벨 부분일치 필터링(임시, RAG 하이브리드 서치로 교체 예정).", 4, 1),
    ("EQ", "GET", "/users/{id}/devices", "사용자 기기 조회", "어르신에 연결된 기기 사양·설치모드를 조회한다(admin).", 12, 1),
    ("EI", "POST", "/users/{id}/erase", "계정 전체 삭제(erasure)",
     "정보주체 삭제요청권 행사 — Postgres cascade(crypto-shredding 포함) + Qdrant/Neo4j/"
     "MinIO 정리 + 감사로그 기록까지 오케스트레이션하는 되돌릴 수 없는 트랜잭션.", 3, 5),
    ("EQ", "GET", "/users/{id}/family-members", "가족 구성원 목록 조회", "어르신에 연결된 가족·복지사 목록을 조회한다.", 7, 1),
    ("EI", "POST", "/users/{id}/family-members", "가족 구성원 생성", "가족/복지사 구성원을 신규 등록한다.", 6, 1),
    ("EQ", "GET", "/users/{id}/photo-requests", "사진 요청 목록 조회", "어르신에 대한 사진 추가 요청 목록을 조회한다.", 5, 1),
    ("EQ", "GET", "/users/{id}/photos", "사진 목록 조회", "어르신의 사진 전체 목록(presigned URL 포함)을 조회한다.", 19, 1),
    ("EI", "PUT", "/users/{id}/organization", "시설 배정/해제",
     "어르신을 B2G 시설에 배정하거나 해제한다 — 존재하는 시설인지 검증 후 반영.", 2, 2),
    ("EQ", "GET", "/users/{id}/questions", "회고 질문 큐 조회", "어르신에게 제시할 회고 질문 큐를 조회한다.", 6, 1),
    ("EQ", "GET", "/users/{id}/schedule-items", "일정 목록 조회", "어르신의 일정·복약 항목 목록을 조회한다.", 9, 1),
    ("EI", "POST", "/users/{id}/schedule-items", "일정 항목 생성", "가족이 일정/복약 항목을 신규 등록한다.", 9, 1),
]

assert len(TX_SERVER) == 46, f"서버 엔드포인트 수 불일치: {len(TX_SERVER)}"

# ────────────────────────────────────────────────────────────────────────────
# 데이터: 모바일 온디바이스 ILF — mobile-schema.md v0.11, 6개 Room/SQLite 테이블
# ────────────────────────────────────────────────────────────────────────────

ILF_MOBILE = [
    ("구술 대화 로컬 버퍼", "conversations", 11, 1,
     "서버 conversation_chunks의 로컬 버퍼 — 오프라인 상태에서도 대화 턴을 즉시 로컬에 "
     "적재한다. 업로드 성공 시 원본 오디오만 삭제, 텍스트는 5일 롤링 윈도우 유지."),
    ("자서전 로컬 검색 인덱스", "autobiography_fts (FTS5)", 5, 1,
     "Zero-Neural RAG의 핵심 — 임베딩 모델 없이 SQLite FTS5(BM25) 키워드 검색만으로 "
     "오프라인 회상 검색을 수행한다."),
    ("회고 질문 로컬 캐시", "questions_cache", 6, 1,
     "서버 questions의 서브셋 — 동기화로 갱신되는 우선순위 회고 질문 큐."),
    ("미회고 사진 로컬 큐", "unrecalled_photos", 4, 1,
     "회고 대상 사진(recall_status=pending) 서브셋 — 대화 세션 시작 시 최우선 제시."),
    ("일정 로컬 캐시", "schedule_cache", 8, 1,
     "서버 schedule_items 서브셋 + 오프라인 등록분(origin=local, 다음 동기화 시 서버 반영)."),
    ("기기 상태", "device_state", 10, 1,
     "설치 시 1회 결정되는 설치모드·SLM버전·최종 동기화 커서·페르소나 스냅샷 등 "
     "단일 행 기기 로컬 상태."),
]

# (구분, 한글기능명, 설명, DET, FTR)
TX_MOBILE = [
    ("EI", "오프라인 대화 턴 로컬 기록",
     "인터넷 연결 여부와 무관하게 온디바이스 STT/SLM 대화 턴을 즉시 로컬 DB에 적재한다 "
     "(오프라인 우선 원칙의 핵심 기능).", 8, 1),
    ("EI", "온보딩 완료 처리(기기 로컬 상태 등록)",
     "이름 입력→동의→서버 3연쇄 호출 완료 후, 발급받은 device_id·install_mode를 "
     "기기 로컬 상태에 최초로 기록한다.", 4, 1),
    ("EI", "설치모드 적용(키오스크 잠금)",
     "device_state.install_mode가 kiosk이면 Device Owner Mode 기반 lockTask를 적용해 "
     "단일 앱 잠금 상태로 전환한다.", 2, 1),
    ("EI", "오프라인 일정 응답 로컬 반영",
     "네트워크 단절 상태에서 어르신이 일정을 확인/거절하면 로컬에 즉시 반영(origin=local)하고 "
     "다음 동기화 때 서버에 병합한다.", 4, 1),
    ("EI", "업로드 성공 후 원본음성 로컬 삭제",
     "서버 200 OK 확인 즉시 로컬 Opus 원본 파일을 삭제하고 동기화 상태를 SYNCED로 갱신한다 "
     "(decisions.md #30).", 3, 1),
    ("EI", "보유기간 경과 대화 자동 정리 배치",
     "매일 자정, 생성 후 5일(잠정)이 경과한 로컬 대화 버퍼 행을 삭제하는 보존정책 배치 "
     "(decisions.md #9).", 2, 1),
    ("EI", "동기화 다운로드 응답 로컬 반영",
     "GET /sync/download 응답을 받아 자서전 검색색인·질문캐시·미회고사진큐·일정캐시 "
     "4개 로컬 저장소를 한 트랜잭션으로 Upsert한다.", 10, 4),
    ("EQ", "로컬 FTS5 키워드 회상 검색",
     "임베딩 연산 없이 SQLite FTS5(BM25)만으로 자서전 청크를 인출하는 온디바이스 "
     "Zero-Neural RAG 검색.", 3, 1),
    ("EQ", "미회고 사진 큐 조회", "대화 세션 시작 시 제시할 미회고 사진 목록을 로컬에서 조회한다.", 4, 1),
    ("EQ", "회고 질문 큐 조회", "다음 질문할 우선순위 회고 질문을 로컬 캐시에서 조회한다.", 6, 1),
    ("EQ", "앱 시작 게이트 판정",
     "device_state.device_id 존재 여부로 온보딩 스킵/최초 동기화/바로 홈 중 시작 목적지를 "
     "판정한다.", 2, 1),
    ("EQ", "일정·복약 로컬 목록 조회", "오늘의 일정·복약 항목을 로컬 캐시에서 조회한다.", 8, 1),
    ("EO", "홈 화면 통계 집계",
     "완성 챕터 수·연속 대화일수·미회고 사진 수를 3개 로컬 저장소(autobiography_fts, "
     "conversations, unrecalled_photos)를 가로질러 집계해 산출한다.", 3, 3),
]

# ────────────────────────────────────────────────────────────────────────────
# 데이터: 일반시스템특성(GSC) 14개 — VAF 산정
# ────────────────────────────────────────────────────────────────────────────

GSC = [
    ("데이터 통신(Data Communications)", 4,
     "Wi-Fi 등록망 한정 배치 동기화(REST, TLS) — 실시간 스트리밍은 아니나 다자간(모바일↔서버) "
     "통신이 핵심 아키텍처."),
    ("분산 데이터 처리(Distributed Data Processing)", 5,
     "온디바이스(오프라인 우선)-온프레미스 서버 하이브리드로 처리가 명확히 분산 — 동일 기능을 "
     "양쪽에서 독립 구현(모바일 FTS5 vs 서버 Qdrant 하이브리드서치)."),
    ("성능(Performance)", 4,
     "실시간 대화 응답속도 목표치 명시(VAD 800ms, 문장단위 스트리밍 TTS 등, 저사양 단말 "
     "제약 하 성능 최적화 요구 큼)."),
    ("과부하 운영환경(Heavily Used Configuration)", 3,
     "RAM 4GB급 저사양·재활용 키오스크 단말 대응이 요구사항."),
    ("트랜잭션 처리율(Transaction Rate)", 2,
     "동시 대량 트랜잭션 요구는 낮음(개인/소규모 시설 단위 사용)."),
    ("온라인 데이터 입력(Online Data Entry)", 5,
     "구술 대화·사진 업로드·동의·감수 등 대부분 기능이 온라인 실시간 입력 기반."),
    ("최종사용자 효율성(End-User Efficiency)", 4,
     "고령자 접근성(BODY 20px 등 최소기준), 원터치 마이크 응답 등 최종사용자 효율 요구 높음."),
    ("온라인 갱신(Online Update)", 4,
     "챕터 감수, 동의 기록, 사진 배치, 일정 응답 등 대부분 온라인 즉시 갱신."),
    ("복잡한 처리(Complex Processing)", 5,
     "RAG 하이브리드 서치·지식그래프·LLM 챕터 생성/Compaction/Critic 평가·PII 필드 암호화· "
     "crypto-shredding 등 처리 로직이 매우 복잡."),
    ("재사용성(Reusability)", 3,
     "모듈러 모놀리스 + 4계층(api/application/domain/infrastructure) 패턴을 도메인 모듈 "
     "단위로 반복해 재사용성을 설계에 반영."),
    ("설치 용이성(Installation Ease)", 3,
     "설치모드(키오스크/일반) 자동 분기, Device Owner 자동 잠금 등 설치 자동화 수준 보통 이상."),
    ("운영 용이성(Operational Ease)", 4,
     "self-hosted 관측 스택(GlitchTip+Prometheus+Grafana+Loki), 자동 백업, 헬스체크 등 "
     "운영 편의 기능 충실."),
    ("다중 사이트(Multiple Sites)", 3,
     "B2C 개인 사용자 + B2G 시설(요양원·복지관) 다중 환경, 시설 테넌시 안전망 존재."),
    ("변경 용이성(Facilitate Change)", 4,
     "import-linter로 모듈 경계를 CI에서 강제, 신규 카테고리/정책을 코드 배포 없이 DB "
     "설정으로 조정 가능하게 설계(retention_policies 등)."),
]

assert len(GSC) == 14
TDI = sum(score for _, score, _ in GSC)
VAF = round(0.65 + TDI * 0.01, 2)

# ────────────────────────────────────────────────────────────────────────────
# 워크북 조립
# ────────────────────────────────────────────────────────────────────────────

wb = Workbook()
wb.remove(wb.active)

# 계산 결과를 누적할 컨테이너 (FP집계 시트에서 참조)
ufp_totals = {}  # {"ILF_서버": (건수, FP합계), ...}


def build_ilf_eif_sheet(sheet_name, title, rows, weight_table, kind_label):
    """ILF/EIF 목록 시트를 만들고 (건수, FP합계)를 반환한다."""
    ws = wb.create_sheet(sheet_name)
    ncols = 8
    sheet_title(ws, title, ncols)
    ws.row_dimensions[2].height = 4
    headers = ["No", "구분", "논리파일명", "대응 테이블/저장소", "DET", "RET", "복잡도", "가중치(FP)"]
    for i, h in enumerate(headers, start=1):
        ws.cell(row=3, column=i, value=h)
    style_header_row(ws, 3, ncols)

    total_fp = 0
    r = 4
    for name_kr, table, det, ret, desc in rows:
        complexity = ilf_eif_complexity(det, ret)
        weight = weight_table[complexity]
        total_fp += weight
        ws.cell(row=r, column=1, value=r - 3)
        ws.cell(row=r, column=2, value=kind_label)
        ws.cell(row=r, column=3, value=name_kr)
        ws.cell(row=r, column=4, value=table)
        ws.cell(row=r, column=5, value=det)
        ws.cell(row=r, column=6, value=ret)
        ws.cell(row=r, column=7, value=complexity)
        ws.cell(row=r, column=8, value=weight)
        r += 1
    last_data_row = r - 1

    # 설명 행을 별도로 병합된 넓은 셀에 추가(표 하단 상세설명 블록) — 가독성을 위해
    # "번호 - 논리파일명: 설명" 형태로 목록화한다.
    r += 1
    ws.cell(row=r, column=1, value="상세 설명").font = SUB_FONT
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
    ws.cell(row=r, column=1).fill = SUB_FILL
    r += 1
    desc_start = r
    for idx, (name_kr, table, det, ret, desc) in enumerate(rows, start=1):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
        cell = ws.cell(row=r, column=1, value=f"{idx}. {name_kr} ({table}) — {desc}")
        cell.font = BODY_FONT
        cell.alignment = WRAP
        ws.row_dimensions[r].height = 28
        r += 1
    desc_end = r - 1

    # 합계 행
    r += 1
    ws.cell(row=r, column=1, value="합계").font = SUB_FONT
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.cell(row=r, column=1).fill = SUB_FILL
    ws.cell(row=r, column=1).alignment = CENTER
    cnt_cell = ws.cell(row=r, column=7, value=len(rows))
    fp_cell = ws.cell(row=r, column=8, value=f"=SUM(H4:H{last_data_row})")
    for c in (7, 8):
        ws.cell(row=r, column=c).font = SUB_FONT
        ws.cell(row=r, column=c).fill = SUB_FILL
        ws.cell(row=r, column=c).alignment = CENTER

    style_data_rows(ws, 4, last_data_row, ncols, wrap_cols={3, 4})
    set_col_widths(ws, {1: 5, 2: 7, 3: 22, 4: 26, 5: 7, 6: 7, 7: 10, 8: 11})
    ws.freeze_panes = "A4"
    ufp_totals[sheet_name] = (len(rows), total_fp)
    return total_fp


def build_tx_sheet(sheet_name, title, rows, has_method_path, weights):
    """EI/EO/EQ 트랜잭션 기능 목록 시트. rows는 구분 컬럼을 포함한 혼합 목록이거나
    (server) method/path를 포함한 목록일 수 있다."""
    ws = wb.create_sheet(sheet_name)
    if has_method_path:
        ncols = 9
        headers = ["No", "구분", "Method", "Path", "기능명", "상세 설명", "DET", "FTR", "가중치(FP)"]
        wrap_cols = {5, 6}
        width_map = {1: 5, 2: 6, 3: 8, 4: 30, 5: 22, 6: 55, 7: 6, 8: 6, 9: 11}
    else:
        ncols = 7
        headers = ["No", "구분", "기능명", "상세 설명", "DET", "FTR", "가중치(FP)"]
        wrap_cols = {3, 4}
        width_map = {1: 5, 2: 6, 3: 26, 4: 55, 5: 6, 6: 6, 7: 11}

    sheet_title(ws, title, ncols)
    ws.row_dimensions[2].height = 4
    for i, h in enumerate(headers, start=1):
        ws.cell(row=3, column=i, value=h)
    style_header_row(ws, 3, ncols)

    r = 4
    ei_total = eo_total = eq_total = 0
    ei_n = eo_n = eq_n = 0
    for row in rows:
        if has_method_path:
            kind, method, path, name_kr, desc, det, ftr = row
        else:
            kind, name_kr, desc, det, ftr = row

        if kind == "EI":
            complexity = ei_complexity(det, ftr)
            weight = EI_WEIGHT[complexity]
            ei_total += weight
            ei_n += 1
        else:
            complexity = eo_eq_complexity(det, ftr)
            weight = (EO_WEIGHT if kind == "EO" else EQ_WEIGHT)[complexity]
            if kind == "EO":
                eo_total += weight
                eo_n += 1
            else:
                eq_total += weight
                eq_n += 1

        c = 1
        ws.cell(row=r, column=c, value=r - 3); c += 1
        ws.cell(row=r, column=c, value=kind); c += 1
        if has_method_path:
            ws.cell(row=r, column=c, value=method); c += 1
            ws.cell(row=r, column=c, value=path); c += 1
        ws.cell(row=r, column=c, value=name_kr); c += 1
        ws.cell(row=r, column=c, value=desc); c += 1
        ws.cell(row=r, column=c, value=det); c += 1
        ws.cell(row=r, column=c, value=ftr); c += 1
        ws.cell(row=r, column=c, value=weight)
        r += 1
    last_data_row = r - 1

    r += 1
    ws.cell(row=r, column=1, value="구분별 합계").font = SUB_FONT
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
    ws.cell(row=r, column=1).fill = SUB_FILL
    r += 1
    for kind, n, total in (("EI", ei_n, ei_total), ("EO", eo_n, eo_total), ("EQ", eq_n, eq_total)):
        if n == 0:
            continue
        ws.cell(row=r, column=1, value=kind).font = SUB_FONT
        ws.cell(row=r, column=2, value=f"{n}건").font = BODY_FONT
        ws.cell(row=r, column=ncols, value=total).font = SUB_FONT
        r += 1

    style_data_rows(ws, 4, last_data_row, ncols, wrap_cols=wrap_cols)
    set_col_widths(ws, width_map)
    ws.freeze_panes = "A4"
    key = sheet_name
    ufp_totals[key] = (ei_n + eo_n + eq_n, ei_total + eo_total + eq_total)
    return ei_total + eo_total + eq_total, (ei_n, ei_total), (eo_n, eo_total), (eq_n, eq_total)


# ── 1. 표지 ──────────────────────────────────────────────────────────────────
ws = wb.create_sheet("표지")
wb.move_sheet("표지", offset=-len(wb.sheetnames))
ncols = 6
sheet_title(ws, "은빛실타래(SilverYarn) FP 기반 SW개발비 산정 내역서", ncols)
ws.row_dimensions[1].height = 32

info_rows = [
    ("프로젝트명", "은빛실타래(SilverYarn) — 어르신 자서전 제작 및 AI 말벗돌봄 플랫폼"),
    ("산정 기준일", TODAY.strftime("%Y-%m-%d")),
    ("적용 방법론", "IFPUG(FPA) 기능점수 방식 — 「소프트웨어산업 진흥법」 제19조 및 한국소프트웨어산업협회 "
     "「소프트웨어사업 대가산정 가이드」의 기능점수(FP) 산정 방식과 동일한 절차를 적용"),
    ("산정 근거 문서", "docs/01-plan/schema.md(v1.17), docs/01-plan/mobile-schema.md(v0.11), "
     "docs/02-design/features/silveryarn-platform.design.md(v0.52), 실행 중인 백엔드 OpenAPI 스펙(46개 엔드포인트)"),
    ("산정 범위", "① 서버 백엔드(FastAPI, services/backend) API 46종 + 데이터저장소 23종\n"
     "② 모바일(Android) 온디바이스 로컬 기능 14종 + 로컬 저장소 6종\n"
     "※ 웹(apps/web)·관리자(apps/admin) 콘솔은 위 서버 기능을 그대로 소비하는 화면이라 "
     "IFPUG 원칙상 별도 기능점수를 산정하지 않음(동일 업무기능 중복계산 배제)"),
    ("제외 범위", "구독·결제 도메인(스코프아웃, decisions.md #18), 정서 모니터링 알림 발송 로직"
     "(Phase 1 피처플래그 OFF, decisions.md #52/#55), 출판 조판 엔진 세부 구현(Phase 3 예정)"),
    ("⚠️ 확인 필요 사항", "[SW개발비산정] 시트의 'FP당 단가'는 한국소프트웨어산업협회가 매년 실측 공표하는 "
     "값을 넣어야 하는 자리로, 이 문서에는 예시값만 넣어 두었다. 실제 사업 대가 산정/계약 시 반드시 "
     "최신 공표자료로 교체할 것."),
]
r = 3
for label, value in info_rows:
    ws.cell(row=r, column=1, value=label).font = SUB_FONT
    ws.cell(row=r, column=1).fill = SUB_FILL
    ws.cell(row=r, column=1).alignment = Alignment(vertical="top", horizontal="left", wrap_text=True)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=ncols)
    vcell = ws.cell(row=r, column=2, value=value)
    vcell.font = BODY_FONT
    vcell.alignment = WRAP
    n_lines = value.count("\n") + 1 + len(value) // 80
    ws.row_dimensions[r].height = max(20, 15 * n_lines)
    ws.cell(row=r, column=1).border = BORDER
    vcell.border = BORDER
    r += 2
set_col_widths(ws, {1: 16, 2: 16, 3: 16, 4: 16, 5: 16, 6: 16})
ws.column_dimensions["A"].width = 16

r += 1
ws.cell(row=r, column=1, value="산정 절차 요약(IFPUG CPM)").font = H1_FONT
ws.cell(row=r, column=1).fill = H1_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
r += 1
steps = [
    "① 데이터기능(ILF 내부논리파일 / EIF 외부연계파일)과 트랜잭션기능(EI 외부입력 / EO 외부출력 / EQ 외부조회)을 식별한다.",
    "② 기능별 DET(사용자 인식 가능 필드 수)·RET(레코드 그룹 수) 또는 FTR(참조 파일 수)를 산정한다.",
    "③ IFPUG 표준 복잡도 매트릭스로 Low/Average/High를 판정하고 가중치를 부여한다.",
    "④ 미조정 기능점수(UFP) = 전체 기능 가중치의 합.",
    "⑤ 14개 일반시스템특성(GSC)에 0~5점을 매겨 총점(TDI)을 구하고, 보정계수 VAF = 0.65 + (TDI × 0.01).",
    "⑥ 조정 기능점수(AFP) = UFP × VAF.",
    "⑦ SW개발비 = AFP × FP당 단가 × (1 + 이윤율) [+ 직접경비].",
]
for s in steps:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
    cell = ws.cell(row=r, column=1, value=s)
    cell.font = BODY_FONT
    cell.alignment = WRAP
    r += 1

r += 1
ws.cell(row=r, column=1, value="시트 구성").font = H1_FONT
ws.cell(row=r, column=1).fill = H1_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
r += 1
sheet_desc = [
    ("ILF_서버", "서버가 유지보수하는 내부논리파일(DB 테이블 19종 + 비RDB 저장소 3종) 22건"),
    ("EIF_서버", "서버가 참조만 하는 외부연계파일(Keycloak) 1건"),
    ("기능_서버", "서버 API 46종을 EI/EO/EQ로 분류·산정"),
    ("ILF_모바일", "모바일 온디바이스 로컬 저장소(Room/SQLite) 6종"),
    ("기능_모바일", "모바일 온디바이스 로컬 기능 14종을 EI/EO/EQ로 분류·산정"),
    ("VAF산정", "14개 일반시스템특성 평가 및 보정계수 계산"),
    ("FP집계", "전체 UFP·VAF·AFP 집계"),
    ("SW개발비산정", "AFP를 원화 금액으로 환산 — FP단가·이윤율 등 조정 가능한 입력 셀 포함"),
]
for name, desc in sheet_desc:
    ws.cell(row=r, column=1, value=name).font = SUB_FONT
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=ncols)
    ws.cell(row=r, column=2, value=desc).font = BODY_FONT
    r += 1

# ── 2~6. 기능 목록 시트 ────────────────────────────────────────────────────
build_ilf_eif_sheet("ILF_서버", "서버 내부논리파일(ILF) 목록", ILF_SERVER, ILF_WEIGHT, "ILF")
build_ilf_eif_sheet("EIF_서버", "서버 외부연계파일(EIF) 목록", EIF_SERVER, EIF_WEIGHT, "EIF")
build_tx_sheet("기능_서버", "서버 트랜잭션 기능(EI/EO/EQ) 목록 — API 46종", TX_SERVER, has_method_path=True, weights=None)
build_ilf_eif_sheet("ILF_모바일", "모바일 온디바이스 내부논리파일(ILF) 목록", ILF_MOBILE, ILF_WEIGHT, "ILF")
build_tx_sheet("기능_모바일", "모바일 온디바이스 트랜잭션 기능(EI/EO/EQ) 목록", TX_MOBILE, has_method_path=False, weights=None)

# ── 7. VAF산정 ────────────────────────────────────────────────────────────
ws = wb.create_sheet("VAF산정")
ncols = 3
sheet_title(ws, "일반시스템특성(GSC) 평가 및 보정계수(VAF) 산정", ncols)
ws.row_dimensions[2].height = 4
headers = ["일반시스템특성(General System Characteristics)", "영향도(0~5)", "산정 근거"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=3, column=i, value=h)
style_header_row(ws, 3, ncols)
r = 4
for name, score, note in GSC:
    ws.cell(row=r, column=1, value=name)
    ws.cell(row=r, column=2, value=score)
    ws.cell(row=r, column=3, value=note)
    r += 1
last = r - 1
style_data_rows(ws, 4, last, ncols, wrap_cols={1, 3})

r += 1
ws.cell(row=r, column=1, value="총점(TDI, Total Degree of Influence)").font = SUB_FONT
ws.cell(row=r, column=1).fill = SUB_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
tdi_cell = ws.cell(row=r, column=3, value=f"=SUM(B4:B{last})")
tdi_cell.font = SUB_FONT
tdi_cell.fill = SUB_FILL
tdi_row = r
r += 1
ws.cell(row=r, column=1, value="보정계수 VAF = 0.65 + (TDI × 0.01)").font = RESULT_FONT
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
ws.cell(row=r, column=1).fill = RESULT_FILL
vaf_cell = ws.cell(row=r, column=3, value=f"=0.65+(C{tdi_row}*0.01)")
vaf_cell.font = RESULT_FONT
vaf_cell.fill = RESULT_FILL
vaf_cell.number_format = "0.00"
vaf_row = r
set_col_widths(ws, {1: 34, 2: 12, 3: 60})
ws.freeze_panes = "A4"

# ── 8. FP집계 ─────────────────────────────────────────────────────────────
ws = wb.create_sheet("FP집계")
ncols = 4
sheet_title(ws, "기능점수(FP) 집계", ncols)
ws.row_dimensions[2].height = 4
headers = ["구분", "출처 시트", "건수", "미조정 FP(UFP)"]
for i, h in enumerate(headers, start=1):
    ws.cell(row=3, column=i, value=h)
style_header_row(ws, 3, ncols)

fp_rows = [
    ("서버 ILF", "ILF_서버"),
    ("서버 EIF", "EIF_서버"),
    ("서버 EI/EO/EQ", "기능_서버"),
    ("모바일 ILF", "ILF_모바일"),
    ("모바일 EI/EO/EQ", "기능_모바일"),
]
r = 4
for label, key in fp_rows:
    n, fp = ufp_totals[key]
    ws.cell(row=r, column=1, value=label)
    ws.cell(row=r, column=2, value=key)
    ws.cell(row=r, column=3, value=n)
    ws.cell(row=r, column=4, value=fp)
    r += 1
last = r - 1
style_data_rows(ws, 4, last, ncols)

r += 1
ws.cell(row=r, column=1, value="미조정 기능점수 합계(UFP)").font = SUB_FONT
ws.cell(row=r, column=1).fill = SUB_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
ufp_cell = ws.cell(row=r, column=4, value=f"=SUM(D4:D{last})")
ufp_cell.font = SUB_FONT
ufp_cell.fill = SUB_FILL
ufp_row = r

r += 1
ws.cell(row=r, column=1, value="보정계수(VAF)").font = SUB_FONT
ws.cell(row=r, column=1).fill = SUB_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
vaf_ref_cell = ws.cell(row=r, column=4, value=f"=VAF산정!C{vaf_row}")
vaf_ref_cell.font = SUB_FONT
vaf_ref_cell.fill = SUB_FILL
vaf_ref_cell.number_format = "0.00"
vaf_ref_row = r

r += 1
ws.cell(row=r, column=1, value="조정 기능점수(AFP = UFP × VAF)").font = RESULT_FONT
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
ws.cell(row=r, column=1).fill = RESULT_FILL
afp_cell = ws.cell(row=r, column=4, value=f"=D{ufp_row}*D{vaf_ref_row}")
afp_cell.font = RESULT_FONT
afp_cell.fill = RESULT_FILL
afp_cell.number_format = "0.00"
afp_row = r
set_col_widths(ws, {1: 22, 2: 20, 3: 10, 4: 16})
ws.freeze_panes = "A4"
fp_afp_ref = f"FP집계!D{afp_row}"
fp_ufp_ref = f"FP집계!D{ufp_row}"

# ── 9. SW개발비산정 ───────────────────────────────────────────────────────
ws = wb.create_sheet("SW개발비산정")
ncols = 3
sheet_title(ws, "SW개발비 산정 (「소프트웨어사업 대가산정 가이드」 FP 방식)", ncols)
ws.row_dimensions[2].height = 4

r = 3
ws.cell(row=r, column=1, value="산식: SW개발비 = 조정기능점수(AFP) × FP당 단가 × (1 + 이윤율) + 직접경비").font = SUB_FONT
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
ws.cell(row=r, column=1).fill = SUB_FILL
r += 2

def kv_row(row, label, value, is_input=False, is_result=False, number_format=None, note=None):
    ws.cell(row=row, column=1, value=label).font = SUB_FONT if not is_result else RESULT_FONT
    ws.cell(row=row, column=1).border = BORDER
    if is_result:
        ws.cell(row=row, column=1).fill = RESULT_FILL
    vcell = ws.cell(row=row, column=2, value=value)
    vcell.border = BORDER
    if is_input:
        vcell.font = INPUT_FONT
        vcell.fill = INPUT_FILL
    elif is_result:
        vcell.font = RESULT_FONT
        vcell.fill = RESULT_FILL
    else:
        vcell.font = BODY_FONT
    if number_format:
        vcell.number_format = number_format
    if note:
        ncell = ws.cell(row=row, column=3, value=note)
        ncell.font = NOTE_FONT
        ncell.alignment = WRAP
        ncell.border = BORDER
    return vcell


r_ufp = r
kv_row(r, "① 미조정 기능점수(UFP)", f"={fp_ufp_ref}", note="FP집계 시트 참조")
r += 1
r_vaf = r
kv_row(r, "② 보정계수(VAF)", f"=VAF산정!C{vaf_row}", note="14개 일반시스템특성 평가 결과(FP집계/VAF산정 시트 참조)", number_format="0.00")
r += 1
r_afp = r
afp_row_cell = kv_row(r, "③ 조정 기능점수(AFP = ①×②)", f"={fp_afp_ref}", is_result=True, number_format="0.00")
r += 2

r_price = r
kv_row(r, "④ FP당 단가(원/FP)", 500000, is_input=True, number_format="#,##0",
       note="★ 예시값 — 실제 사업 대가 산정 시 한국소프트웨어산업협회가 공표하는 최신 "
            "'소프트웨어사업 대가산정 가이드'의 기능점수당 단가로 반드시 교체할 것. "
            "이 셀만 바꾸면 아래 전체 금액이 자동 재계산된다.")
r += 1
r_cost = r
kv_row(r, "⑤ 소프트웨어 개발원가(③×④)", f"=B{r_afp}*B{r_price}", is_result=True, number_format="#,##0")
r += 2

r_profit_rate = r
kv_row(r, "⑥ 이윤율", 0.25, is_input=True, number_format="0%",
       note="★ 예시값(25%) — 사업 유형·협상에 따라 조정. 공공 SW사업은 통상 이윤율 상한 "
            "가이드라인을 따른다.")
r += 1
r_profit = r
kv_row(r, "⑦ 이윤(⑤×⑥)", f"=B{r_cost}*B{r_profit_rate}", number_format="#,##0")
r += 1
r_direct = r
kv_row(r, "⑧ 직접경비", 0, is_input=True, number_format="#,##0",
       note="★ 예시값(0원) — DBMS/상용 라이선스, GPU 서버 등 하드웨어, 외부 인증·인프라 "
            "비용 등 실제 조달 항목이 있으면 별도 산정해 입력. 본 문서는 온프레미스 "
            "자체 인프라(Zero External Data Egress 원칙)를 전제해 0으로 둠.")
r += 1
r_total = r
kv_row(r, "⑨ SW개발비 합계(⑤+⑦+⑧, 부가세 별도)", f"=B{r_cost}+B{r_profit}+B{r_direct}",
       is_result=True, number_format="#,##0")
last = r

style_data_rows(ws, r_ufp, r_ufp, ncols)
set_col_widths(ws, {1: 34, 2: 18, 3: 62})
for row in range(r_ufp, last + 1):
    ws.row_dimensions[row].height = 30
ws.freeze_panes = "A3"

r = last + 3
ws.cell(row=r, column=1, value="참고 — 산정 범위별 UFP 구성").font = H1_FONT
ws.cell(row=r, column=1).fill = H1_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
r += 1
ws.cell(row=r, column=1, value="구분").font = HEADER_FONT
ws.cell(row=r, column=2, value="UFP").font = HEADER_FONT
ws.cell(row=r, column=3, value="비중").font = HEADER_FONT
for c in (1, 2, 3):
    ws.cell(row=r, column=c).fill = HEADER_FILL
    ws.cell(row=r, column=c).border = BORDER
    ws.cell(row=r, column=c).alignment = CENTER
header_r = r
r += 1
breakdown_start = r
for label, key in fp_rows:
    n, fp = ufp_totals[key]
    ws.cell(row=r, column=1, value=label).font = BODY_FONT
    ws.cell(row=r, column=2, value=fp).font = BODY_FONT
    pct_cell = ws.cell(row=r, column=3, value=f"=B{r}/B{r_ufp}")
    pct_cell.number_format = "0.0%"
    pct_cell.font = BODY_FONT
    for c in (1, 2, 3):
        ws.cell(row=r, column=c).border = BORDER
    r += 1

import os
_here = os.path.dirname(os.path.abspath(__file__))
wb.save(os.path.join(_here, "silveryarn-platform.fp-cost-estimate.xlsx"))
print("UFP total:", ufp_totals)
print("TDI:", TDI, "VAF:", VAF)
print("Saved.")

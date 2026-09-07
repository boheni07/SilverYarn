# -*- coding: utf-8 -*-
"""
은빛실타래(SilverYarn) 개발팀 착수회의 발표자료 생성 스크립트
Source of truth: docs/01-plan/*, docs/02-design/*, CLAUDE.md, CONVENTIONS.md, Plan/*
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

# ---------------------------------------------------------------- palette
INK = RGBColor(0x20, 0x24, 0x2B)
INK_MUTED = RGBColor(0x5B, 0x64, 0x72)
INK_FAINT = RGBColor(0x90, 0x96, 0xA0)
PAPER = RGBColor(0xF4, 0xF2, 0xEE)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
SUBTLE = RGBColor(0xEC, 0xE8, 0xE1)
BORDER = RGBColor(0xDE, 0xDA, 0xCF)
TEAL = RGBColor(0x1E, 0x7A, 0x8C)
TEAL_DEEP = RGBColor(0x15, 0x5C, 0x6B)
TEAL_TINT = RGBColor(0xE4, 0xF0, 0xF2)
SILVER = RGBColor(0x8E, 0x97, 0xA6)
SILVER_DEEP = RGBColor(0x4B, 0x55, 0x63)
GOLD = RGBColor(0xB8, 0x93, 0x5A)
GOLD_DEEP = RGBColor(0x96, 0x72, 0x3F)
GOLD_TINT = RGBColor(0xF3, 0xE9, 0xD8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xB8, 0x49, 0x3F)
GREEN = RGBColor(0x2E, 0x7D, 0x5B)

FONT = "맑은 고딕"
FONT_BOLD = "맑은 고딕"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height

PAGE_NO = [0]


def new_slide(bg=PAPER):
    s = prs.slides.add_slide(BLANK)
    bgfill = s.background.fill
    bgfill.solid()
    bgfill.fore_color.rgb = bg
    PAGE_NO[0] += 1
    return s


def add_footer(slide, label="은빛실타래 · SilverYarn"):
    tb = slide.shapes.add_textbox(Inches(0.5), SH - Inches(0.4), Inches(6), Inches(0.3))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = label
    r.font.size = Pt(10)
    r.font.color.rgb = INK_FAINT
    r.font.name = FONT
    pn = slide.shapes.add_textbox(SW - Inches(1.2), SH - Inches(0.4), Inches(0.8), Inches(0.3))
    p2 = pn.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run()
    r2.text = str(PAGE_NO[0])
    r2.font.size = Pt(10)
    r2.font.color.rgb = INK_FAINT
    r2.font.name = FONT


def set_text(tf, text, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT, font=FONT, line_spacing=1.15):
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.name = font
    return p


def add_rect(slide, x, y, w, h, fill=TEAL, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp


def title_bar(slide, kicker, title):
    add_rect(slide, 0, 0, SW, Inches(1.15), fill=INK)
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.12), SW - Inches(1.1), Inches(0.35))
    set_text(tb.text_frame, kicker, size=13, color=GOLD, bold=True)
    tb2 = slide.shapes.add_textbox(Inches(0.5), Inches(0.42), SW - Inches(1.0), Inches(0.7))
    set_text(tb2.text_frame, title, size=26, color=WHITE, bold=True)


def add_title_slide():
    s = new_slide(bg=INK)
    add_rect(s, 0, SH - Inches(0.12), SW, Inches(0.12), fill=TEAL)
    add_rect(s, 0, Inches(0), Inches(0.12), SH, fill=GOLD)
    tb = s.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(11), Inches(0.5))
    set_text(tb.text_frame, "개발팀 착수회의 (Kickoff Meeting)", size=18, color=GOLD, bold=True)
    tb2 = s.shapes.add_textbox(Inches(1.0), Inches(2.65), Inches(11), Inches(1.3))
    set_text(tb2.text_frame, "은빛실타래", size=54, color=WHITE, bold=True)
    tb3 = s.shapes.add_textbox(Inches(1.0), Inches(3.55), Inches(11), Inches(0.6))
    set_text(tb3.text_frame, "SilverYarn — 어르신 자서전 제작 및 AI 말벗돌봄 플랫폼", size=22, color=SILVER)
    tb4 = s.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(11), Inches(0.5))
    set_text(tb4.text_frame, "온디바이스(오프라인 우선) × 온프레미스 서버 하이브리드 아키텍처", size=15, color=TEAL_TINT)
    tb5 = s.shapes.add_textbox(Inches(1.0), Inches(6.55), Inches(11), Inches(0.5))
    set_text(tb5.text_frame, "2026년 9월 · NUBiz AX(AI Transformation) Initiative", size=14, color=INK_FAINT)
    return s


def add_section_divider(no, title, sub=""):
    s = new_slide(bg=TEAL)
    tb = s.shapes.add_textbox(Inches(1.0), Inches(2.7), Inches(4), Inches(1.2))
    set_text(tb.text_frame, f"{no:02d}", size=60, color=TEAL_DEEP, bold=True)
    tb2 = s.shapes.add_textbox(Inches(1.0), Inches(3.7), Inches(11), Inches(1.0))
    set_text(tb2.text_frame, title, size=36, color=WHITE, bold=True)
    if sub:
        tb3 = s.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11), Inches(0.6))
        set_text(tb3.text_frame, sub, size=16, color=TEAL_TINT)
    add_footer(s, "은빛실타래 · SilverYarn")
    return s


def add_bullets_slide(kicker, title, bullets, note=None):
    """bullets: list of (text, level, bold, color) — level 0/1, color optional"""
    s = new_slide()
    title_bar(s, kicker, title)
    box = s.shapes.add_textbox(Inches(0.7), Inches(1.5), SW - Inches(1.4), SH - Inches(2.1))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for item in bullets:
        text, level = item[0], item[1]
        bold = item[2] if len(item) > 2 else False
        color = item[3] if len(item) > 3 else INK
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = 0
        p.space_after = Pt(10 if level == 0 else 4)
        prefix = "▪  " if level == 0 else "-  "
        indent = Inches(0) if level == 0 else Inches(0.35)
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = prefix + text
        r.font.size = Pt(19 if level == 0 else 16)
        r.font.bold = bold
        r.font.color.rgb = color if level == 0 else INK_MUTED
        r.font.name = FONT
        # manual indent via paragraph_format not directly supported per-run; use tab via level marker string offset
        if level == 1:
            p.text = "     " + p.runs[0].text
            p.runs[0].text = p.runs[0].text  # no-op, keep
    if note:
        nb = s.shapes.add_textbox(Inches(0.7), SH - Inches(1.15), SW - Inches(1.4), Inches(0.6))
        set_text(nb.text_frame, note, size=13, color=GOLD_DEEP, bold=True)
    add_footer(s)
    return s


def add_table_slide(kicker, title, headers, rows, col_widths=None, note=None, font_size=13):
    s = new_slide()
    title_bar(s, kicker, title)
    n_cols = len(headers)
    n_rows = len(rows) + 1
    left = Inches(0.6)
    top = Inches(1.45)
    width = SW - Inches(1.2)
    height = Inches(0.5) * n_rows if Inches(0.5) * n_rows < SH - Inches(2.2) else SH - Inches(2.2)
    gtable = s.shapes.add_table(n_rows, n_cols, left, top, width, height).table
    if col_widths:
        total = sum(col_widths)
        for i, w in enumerate(col_widths):
            gtable.columns[i].width = Emu(int(width * (w / total)))
    for c, h in enumerate(headers):
        cell = gtable.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = INK
        cell.text_frame.word_wrap = True
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = h
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.name = FONT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_top = Pt(4)
        cell.margin_bottom = Pt(4)
    for ridx, row in enumerate(rows, start=1):
        rowfill = SURFACE if ridx % 2 == 1 else TEAL_TINT
        for c, val in enumerate(row):
            cell = gtable.cell(ridx, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rowfill
            cell.text_frame.word_wrap = True
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c > 0 else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(font_size)
            r.font.color.rgb = INK
            r.font.name = FONT
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Pt(6)
            cell.margin_top = Pt(3)
            cell.margin_bottom = Pt(3)
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


def add_flow_slide(kicker, title, steps, note=None):
    """steps: list[str] vertical numbered flow with connecting arrows"""
    s = new_slide()
    title_bar(s, kicker, title)
    n = len(steps)
    top = Inches(1.5)
    avail_h = SH - Inches(2.3)
    box_h = min(Inches(0.72), Emu(int(avail_h / n) - Inches(0.12)))
    gap = Emu(int((avail_h - box_h * n) / max(n - 1, 1))) if n > 1 else Inches(0)
    y = top
    left = Inches(1.0)
    width = SW - Inches(2.0)
    for i, step in enumerate(steps):
        box = add_rect(s, left, y, width, box_h, fill=SURFACE, line=BORDER)
        numchip = add_rect(s, left, y, Inches(0.55), box_h, fill=TEAL)
        ntf = numchip.text_frame
        ntf.word_wrap = True
        p = ntf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(i + 1)
        r.font.size = Pt(18)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.name = FONT
        numchip.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        txt = box.text_frame
        txt.word_wrap = True
        txt.margin_left = Inches(0.75)
        txt.vertical_anchor = MSO_ANCHOR.MIDDLE
        p2 = txt.paragraphs[0]
        r2 = p2.add_run()
        r2.text = step
        r2.font.size = Pt(15)
        r2.font.color.rgb = INK
        r2.font.name = FONT
        if i < n - 1:
            arrow_y = Emu(int(y) + int(box_h) + int(gap) // 2 - Inches(0.09))
            arr = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Emu(int(left) + int(width) // 2 - Inches(0.09)), arrow_y, Inches(0.18), Inches(0.18))
            arr.fill.solid(); arr.fill.fore_color.rgb = GOLD; arr.line.fill.background(); arr.shadow.inherit = False
        y = Emu(int(y) + int(box_h) + int(gap))
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


def add_boxes_slide(kicker, title, boxes, note=None):
    """boxes: list of dict(x,y,w,h in inches, text, fill, textcolor) for free-form diagrams"""
    s = new_slide()
    title_bar(s, kicker, title)
    for b in boxes:
        shp = add_rect(s, Inches(b["x"]), Inches(b["y"]), Inches(b["w"]), Inches(b["h"]), fill=b.get("fill", SURFACE), line=b.get("line", BORDER))
        tf = shp.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        lines = b["text"].split("\n")
        for li, line in enumerate(lines):
            p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = line
            r.font.size = Pt(b.get("size", 13))
            r.font.bold = b.get("bold", False)
            r.font.color.rgb = b.get("textcolor", INK)
            r.font.name = FONT
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


def add_arrow(slide, x, y, w, h, direction="down", fill=GOLD):
    shape_map = {
        "down": MSO_SHAPE.DOWN_ARROW,
        "up": MSO_SHAPE.UP_ARROW,
        "right": MSO_SHAPE.RIGHT_ARROW,
        "left": MSO_SHAPE.LEFT_ARROW,
        "updown": MSO_SHAPE.UP_DOWN_ARROW,
    }
    arr = slide.shapes.add_shape(shape_map.get(direction, MSO_SHAPE.DOWN_ARROW), x, y, w, h)
    arr.fill.solid(); arr.fill.fore_color.rgb = fill
    arr.line.fill.background()
    arr.shadow.inherit = False
    return arr


def add_code_slide(kicker, title, code_text, note=None, size=13):
    s = new_slide(bg=INK)
    title_bar(s, kicker, title)
    box = add_rect(s, Inches(0.7), Inches(1.5), SW - Inches(1.4), SH - Inches(2.1), fill=RGBColor(0x15, 0x18, 0x1D), line=None)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3); tf.margin_top = Inches(0.25)
    first = True
    for line in code_text.strip("\n").split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = line if line.strip() != "" else " "
        r.font.size = Pt(size)
        r.font.name = "Consolas"
        r.font.color.rgb = RGBColor(0xE4, 0xF0, 0xF2)
        p.space_after = Pt(2)
    if note:
        nb = s.shapes.add_textbox(Inches(0.7), SH - Inches(0.55), SW - Inches(1.4), Inches(0.4))
        set_text(nb.text_frame, note, size=12, color=GOLD)
    add_footer(s, "은빛실타래 · SilverYarn")
    return s


def add_swatch_slide(kicker, title, swatches, typo_rows):
    s = new_slide()
    title_bar(s, kicker, title)
    x = Inches(0.7)
    y = Inches(1.6)
    w = Inches(1.85)
    h = Inches(1.4)
    gap = Inches(0.15)
    for i, sw in enumerate(swatches):
        bx = Emu(int(x) + i * (int(w) + int(gap)))
        rect = add_rect(s, bx, y, w, h, fill=sw["hex"])
        label = s.shapes.add_textbox(bx, Emu(int(y) + int(h) + Inches(0.05)), w, Inches(0.75))
        tf = label.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = sw["name"]; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = INK; r.font.name = FONT
        p2 = tf.add_paragraph()
        r2 = p2.add_run(); r2.text = sw["hexlabel"]; r2.font.size = Pt(11); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
    ty = Inches(3.5)
    tb = s.shapes.add_textbox(Inches(0.7), ty, Inches(3), Inches(0.4))
    set_text(tb.text_frame, "타입 스케일", size=15, color=GOLD_DEEP, bold=True)
    gtable = s.shapes.add_table(len(typo_rows) + 1, 3, Inches(0.7), Inches(4.0), SW - Inches(1.4), Inches(2.6)).table
    headers = ["레벨", "크기/굵기", "서체"]
    for c, hh in enumerate(headers):
        cell = gtable.cell(0, c)
        cell.fill.solid(); cell.fill.fore_color.rgb = INK
        p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = hh
        r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
    for ridx, row in enumerate(typo_rows, start=1):
        for c, val in enumerate(row):
            cell = gtable.cell(ridx, c)
            cell.fill.solid(); cell.fill.fore_color.rgb = SURFACE if ridx % 2 else TEAL_TINT
            p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = str(val)
            r.font.size = Pt(13); r.font.color.rgb = INK; r.font.name = FONT
    add_footer(s)
    return s


# ================================================================ CONTENT
add_title_slide()

# 목차
add_bullets_slide("Agenda", "목차", [
    ("1부. 프로젝트 개요 — 배경 · 목적 · 대상 사용자 · 서비스 컨셉", 0),
    ("2부. 시스템 아키텍처 — 하이브리드 구조 · 온디바이스/온프레미스 · 설치모드", 0),
    ("3부. 핵심 기능 파이프라인 — 사진회고 · RAG · 정서모니터링 · 출판 · 온보딩", 0),
    ("4부. 데이터 모델 & API 설계", 0),
    ("5부. UI/UX & 디자인 시스템", 0),
    ("6부. 보안 · 컨벤션 · 기술스택", 0),
    ("7부. 의사결정 현황 & 설계 검증 결과 (design-validator)", 0),
    ("8부. CTO팀 검토 의견", 0),
    ("9부. 로드맵 & 착수 실행 계획", 0),
])

# ---------------------------------------------------------------- 1부
add_section_divider(1, "프로젝트 개요", "배경 · 목적 · 대상 사용자 · 서비스 컨셉")

add_table_slide("1부 · 개요", "Executive Summary", ["관점", "내용"], [
    ["Problem", "고령화로 어르신 삶의 기록이 소실되고, 독거·정서적 고립으로 돌봄 공백 확대. 저사양/재활용 단말·비상시 인터넷 환경 고려 필요"],
    ["Solution", "온디바이스 STT/SLM/TTS로 평소 대화를 오프라인 완결, 등록 Wi-Fi 접속 시에만 온프레미스 서버(LLM·RAG·VectorDB)와 배치 동기화"],
    ["Function/UX Effect", "끊김 없는 대화 경험, 사진 기반 자동 회고로 자연스러운 콘텐츠 축적, 단말 사양별 키오스크/일반 자동 설치"],
    ["Core Value", "자서전 제작(입구)→말벗돌봄·비서(체류)로 이어지는 락인 라이프사이클, 초개인화 대화로 범용 챗봇 대비 높은 몰입도"],
], col_widths=[2, 8])

add_bullets_slide("1부 · 개요", "프로젝트 배경", [
    ("고령화 심화로 어르신 삶의 기록이 보존되지 못한 채 소실되는 경우 증가", 0),
    ("독거 및 정서적 고립으로 인한 돌봄 공백 문제 심화", 0),
    ("재활용 스마트폰 등 저비용 단말 활용한 시니어 접근성 개선 요구 증가", 0),
    ("재활용·저사양 단말과 고사양 개인 단말은 하드웨어·사용맥락이 달라 설치방식 자동 분기 구조 필요", 0),
    ("시니어 생활 환경상 상시 인터넷 연결 기대 어려움 → 오프라인 완결 + 자택 등 Wi-Fi 동기화 구조 요구", 0),
])

add_bullets_slide("1부 · 개요", "프로젝트 목적 & 핵심 차별점", [
    ("목적: 온디바이스 음성 인터페이스(VAD·STT·SLM·TTS) + 중앙 서버 생성형 AI(LLM·RAG·VectorDB) 연계", 0),
    ("오프라인 우선(Offline-First): 평상시 대화는 인터넷 연결 없이 온디바이스에서 완결", 1),
    ("Wi-Fi 배치 동기화: 등록 Wi-Fi 접속 시에만 서버 고성능 엔진으로 최신화 후 재동기화", 1),
    ("사진 기반 자동 회고 트리거: 신규 사진을 AI가 먼저 제시하며 자연스러운 회고 유도", 1),
    ("디바이스 사양 기반 설치모드 자동 분기: 저사양은 키오스크, 고사양은 일반 앱 모드", 1),
    ("작가 모드 → 말벗돌봄 모드 → 비서 모드로 이어지는 3단계 라이프사이클 통합 제공", 1),
])

add_table_slide("1부 · 개요", "대상 사용자", ["구분", "설명"], [
    ["1차 사용자", "구술의 주체가 되는 어르신 본인"],
    ["2차 사용자", "자서전을 감수·열람하는 가족, 돌봄 연계가 필요한 요양보호사·복지사"],
    ["잠재 고객", "복지관·요양기관·지자체 등 B2G/B2B 파일럿 운영 주체 (채널 전략: B2C/B2G 병행 추진 확정)"],
], col_widths=[3, 9])

add_table_slide("1부 · 개요", "서비스 컨셉 — 3대 운영 모드", ["모드", "목표", "주요 기능"], [
    ["① 자서전 작가 모드", "연대기적 구술 발굴 및 문학적 초안 생성", "질문 생성기 · 사진 기반 회고 질문 · 심층 인터뷰잉 · 구술체→문어체 정제·챕터 자동귀속"],
    ["② 말벗돌봄 모드", "초개인화 공감 대화 및 고독감 해소", "RAG 기반 추억 회상 · 사진 기반 회고 대화 · 정서 모니터링 및 알림 연동"],
    ["③ 비서 모드", "인지 기능 보조 및 일상 건강·일정 관리", "일정·복약 엔티티 추출·등록 · 지정 시각 능동형 음성 브리핑"],
], col_widths=[3, 4, 6], note="세 모드는 상호 배타적이지 않으며 의도 분류(Intent Classification)로 하나의 대화 흐름 안에서 전환됨")

add_bullets_slide("1부 · 개요", "에이전트 페르소나 정의", [
    ("AuthorAgent — 경청하는 인터뷰어 페르소나 (표시명 미정, 은빛이와 통일 여부 결정 필요)", 0),
    ("CareAgent — 사용자의 일생을 아는 친근한 오랜 벗 페르소나", 0),
    ("표시명 확정: '은빛이' (UI/UX 화면설계서 확정)", 1),
    ("ScheduleAgent — 정확한 확인형 비서 페르소나 (표시명 미정)", 0),
], note="Design 문서 §2.10 — 페르소나 명칭 통일은 Do 단계 전 확정 권장")

# ---------------------------------------------------------------- 2부
add_section_divider(2, "시스템 아키텍처", "온디바이스-온프레미스 하이브리드 구조")

add_bullets_slide("2부 · 아키텍처", "데이터·운영 4원칙", [
    ("원칙 1 (오프라인 우선): 평상시 대화는 인터넷 연결 없이 온디바이스에서 완결, 서버 동기화는 등록 Wi-Fi 접속 시에만", 0),
    ("원칙 2 (전면 온프레미스): 원본 음성·자서전 원고·임베딩 벡터 등 PII 포함 데이터는 100% 자체 GPU 서버(vLLM·A100)·자체 DB에서만 처리", 0),
    ("원칙 3 (제한적·선택적 외부 연계): 외부 클라우드 AI는 비식별화 데이터에 한해, 사용자 명시적 동의(Opt-in) 하에만 연계", 0),
    ("원칙 4 (계약적 통제): 외부 연계 범위는 DPA 체결 및 내부 보안 검토를 통과한 항목으로 한정", 0),
], note="Zero External Data Egress — bkit Enterprise 기본 AWS 템플릿은 적용하지 않음")

add_table_slide("2부 · 아키텍처", "아키텍처 옵션 비교", ["기준", "A. 완전 클라우드", "B. 하이브리드 (선정)", "C. 완전 온디바이스"], [
    ["오프라인 대응", "불가", "가능 (평소 대화 전량 오프라인)", "가능하나 정교화 불가"],
    ["데이터 주권", "취약(상시 전송)", "강함(PII 전량 온프레미스)", "강함(단, 협업·감수 불가)"],
    ["정확도/개인화", "높음(상시 최신)", "높음(Wi-Fi 동기화 시 정교화)", "낮음(저사양 SLM 한계)"],
    ["가족 협업(웹콘솔)", "가능", "가능", "불가"],
    ["결론", "시니어 오프라인 환경 부적합", "★ 선정 — 오프라인+데이터주권+협업 모두 충족", "협업·정교화 기능 상실"],
], col_widths=[2.5, 3, 4, 3])

add_boxes_slide("2부 · 아키텍처", "전체 컴포넌트 다이어그램", [
    {"x": 0.7, "y": 1.6, "w": 4.0, "h": 1.9, "text": "📱 모바일앱\n온디바이스 (오프라인 우선)\nVAD·STT·SLM·TTS\n로컬캐시(최근5일·자서전·FTS5 RAG)", "fill": TEAL_TINT, "size": 13},
    {"x": 5.1, "y": 1.6, "w": 4.2, "h": 1.9, "text": "🖥️ 서버\n전량 온프레미스 (FastAPI)\n작가·말벗돌봄·비서 엔진\nvLLM·A100 · Qdrant · Neo4j · PG · MinIO", "fill": PAPER, "line": TEAL, "size": 12},
    {"x": 9.7, "y": 1.6, "w": 2.9, "h": 1.9, "text": "🖊️ 웹 콘솔\n(Next.js)\n자서전/가족/관리자", "fill": SUBTLE, "size": 13},
    {"x": 0.7, "y": 3.9, "w": 4.0, "h": 1.0, "text": "Wi-Fi 접속 시\n자동 업/다운로드", "fill": GOLD_TINT, "size": 12},
    {"x": 5.1, "y": 3.9, "w": 4.2, "h": 1.0, "text": "인증: Keycloak SSO\nAPI: /api/v1, snake_case", "fill": GOLD_TINT, "size": 12},
    {"x": 9.7, "y": 3.9, "w": 2.9, "h": 1.0, "text": "선택·Opt-in\n외부 고품질 TTS\n(Phase 3)", "fill": SUBTLE, "size": 11},
    {"x": 0.7, "y": 5.3, "w": 11.9, "h": 0.9, "text": "핵심 원칙: 오프라인 우선 + 전면 온프레미스(Zero External Data Egress) + 제한적 선택적 외부연계", "fill": INK, "textcolor": WHITE, "size": 14, "bold": True},
])

# ---- Closed-Loop Architecture 시각화 (신규) ----
s = new_slide()
title_bar(s, "2부 · 아키텍처", "Closed-Loop Architecture — Edge-Cloud 피드백 루프")
add_rect(s, Inches(0.6), Inches(1.35), SW - Inches(1.2), Inches(0.4), fill=TEAL)
tb = s.shapes.add_textbox(Inches(0.6), Inches(1.35), SW - Inches(1.2), Inches(0.4))
set_text(tb.text_frame, "📱 EDGE TIER — 온디바이스 (Low-Latency)", size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
edge_steps = ["VAD", "경량 STT", "FTS5 RAG", "SLM", "Native TTS"]
ew = Emu(int((SW - Inches(1.2) - Inches(0.4) * 4) / 5))
ex = Inches(0.6)
for i, step in enumerate(edge_steps):
    bx = Emu(int(ex) + i * (int(ew) + Inches(0.4)))
    box = add_rect(s, bx, Inches(1.95), ew, Inches(0.85), fill=TEAL_TINT, line=TEAL)
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = step; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = TEAL_DEEP; r.font.name = FONT
    if i < len(edge_steps) - 1:
        add_arrow(s, Emu(int(bx) + int(ew)), Inches(2.2), Inches(0.35), Inches(0.2), direction="right", fill=GOLD)
note1 = s.shapes.add_textbox(Inches(0.6), Inches(2.9), SW - Inches(1.2), Inches(0.35))
set_text(note1.text_frame, "로컬 영속화: Opus(16kbps) 압축 음성 + 대화턴 DB(conversations)", size=12, color=INK_MUTED, align=PP_ALIGN.CENTER)

add_arrow(s, Inches(3.3), Inches(3.35), Inches(1.0), Inches(0.5), direction="down", fill=GOLD)
up_lbl = s.shapes.add_textbox(Inches(4.4), Inches(3.35), Inches(4.0), Inches(0.5))
set_text(up_lbl.text_frame, "▲ 상향: Opus 음성 + 로컬 STT 텍스트", size=12, color=GOLD_DEEP, bold=True)
add_arrow(s, Inches(8.6), Inches(3.35), Inches(1.0), Inches(0.5), direction="up", fill=TEAL)
down_lbl = s.shapes.add_textbox(Inches(4.4), Inches(3.85), Inches(4.0), Inches(0.5))
set_text(down_lbl.text_frame, "▼ 하향: 정제지식·프롬프트·질문셋·일정룰 (Wi-Fi 접속 시)", size=12, color=TEAL_DEEP, bold=True)

add_rect(s, Inches(0.6), Inches(4.5), SW - Inches(1.2), Inches(0.4), fill=INK)
tb2 = s.shapes.add_textbox(Inches(0.6), Inches(4.5), SW - Inches(1.2), Inches(0.4))
set_text(tb2.text_frame, "🖥️ CLOUD TIER — 온프레미스 서버 (Deep Processing)", size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
cloud_steps = [
    ("1. 검증·교정", "Whisper Large-v3\n정밀 재전사"),
    ("2. 지식화", "Neo4j 그래프 +\nQdrant 벡터색인"),
    ("3. 생성·감수", "온프레미스 vLLM 윤문\n+ Critic Agent Gap분석"),
]
cw = Emu(int((SW - Inches(1.2) - Inches(0.4) * 2) / 3))
for i, (t, d) in enumerate(cloud_steps):
    bx = Emu(int(Inches(0.6)) + i * (int(cw) + Inches(0.4)))
    box = add_rect(s, bx, Inches(5.1), cw, Inches(1.0), fill=SURFACE, line=BORDER)
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = t; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = TEAL_DEEP; r.font.name = FONT
    for dline in d.split("\n"):
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = dline; r2.font.size = Pt(11); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
    if i < len(cloud_steps) - 1:
        add_arrow(s, Emu(int(bx) + int(cw)), Inches(5.45), Inches(0.35), Inches(0.2), direction="right", fill=GOLD)
add_arrow(s, Inches(6.3), Inches(6.15), Inches(0.7), Inches(0.3), direction="down", fill=GOLD)
box_pack = add_rect(s, Inches(0.6), Inches(6.5), SW - Inches(1.2), Inches(0.55), fill=GOLD_TINT, line=GOLD)
tfp = box_pack.text_frame; tfp.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tfp.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "4. Compaction Engine — 자서전 요약 FTS5 차분 + 압축 프롬프트 + 우선순위 질문 → 온디바이스 패키징"
r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = GOLD_DEEP; r.font.name = FONT
add_footer(s)

add_flow_slide("2부 · 아키텍처", "데이터 흐름 — 오프라인 구술 → 동기화 → 챕터 반영", [
    "[오프라인] 구술 발화 → On-Device STT/SLM 즉시 응답, 원본음성+1차전사 로컬 저장(최근 5일 잠정)",
    "[Wi-Fi 접속 감지] 자동 업로드(음성+전사+신규사진)",
    "서버: 고정밀 STT 재전사 → 기존 청크와 Diff 비교(멱등성) → 신규분만 처리",
    "청킹/메타태깅 → 임베딩 → Vector DB Upsert → LLM 챕터 초안 생성/갱신",
    "가족 웹 감수 대기열 등록 → (승인) 챕터 확정 & 이력 기록 / (반려) 재생성 루프",
    "자동 다운로드(최신 자서전·RAG스냅샷·사진·질문목록) → 로컬 캐시 갱신",
])

add_table_slide("2부 · 아키텍처", "온디바이스 오프라인 아키텍처", ["구성요소", "내용"], [
    ["On-Device STT/SLM/TTS", "경량 모델로 즉각 응답하는 오프라인 대화 엔진"],
    ["최근 5일 대화 캐시", "최근 5일간 원본 음성 + 전사 텍스트 로컬 보관 (잠정값, 벤치마크 후 재확정)"],
    ["자서전 로컬 캐시", "최신 동기화 시점 기준 자서전 전체 콘텐츠 사본"],
    ["경량 RAG Vector Store", "서버 Vector DB 서브셋을 경량화한 스냅샷 (오프라인 회상 대화용)"],
    ["미회고 사진 큐", "아직 대화로 다루지 않은 신규 사진 목록 — 대화 세션 진입 시 우선 제시"],
    ["질문 목록 캐시", "서버가 정비한 미중복 회고 질문 큐"],
], col_widths=[4, 8])

add_table_slide("2부 · 아키텍처", "온프레미스 서버 아키텍처", ["영역", "구성"], [
    ["LLM 추론", "자체 호스팅 vLLM · A100 서버 — 3개 엔진 전체 처리"],
    ["STT", "온프레미스 고정밀 STT(Whisper 계열)로 온디바이스 1차 전사분 재전사·오류 보정"],
    ["Vector DB", "Qdrant self-hosted — 하이브리드 서치(BM25 + Dense)"],
    ["RDB", "PostgreSQL — 사용자·일정·복약·원고 이력 등 17개 엔티티"],
    ["Object Storage", "자체 MinIO — 원본 음성, 완성 PDF/ePub"],
    ["임베딩 모델", "BGE-M3 계열 (한국어 다국어 임베딩)"],
], col_widths=[3, 9])

add_table_slide("2부 · 아키텍처", "설치모드 자동 분기 — 키오스크 / 일반 앱", ["구분", "키오스크 모드", "일반 앱 모드"], [
    ["대상 단말", "저사양·재활용 단말", "고사양 개인 단말"],
    ["설치 방식", "Device Owner Mode(COSU)로 단일 실행 잠금 ★확정", "여러 앱 중 하나로 아이콘 설치"],
    ["실행 방식", "부팅 시 자동 실행, 다른 앱 접근 차단", "사용자가 직접 실행, 자유 전환"],
    ["앱 기능(3대 모드 등)", "완전히 동일", "완전히 동일"],
    ["모드 결정 시점", "설치 시 1회 자동 판별, 재설치 전까지 고정 — 서버 원격 전환 없음", "좌동"],
])

add_bullets_slide("2부 · 아키텍처", "설치모드 판별 기준 (확정)", [
    ("판별 로직: RAM 6GB 미만 또는 Android 11(API 30) 이하 → 키오스크 모드 (둘 중 하나라도 미달 시 보수적 판정)", 0, True, TEAL_DEEP),
    ("근거: 2B급 SLM+STT+TTS 동시구동 최소 RAM 6GB, 구형 모델(S10/노트10)은 RAM 충분해도 보안업데이트 종료 → OS버전 병행 필요", 0),
    ("실기기 매핑 예시 — 키오스크 대상: 갤럭시 S9/S10/A10~A30, J시리즈", 1),
    ("실기기 매핑 예시 — 일반 앱 대상: 갤럭시 A35/A55/A56, S23/S24/S25", 1),
    ("보조지표: AP/NPU 성능(TOPS) — 향후 임계값 재조정 시 참고", 1),
    ("키오스크 구현 방식: Android Device Owner Mode(COSU) 채택, Screen Pinning 미채택 (사용자 자체 해제 가능해 탈락)", 0, True, TEAL_DEEP),
])

# ---------------------------------------------------------------- 3부
add_section_divider(3, "핵심 기능 파이프라인", "사진회고 · RAG · 정서모니터링 · 출판 · 온보딩")

add_flow_slide("3부 · 파이프라인", "사진 기반 회고 → 챕터 인라인 편입", [
    "가족(웹) 또는 당사자(모바일)가 사진 업로드",
    "미회고 사진 큐 등록 (연도 태그 기반 예상 챕터 매핑)",
    "다음 Wi-Fi 동기화 시 미회고 큐 스마트폰 동기화",
    "다음 대화 세션 시작 시 사진 우선 제시 (작가/말벗돌봄 모드 무관)",
    "음성 답변 수집 → 사진ID+회고 텍스트 연결, 미회고 큐에서 제거",
    "서버 처리 → 해당 시기 챕터 본문에 자동 인라인 삽입 (placement_status='proposed')",
    "가족 웹 감수 대기열 등록 → 위치·설명 확정 시 'confirmed'",
])

add_flow_slide("3부 · 파이프라인", "RAG 검색(Retrieval) 파이프라인", [
    "사용자 발화 → Query 임베딩(BGE-M3)",
    "하이브리드 서치(BM25 + Dense, Qdrant)",
    "메타 필터(시기·인물)",
    "Top-K 청크 추출 → Re-rank",
    "LLM Context 구성 → 응답 생성",
])

add_flow_slide("3부 · 파이프라인", "정서 모니터링 처리 흐름", [
    "말벗돌봄 대화 → 발화 톤 + 부정 어휘 빈도 분석 → 정서 점수 산출",
    "emotion_scores에 일별 1건 기록 (임계치 초과 여부와 무관하게 항상 수행)",
    "임계치 초과 시 emotion_alerts 생성 → notification_settings 조회 → 설정 채널로 알림 발송",
    "확인 응답 없으면(N분 경과) 재알림(에스컬레이션), 확인되면 케이스 종료",
], note="⚠️ '언제 알릴지(임계치)'는 법무·윤리 검토 대기 중 — '누가·어떤 채널로 받을지'만 지금 구현")

add_flow_slide("3부 · 파이프라인", "출판/인쇄 파이프라인", [
    "전체 챕터 confirmed 상태 도달",
    "사용자/가족이 출판 요청 (publications.status='requested')",
    "조판 엔진: 하드커버 PDF(CMYK 300DPI) 또는 ePub 생성 → MinIO 저장",
    "완료 알림 → (하드커버) 인쇄 발주 / (ePub) 다운로드 링크 제공",
])

add_flow_slide("3부 · 파이프라인", "온보딩 · 가족 페어링 흐름", [
    "스마트폰 최초 수령 → 설치모드 자동분기 → 초기설정(이름·Wi-Fi 등록)",
    "개인정보 수집 동의(consent_logs)",
    "가족 계정 웹 콘솔 초대(invitations 생성·토큰 발송)",
    "가족이 초대 수락 → 최초 Wi-Fi 동기화 → 첫 구술 인터뷰 시작",
])

add_flow_slide("3부 · 파이프라인", "말벗돌봄 실시간 대화 파이프라인 (저사양 단말 최적화, 8단계)", [
    "① VAD 감지(WebRTC VAD) — 800ms 묵음판정으로 발화종료 확정",
    "② 온디바이스 STT 스트리밍 디코딩 — 청크 단위 누적 처리",
    "③ 키워드 추출 & 의도분류 — 경량 룰/정규식",
    "④ SQLite FTS5(BM25) 키워드 검색 — Zero-Neural RAG, 임베딩 연산 없이 자서전 청크 인출",
    "⑤ 동적 프롬프트 합성 — 페르소나+회상기억+발화, Context 1,024 토큰 제한",
    "⑥ SLM 스트리밍 추론 — 문장 종결부호 감지 시 즉시 문장 단위 분할",
    "⑦ 문장 단위 TTS 파이프라이닝 — 전체 응답 대기 없이 첫 문장 즉시 합성",
    "⑧ 로컬 DB 영속화 — 발화·참조챕터ID·응답소요시간 기록",
], note="핵심 최적화: 임베딩모델 미상주(RAM 절감) + 문장단위 스트리밍(체감속도 단축) — decisions.md #31,#32")

add_table_slide("3부 · 파이프라인", "메모리 예산 목표치 (RAM 4GB급 단말 기준)", ["모듈", "목표 RAM", "비고"], [
    ["VAD (WebRTC VAD)", "< 1MB", "후보"],
    ["STT (Sherpa-ONNX 등 후보, INT8)", "~95MB", "후보"],
    ["로컬 RAG (SQLite FTS5)", "~0MB", "OS 파일 캐시 공유"],
    ["SLM (Qwen2.5-0.5B 등 후보, Q4 양자화)", "~680MB", "Context+KV캐시 포함"],
    ["TTS (Android 네이티브)", "~0MB", "시스템 서비스"],
    ["앱 런타임(UI·Room·코루틴)", "~75MB", ""],
    ["합계(목표)", "~850MB", "4GB 단말 대비 안전마진 확보 목표"],
], col_widths=[5, 3, 5], note="⚠️ 제안자 설계 목표치 — 구체 라이브러리·수치는 실기기 벤치마크(decisions.md #27) 전까지 미검증")

add_code_slide("3부 · 파이프라인", "Wi-Fi 하향 동기화 페이로드 예시 (GET /api/v1/sync/download)", """
{
  "data": {
    "sync_version": "sync_v20260906_02",
    "chapter_updates": [
      {
        "chapter_id": "b3f1...-uuid",
        "chapter_no": 2,
        "period": "youth",
        "keywords": ["1978년", "인천공장", "김반장", "월급"],
        "summary": "1978년 인천 기계공장 근무 시절 김 반장과의 갈등 및 극복기"
      }
    ],
    "priority_questions": [
      { "question_id": "q_...-uuid",
        "text": "인천 공장 계실 때 첫 월급 타서 사모님께 어떤 선물을 하셨는지 기억나세요?",
        "type": "follow_up" }
    ],
    "schedule_items": [
      { "id": "s_...-uuid", "kind": "medication",
        "due_at": "2026-09-07T08:30:00+09:00", "description": "혈압약" }
    ]
  }
}
""", note="필드 케이싱: 서버 wire format은 snake_case 확정 (decisions.md #20) — Design 문서 §4.3")

add_table_slide("3부 · 파이프라인", "온디바이스 로컬 스키마 (mobile-schema.md, 신규)", ["테이블", "역할"], [
    ["conversations", "구술/대화 턴 로컬 버퍼 — 업로드 성공 시 오디오만 삭제, 텍스트는 5일 유지"],
    ["autobiography_fts", "자서전 로컬 검색 인덱스 (FTS5 가상테이블, Zero-Neural RAG 핵심)"],
    ["questions_cache", "회고 질문 큐 로컬 캐시"],
    ["unrecalled_photos", "미회고 사진 큐 로컬 캐시 — 대화 세션 시작 시 최우선 제시"],
    ["schedule_cache", "일정·복약 로컬 캐시 (오프라인 등록분 포함)"],
    ["device_state", "설치모드·Wi-Fi 등록정보(로컬 전용)·SLM/프롬프트팩 버전"],
], col_widths=[4, 9])

# ---------------------------------------------------------------- 4부
add_section_divider(4, "데이터 모델 & API", "17개 엔티티 · 표준 API 설계")

add_bullets_slide("4부 · 데이터/API", "데이터 모델 개요 — 17개 엔티티 (schema.md v1.1)", [
    ("핵심: users · family_members · devices · chapters · chapter_revisions", 0),
    ("사진/구술: photos · photo_requests · conversation_chunks · questions", 0),
    ("비서/정서: schedule_items · emotion_alerts · emotion_scores", 0),
    ("운영/거버넌스: sync_sessions · consent_logs · notification_settings · invitations · publications", 0),
    ("설계 원칙: DB enum은 영문 통일(표시명은 별도 매핑), API는 snake_case, 구독·결제 도메인은 Phase 1 스코프 아웃", 0, True, TEAL_DEEP),
])

add_boxes_slide("4부 · 데이터/API", "핵심 엔티티 관계 (요약 ERD)", [
    {"x": 0.6, "y": 1.5, "w": 2.6, "h": 0.8, "text": "users", "fill": TEAL, "textcolor": WHITE, "bold": True, "size": 15},
    {"x": 3.6, "y": 1.5, "w": 2.6, "h": 0.8, "text": "family_members", "fill": SURFACE, "line": TEAL},
    {"x": 6.6, "y": 1.5, "w": 2.6, "h": 0.8, "text": "devices → sync_sessions", "fill": SURFACE, "line": TEAL},
    {"x": 9.6, "y": 1.5, "w": 3.0, "h": 0.8, "text": "invitations / notification_settings", "fill": SURFACE, "line": TEAL},
    {"x": 0.6, "y": 2.7, "w": 2.6, "h": 0.8, "text": "chapters → chapter_revisions", "fill": SURFACE, "line": GOLD},
    {"x": 3.6, "y": 2.7, "w": 2.6, "h": 0.8, "text": "photos ↔ conversation_chunks\n(+ graph_node_ref → Neo4j)", "fill": SURFACE, "line": GOLD, "size": 11},
    {"x": 6.6, "y": 2.7, "w": 2.6, "h": 0.8, "text": "photo_requests", "fill": SURFACE, "line": GOLD},
    {"x": 9.6, "y": 2.7, "w": 3.0, "h": 0.8, "text": "questions", "fill": SURFACE, "line": GOLD},
    {"x": 0.6, "y": 3.9, "w": 2.6, "h": 0.8, "text": "schedule_items", "fill": SURFACE, "line": SILVER},
    {"x": 3.6, "y": 3.9, "w": 2.6, "h": 0.8, "text": "emotion_alerts", "fill": SURFACE, "line": SILVER},
    {"x": 6.6, "y": 3.9, "w": 2.6, "h": 0.8, "text": "emotion_scores", "fill": SURFACE, "line": SILVER},
    {"x": 9.6, "y": 3.9, "w": 3.0, "h": 0.8, "text": "consent_logs / publications", "fill": SURFACE, "line": SILVER},
    {"x": 0.6, "y": 5.1, "w": 12.0, "h": 0.7, "text": "모든 엔티티는 users를 루트로 하는 1:N 소유 구조 — 상세 DDL은 schema.md §5 참조", "fill": INK, "textcolor": WHITE},
])

add_table_slide("4부 · 데이터/API", "API 설계 개요", ["항목", "내용"], [
    ["프레임워크", "Python 3.11+ / FastAPI (온프레미스 자체 호스팅, 확정)"],
    ["버전 관리", "/api/v1 프리픽스, 리소스는 소유자(users) 하위로 중첩"],
    ["표준 응답 포맷", "성공: {data}, 목록: {data, pagination}, 에러: {error:{code,message,details}}"],
    ["표준 에러 코드", "VALIDATION_ERROR(400) · UNAUTHORIZED(401) · FORBIDDEN(403) · NOT_FOUND(404) · CONFLICT(409) · INTERNAL_ERROR(500)"],
    ["필드 케이싱", "서버 wire format은 snake_case 통일, 클라이언트는 각 스택 컨벤션으로 변환"],
    ["인증", "Keycloak SSO (원본 프로세스흐름도와 정합)"],
], col_widths=[3, 9])

# ---------------------------------------------------------------- 5부
add_section_divider(5, "UI/UX & 디자인 시스템", "23개 화면 · BI 가이드 기반 토큰화")

add_table_slide("5부 · UI/UX", "화면 인벤토리 (23개)", ["영역", "화면"], [
    ["모바일앱(당사자)", "온보딩·동의 / 홈·음성대화 / 작가모드 인터뷰 / 말벗돌봄 대화 / 비서모드 일정·복약 / 설정·동기화 / 사진 추가하기"],
    ["웹·자서전 사용자", "로그인·대시보드 / 자서전 뷰어 / 사진·타임라인 갤러리 / 계정 설정 (구독·결제는 스코프 아웃)"],
    ["웹·가족", "가족 대시보드 / 원고 감수·대조편집 / 사진 업로드·타임라인 배치 / 정서 모니터링 상세 / 알림·구성원 설정"],
    ["웹·관리자", "관리자 대시보드 / 사용자 관리 / Wi-Fi 동기화 모니터링 / 정서 알림 이력 / 시스템 설정 / 기기 관리"],
], col_widths=[3, 9])

add_swatch_slide("5부 · UI/UX", "디자인 시스템 — 컬러 & 타이포그래피", [
    {"name": "Thread Teal", "hex": TEAL, "hexlabel": "#1E7A8C · Primary 25%"},
    {"name": "Silver Mist", "hex": SILVER, "hexlabel": "#8E97A6 · Secondary 12%"},
    {"name": "Heritage Gold", "hex": GOLD, "hexlabel": "#B8935A · Accent 8%"},
    {"name": "Ink", "hex": INK, "hexlabel": "#20242B · Text 55%(Paper 포함)"},
    {"name": "Paper Stone", "hex": PAPER, "hexlabel": "#F4F2EE · Base"},
], [
    ["DISPLAY", "34px / 700", "Noto Serif KR"],
    ["H1", "26px / 700", "Noto Serif KR"],
    ["H2", "20px / 600", "Noto Serif KR"],
    ["BODY", "16px / 400", "Pretendard"],
    ["CAPTION", "12.5px / 500", "Pretendard"],
])

# ---------------------------------------------------------------- 6부
add_section_divider(6, "보안 · 컨벤션 · 기술스택", "3중 스택 · RBAC · 온프레미스 원칙")

add_bullets_slide("6부 · 보안", "보안 설계 원칙", [
    ("DB 암호화(AES-256) 및 전송구간 암호화(TLS 1.3) — 온디바이스 로컬 캐시도 동일 수준", 0),
    ("웹 콘솔 2FA, 역할별 차등 열람 권한(RBAC — 다음 슬라이드)", 0),
    ("외부 연계 시 PII 마스킹 전처리 + 동의 로그 필수, 미동의 시 전량 온프레미스 경로", 0),
    ("Wi-Fi 동기화는 등록된 신뢰 네트워크에서만 — SSID 등은 온디바이스 로컬 전용 저장(서버 미전송)", 0),
    ("Device Owner Mode(COSU) 채택 — 단말 탈취·우회 방지 상세 구현은 Do 단계에서 검토", 0),
])

add_table_slide("6부 · 보안", "RBAC 권한 매트릭스", ["리소스", "family", "caregiver", "social_worker", "admin"], [
    ["챕터 조회", "✅", "✅", "✅(동의시)", "✅"],
    ["챕터 감수(승인/반려)", "✅", "❌", "❌", "✅"],
    ["사진 업로드", "✅", "✅", "❌", "✅"],
    ["정서 알림 조회/확인", "✅", "✅", "✅", "✅"],
    ["알림 수신 설정 변경", "본인만", "본인만", "본인만", "✅"],
    ["기기 관리(조회)", "❌", "❌", "❌", "✅"],
    ["사용자/동기화 관리", "❌", "❌", "❌", "✅"],
], col_widths=[3, 2, 2, 2.5, 2])

add_table_slide("6부 · 보안", "기술 스택 요약", ["영역", "스택", "상태"], [
    ["모바일", "Android 네이티브(Kotlin), Device Owner Mode", "✅ 확정"],
    ["서버 백엔드", "Python 3.11+ / FastAPI", "✅ 확정"],
    ["웹 콘솔", "Next.js(App Router) + TypeScript + Tailwind", "✅ 확정"],
    ["LLM 추론", "자체 호스팅 vLLM · A100 GPU 서버 (챕터 윤문·Gap분석 포함)", "✅ 확정 — 외부 GPT-4o/Claude 미채택"],
    ["Vector DB", "Qdrant self-hosted", "✅ 확정 (Milvus 검토 후 미채택)"],
    ["지식 그래프", "Neo4j self-hosted (신규)", "✅ 확정 — 인물·사건·감정 관계 추적"],
    ["RDB", "PostgreSQL + Alembic 마이그레이션", "✅ 확정"],
    ["Object Storage", "자체 MinIO", "✅ 확정"],
    ["인증", "Keycloak SSO", "✅ 확정"],
    ["인프라 호스팅", "온프레미스 K8s/베어메탈 GPU 클러스터", "✅ 원칙 확정 (구체 구성 설계 필요)"],
    ["온디바이스 SLM", "Kanana-2, Qwen2.5-0.5B 등 벤치마크 후보 2종", "🔄 후보 확보, 최종선정은 벤치마크 후"],
    ["온디바이스 로컬 RAG", "SQLite FTS5(BM25) 단독 — Phase 1 기본값", "✅ 확정 (경량 VectorDB는 Phase 2+)"],
], col_widths=[3, 6, 4], font_size=12)

add_bullets_slide("6부 · 컨벤션", "컨벤션 & 폴더 구조", [
    ("서버(Python): snake_case, Clean Architecture(api/application/domain/infrastructure), ruff+mypy+pytest", 0),
    ("모바일(Kotlin): PascalCase 클래스, ktlint, Jetpack Compose", 0),
    ("웹(TypeScript): PascalCase 컴포넌트, kebab-case 폴더, ESLint/Prettier", 0),
    ("모노레포: apps/(mobile,web,admin) · services/(gateway,author-engine,care-engine,schedule-engine,sync-gateway,rag-core) · packages/py-common · infra/ · docs/ · Plan/", 0),
    ("환경변수 접두사: NEXT_PUBLIC_ / DB_ / STORAGE_(MinIO) / VECTORDB_(Qdrant) / LLM_(vLLM) / AUTH_ / SYNC_", 0),
])

# ---------------------------------------------------------------- 7부
add_section_divider(7, "의사결정 현황 & 설계 검증", "23개 항목 확정 · design-validator 33건 수정")

add_bullets_slide("7부 · 의사결정", "확정된 주요 의사결정", [
    ("설치모드 임계값: RAM<6GB 또는 Android≤11 → 키오스크 / 구현: Device Owner Mode(COSU)", 0),
    ("모바일: Android 네이티브(Kotlin) · 서버: FastAPI · 웹: Next.js · 인증: Keycloak SSO", 0),
    ("채널: B2C/B2G 병행 추진 / 외부 TTS: Phase 1~2 온프레미스만, 외부연계 Phase 3 유예", 0),
    ("Wi-Fi 동기화: 등록 Wi-Fi 한정, 접속 즉시 자동 트리거 / 사진 업로드: 촬영+갤러리 모두 지원", 0),
    ("구독·결제 도메인: Phase 1 스코프 아웃 (PG사·요금제 경영 결정 대기)", 0),
    ("'기억의 서재' 프로젝트와는 완전 별개로 최종 확정", 0),
    ("챕터 윤문·Gap분석 LLM: 온프레미스 vLLM 확정 (외부 GPT-4o/Claude 미채택) · 지식그래프 Neo4j 신규 채택", 0, True, TEAL_DEEP),
    ("온디바이스 로컬 RAG: SQLite FTS5 단독을 Phase 1 기본값으로 확정 (경량 VectorDB는 Phase 2+)", 0, True, TEAL_DEEP),
])

add_table_slide("7부 · 의사결정", "미결 의사결정 — 승인 대기 중", ["항목", "필요 조치", "담당"], [
    ["정서 모니터링 알림의 법적/윤리적 기준", "임계치·수신대상 정책 최종 확정", "⚖️ 법무·윤리 검토"],
    ["Phase 1~3 착수 일정·예산·인력", "리소스 확정 승인", "⚖️ 경영진"],
    ["구독·결제 PG사·요금제", "과금 방식 결정 후 도메인 설계 착수", "⚖️ 경영진·법무"],
    ["온디바이스 SLM 모델 자체 선정", "Kanana-2 등 벤치마크 후 확정", "기술팀"],
    ["로컬 '최근 5일' 캐시 기준", "실기기 저장용량 벤치마크 후 재확정", "기술팀"],
], col_widths=[5, 5, 3])

add_table_slide("7부 · 검증", "설계 검증 결과 — design-validator", ["항목", "1차 검증", "수정 후"], [
    ["종합 완성도 점수", "74/100", "권고 조치 33건 전체 반영 완료"],
    ["High 심각도", "5건 (백엔드 미확정, 챕터 제목 누락, 정서 시계열 저장처 없음 등)", "5/5 해결"],
    ["Medium 심각도", "18건 (필드 누락, 문서 간 불일치, API 표준 부재 등)", "18/18 해결"],
    ["Low 심각도 + 원본 문서 오류", "10건 + 원본 화면ID/절번호 오기 7건", "전체 해결 (원본 Plan/ 파일도 정정 완료)"],
    ["엔티티 수 변화", "11개 (v1.0)", "17개 (v1.1) — emotion_scores, chapter_revisions 등 6개 신설"],
], col_widths=[3, 5, 5])

# ---------------------------------------------------------------- 8부 (CTO 검토)
add_section_divider(8, "CTO팀 검토 의견", "아키텍처 · 인프라 · 보안 · 프론트엔드 · 백엔드/API · QA · PM 7개 관점")

add_bullets_slide("8부 · CTO팀 검토", "검토 방법 및 참여 전문가", [
    ("참여 관점 7종: Enterprise Architect(아키텍처 전략) · Infrastructure Architect(온프레미스 인프라) · Security Architect(보안·법무) · Frontend Architect(UI·접근성) · Backend/API(bkend-expert) · QA Strategist(테스트 전략) · Product Manager(스코프·일정)", 0),
    ("방법: 원본 기획 산출물(기획서·흐름도·BI가이드·UIUX설계서) + PDCA 문서 전체(plan/design/decisions/schema/CONVENTIONS)를 각 관점에서 독립 교차검토, 후행 관점은 선행 리뷰와 중복 배제", 0),
    ("판정 기준: 강점 3개 이내 / Blocker(착수 전 반드시 해결) / Concern(병행 가능)으로 구분", 0),
    ("7개 관점 전원 공통 판정:", 0, True, TEAL_DEEP),
    ("Go with Conditions (조건부 착수) — 제품·데이터 설계는 착수 가능 수준이나 실행축(분산·동기화·보안·접근성·API계약·QA기준) 공백 다수, No-go 시사 관점 없음", 1, True, TEAL_DEEP),
])

add_bullets_slide("8부 · 아키텍처(Enterprise)", "강점 & 핵심 Blocker", [
    ("강점: 미결정책을 '누가·언제'로 쪼개는 규율(#19) · 하이브리드 구조가 제약조건상 유일해 · 23개 화면↔17개 엔티티 역추적 완료", 0, False, TEAL_DEEP),
    ("B1. 동기화 계약(Sync Contract) 부재 → 실제 데이터 영구 소실 경로 존재", 0, True, RED),
    ("5일 보존창 + 'Server-Wins' 무차별 적용 시, 단말 전용 생성 데이터(일정·구술·사진)가 서버 사본에 덮여 소실", 1),
    ("B2. 온디바이스 SLM 모델 미선정 → 모바일 크리티컬 패스(Session 4) 전체 대기", 0, True, RED),
    ("런타임·메모리예산·프롬프트포맷·부록A 임계값 검증이 모두 모델 종속 — 실기기 2주 벤치마크 필요", 1),
    ("B3. 6개 마이크로서비스 분해 근거 부재 → 단일 DB·단일 마이그레이션 체인이라 독립성 이득 없이 비용만 발생", 0, True, RED),
    ("권고: Phase 1은 모듈러 모놀리스 2프로세스(api / worker)로 재정의, 서비스 경계는 폴더·import-linter로만 유지", 1),
    ("B4. 이중 두뇌(온디바이스 SLM vs 서버 LLM) 설계 미정 — 서버가 실시간 대화에 개입하는지 자체가 불명확", 0, True, RED),
])

add_table_slide("8부 · 인프라", "강점 & Blocker", ["구분", "내용"], [
    ["강점", "오프라인 우선 설계가 가용성 목표를 현실화(월 7시간 다운 허용 가능) · 서버 워크로드=배치 큐(대화형 아님)로 GPU 최소화 가능 · 전 스택 자체호스팅 가능 OSS"],
    ["B1", "로컬 개발환경(docker-compose) 자체가 리포지토리에 없음 — LLM/STT/임베딩 스텁 포함 구성 필요 (1~1.5주)"],
    ["B2", "'Zero External Data Egress' 사정거리 미정의 — 빌드타임 레지스트리·NTP 등 허용범위를 경영·보안 합동 결정 필요"],
    ["B3", "원본 음성 보유·파기기간 미정 — 법무 필요, WAV 무기한 보관 시 스토리지 10배 차이(14GB vs 1.3GB/인·년)"],
    ["B4", "예산·상면·전력 승인 미착수 — GPU 조달 리드타임 8~16주, 실장비 가동까지 총 12~24주 소요 예상"],
], col_widths=[1.5, 10.5], note="참고 산정(가정): 파일럿 200명 기준 A100 2장·Qdrant 100만벡터·MinIO 2.8TB/년 — 팀 반박·확정 필요")

add_bullets_slide("8부 · 보안(Security)", "강점 & 핵심 Blocker — 가장 중대한 관점", [
    ("강점: 데이터 등급에 맞는 아키텍처 기본값(Zero Egress·온프레미스) · 법적 미결사항을 코드에 밀어넣지 않는 절제(#19) · 리뷰 가능한 설계 상세", 0, False, TEAL_DEEP),
    ("B1. 정서 데이터는 '알림' 이전 '기록' 시점부터 이미 민감정보 소지 가능 — 별도 동의 없이 emotion_scores 축적 예정", 0, True, RED),
    ("B2. 대리동의(가족)의 법적 근거 공백 — 어르신 본인 동의 경로가 스키마·API 어디에도 없음", 0, True, RED),
    ("B3. 보유기간·파기정책 전무 — 보유기간 고지 없이는 적법한 동의서 작성 자체가 불가능", 0, True, RED),
    ("B4. PII 암호화 방식 미결은 'Do 단계 이연'이 아니라 스키마 결정 — 나중에 못 바꿈 (3계층 권고안 제시됨)", 0, True, RED),
    ("B5. 인증/인가/테넌시/감사모델 공백 — Keycloak↔DB 매핑 컬럼조차 없어 '첫 API를 짤 수 없는' 수준", 0, True, RED),
    ("B6. Zero External Data Egress가 설계 내부와 이미 충돌 — SMS/이메일/Push 알림, Google Fonts CDN 등", 0, True, RED),
])

add_table_slide("8부 · 보안", "법무 검토 요청 항목 (원문)", ["#", "질의"], [
    ["1", "정서 점수(발화톤·부정어휘 기반)가 개인정보보호법 제23조 민감정보에 해당하는가? 알림 없이 기록만 해도 별도동의가 필요한가?"],
    ["2", "성년후견 미개시 어르신에 대한 가족의 대리동의가 유효한가? 본인 동의 필수 범위는?"],
    ["3", "가족·복지사의 웹콘솔 열람은 제17조 제3자 제공인가, 제26조 위탁 범위 내 이용인가?"],
    ["4", "정서 점수 산출·통보 기능이 의료기기법상 규제 대상이 될 위험이 있는가?"],
    ["5", "원본음성/전사/벡터/사진/백업 각각의 보유기간·파기방법은? 암호키 폐기(crypto-shredding)가 적법한 파기로 인정되는가?"],
    ["6", "FCM/SMS/이메일 알림 발송, Google Fonts CDN 로딩이 국외이전 고지·동의 대상인가?"],
], col_widths=[1, 11], note="Security Architect 리뷰 원문 인용 — 법무팀 전달용")

add_bullets_slide("8부 · 프론트엔드", "강점 & 핵심 Blocker", [
    ("강점: BI 가이드→디자인 토큰 매핑 값 단위 100% 일치 · 23개 화면 인벤토리 완결 · 요소 테이블이 이벤트 수준까지 상세", 0, False, TEAL_DEEP),
    ("B1. 브랜드 컬러 토큰이 WCAG AA 미달 — 본문·캡션·경계선 전 계층에서 발견 (다음 슬라이드 실측치)", 0, True, RED),
    ("고령자 접근성이 제품 핵심 차별점인데, 정작 기본 팔레트가 못 버팀 — 컴포넌트 완성 후 발견되면 전면 재도색 필요", 1),
    ("B2. 디자인 토큰의 3플랫폼(web/admin/mobile) 배포 메커니즘 부재 — 동일 HEX가 3벌 수기 복제 예정", 0, True, RED),
    ("B3. Next.js App Router가 컨벤션상 '동작하지 않는 경로'(src/presentation/app/)에 배치됨 — 첫 next dev 시점에 막힘", 0, True, RED),
    ("B4. 접근성 최소기준(폰트 하한·터치타깃·대비등급) 수치가 문서 전체에 0건", 0, True, RED),
])

add_table_slide("8부 · 프론트엔드", "컬러 토큰 실측 대비비 — WCAG 위반 사례", ["조합", "실측 대비비", "AA 본문(4.5)", "판정"], [
    ["teal #1E7A8C / paper #F4F2EE", "4.45 : 1", "미달", "❌ 본문·링크색 사용 불가"],
    ["ink-faint #9096A0 / paper (현 CAPTION 지정색)", "2.66 : 1", "미달", "❌ 사용 불가"],
    ["gold #B8935A / paper", "2.55 : 1", "미달", "❌ 텍스트·아이콘 전면 금지"],
    ["silver #8E97A6 / paper", "2.63 : 1", "미달", "❌ 로고 stroke 등 장식 전용으로 제한 필요"],
    ["border #DEDACF / paper", "1.25 : 1", "비텍스트 기준(3.0)도 미달", "❌ 입력필드·카드 경계 사실상 비가시"],
    ["teal-deep #155C6B / white", "7.57 : 1", "AAA 통과", "✅ 권장 텍스트색으로 대체"],
], col_widths=[4, 2.5, 2.5, 3.5], note="Frontend Architect 실측(WCAG 2.x relative luminance) — 팔레트는 SoR(BI가이드) 개정 후 토큰 반영 필요")

add_table_slide("8부 · PM/스코프", "강점 & Blocker — '진짜 착수를 막는 것은 무엇인가'", ["구분", "내용"], [
    ["강점", "의사결정 밀도 이례적으로 높음(23건 중 17건 확정) · 상류 산출물이 코드 직전까지 완비 · 리스크가 정직하게 문서화됨"],
    ["B1 (진짜 Blocker)", "Phase 1 예산·인력 미승인 — GPU 조달 리드타임이 승인일에 종속, 오늘 승인해도 실장비는 3~6개월 뒤"],
    ["B2 (부분 Blocker)", "온디바이스 SLM 모델 미선정 — Session 3(서버)는 무관하게 착수 가능, Session 4(모바일)만 차단. 예산 없이 착수 가능한 2주 스파이크로 해소"],
    ["B3 (즉시 해소 가능)", "Phase 1/2/3 스코프 경계가 어느 문서에도 없음 — plan §2.1 In Scope가 3개 Phase 전체를 뭉뚱그림. 킥오프 당일 승인만으로 해결"],
    ["핵심 통찰", "미결 7건 중 실제 Phase 1 착수를 막는 것은 예산 1건뿐. 법무 검토(#12)는 Phase 2 사안이라 착수를 막지 않음 (단, 보안 관점은 이 판단에 이견 — 다음 슬라이드)"],
], col_widths=[2.2, 9.8])

add_bullets_slide("8부 · PM/스코프", "검증되지 않은 최대 제품 가정 — 최저비용 실험 제안", [
    ("가정 A: '어르신이 몇 달간 스스로, 반복해서, 스마트폰에 인생을 말한다' — 전체 아키텍처가 이 가정 위에 세워짐, 검증 데이터 없음", 0),
    ("실험: 복지관 협조 Wizard-of-Oz 인터뷰(사람이 진행, 코드 0줄, 2주) — 14일 지속률·세션당 발화시간 측정, Phase 1 개발과 병행 착수 가능", 1),
    ("가정 B: '1~3B 4bit 온디바이스 SLM이 한국어 회고 대화 품질을 지탱한다' — plan §5가 Likelihood 'High'로 인정한 리스크", 0),
    ("실험: B2 SLM 벤치마크와 동일 작업으로 병행 — 품질 미달 시 폴백 설계(오프라인은 질문 낭독+녹음만, 생성은 서버 위임)까지 스파이크 산출물에 포함", 1),
])

add_table_slide("8부 · 백엔드/API", "강점 & Blocker — 자체 FastAPI 선택 타당성 재확인", ["구분", "내용"], [
    ["타당성 검증", "bkend.ai 같은 BaaS는 GPU 상주추론·Zero Egress 원칙과 구조적으로 충돌 — 자체호스팅 FastAPI가 데이터주권상 유일하게 타당한 선택임을 재확인"],
    ["강점", "서버 내부 wire format이 DB와 동일 snake_case라 변환계층 불필요 · 표준 응답/에러포맷 선확정 · Clean Architecture 규칙이 CI 룰로 즉시 전환 가능한 수준"],
    ["B1", "장시간 작업(STT재전사·LLM챕터생성)의 비동기 계약 부재 — 동기화 진행상황 조회 API 자체가 없음 (202+job_id 패턴 필요)"],
    ["B2", "파일(음성·사진) 업로드 전송 방식 미정 — 프록시 업로드시 배치 음성 수백MB에 타임아웃 위험 (Presigned URL 직결 권고)"],
    ["B3", "17개 엔티티↔6개 서비스 소유권 매핑 표 부재 — 공유 엔티티(users 등) 중복정의로 스키마 드리프트 확실"],
    ["B4", "GET /sync/download 증분 계약 없음 — 매번 전량 다운로드면 오프라인 우선 원칙과 충돌"],
], col_widths=[1.5, 10.5])

add_table_slide("8부 · QA전략", "강점 & Blocker — '얼마나 되어야 통과인가'", ["구분", "내용"], [
    ["강점", "Test Scope 표가 6개 시나리오축 선제 식별 · 동기화 실패·Diff 멱등성 최소 기준선 존재 · 설치모드 경계기기 5종 실명 명시로 실기기 랩 리스트 즉시 추출 가능"],
    ["B1", "테스트 정량 기준(Pass/Fail 임계값) 전무 — 재시도 최대횟수 N조차 미정, PM의 제품 완료기준과는 별개로 테스트케이스 단위 수치 없음"],
    ["B2", "고령 화자 음성인식 정확도가 Test Scope에서 통째로 누락 — SLM 벤치마크는 성능만 보고 인식정확도(WER) 데이터셋·계획이 없음"],
    ["B3", "네트워크 장애주입·실기기 랩의 조달 주체·일정 부재 — 서버 로컬환경(docker-compose)과는 다른 별도 QA 인프라"],
], col_widths=[1.5, 10.5], note="3건 모두 코드 착수를 막을 필요 없는 1~2주 문서/조달 작업 — SLM 벤치마크·인프라 트랙과 병행 권고")

add_table_slide("8부 · 종합", "관점 간 이견 — 정서 모니터링 착수 가능 시점", ["관점", "판단"], [
    ["PM/Product", "정서 모니터링은 design §11.2 구현순서 6 = Phase 2 사안. Phase 1 임계경로 밖이므로 착수를 막지 않음"],
    ["Security", "emotion_scores '기록'(알림과 무관) 자체가 민감정보 소지 가능 — 이 write 경로는 Phase 1 온보딩(consent_logs)과 맞물려 있어 더 이르게 문제화됨"],
    ["종합 권고", "이견을 경영진이 인지한 채 진행: Phase 1 코드에서 정서 파이프라인(emotion_scores write, meta_emotion/meta_prosody 산출)을 피처 플래그로 OFF, 법무 회신 후 ON"],
], col_widths=[2.5, 9.5])

add_table_slide("8부 · 종합", "Blocker 총괄 매트릭스 (7개 관점, 우선순위순)", ["관점", "Blocker", "소요"], [
    ["PM", "Phase 1 예산·인력 승인", "경영진 결정 즉시 / 실현 3~6개월"],
    ["보안", "동의·보유기간·인가모델·암호화 5대 공백 (법적 리스크)", "설계 1~2주 + 법무 회신 2~3주"],
    ["아키텍처", "온디바이스 SLM 모델 미선정", "실기기 벤치마크 2주"],
    ["QA", "고령 화자 음성인식 정확도 데이터셋·계획 부재", "SLM 벤치마크와 동시 진행"],
    ["아키텍처", "동기화 계약(보존·충돌·재개) 부재 → 데이터 소실 위험", "설계 3~4일 + 리뷰 1일"],
    ["백엔드", "비동기 job/파일업로드/증분동기화 API 계약 부재", "1주"],
    ["아키텍처", "6개 마이크로서비스 근거 부재 → 모듈러 모놀리스 권고", "결정 회의 반나절 + ADR 1일"],
    ["백엔드", "17개 엔티티↔서비스 소유권 매핑 표 부재", "반나절"],
    ["인프라", "로컬 개발환경(docker-compose+스텁) 부재", "1~1.5주"],
    ["QA", "네트워크 장애주입·실기기 랩 조달 미정", "인프라 트랙과 통합 1.5주"],
    ["프론트엔드", "컬러 토큰 WCAG AA 미달 (본문/캡션/경계선)", "2~3일"],
    ["프론트엔드", "Next.js App Router 폴더 구조 오류", "1일"],
    ["QA", "테스트 정량 Pass/Fail 기준 전무", "1주"],
    ["PM", "Phase 1/2/3 스코프 경계 미문서화", "즉시 (킥오프 당일)"],
], col_widths=[2, 8, 3], font_size=11)

add_bullets_slide("8부 · CTO 종합 의견", "Go with Conditions — 조건부 착수", [
    ("7개 관점 전원 일치: 제품 정의·데이터 모델은 착수 가능 수준이나, '어떻게 분산·동기화·보호·검증할지' 실행축이 비어 있음", 0, True, TEAL_DEEP),
    ("오늘 처리 가능(비용 0): Phase 1/2/3 스코프 경계 승인, 정서 파이프라인 Phase 1 한정 OFF 결정", 0),
    ("1~2주 내 필요: SLM 벤치마크+고령화자 음성데이터셋, 동기화·API 비동기 계약 설계, PII 암호화 방식, docker-compose+장애주입 환경, 컬러 토큰 재조정, 테스트 정량기준 수립", 0),
    ("2~3주 내 필요: 법무 검토 착수(동의·보유기간·정서데이터), Phase 1 한정 예산 승인", 0),
    ("착수를 실제로 막는 것은 예산 승인 1건 — 나머지 20건은 병행 착수 가능한 조건부 항목", 0, True, GOLD_DEEP),
    ("단, 보안 관점의 법적 Blocker(동의·보유기간·인가모델)는 온보딩·정서모니터링 모듈 착수 전 반드시 해소 필요", 0, True, RED),
])

# ---------------------------------------------------------------- 9부
add_section_divider(9, "로드맵 & 착수 실행 계획", "Phase 1~3 · Do 단계 세션 가이드")

add_table_slide("9부 · 로드맵", "단계별 개발 로드맵", ["단계", "범위", "핵심 목표"], [
    ["Phase 1 (MVP)", "자서전 작가 모드 + 오프라인 코어", "온디바이스 STT/SLM/TTS 오프라인 대화, 로컬캐시·Wi-Fi 배치동기화 기본 흐름 검증"],
    ["Phase 2", "말벗돌봄 모드 확장", "로컬 경량 RAG 스냅샷 기반 오프라인 회상 대화, 정서 모니터링·알림 고도화"],
    ["Phase 3", "비서 모드 + 외부 연계 옵션", "오프라인 일정·복약 비서 통합, 선택적 외부 TTS 파일럿, B2G 확장 검토"],
])

add_table_slide("9부 · 로드맵", "Do 단계 실행 계획 (세션 가이드)", ["세션", "Phase", "범위"], [
    ["Session 1", "Plan + Design", "전체 (완료)"],
    ["Session 2", "Phase 1+2", "스키마·컨벤션 확정 (완료)"],
    ["Session 3", "Do", "module-author-engine"],
    ["Session 4", "Do", "module-mobile-offline-core"],
    ["Session 5", "Check + Report", "전체 Gap 분석 및 완료 보고"],
])

add_bullets_slide("9부 · 로드맵", "팀 구성 제안", [
    ("아키텍트 — 전체 구조·마이크로서비스 경계 관리 (enterprise-expert 관점)", 0),
    ("백엔드 개발자 — FastAPI 서비스(author/care/schedule-engine, sync-gateway, rag-core)", 0),
    ("모바일 개발자 — Kotlin 온디바이스 앱, 설치모드 자동분기 구현", 0),
    ("프론트엔드 개발자 — Next.js 웹 콘솔(사용자/가족/관리자)", 0),
    ("인프라/DevOps — 온프레미스 K8s/GPU 클러스터, CI/CD", 0),
    ("QA — 오프라인·동기화·설치모드 분기 등 특수 시나리오 검증", 0),
    ("보안 담당 — PII 암호화, RBAC, Device Owner Mode 보안 검토", 0),
])

add_table_slide("9부 · Next Steps", "Action Items (CTO팀 7개 관점 검토 반영)", ["#", "액션", "담당/기한"], [
    ["1", "Phase 1 한정 예산·인력 승인 (GPU 조달 리드타임 감안)", "경영진 / 킥오프 후 1주 내"],
    ["2", "Phase 1/2/3 스코프 경계 공식 승인 (plan §2.1 대체)", "PM / 킥오프 당일"],
    ["3", "온디바이스 SLM 벤치마크 + 고령화자 음성데이터셋 확보 스파이크", "모바일·ML·QA 리드 / 즉시 착수"],
    ["4", "동의·보유기간·정서데이터 법적 리스크 6개 항목 법무 검토 요청", "법무팀 / 즉시 착수, 회신 2~3주"],
    ["5", "동기화 계약 + 비동기 job/파일업로드 API 계약 + PII 암호화 방식 설계", "서버·모바일 리드 / 1~2주"],
    ["6", "로컬 개발환경(docker-compose+스텁) + QA 장애주입 인프라 구축", "인프라·백엔드·QA / 1~1.5주"],
    ["7", "컬러 토큰 WCAG AA 재조정 + Next.js 폴더구조 정정", "프론트엔드 리드 / 2~3일"],
    ["8", "테스트 정량 Pass/Fail 기준 수립", "QA 리드 / 1주"],
    ["9", "정서 파이프라인 Phase 1 한정 OFF(피처플래그) 반영 후 Do 단계 착수", "개발팀 / 위 1~8 병행 완료 후"],
], font_size=11)

s = new_slide(bg=INK)
add_rect(s, 0, SH - Inches(0.12), SW, Inches(0.12), fill=TEAL)
add_rect(s, 0, 0, Inches(0.12), SH, fill=GOLD)
tb = s.shapes.add_textbox(Inches(1.0), Inches(3.0), Inches(11), Inches(1.0))
set_text(tb.text_frame, "감사합니다", size=44, color=WHITE, bold=True)
tb2 = s.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(11), Inches(0.6))
set_text(tb2.text_frame, "Q&A", size=20, color=GOLD)
tb3 = s.shapes.add_textbox(Inches(1.0), Inches(6.6), Inches(11), Inches(0.5))
set_text(tb3.text_frame, "은빛실타래 (SilverYarn) · NUBiz AX Initiative · 2026년 9월", size=13, color=INK_FAINT)

prs.save(r"C:\PROJECT\SilverYarn\docs\presentations\은빛실타래_개발착수회의_kickoff.pptx")
print("SLIDES:", PAGE_NO[0])

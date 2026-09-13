# -*- coding: utf-8 -*-
"""
은빛실타래(SilverYarn) 설계발표 — "시스템 흐름 이해" 중심 PPT 생성 스크립트.

기존 은빛실타래_개발착수회의_kickoff.pptx(66슬라이드, generate_kickoff_deck.py)와는
별개의 산출물이다 — 그 파일은 손대지 않는다(과거 착수회의 스냅샷 보존).

Source of truth: docs/01-plan/*, docs/02-design/*, CLAUDE.md,
docs/presentations/은빛실타래_설계발표_슬라이드.html(동일 내용의 인터랙티브 HTML판).

이 스크립트의 목적(사용자 요청, 2026-09-14): "시스템 전반의 흐름"과 "단위 시스템별
업무흐름도"를 전체 그림과 세부 디테일 둘 다 파악할 수 있도록 실제 다이어그램(도형+화살표)
으로 시각화한 PPT. 텍스트 불릿보다 흐름도·구성도를 압도적으로 우선한다.

스코프 결정: governance 성격 콘텐츠(CTO 7개 관점 상세, 의사결정 47건 개별 나열,
design-validator 세부 점수표)는 이 세션의 실제 요청(흐름 이해)과 결이 달라 요약
1~2슬라이드로 압축했다 — 전체 상세는 이미 은빛실타래_설계발표_슬라이드.html(72슬라이드)에
있으므로 중복 전사하지 않는다.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

# ---------------------------------------------------------------- palette
# (design-tokens.md와 동일 — generate_kickoff_deck.py와 값 일치)
INK = RGBColor(0x20, 0x24, 0x2B)
INK_MUTED = RGBColor(0x5B, 0x64, 0x72)
INK_FAINT = RGBColor(0x90, 0x96, 0xA0)
PAPER = RGBColor(0xF4, 0xF2, 0xEE)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
SUBTLE = RGBColor(0xEC, 0xE8, 0xE1)
SUBTLE2 = RGBColor(0xF7, 0xF5, 0xF1)
BORDER = RGBColor(0xDE, 0xDA, 0xCF)
BORDER_STRONG = RGBColor(0xB7, 0xAD, 0x9B)
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
CODE_BG = RGBColor(0x15, 0x18, 0x1D)
CODE_TX = RGBColor(0xE4, 0xF0, 0xF2)

FONT = "맑은 고딕"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height

PAGE_NO = [0]


# ================================================================ 기본 헬퍼
def new_slide(bg=PAPER):
    s = prs.slides.add_slide(BLANK)
    bgfill = s.background.fill
    bgfill.solid()
    bgfill.fore_color.rgb = bg
    PAGE_NO[0] += 1
    return s


def add_footer(slide, label="은빛실타래 · SilverYarn · 설계발표"):
    tb = slide.shapes.add_textbox(Inches(0.5), SH - Inches(0.4), Inches(7), Inches(0.3))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = label
    r.font.size = Pt(10); r.font.color.rgb = INK_FAINT; r.font.name = FONT
    pn = slide.shapes.add_textbox(SW - Inches(1.2), SH - Inches(0.4), Inches(0.8), Inches(0.3))
    p2 = pn.text_frame.paragraphs[0]; p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run(); r2.text = str(PAGE_NO[0])
    r2.font.size = Pt(10); r2.font.color.rgb = INK_FAINT; r2.font.name = FONT


def set_text(tf, text, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT, font=FONT, line_spacing=1.15):
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold; r.font.name = font
    return p


def add_rect(slide, x, y, w, h, fill=TEAL, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    shp = slide.shapes.add_shape(shape, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1.25)
    shp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    return shp


def add_line(slide, x1, y1, x2, y2, color=BORDER_STRONG, width=1.25, dashed=False):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    if dashed:
        ln = conn.line._get_or_add_ln()
        from pptx.oxml.ns import qn
        dash = ln.makeelement(qn("a:prstDash"), {"val": "dash"})
        ln.append(dash)
    conn.shadow.inherit = False
    return conn


def title_bar(slide, kicker, title):
    add_rect(slide, 0, 0, SW, Inches(1.15), fill=INK)
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.12), SW - Inches(1.1), Inches(0.35))
    set_text(tb.text_frame, kicker, size=13, color=GOLD, bold=True)
    tb2 = slide.shapes.add_textbox(Inches(0.5), Inches(0.42), SW - Inches(1.0), Inches(0.7))
    set_text(tb2.text_frame, title, size=25, color=WHITE, bold=True)


def add_title_slide():
    s = new_slide(bg=INK)
    add_rect(s, 0, SH - Inches(0.12), SW, Inches(0.12), fill=TEAL)
    add_rect(s, 0, Inches(0), Inches(0.12), SH, fill=GOLD)
    tb = s.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11), Inches(0.5))
    set_text(tb.text_frame, "설계발표 — 시스템 흐름 이해 중심", size=18, color=GOLD, bold=True)
    tb2 = s.shapes.add_textbox(Inches(1.0), Inches(2.45), Inches(11), Inches(1.3))
    set_text(tb2.text_frame, "은빛실타래", size=54, color=WHITE, bold=True)
    tb3 = s.shapes.add_textbox(Inches(1.0), Inches(3.35), Inches(11), Inches(0.6))
    set_text(tb3.text_frame, "SilverYarn — 어르신 자서전 제작 및 AI 말벗돌봄 플랫폼", size=22, color=SILVER)
    tb4 = s.shapes.add_textbox(Inches(1.0), Inches(3.95), Inches(11), Inches(0.5))
    set_text(tb4.text_frame, "전체 아키텍처 · 단위 시스템별 업무흐름도(개요+상세) · UI/UX 실 구현 화면", size=15, color=TEAL_TINT)
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
    add_footer(s)
    return s


def add_bullets_slide(kicker, title, bullets, note=None):
    """bullets: list of (text, level[, bold[, color]])"""
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
        p.space_after = Pt(10 if level == 0 else 4)
        prefix = ("▪  " if level == 0 else "     -  ")
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = prefix + text
        r.font.size = Pt(19 if level == 0 else 16)
        r.font.bold = bold
        r.font.color.rgb = color if level == 0 else INK_MUTED
        r.font.name = FONT
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
        cell.fill.solid(); cell.fill.fore_color.rgb = INK
        cell.text_frame.word_wrap = True
        p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = h
        r.font.size = Pt(font_size); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_top = Pt(4); cell.margin_bottom = Pt(4)
    for ridx, row in enumerate(rows, start=1):
        rowfill = SURFACE if ridx % 2 == 1 else TEAL_TINT
        for c, val in enumerate(row):
            cell = gtable.cell(ridx, c)
            cell.fill.solid(); cell.fill.fore_color.rgb = rowfill
            cell.text_frame.word_wrap = True
            p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(val)
            r.font.size = Pt(font_size); r.font.color.rgb = INK; r.font.name = FONT
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Pt(6); cell.margin_top = Pt(3); cell.margin_bottom = Pt(3)
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


def add_arrow(slide, x, y, w, h, direction="down", fill=GOLD):
    shape_map = {
        "down": MSO_SHAPE.DOWN_ARROW, "up": MSO_SHAPE.UP_ARROW,
        "right": MSO_SHAPE.RIGHT_ARROW, "left": MSO_SHAPE.LEFT_ARROW,
    }
    arr = slide.shapes.add_shape(shape_map.get(direction, MSO_SHAPE.DOWN_ARROW), x, y, w, h)
    arr.fill.solid(); arr.fill.fore_color.rgb = fill
    arr.line.fill.background(); arr.shadow.inherit = False
    return arr


def add_code_slide(kicker, title, code_text, note=None, size=13):
    s = new_slide(bg=INK)
    title_bar(s, kicker, title)
    box = add_rect(s, Inches(0.7), Inches(1.5), SW - Inches(1.4), SH - Inches(2.1), fill=CODE_BG, line=None)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3); tf.margin_top = Inches(0.25)
    first = True
    for line in code_text.strip("\n").split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run(); r.text = line if line.strip() != "" else " "
        r.font.size = Pt(size); r.font.name = "Consolas"; r.font.color.rgb = CODE_TX
        p.space_after = Pt(2)
    if note:
        nb = s.shapes.add_textbox(Inches(0.7), SH - Inches(0.55), SW - Inches(1.4), Inches(0.4))
        set_text(nb.text_frame, note, size=12, color=GOLD)
    add_footer(s)
    return s


def add_swatch_slide(kicker, title, swatches, typo_rows):
    s = new_slide()
    title_bar(s, kicker, title)
    x, y, w, h, gap = Inches(0.7), Inches(1.6), Inches(1.85), Inches(1.4), Inches(0.15)
    for i, sw in enumerate(swatches):
        bx = Emu(int(x) + i * (int(w) + int(gap)))
        add_rect(s, bx, y, w, h, fill=sw["hex"])
        label = s.shapes.add_textbox(bx, Emu(int(y) + int(h) + Inches(0.05)), w, Inches(0.75))
        tf = label.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = sw["name"]; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = INK; r.font.name = FONT
        p2 = tf.add_paragraph()
        r2 = p2.add_run(); r2.text = sw["hexlabel"]; r2.font.size = Pt(11); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
    tb = s.shapes.add_textbox(Inches(0.7), Inches(3.5), Inches(3), Inches(0.4))
    set_text(tb.text_frame, "타입 스케일", size=15, color=GOLD_DEEP, bold=True)
    gtable = s.shapes.add_table(len(typo_rows) + 1, 3, Inches(0.7), Inches(4.0), SW - Inches(1.4), Inches(2.6)).table
    for c, hh in enumerate(["레벨", "크기/굵기", "서체"]):
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


# ================================================================ 흐름도 헬퍼 (신규)
def add_flow_v_slide(kicker, title, steps, note=None):
    """steps: list[(title, desc)] — 세로 번호 흐름(위→아래), 사이 화살표."""
    s = new_slide()
    title_bar(s, kicker, title)
    n = len(steps)
    top = Inches(1.4)
    avail_h = SH - Inches(2.2)
    box_h = min(Inches(0.78), Emu(int(avail_h / n) - Inches(0.10)))
    gap = Emu(int((avail_h - int(box_h) * n) / max(n - 1, 1))) if n > 1 else Inches(0)
    y = top
    left = Inches(1.1)
    width = SW - Inches(2.2)
    for i, (t, d) in enumerate(steps):
        box = add_rect(s, left, y, width, box_h, fill=SURFACE, line=BORDER_STRONG)
        chip = add_rect(s, left, y, Inches(0.6), box_h, fill=TEAL)
        ctf = chip.text_frame; ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
        cp = ctf.paragraphs[0]; cp.alignment = PP_ALIGN.CENTER
        cr = cp.add_run(); cr.text = str(i + 1)
        cr.font.size = Pt(18); cr.font.bold = True; cr.font.color.rgb = WHITE; cr.font.name = FONT
        txt = box.text_frame; txt.word_wrap = True
        txt.margin_left = Inches(0.8); txt.vertical_anchor = MSO_ANCHOR.MIDDLE
        p1 = txt.paragraphs[0]
        r1 = p1.add_run(); r1.text = t
        r1.font.size = Pt(15); r1.font.bold = True; r1.font.color.rgb = TEAL_DEEP; r1.font.name = FONT
        p2 = txt.add_paragraph()
        r2 = p2.add_run(); r2.text = d
        r2.font.size = Pt(12.5); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
        if i < n - 1:
            ay = Emu(int(y) + int(box_h) + int(gap) // 2 - Inches(0.09))
            add_arrow(s, Emu(int(left) + int(width) // 2 - Inches(0.09)), ay, Inches(0.18), Inches(0.18), "down")
        y = Emu(int(y) + int(box_h) + int(gap))
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


def add_flow_h_slide(kicker, title, steps, note=None):
    """steps: list[(title, desc)] — 가로 번호 흐름(좌→우), 사이 화살표."""
    s = new_slide()
    title_bar(s, kicker, title)
    n = len(steps)
    gap = Inches(0.35)
    top = Inches(2.1)
    box_h = Inches(4.1)
    avail_w = SW - Inches(1.2) - int(gap) * (n - 1)
    box_w = Emu(int(avail_w / n))
    x = Inches(0.6)
    badge_d = Inches(0.7)
    for i, (t, d) in enumerate(steps):
        add_rect(s, x, top, box_w, box_h, fill=SURFACE, line=BORDER_STRONG)
        bx = Emu(int(x) + int(box_w) // 2 - int(badge_d) // 2)
        badge = add_rect(s, bx, Emu(int(top) + Inches(0.4)), badge_d, badge_d, fill=TEAL, shape=MSO_SHAPE.OVAL)
        btf = badge.text_frame; btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]; bp.alignment = PP_ALIGN.CENTER
        br = bp.add_run(); br.text = str(i + 1)
        br.font.size = Pt(22); br.font.bold = True; br.font.color.rgb = WHITE; br.font.name = FONT
        ttb = s.shapes.add_textbox(Emu(int(x) + Inches(0.1)), Emu(int(top) + Inches(1.5)), Emu(int(box_w) - Inches(0.2)), Inches(0.75))
        ttf = ttb.text_frame; ttf.word_wrap = True
        tp = ttf.paragraphs[0]; tp.alignment = PP_ALIGN.CENTER
        tr = tp.add_run(); tr.text = t
        tr.font.size = Pt(16.5); tr.font.bold = True; tr.font.color.rgb = INK; tr.font.name = FONT
        dtb = s.shapes.add_textbox(Emu(int(x) + Inches(0.2)), Emu(int(top) + Inches(2.35)), Emu(int(box_w) - Inches(0.4)), Emu(int(box_h) - Inches(2.5)))
        dtf = dtb.text_frame; dtf.word_wrap = True
        dp = dtf.paragraphs[0]; dp.alignment = PP_ALIGN.CENTER
        dr = dp.add_run(); dr.text = d
        dr.font.size = Pt(13); dr.font.color.rgb = INK_MUTED; dr.font.name = FONT
        if i < n - 1:
            ax = Emu(int(x) + int(box_w))
            add_arrow(s, ax, Emu(int(top) + int(box_h) // 2 - Inches(0.09)), gap, Inches(0.18), "right")
        x = Emu(int(x) + int(box_w) + int(gap))
    if note:
        nb = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.5))
        set_text(nb.text_frame, note, size=12, color=INK_FAINT)
    add_footer(s)
    return s


# ================================================================ CONTENT
add_title_slide()

add_bullets_slide("Agenda", "목차", [
    ("1부. 프로젝트 개요 — 배경 · 목적 · 3대 운영 모드 · 에이전트 페르소나", 0),
    ("2부. 시스템 아키텍처 — 전체 컴포넌트 구성도 · Closed-Loop · 마스터 업무흐름도", 0),
    ("3부. 단위 시스템별 상세 업무흐름도 — 13개 흐름(온보딩~관리자 업무)", 0),
    ("4부. 데이터 모델 & API — 엔티티 관계도", 0),
    ("5부. UI/UX — 디자인 시스템 · 실 구현 화면 미리보기", 0),
    ("6부. 보안 · 기술스택 요약", 0),
    ("7부. 의사결정 & CTO팀 검토 하이라이트", 0),
    ("8부. 로드맵 & Action Items", 0),
])

# ---------------------------------------------------------------- 1부 개요
add_section_divider(1, "프로젝트 개요", "배경 · 목적 · 대상 사용자 · 서비스 컨셉")

add_table_slide("1부 · 개요", "Executive Summary", ["관점", "내용"], [
    ["Problem", "고령화로 어르신 삶의 기록이 소실되고, 독거·정서적 고립으로 돌봄 공백 확대. 저사양/재활용 단말·비상시 인터넷 환경 고려 필요"],
    ["Solution", "온디바이스 STT/SLM/TTS로 평소 대화를 오프라인 완결, 등록 Wi-Fi 접속 시에만 온프레미스 서버(LLM·RAG·지식그래프)와 배치 동기화"],
    ["Function/UX Effect", "끊김 없는 대화 경험, 사진 기반 자동 회고로 자연스러운 콘텐츠 축적, 단말 사양별 키오스크/일반 자동 설치"],
    ["Core Value", "자서전 제작(입구) → 말벗돌봄·비서(체류)로 이어지는 락인 라이프사이클, 초개인화 대화로 범용 챗봇 대비 높은 몰입도"],
], col_widths=[2, 8])

add_bullets_slide("1부 · 개요", "프로젝트 목적 & 핵심 차별점", [
    ("목적: 온디바이스 음성 인터페이스(VAD·STT·SLM·TTS) + 중앙 서버 생성형 AI(LLM·RAG·지식그래프) 연계", 0, True, TEAL_DEEP),
    ("오프라인 우선(Offline-First): 평상시 대화는 인터넷 연결 없이 온디바이스에서 완결", 1),
    ("Wi-Fi 배치 동기화: 등록 Wi-Fi 접속 시에만 서버 고성능 엔진으로 최신화 후 재동기화", 1),
    ("사진 기반 자동 회고 트리거: 신규 사진을 AI가 먼저 제시하며 자연스러운 회고 유도", 1),
    ("디바이스 사양 기반 설치모드 자동 분기: 저사양은 키오스크, 고사양은 일반 앱 모드", 1),
    ("작가 모드 → 말벗돌봄 모드 → 비서 모드로 이어지는 3단계 라이프사이클 통합 제공", 1),
])

add_table_slide("1부 · 개요", "서비스 컨셉 — 3대 운영 모드", ["모드", "목표", "주요 기능"], [
    ["① 자서전 작가 모드", "연대기적 구술 발굴 및 문학적 초안 생성", "질문 생성기 · 사진 기반 회고 질문 · 심층 인터뷰잉 · 구술체→문어체 정제·챕터 자동귀속"],
    ["② 말벗돌봄 모드", "초개인화 공감 대화 및 고독감 해소", "RAG 기반 추억 회상 · 사진 기반 회고 대화 · 정서 모니터링 및 알림 연동"],
    ["③ 비서 모드", "인지 기능 보조 및 일상 건강·일정 관리", "일정·복약 엔티티 추출·등록 · 지정 시각 능동형 음성 브리핑"],
], col_widths=[3, 4, 6], note="세 모드는 상호 배타적이지 않으며, 의도 분류(Intent Classification)로 하나의 대화 흐름 안에서 자연스럽게 전환됨 — 2026-09 Do 단계에서 '은실이' 하나의 대화 UI로 통합 구현(decisions.md #66~#68)")

add_table_slide("1부 · 개요", "대상 사용자", ["구분", "설명"], [
    ["1차 사용자", "구술의 주체가 되는 어르신 본인"],
    ["2차 사용자", "자서전을 감수·열람하는 가족, 돌봄 연계가 필요한 요양보호사·복지사"],
    ["잠재 고객", "복지관·요양기관·지자체 등 B2G/B2B 파일럿 운영 주체 — 채널 전략은 B2C/B2G 병행 추진으로 확정"],
], col_widths=[3, 9])

# ---------------------------------------------------------------- 2부 아키텍처
add_section_divider(2, "시스템 아키텍처", "전체 컴포넌트 구성도 · Closed-Loop · 마스터 업무흐름도")

add_bullets_slide("2부 · 아키텍처", "데이터·운영 4원칙", [
    ("원칙 1 (오프라인 우선): 평상시 대화는 인터넷 연결 없이 온디바이스에서 완결, 서버 동기화는 등록 Wi-Fi 접속 시에만", 0, True, TEAL_DEEP),
    ("원칙 2 (전면 온프레미스): 원본 음성·자서전 원고·임베딩 벡터 등 PII 포함 데이터는 100% 자체 GPU 서버(vLLM·A100)·자체 DB에서만 처리", 0, True, TEAL_DEEP),
    ("원칙 3 (제한적·선택적 외부 연계): 외부 클라우드 AI는 비식별화 데이터에 한해, 사용자 명시적 동의(Opt-in) 하에만 연계", 0),
    ("원칙 4 (계약적 통제): 외부 연계 범위는 DPA 체결 및 내부 보안 검토를 통과한 항목으로 한정", 0),
], note="Zero External Data Egress — bkit Enterprise 기본 AWS 템플릿은 적용하지 않음")

# ---- 전체 컴포넌트 다이어그램 ----
s = new_slide()
title_bar(s, "2부 · 아키텍처", "전체 컴포넌트 다이어그램")
b1 = add_rect(s, Inches(0.7), Inches(1.55), Inches(3.85), Inches(1.85), fill=TEAL_TINT, line=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
set_text(b1.text_frame, "📱 모바일앱", 15, TEAL_DEEP, True, PP_ALIGN.CENTER)
b1.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
for line in ["온디바이스 (오프라인 우선)", "VAD·STT·FTS5 RAG·SLM·TTS"]:
    p = b1.text_frame.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = line; r.font.size = Pt(12); r.font.color.rgb = TEAL_DEEP; r.font.name = FONT
b2 = add_rect(s, Inches(4.75), Inches(1.55), Inches(3.95), Inches(1.85), fill=PAPER, line=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
b2.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
set_text(b2.text_frame, "🖥️ 서버 — 전량 온프레미스", 14, TEAL_DEEP, True, PP_ALIGN.CENTER)
for line in ["FastAPI · 작가/말벗돌봄/비서 엔진", "vLLM·A100 · Qdrant · Neo4j · PG · MinIO"]:
    p = b2.text_frame.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = line; r.font.size = Pt(11); r.font.color.rgb = INK_MUTED; r.font.name = FONT
b3 = add_rect(s, Inches(8.85), Inches(1.55), Inches(3.8), Inches(1.85), fill=SUBTLE, line=BORDER_STRONG, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
b3.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
set_text(b3.text_frame, "🖊️ 웹 콘솔 (Next.js)", 15, INK, True, PP_ALIGN.CENTER)
p = b3.text_frame.add_paragraph(); p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "자서전 사용자 / 가족 / 관리자"; r.font.size = Pt(12); r.font.color.rgb = INK_MUTED; r.font.name = FONT
add_arrow(s, Inches(2.5), Inches(3.45), Inches(0.35), Inches(0.35), "down")
add_arrow(s, Inches(10.6), Inches(3.45), Inches(0.35), Inches(0.35), "down")
g1 = add_rect(s, Inches(0.7), Inches(3.9), Inches(3.85), Inches(1.0), fill=GOLD_TINT, line=GOLD)
set_text(g1.text_frame, "Wi-Fi 접속 시 자동 배치 동기화", 12.5, GOLD_DEEP, True, PP_ALIGN.CENTER)
g1.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
g2 = add_rect(s, Inches(8.85), Inches(3.9), Inches(3.8), Inches(1.0), fill=GOLD_TINT, line=GOLD)
set_text(g2.text_frame, "Keycloak SSO · /api/v1 · snake_case", 12.5, GOLD_DEEP, True, PP_ALIGN.CENTER)
g2.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
add_line(s, Inches(6.725), Inches(3.4), Inches(6.725), Inches(3.9), color=GOLD, width=1.5, dashed=True)
opt = add_rect(s, Inches(4.75), Inches(3.9), Inches(3.95), Inches(1.0), fill=SUBTLE2, line=BORDER_STRONG, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
set_text(opt.text_frame, "선택 · Opt-in — 외부 고품질 TTS (Phase 3 한정)", 11.5, INK_FAINT, False, PP_ALIGN.CENTER)
opt.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
rule = add_rect(s, Inches(0.7), Inches(5.35), SW - Inches(1.4), Inches(1.05), fill=INK)
set_text(rule.text_frame, "🔒 핵심 원칙 — 오프라인 우선 + 전면 온프레미스(Zero External Data Egress) + 제한적·선택적 외부연계", 14.5, WHITE, True, PP_ALIGN.CENTER)
rule.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
rule.text_frame.word_wrap = True
add_footer(s)

# ---- Closed-Loop Architecture ----
s = new_slide()
title_bar(s, "2부 · 아키텍처", "Closed-Loop Architecture — Edge ⇄ Cloud 피드백 루프")
edge_hdr = add_rect(s, Inches(0.6), Inches(1.35), SW - Inches(1.2), Inches(0.4), fill=TEAL)
set_text(edge_hdr.text_frame, "📱 EDGE TIER — 온디바이스 (Low-Latency)", 14, WHITE, True, PP_ALIGN.CENTER)
edge_hdr.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
edge_steps = ["VAD", "경량 STT", "FTS5 RAG\n(Zero-Neural)", "온디바이스 SLM", "Native TTS"]
ew = Emu(int((SW - Inches(1.2) - Inches(0.35) * 4) / 5))
ex = Inches(0.6)
for i, step in enumerate(edge_steps):
    bx = Emu(int(ex) + i * (int(ew) + Inches(0.35)))
    box = add_rect(s, bx, Inches(1.95), ew, Inches(0.9), fill=TEAL_TINT, line=TEAL)
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    box.text_frame.word_wrap = True
    lines = step.split("\n")
    p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = lines[0]; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = TEAL_DEEP; r.font.name = FONT
    for extra in lines[1:]:
        p2 = box.text_frame.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = extra; r2.font.size = Pt(10.5); r2.font.color.rgb = TEAL_DEEP; r2.font.name = FONT
    if i < len(edge_steps) - 1:
        add_arrow(s, Emu(int(bx) + int(ew)), Inches(2.28), Inches(0.32), Inches(0.2), "right")
note1 = s.shapes.add_textbox(Inches(0.6), Inches(2.95), SW - Inches(1.2), Inches(0.35))
set_text(note1.text_frame, "로컬 영속화: Opus(16kbps) 압축 음성 + 대화턴 DB(conversations)", 12, INK_MUTED, align=PP_ALIGN.CENTER)
add_arrow(s, Inches(3.3), Inches(3.4), Inches(1.0), Inches(0.45), "down")
up_lbl = s.shapes.add_textbox(Inches(4.4), Inches(3.4), Inches(5.5), Inches(0.45))
set_text(up_lbl.text_frame, "▲ 상향: Opus 음성 + 로컬 STT 텍스트", 12.5, GOLD_DEEP, True)
add_arrow(s, Inches(8.6), Inches(3.4), Inches(1.0), Inches(0.45), "up", fill=TEAL)
down_lbl = s.shapes.add_textbox(Inches(4.4), Inches(3.88), Inches(6.5), Inches(0.45))
set_text(down_lbl.text_frame, "▼ 하향: 정제지식·프롬프트·질문셋·일정룰 (Wi-Fi 접속 시)", 12.5, TEAL_DEEP, True)
cloud_hdr = add_rect(s, Inches(0.6), Inches(4.45), SW - Inches(1.2), Inches(0.4), fill=INK)
set_text(cloud_hdr.text_frame, "🖥️ CLOUD TIER — 온프레미스 서버 (Deep Processing)", 14, WHITE, True, PP_ALIGN.CENTER)
cloud_hdr.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
cloud_steps = [("1. 검증·교정", "Whisper Large-v3\n정밀 재전사"), ("2. 지식화", "Neo4j 그래프 +\nQdrant 벡터색인"), ("3. 생성·감수", "온프레미스 vLLM 윤문\n+ Critic Agent Gap분석")]
cw = Emu(int((SW - Inches(1.2) - Inches(0.35) * 2) / 3))
for i, (t, d) in enumerate(cloud_steps):
    bx = Emu(int(Inches(0.6)) + i * (int(cw) + Inches(0.35)))
    box = add_rect(s, bx, Inches(5.05), cw, Inches(1.0), fill=SURFACE, line=BORDER_STRONG)
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE; box.text_frame.word_wrap = True
    p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = t; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = TEAL_DEEP; r.font.name = FONT
    for dline in d.split("\n"):
        p2 = box.text_frame.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = dline; r2.font.size = Pt(11); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
    if i < len(cloud_steps) - 1:
        add_arrow(s, Emu(int(bx) + int(cw)), Inches(5.4), Inches(0.32), Inches(0.2), "right")
add_arrow(s, Inches(6.3), Inches(6.1), Inches(0.7), Inches(0.28), "down")
compact = add_rect(s, Inches(0.6), Inches(6.42), SW - Inches(1.2), Inches(0.55), fill=GOLD_TINT, line=GOLD)
compact.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
set_text(compact.text_frame, "4. Compaction Engine — 자서전 요약 FTS5 차분 + 압축 프롬프트 + 우선순위 질문 → 온디바이스 패키징", 12.5, GOLD_DEEP, True, PP_ALIGN.CENTER)
add_footer(s)

# ---- 마스터 업무 프로세스 흐름도 (Swimlane, 신규) ----
s = new_slide()
title_bar(s, "2부 · 아키텍처", "전체 업무 프로세스 흐름도 (마스터 · Swimlane)")
lanes = [("👤 당사자(스마트폰)", TEAL), ("🖥️ 온프레미스 서버", SILVER_DEEP), ("👨‍👩‍👧 가족(웹 콘솔)", GOLD_DEEP)]
lx = Inches(0.6); ly = Inches(1.35); lw = Emu(int((SW - Inches(1.2) - Inches(0.2) * 2) / 3))
for i, (label, color) in enumerate(lanes):
    bx = Emu(int(lx) + i * (int(lw) + Inches(0.2)))
    tag = add_rect(s, bx, ly, lw, Inches(0.4), fill=color)
    set_text(tag.text_frame, label, 13, WHITE, True, PP_ALIGN.CENTER)
    tag.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
master_steps = [
    ("①", "온보딩 · 설치모드 자동분기 · 초기설정 · 동의", 0, TEAL_TINT, TEAL_DEEP),
    ("②", "오프라인 구술 반복 (작가/말벗돌봄/비서, 온디바이스 완결)", 0, SURFACE, INK),
    ("③", "Wi-Fi 접속 감지 → 배치 동기화 (업로드: 음성+전사+사진)", 0, GOLD_TINT, GOLD_DEEP),
    ("④", "서버 처리: STT 정밀보정 → 지식화 → LLM 챕터 초안 생성", 1, SURFACE, INK),
    ("⑤", "가족 웹 감수 — 승인 / 반려(재생성 루프 → ④로)", 2, GOLD_TINT, GOLD_DEEP),
    ("⑥", "확정 챕터 하향 동기화 → 로컬 캐시 갱신", 1, SURFACE, INK),
    ("⑦", "전체 챕터 확정 시 → 출판(PDF/ePub) 및 말벗돌봄 모드 본격 전환", 0, INK, WHITE),
]
top = Inches(1.95); avail_h = Inches(4.75); n = len(master_steps)
bh = Emu(int(avail_h / n) - Inches(0.12))
gap = Emu(int((int(avail_h) - int(bh) * n) / (n - 1)))
y = top
for i, (num, text, lane_i, fill, tc) in enumerate(master_steps):
    is_final = (fill == INK)
    box = add_rect(s, Inches(0.6), y, SW - Inches(1.2), bh, fill=fill, line=(None if is_final else BORDER_STRONG))
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = box.text_frame.paragraphs[0]
    r = p.add_run(); r.text = f"{num}  {text}"
    r.font.size = Pt(13.5); r.font.bold = True; r.font.color.rgb = tc; r.font.name = FONT
    box.text_frame.margin_left = Inches(0.3)
    if i < n - 1:
        add_arrow(s, Emu(int(Inches(0.6)) + int(SW - Inches(1.2)) // 2 - Inches(0.09)), Emu(int(y) + int(bh) + int(gap) // 2 - Inches(0.09)), Inches(0.18), Inches(0.18), "down")
    y = Emu(int(y) + int(bh) + int(gap))
note = s.shapes.add_textbox(Inches(0.6), SH - Inches(0.85), SW - Inches(1.2), Inches(0.45))
set_text(note.text_frame, "③↔⑥은 Wi-Fi 접속마다 반복되는 순환 구조 — 전체 라이프사이클은 프로세스흐름도 §5.2 참조", 12, INK_FAINT)
add_footer(s)

# ---------------------------------------------------------------- 3부 단위 시스템별 상세 흐름
add_section_divider(3, "단위 시스템별 상세 업무흐름도", "온보딩 · 작가엔진 · 사진회고 · RAG · 실시간대화 · 정서모니터링 · 비서 · 동기화 · 출판 · 감수 · 관리")

add_flow_v_slide("분야: 온보딩", "온보딩 · 가족 페어링 흐름", [
    ("스마트폰 최초 수령", "설치모드 자동분기(키오스크/일반) → 초기설정(이름·Wi-Fi 등록)"),
    ("개인정보 수집 동의", "consent_logs 기록"),
    ("가족 계정 초대", "invitations 생성 · 토큰 발송 (웹 콘솔)"),
    ("초대 수락", "가족이 링크 수락(status=accepted)"),
    ("최초 Wi-Fi 동기화", "초기 질문목록 다운로드"),
    ("첫 구술 인터뷰 시작", "온보딩 완료 → 정기 사용 전환"),
])

add_flow_h_slide("분야: 자서전 작가", "자서전 작가 엔진 상세 흐름", [
    ("STT 재전사", "Whisper Large-v3 정밀 보정"),
    ("청킹·메타태깅", "시간·인물·장소·감정·사진ID"),
    ("질문 이력 대조", "미응답 주제 탐지 → 신규/꼬리질문"),
    ("LLM 챕터 생성", "RAG 컨텍스트 기반 초안/갱신"),
    ("구술체→문어체", "정제 및 챕터 자동 귀속"),
])

add_flow_v_slide("분야: 사진 회고", "사진 기반 회고 → 챕터 인라인 편입", [
    ("사진 업로드", "가족(웹) 또는 당사자(모바일) — 업로더 무관 동일 처리"),
    ("미회고 사진 큐 등록", "연도 태그 기반 예상 챕터 매핑"),
    ("다음 대화 세션 우선 제시", "작가/말벗돌봄 모드 무관 — 사진 먼저 보여주며 회고 유도"),
    ("음성 답변 수집", "사진ID + 회고 텍스트 연결, 미회고 큐에서 제거"),
    ("서버 처리", "해당 시기 챕터 본문에 자동 인라인 삽입 (placement_status=proposed)"),
    ("가족 웹 감수", "위치·설명 확정 시 placement_status=confirmed"),
])

add_flow_h_slide("분야: RAG", "RAG 검색(Retrieval) 파이프라인", [
    ("Query 임베딩", "BGE-M3"),
    ("하이브리드 서치", "BM25 + Dense (Qdrant)"),
    ("메타 필터", "시기 · 인물"),
    ("Top-K 추출", "Re-rank"),
    ("LLM Context 구성", "응답 생성"),
])

add_flow_v_slide("분야: 실시간 대화", "말벗돌봄 실시간 대화 파이프라인 (저사양 단말 최적화, 8단계)", [
    ("① VAD 감지", "WebRTC VAD — 800ms 묵음판정으로 발화종료 확정"),
    ("② 온디바이스 STT", "스트리밍 디코딩, 청크 단위 누적 처리"),
    ("③ 키워드 추출 & 의도분류", "경량 룰/정규식"),
    ("④ FTS5(BM25) 키워드 검색", "Zero-Neural RAG — 임베딩 연산 없이 자서전 청크 인출"),
    ("⑤ 동적 프롬프트 합성", "페르소나+회상기억+발화, Context 1,024 토큰 제한"),
    ("⑥ SLM 스트리밍 추론", "문장 종결부호 감지 시 즉시 문장 단위 분할"),
    ("⑦ 문장 단위 TTS 파이프라이닝", "전체 응답 대기 없이 첫 문장 즉시 합성"),
    ("⑧ 로컬 DB 영속화", "발화·참조챕터ID·응답소요시간 기록"),
], note="핵심 최적화: 임베딩모델 미상주(RAM 절감) + 문장단위 스트리밍(체감속도 단축) — decisions.md #31, #32")

add_flow_v_slide("분야: 정서 모니터링", "정서 모니터링 처리 흐름", [
    ("발화 분석", "톤 분석 + 부정 어휘 빈도 분석"),
    ("정서 점수 산출", "emotion_scores에 일별 1건 기록 (임계치와 무관하게 항상 수행)"),
    ("임계치 초과 판정", "No → 종료 / Yes → emotion_alerts 생성"),
    ("알림 발송", "notification_settings 조회 → 설정된 채널로 가족·복지사 알림"),
    ("확인 응답 대기", "No(N분 경과) → 재알림 에스컬레이션 / Yes → 케이스 종료"),
], note="⚠️ '언제 보낼지'(임계치)는 법무·윤리 검토 대기 중 — '누가·어디로 받을지'만 지금 구현 가능 (decisions.md #12, #19)")

add_flow_h_slide("분야: 비서", "비서 모드 — 일정·복약 로컬 흐름", [
    ("발화 파싱", "날짜·시간·장소·목적 엔티티 추출"),
    ("정보 충족 확인", "부족 시 재질문 루프"),
    ("로컬 DB 저장", "알림 예약 (OS 스케줄러)"),
    ("지정 시각 도달", "능동형 음성 브리핑"),
    ("응답 처리", "복용확인/무응답 에스컬레이션/거부사유 기록"),
])

add_flow_v_slide("분야: 동기화", "Wi-Fi 동기화 실패 · 충돌 해결 프로세스", [
    ("업로드 시도", "실패 시 지수 백오프 재시도(최대 N회, Do단계 확정)"),
    ("다운로드 시도", "실패 시 재시도"),
    ("체크섬 검증", "실패 시 손상 데이터 폐기 후 재다운로드"),
    ("버전 충돌 확인", "로컬-서버 충돌 시 서버 마스터 우선 적용(Server-Wins)"),
    ("동기화 완료", "로컬 캐시 정상 갱신"),
])

add_flow_h_slide("분야: 출판", "출판/인쇄 파이프라인", [
    ("전체 챕터 확정", "모든 chapters.status=confirmed"),
    ("출판 요청", "publications.status=requested"),
    ("조판 생성", "PDF(CMYK 300DPI) 또는 ePub, MinIO 저장"),
    ("완료 알림", "status=ready"),
    ("인쇄발주/다운로드", "하드커버 발주 또는 전자책 링크 제공"),
])

add_flow_v_slide("분야: 가족 협업", "가족 협업 · 감수 워크플로우 (웹)", [
    ("신규 챕터 초안 알림", "AI 생성 완료 시 가족에게 통지"),
    ("원고 대조 편집", "구술 녹취록 ↔ AI 초안 비교, 사진 업로드·타임라인 배치"),
    ("승인/반려 결정", "반려 시 AI 재생성 요청 → 초안 루프"),
    ("챕터 확정", "chapter_revisions 기록, 버전 저장"),
    ("전체 완료 확인", "모든 챕터 완료 시 출판 단계로 전환"),
])

add_flow_h_slide("분야: Closed-Loop", "서버측 Closed-Loop 3단계 상세", [
    ("검증·교정", "Whisper Large-v3 정밀 재전사 — 사투리·고유명사 보정"),
    ("지식화", "Neo4j 그래프(인물·사건·감정 관계) + Qdrant 벡터색인(BGE-M3)"),
    ("생성·감수", "온프레미스 vLLM 윤문 + Critic Agent Gap분석(Fact/Emotion/Relation/Reflection)"),
])

add_table_slide("분야: 설치모드", "설치모드 자동 분기 흐름 — 키오스크 / 일반 앱", ["구분", "키오스크 모드", "일반 앱 모드"], [
    ["대상 단말", "저사양·재활용 단말 (RAM<6GB 또는 Android≤11)", "고사양 개인 단말"],
    ["설치 방식", "Device Owner Mode(COSU)로 단일실행 잠금", "여러 앱 중 하나로 아이콘 설치"],
    ["앱 기능", "완전히 동일", "완전히 동일"],
    ["모드 결정", "설치 시 1회 자동판별, 재설치 전까지 고정 — 서버 원격전환 없음", "좌동"],
], col_widths=[3, 5, 5], note="판별기준: RAM<6GB 또는 Android≤11 중 하나라도 미달 시 보수적으로 키오스크 판정 (decisions.md #5)")

add_table_slide("분야: 관리", "관리자 업무 흐름 — 기기관리/모니터링", ["업무", "내용", "근거 화면"], [
    ["사용자 관리", "전체 사용자·가족 계정 현황 조회", "A-03"],
    ["Wi-Fi 동기화 모니터링", "sync_sessions 상태·재시도·실패 이력 추적", "A-08"],
    ["정서 알림 이력 관리", "emotion_alerts 발생·확인·케이스 종료 이력", "A-04 부속"],
    ["시스템 설정", "LLM/STT 모델 버전, 외부연계 Opt-in 정책 관리", "A-06/A-07"],
    ["기기 관리", "기기ID·사양(RAM/OS)·설치모드 조회 전용 (원격제어 없음)", "A-04"],
], col_widths=[3, 6, 3])

add_code_slide("분야: 동기화 페이로드", "Wi-Fi 하향 동기화 페이로드 예시", """{
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
}""", note="GET /api/v1/sync/download 응답 — 필드 케이싱은 snake_case 확정 (decisions.md #20)")

# ---------------------------------------------------------------- 4부 데이터모델
add_section_divider(4, "데이터 모델 & API", "17개 엔티티 · 표준 API 설계")

add_bullets_slide("4부 · 데이터/API", "데이터 모델 개요 — 17개 엔티티 (schema.md)", [
    ("핵심: users · family_members · devices · chapters · chapter_revisions", 0),
    ("사진/구술: photos · photo_requests · conversation_chunks · questions", 0),
    ("비서/정서: schedule_items · emotion_alerts · emotion_scores", 0),
    ("운영/거버넌스: sync_sessions · consent_logs · notification_settings · invitations · publications", 0),
    ("설계 원칙: DB enum은 영문 통일, API는 snake_case, 구독·결제 도메인은 Phase 1 스코프 아웃", 0, True, TEAL_DEEP),
])

# ---- ERD 허브-스포크 다이어그램 ----
s = new_slide()
title_bar(s, "4부 · 데이터/API", "핵심 엔티티 관계 (요약 ERD)")
hub = add_rect(s, Inches(5.17), Inches(1.5), Inches(3.0), Inches(0.75), fill=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
set_text(hub.text_frame, "users (어르신 — 소유 루트)", 14, WHITE, True, PP_ALIGN.CENTER)
hub.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
spokes = [
    "family_members", "devices → sync_sessions", "invitations /\nnotification_settings", "chapters →\nchapter_revisions",
    "photos ↔ conversation_chunks\n+ graph_node_ref → Neo4j", "photo_requests",
    "questions", "schedule_items", "emotion_alerts", "emotion_scores", "consent_logs /\npublications",
]
cols = 4
sw_ = Inches(2.85); sh_ = Inches(1.0); gapx = Inches(0.18); gapy = Inches(0.22)
gx0 = Inches(0.6); gy0 = Inches(3.15)
centers = []
for i, label in enumerate(spokes):
    col = i % cols; row = i // cols
    bx = Emu(int(gx0) + col * (int(sw_) + int(gapx)))
    by = Emu(int(gy0) + row * (int(sh_) + int(gapy)))
    fill = GOLD_TINT if i < 7 else SUBTLE2
    line = GOLD if i < 7 else BORDER_STRONG
    box = add_rect(s, bx, by, sw_, sh_, fill=fill, line=line)
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE; box.text_frame.word_wrap = True
    lines = label.split("\n")
    p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = lines[0]; r.font.size = Pt(11.5); r.font.bold = True; r.font.color.rgb = (GOLD_DEEP if i < 7 else INK); r.font.name = FONT
    for extra in lines[1:]:
        p2 = box.text_frame.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = extra; r2.font.size = Pt(9.5); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
    centers.append((Emu(int(bx) + int(sw_) // 2), by))
hub_bottom_center = (Emu(int(Inches(5.17)) + int(Inches(3.0)) // 2), Emu(int(Inches(1.5)) + int(Inches(0.75))))
for cx, cy in centers:
    add_line(s, hub_bottom_center[0], hub_bottom_center[1], cx, cy, color=SILVER, width=1.0)
add_footer(s)

add_table_slide("4부 · 데이터/API", "API 설계 개요", ["항목", "내용"], [
    ["프레임워크", "Python 3.11+ / FastAPI (온프레미스 자체 호스팅, 확정)"],
    ["버전 관리", "/api/v1 프리픽스, 리소스는 소유자(users) 하위로 중첩"],
    ["표준 응답 포맷", "성공: {data}, 목록: {data, pagination}, 에러: {error:{code,message,details}}"],
    ["표준 에러 코드", "VALIDATION_ERROR(400) · UNAUTHORIZED(401) · FORBIDDEN(403) · NOT_FOUND(404) · CONFLICT(409) · INTERNAL_ERROR(500)"],
    ["필드 케이싱", "서버 wire format은 snake_case 통일, 클라이언트는 각 스택 컨벤션으로 변환"],
    ["인증", "Keycloak SSO — GET /me로 로그인 세션→연결된 어르신 자동 해석(2026-09 신규)"],
], col_widths=[3, 9])

# ---------------------------------------------------------------- 5부 UI/UX
add_section_divider(5, "UI/UX · 디자인시스템", "실제 구현 화면 · BI 가이드 기반 토큰화")

add_swatch_slide("5부 · UI/UX", "디자인 시스템 — 컬러 & 타이포그래피", [
    {"hex": TEAL, "name": "Thread Teal", "hexlabel": "#1E7A8C · Primary"},
    {"hex": SILVER, "name": "Silver Mist", "hexlabel": "#8E97A6 · Secondary"},
    {"hex": GOLD, "name": "Heritage Gold", "hexlabel": "#B8935A · Accent"},
    {"hex": INK, "name": "Ink", "hexlabel": "#20242B · Text"},
    {"hex": PAPER, "name": "Paper Stone", "hexlabel": "#F4F2EE · Base"},
], [["DISPLAY", "34px / 700", "Noto Serif KR"], ["H1", "26px / 700", "Noto Serif KR"], ["H2", "20px / 600", "Noto Serif KR"], ["BODY", "16px / 400", "Pretendard"], ["CAPTION", "14px / 500", "Pretendard(WCAG AA)"]])

# ---- UI/UX 실 구현 화면 미리보기 (Phone + Browser 목업) ----
s = new_slide()
title_bar(s, "5부 · UI/UX", "실제 구현 화면 미리보기 (Do 단계, 2026-09)")
# Phone: 은실이 대화
px, py, pw, ph = Inches(0.8), Inches(1.5), Inches(3.1), Inches(5.35)
phone = add_rect(s, px, py, pw, ph, fill=INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
scr = add_rect(s, Emu(int(px) + Inches(0.12)), Emu(int(py) + Inches(0.12)), Emu(int(pw) - Inches(0.24)), Emu(int(ph) - Inches(0.24)), fill=SUBTLE2, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
avatar = add_rect(s, Emu(int(px) + int(pw) // 2 - Inches(0.45)), Emu(int(py) + Inches(0.45)), Inches(0.9), Inches(0.9), fill=TEAL, shape=MSO_SHAPE.OVAL)
try:
    from pptx.oxml.ns import qn as _qn
    gs = avatar.fill.gradient_stops
    gs[0].color.rgb = TEAL; gs[0].position = 0.0
    gs[1].color.rgb = GOLD; gs[1].position = 1.0
    avatar.fill.gradient_angle = 45
except Exception:
    avatar.fill.solid(); avatar.fill.fore_color.rgb = TEAL
name_tb = s.shapes.add_textbox(px, Emu(int(py) + Inches(1.5)), pw, Inches(0.35))
set_text(name_tb.text_frame, "은실이", 14, INK, True, PP_ALIGN.CENTER)
bubbles = [
    ("오늘 날씨가 참 좋네요. 산책은 다녀오셨어요?", False),
    ("응, 공원 한 바퀴 돌고 왔어", True),
    ("잘하셨어요! 그날 사진 한 장 보내주시면 제가 기억해둘게요 📷", False),
]
by_ = Emu(int(py) + Inches(2.0))
for text, mine in bubbles:
    bw = Inches(2.55)
    bx_ = Emu(int(px) + int(pw) - Inches(0.22) - int(bw)) if mine else Emu(int(px) + Inches(0.22))
    bh_ = Inches(0.7)
    bshape = add_rect(s, bx_, by_, bw, bh_, fill=(TEAL if mine else SURFACE), line=(None if mine else BORDER), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.28)
    bshape.text_frame.word_wrap = True; bshape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    bshape.text_frame.margin_left = Inches(0.12); bshape.text_frame.margin_right = Inches(0.12)
    p = bshape.text_frame.paragraphs[0]
    r = p.add_run(); r.text = text; r.font.size = Pt(10.5); r.font.color.rgb = (WHITE if mine else INK); r.font.name = FONT
    by_ = Emu(int(by_) + int(bh_) + Inches(0.12))
mic = add_rect(s, Emu(int(px) + int(pw) // 2 - Inches(0.3)), Emu(int(py) + int(ph) - Inches(0.85)), Inches(0.6), Inches(0.6), fill=TEAL, shape=MSO_SHAPE.OVAL)
set_text(mic.text_frame, "🎙", 18, WHITE, True, PP_ALIGN.CENTER)
mic.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
cap1 = s.shapes.add_textbox(px, Emu(int(py) + int(ph) + Inches(0.08)), pw, Inches(0.3))
set_text(cap1.text_frame, "모바일 · 은실이 대화 (통합 홈)", 12.5, TEAL_DEEP, True, PP_ALIGN.CENTER)

# Browser 1: 가족 대시보드
bx1, by1, bw1, bh1 = Inches(4.35), Inches(1.7), Inches(4.15), Inches(4.55)
brow1 = add_rect(s, bx1, by1, bw1, bh1, fill=SURFACE, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
chrome1 = add_rect(s, bx1, by1, bw1, Inches(0.4), fill=SUBTLE2, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
for i, c in enumerate([RED, GOLD, GREEN]):
    dot = add_rect(s, Emu(int(bx1) + Inches(0.15) + i * Inches(0.22)), Emu(int(by1) + Inches(0.14)), Inches(0.12), Inches(0.12), fill=c, shape=MSO_SHAPE.OVAL)
url1 = s.shapes.add_textbox(Emu(int(bx1) + Inches(1.0)), Emu(int(by1) + Inches(0.08)), Emu(int(bw1) - Inches(1.15)), Inches(0.28))
set_text(url1.text_frame, "silveryarn.family/dashboard", 9.5, INK_FAINT)
t1 = s.shapes.add_textbox(Emu(int(bx1) + Inches(0.25)), Emu(int(by1) + Inches(0.55)), Emu(int(bw1) - Inches(0.5)), Inches(0.4))
set_text(t1.text_frame, "오늘의 기억 리포트", 15, INK, True)
stat_labels = [("3회", "오늘 대화"), ("1건", "오늘 새 회고"), ("준비 중", "정서 상태")]
sw1 = Emu(int((int(bw1) - Inches(0.5) - Inches(0.16) * 2) / 3))
for i, (val, lbl) in enumerate(stat_labels):
    sx = Emu(int(bx1) + Inches(0.25) + i * (int(sw1) + Inches(0.16)))
    stat = add_rect(s, sx, Emu(int(by1) + Inches(1.05)), sw1, Inches(0.85), fill=SUBTLE2)
    stat.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = stat.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = val; r.font.size = Pt(15 if i < 2 else 11); r.font.bold = True; r.font.color.rgb = (TEAL_DEEP if i < 2 else INK_FAINT); r.font.name = FONT
    p2 = stat.text_frame.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run(); r2.text = lbl; r2.font.size = Pt(9); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
card1 = add_rect(s, Emu(int(bx1) + Inches(0.25)), Emu(int(by1) + Inches(2.1)), Emu(int(bw1) - Inches(0.5)), Emu(int(bh1) - Inches(2.35)), fill=SURFACE, line=BORDER)
card1.text_frame.word_wrap = True; card1.text_frame.margin_left = Inches(0.15); card1.text_frame.margin_top = Inches(0.12)
p = card1.text_frame.paragraphs[0]
r = p.add_run(); r.text = "AI 요약 · 주요 회고"; r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = GOLD_DEEP; r.font.name = FONT
p2 = card1.text_frame.add_paragraph()
r2 = p2.add_run(); r2.text = "\"국민학교 시절, 겨울이면 운동장에 물을 얼려 스케이트장을 만들곤 했지요…\""; r2.font.size = Pt(10.5); r2.font.color.rgb = INK_MUTED; r2.font.name = FONT
cap2 = s.shapes.add_textbox(bx1, Emu(int(by1) + int(bh1) + Inches(0.08)), bw1, Inches(0.3))
set_text(cap2.text_frame, "웹 · 가족 대시보드", 12.5, TEAL_DEEP, True, PP_ALIGN.CENTER)

# Browser 2: 사진 갤러리
bx2, by2, bw2, bh2 = Inches(8.85), Inches(1.7), Inches(3.75), Inches(4.55)
brow2 = add_rect(s, bx2, by2, bw2, bh2, fill=SURFACE, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
chrome2 = add_rect(s, bx2, by2, bw2, Inches(0.4), fill=SUBTLE2, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
for i, c in enumerate([RED, GOLD, GREEN]):
    dot = add_rect(s, Emu(int(bx2) + Inches(0.15) + i * Inches(0.22)), Emu(int(by2) + Inches(0.14)), Inches(0.12), Inches(0.12), fill=c, shape=MSO_SHAPE.OVAL)
url2 = s.shapes.add_textbox(Emu(int(bx2) + Inches(1.0)), Emu(int(by2) + Inches(0.08)), Emu(int(bw2) - Inches(1.15)), Inches(0.28))
set_text(url2.text_frame, "silveryarn.family/photos", 9.5, INK_FAINT)
t2 = s.shapes.add_textbox(Emu(int(bx2) + Inches(0.25)), Emu(int(by2) + Inches(0.55)), Emu(int(bw2) - Inches(0.5)), Inches(0.4))
set_text(t2.text_frame, "사진 갤러리", 15, INK, True)
tile_colors = [SILVER, TEAL, GOLD, GREEN, SILVER_DEEP, GOLD_DEEP]
tile_years = ["1972", "1985", "1998", "2005", "2018", "2024"]
tcols = 3; tw = Emu(int((int(bw2) - Inches(0.5) - Inches(0.12) * 2) / 3)); th = Inches(0.85)
for i, (c, yr) in enumerate(zip(tile_colors, tile_years)):
    col = i % tcols; row = i // tcols
    tx = Emu(int(bx2) + Inches(0.25) + col * (int(tw) + Inches(0.12)))
    ty = Emu(int(by2) + Inches(1.1) + row * (int(th) + Inches(0.12)))
    tile = add_rect(s, tx, ty, tw, th, fill=c)
    tile.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    p = tile.text_frame.paragraphs[0]
    r = p.add_run(); r.text = yr; r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
    tile.text_frame.margin_left = Inches(0.08); tile.text_frame.margin_bottom = Inches(0.05)
cap3 = s.shapes.add_textbox(bx2, Emu(int(by2) + int(bh2) + Inches(0.08)), bw2, Inches(0.3))
set_text(cap3.text_frame, "웹 · 사진 갤러리", 12.5, TEAL_DEEP, True, PP_ALIGN.CENTER)
note = s.shapes.add_textbox(Inches(0.8), SH - Inches(0.42), SW - Inches(1.6), Inches(0.32))
set_text(note.text_frame, "모바일은 하단 탭 없이 대화 하나로 통합(눌러서 시작 또는 실 VAD 자동 감지) · 웹은 Next.js Server Component + Keycloak 세션 기반", 11, INK_FAINT)

# ---------------------------------------------------------------- 6부 보안/기술스택
add_section_divider(6, "보안 · 기술스택", "3중 스택 · RBAC · 온프레미스 원칙")

add_bullets_slide("6부 · 보안", "보안 설계 원칙", [
    ("DB 암호화(AES-256) 및 전송구간 암호화(TLS 1.3) — 온디바이스 로컬 캐시도 동일 수준", 0),
    ("웹 콘솔 2FA, 역할별 차등 열람 권한(RBAC)", 0),
    ("외부 연계 시 PII 마스킹 전처리 + 동의 로그 필수, 미동의 시 전량 온프레미스 경로", 0),
    ("Wi-Fi 동기화는 등록된 신뢰 네트워크에서만 — SSID 등은 온디바이스 로컬 전용 저장", 0),
    ("Device Owner Mode(COSU) 채택 — 단말 탈취·우회 방지", 0),
    ("설치모드 판별 임계값(확정): RAM<6GB 또는 Android≤11 → 키오스크", 0, True, TEAL_DEEP),
])

add_table_slide("6부 · 기술스택", "기술 스택 요약", ["영역", "스택", "상태"], [
    ["모바일", "Android 네이티브(Kotlin), Device Owner Mode", "✅ 확정"],
    ["서버 백엔드", "Python 3.11+ / FastAPI", "✅ 확정"],
    ["웹 콘솔", "Next.js(App Router) + TypeScript + Tailwind", "✅ 확정"],
    ["LLM 추론", "자체 호스팅 vLLM · A100 GPU", "✅ 확정 — 외부 GPT-4o/Claude 미채택"],
    ["Vector DB", "Qdrant self-hosted", "✅ 확정"],
    ["지식 그래프", "Neo4j self-hosted", "✅ 확정"],
    ["RDB / Storage", "PostgreSQL+Alembic / 자체 MinIO", "✅ 확정"],
    ["인증", "Keycloak SSO", "✅ 확정"],
    ["온디바이스 SLM", "Kanana-2, Qwen2.5-0.5B 벤치마크 후보", "🔄 실기기 벤치마크 대기(#27)"],
], col_widths=[2.2, 5.3, 4.5])

# ---------------------------------------------------------------- 7부 의사결정 & CTO 요약
add_section_divider(7, "의사결정 & CTO팀 검토 하이라이트", "확정 사항 요약 · 7개 관점 종합판정")

add_bullets_slide("7부 · 의사결정", "확정된 주요 의사결정", [
    ("설치모드 임계값: RAM<6GB 또는 Android≤11 → 키오스크 / 구현: Device Owner Mode(COSU)", 0),
    ("모바일: Android 네이티브(Kotlin) · 서버: FastAPI · 웹: Next.js · 인증: Keycloak SSO", 0),
    ("법무·인프라·경영 미결 14건(Q1~Q6·I1~I5·경영3) 전부 확정 + 구현 완료 (decisions.md #52~#65)", 0, True, TEAL_DEEP),
    ("모바일 UI 패러다임 전환 — 하단 탭 제거, '은실이' 대화 화면 하나로 통합 (decisions.md #66~#68)", 0, True, TEAL_DEEP),
    ("웹 실 인증 세션 연결 — GET /me 신규, ?userId= 임시 패턴 제거 (decisions.md #69)", 0, True, TEAL_DEEP),
    ("남은 유일한 실측 대기 항목: 온디바이스 SLM 모델 선정 — 실기기 벤치마크 필요 (#27/#9/#31)", 0),
], note="상세 47건 전체 이력은 docs/01-plan/decisions/silveryarn-platform.decisions.md 참조")

add_table_slide("7부 · CTO팀 검토", "CTO팀 검토 — 7개 관점 종합", ["관점", "종합 판정"], [
    ["Enterprise Architect", "Go with Conditions — 하이브리드 구조·동기화 계약 정비 후 착수"],
    ["Infrastructure Architect", "Go with Conditions — 온프레미스 GPU 클러스터 구성 확정 필요"],
    ["Security Architect", "Go with Conditions — PII 암호화·동의·보유기간·인가모델 5대 리스크 전부 해소 완료"],
    ["Frontend Architect", "Go with Conditions — WCAG AA 대비비 컬러 토큰 재조정 완료"],
    ["Backend/API", "Go with Conditions — 엔티티↔서비스 소유권 매핑 정비 완료"],
    ["QA Strategist", "Go with Conditions — 실기기 벤치마크 하니스 준비 완료"],
    ["Product Manager", "Go with Conditions — 스코프 우선순위 명확"],
], col_widths=[3, 9], note="7개 관점 전원 공통 판정: Go with Conditions — No-go 시사 관점 없음. Blocker 28건 전부 정책 확정 또는 구현 완료(cto-review-2026-09-05.md, 2026-09-05 착수 시점 스냅샷)")

# ---------------------------------------------------------------- 8부 로드맵
add_section_divider(8, "로드맵 & Action Items", "Phase 1~3 · 파일럿 목표 · 다음 실행 항목")

add_table_slide("8부 · 로드맵", "단계별 개발 로드맵", ["Phase", "범위", "상태"], [
    ["Phase 1", "온디바이스 오프라인 대화 + 온프레미스 배치 동기화 + 자서전/말벗돌봄/비서 3모드 + 출판 파이프라인", "🔄 Do 단계 진행 중"],
    ["Phase 2", "정서 모니터링 파이프라인 활성화(법무 기준 확정 후), 외부 TTS 고급 연계 검토", "⏳ 대기"],
    ["Phase 3", "외부 클라우드 AI 선택적 연계(Opt-in, DPA 체결 후), 구독·결제 도메인", "⏳ 대기"],
], col_widths=[2, 8, 3], note="3개월 내 소규모 파일럿을 1차 목표로 확정 (decisions.md #63)")

add_bullets_slide("8부 · Next Steps", "Action Items", [
    ("온디바이스 SLM 모델 최종 선정 — 실기기 3종(S10급/A35급/S24급) 벤치마크 실행 (#27/#9/#31)", 0, True, GOLD_DEEP),
    ("정서 모니터링 알림 임계치·수신대상 — 법무·윤리 검토 완료 후 피처플래그 ON", 0),
    ("모바일 사진 화면 신규 — report.md '다음 사이클' 후보로 계속 검토", 0),
    ("Phase 1~3 정식 예산·인력 — 경영진 최종 승인 대기", 0),
], note="세부 이력·근거는 docs/04-report/features/silveryarn-platform.report.md 및 decisions.md 참조")

s = new_slide(bg=INK)
add_rect(s, 0, SH - Inches(0.12), SW, Inches(0.12), fill=TEAL)
add_rect(s, 0, Inches(0), Inches(0.12), SH, fill=GOLD)
tb = s.shapes.add_textbox(Inches(1.0), Inches(3.0), Inches(11), Inches(1.2))
set_text(tb.text_frame, "감사합니다", 56, WHITE, True)
tb2 = s.shapes.add_textbox(Inches(1.0), Inches(4.0), Inches(11), Inches(0.6))
set_text(tb2.text_frame, "Q & A", 24, TEAL_TINT)
tb3 = s.shapes.add_textbox(Inches(1.0), Inches(6.55), Inches(11), Inches(0.5))
set_text(tb3.text_frame, "은빛실타래 (SilverYarn) · NUBiz AX Initiative · 2026년 9월", 14, INK_FAINT)

# ================================================================ SAVE
OUT = "은빛실타래_설계발표_슬라이드.pptx"
prs.save(OUT)
print("Saved " + OUT + " - " + str(len(prs.slides._sldIdLst)) + " slides")

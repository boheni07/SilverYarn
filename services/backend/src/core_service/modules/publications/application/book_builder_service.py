"""조판 엔진 — design.md §2.6 "조판 엔진: 하드커버용 PDF 또는 ePub 생성 → MinIO 저장"의
실제 구현. `worker.py`의 `process_publication` arq 잡이 이 서비스를 호출한다.

PDF는 reportlab, ePub은 EbookLib으로 생성한다 — 둘 다 순수 로컬 라이브러리라
vLLM/STT처럼 "실제 서비스가 없어 REST 계약을 추정"할 필요가 없는 몇 안 되는
파이프라인이다(Zero External Data Egress 원칙과도 자연히 부합).

⚠️ **스코프**: 여기서 만드는 PDF는 "하드커버 인쇄 발주"에 바로 넘길 수 있는
CMYK 300DPI 인쇄소 규격 조판물이 아니다 — 실제 표지 디자인·트림/블리드 규격은
BI 가이드·인쇄소 사양이 확정돼야 나올 수 있는 산출물이라(디자인 결정 필요),
지금은 RGB, 화면/가정용 프린터 기준의 "읽을 수 있는 완성본"까지만 만든다.
"하드커버 인쇄 발주·배송"(schema.md §3.17 Description)은 여전히 스코프 밖.
"""

import io
import uuid

from ebooklib import epub
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from core_service.core.clients.storage_client import StorageClient
from core_service.modules.author.application.chapter_service import ChapterService
from core_service.modules.author.domain.chapter import Chapter, ChapterPeriod
from core_service.modules.publications.domain.publication import PublicationFormat
from core_service.modules.publications.infrastructure.publication_repository import (
    PublicationRepository,
)

# schema.md §7 한글 표시명 매핑 — upload_pipeline_service.PERIOD_DISPLAY_NAME과 동일
# 내용을 이 모듈에서도 필요로 해 복제했다(모듈 경계상 sync.application을 직접
# import할 수 없음). 두 곳 다 4개 고정값이라 당장은 shared/ 승격 없이 유지.
_PERIOD_DISPLAY_NAME: dict[ChapterPeriod, str] = {
    ChapterPeriod.CHILDHOOD: "유년기",
    ChapterPeriod.YOUTH: "청년기",
    ChapterPeriod.ADULTHOOD: "중장년기",
    ChapterPeriod.PRESENT: "현재",
}

# Adobe 표준 CJK CID 폰트 — 별도 폰트 파일 임베딩 없이 reportlab이 기본 제공하는
# 리소스만으로 한글을 렌더링한다(PDF 리더가 자체 CJK 폰트로 대체 렌더링).
_KOREAN_FONT = "HYSMyeongJo-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(_KOREAN_FONT))


class BookBuilderService:
    def __init__(
        self,
        publication_repo: PublicationRepository,
        chapter_service: ChapterService,
        storage_client: StorageClient,
    ):
        self._publications = publication_repo
        self._chapters = chapter_service
        self._storage = storage_client

    async def build(self, publication_id: uuid.UUID) -> None:
        publication = await self._publications.get_by_id(publication_id)
        if publication is None:
            raise LookupError(f"publication {publication_id} not found")

        await self._publications.mark_processing(publication_id)
        chapters = await self._chapters.list_chapters_for_user(publication.user_id)

        if publication.format == PublicationFormat.EPUB:
            data = self._build_epub(publication.user_id, chapters)
            content_type = "application/epub+zip"
            ext = "epub"
        else:
            data = self._build_pdf(chapters)
            content_type = "application/pdf"
            ext = "pdf"

        object_name = f"{publication.user_id}/{publication.id}.{ext}"
        bucket = self._storage.publications_bucket
        await self._storage.ensure_bucket(bucket=bucket)
        await self._storage.put_object(object_name, data, content_type, bucket=bucket)
        await self._publications.mark_ready(publication_id, object_name)

    def _build_pdf(self, chapters: list[Chapter]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=25 * mm,
            bottomMargin=25 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )
        title_style = ParagraphStyle("title", fontName=_KOREAN_FONT, fontSize=20, leading=28, spaceAfter=12)
        chapter_title_style = ParagraphStyle(
            "chapter_title", fontName=_KOREAN_FONT, fontSize=16, leading=22, spaceAfter=10
        )
        body_style = ParagraphStyle("body", fontName=_KOREAN_FONT, fontSize=11, leading=18)

        story = [Paragraph("자서전", title_style), Spacer(1, 20 * mm), PageBreak()]
        for chapter in chapters:
            period_kr = _PERIOD_DISPLAY_NAME[chapter.period]
            story.append(
                Paragraph(f"제{chapter.chapter_no}장 — {chapter.title} ({period_kr})", chapter_title_style)
            )
            # reportlab Paragraph는 원문의 개행을 그대로 살리지 않으므로 <br/>로 치환.
            for paragraph_text in chapter.body_text.split("\n\n"):
                escaped = paragraph_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(escaped.replace("\n", "<br/>"), body_style))
                story.append(Spacer(1, 4 * mm))
            story.append(PageBreak())

        doc.build(story)
        return buffer.getvalue()

    def _build_epub(self, user_id: uuid.UUID, chapters: list[Chapter]) -> bytes:
        book = epub.EpubBook()
        book.set_identifier(str(user_id))
        book.set_title("자서전")
        book.set_language("ko")

        items = []
        for chapter in chapters:
            period_kr = _PERIOD_DISPLAY_NAME[chapter.period]
            html_body = "".join(f"<p>{p}</p>" for p in chapter.body_text.split("\n\n"))
            item = epub.EpubHtml(
                title=f"제{chapter.chapter_no}장 — {chapter.title}",
                file_name=f"chapter_{chapter.chapter_no}.xhtml",
                lang="ko",
            )
            item.content = f"<h1>제{chapter.chapter_no}장 — {chapter.title} ({period_kr})</h1>{html_body}"
            book.add_item(item)
            items.append(item)

        book.toc = tuple(items)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", *items]

        # EbookLib의 write_epub은 내부적으로 zipfile.ZipFile(name, ...)을 그대로 열므로
        # 파일 경로 문자열 대신 BytesIO(파일 유사 객체)를 넘겨도 그대로 동작한다 —
        # 디스크에 임시 파일을 만들 필요가 없다.
        buffer = io.BytesIO()
        epub.write_epub(buffer, book)
        return buffer.getvalue()

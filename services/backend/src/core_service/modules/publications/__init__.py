"""publications 모듈 — 자서전 인쇄/출판 파이프라인(schema.md §3.17, design.md §2.6).

기획서 3.3(MinIO "완성 PDF/ePub")·6장(자동 조판)·흐름도 2.4(Publish→Print) 대응.
전체 챕터가 `confirmed` 상태에 도달해야 출판 요청이 가능하다(design.md §2.6 전제조건).

**스코프**: 조판(PDF/ePub 생성)과 MinIO 저장까지만 다룬다. 하드커버 인쇄 발주·배송·
주문관리는 "Phase 3 이후 별도 확정"으로 스코프 아웃(schema.md §3.17, decisions.md #64
결제 도메인 스코프아웃과 동일한 이유 — 실제 인쇄소·배송사 연동은 경영/조달 결정 필요).
그래서 `status`는 이 구현에서 `requested → processing → ready`까지만 자동 전이하고
`delivered`(인쇄물 수령/전자책 다운로드 완료)는 아직 별도 엔드포인트로 노출하지 않는다.

PDF는 reportlab(한글 CID 폰트, 외부 폰트 파일 임베딩 없이 Adobe 표준 CJK 리소스만
사용), ePub은 EbookLib로 생성한다 — 둘 다 순수 로컬 라이브러리라 Zero External Data
Egress 원칙(기획서 3.1)에 저촉되지 않는다(vLLM/STT처럼 외부 서비스 계약을 추정할
필요가 없는 몇 안 되는 파이프라인).
"""

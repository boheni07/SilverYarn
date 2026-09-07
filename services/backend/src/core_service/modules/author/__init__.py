"""author 모듈 — 자서전 작가 모드.

chapters/chapter_revisions: 4계층(api/application/domain/infrastructure) 구현 완료 —
참조 패턴은 users/devices 모듈과 동일. workflow-diagrams.md §4(초안 생성)와
§7(감수)을 코드 레벨에서 분리했다 — ChapterService.save_draft()는 §4에서
worker.py 파이프라인이 호출할 자리(TODO, 아직 미연결)이고, review_chapter()만
chapter_revisions를 생성한다(M-5).

TODO(다음 스프린트):
- questions: 회고 질문 큐
- photos/photo_requests: 사진 인라인 편입
- worker.py의 process_upload 잡에서 save_draft() 실제 호출 연결
설계 근거: workflow-diagrams.md §4/§7, design.md §2.11.
"""

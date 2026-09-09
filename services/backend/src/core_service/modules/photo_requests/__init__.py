"""photo_requests 모듈 — 가족→당사자 사진 추가 요청(schema.md §3.7).

invitations 모듈과 같은 이유로 조회·닫기 엔드포인트를 함께 둔다(만들기만 하고 볼
방법이 없으면 WU3→WF3 루프가 끝나지 않음). 요청 충족(fulfilled)은 별도 엔드포인트가
아니라 `POST /photos/{id}/complete`가 `deps.py`를 통해 이 모듈을 호출해 자동 처리한다.
"""

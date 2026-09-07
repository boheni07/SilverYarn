"""family_members 모듈 — 가족/복지사(2차 사용자). users/devices/author와 동일한 4계층 참조 패턴.

이 모듈은 author 모듈의 `chapter_revisions.reviewer_id`, sync-contract.md 무관 다수의
FK(photo_requests.requested_by, emotion_alerts.acknowledged_by, consent_logs.granted_by,
invitations.invited_by 등)가 참조하는 루트 엔티티라 먼저 구현했다.

TODO(다음 스프린트): invitations 모듈 구현 후 "초대 수락 → family_members 행 생성" 흐름을
정식 온보딩 경로로 연결(design.md §4.2 `POST /api/v1/invitations`). 지금 이 모듈의
`POST /users/{userId}/family-members`는 그 전 단계의 임시 직접생성 경로다.
"""

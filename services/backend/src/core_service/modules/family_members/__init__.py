"""family_members 모듈 — 가족/복지사(2차 사용자). users/devices/author와 동일한 4계층 참조 패턴.

이 모듈은 author 모듈의 `chapter_revisions.reviewer_id`, sync-contract.md 무관 다수의
FK(photo_requests.requested_by, emotion_alerts.acknowledged_by, consent_logs.granted_by,
invitations.invited_by 등)가 참조하는 루트 엔티티라 먼저 구현했다.

정식 온보딩 경로는 `invitations` 모듈(구현 완료)의 `POST /invitations/{token}/accept`다 —
이 모듈의 `POST /users/{userId}/family-members`는 여전히 존재하지만 임시 직접생성
경로로 남겨둔다(테스트·관리자 도구용). 프런트엔드 사용자 온보딩 플로우는 초대 경로를
써야 한다.
"""

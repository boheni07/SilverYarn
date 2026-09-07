"""invitations 모듈 — 가족 구성원 초대(design.md §4.2 `POST /api/v1/invitations`).

family_members 모듈의 `POST /users/{userId}/family-members`(임시 직접생성 경로,
family_members/__init__.py TODO 참조)를 대체하는 정식 온보딩 경로다: 초대 생성 →
초대 수락 시 이 모듈이 family_members.deps를 통해 실제 family_members 행을 만든다.

만료 정책(현재 7일 기본값, `DEFAULT_EXPIRY_DAYS`)은 비즈니스 결정 없이 편의상 정한
값이다 — decisions.md에 정식 등재된 수치가 아니므로 Do 단계에서 재확인 필요.
"""

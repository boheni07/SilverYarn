# GlitchTip 초기 부트스트랩(계정·조직·프로젝트·DSN) — decisions.md #61(I4).
#
# Keycloak realm처럼 --import-realm으로 한 번에 못 올린다(GlitchTip은 그런 가져오기
# 기능이 없다) — 대신 Django ORM을 `manage.py shell`로 직접 돌려 동일한 결과(수동
# UI 클릭 없이 재현 가능한 로컬 개발 계정)를 만든다. get_or_create라 여러 번 실행해도
# 안전하고, 한 번 만든 프로젝트 키(DSN)는 볼륨에 남아 재부팅해도 그대로다.
#
# docker-compose.yml의 glitchtip-bootstrap 서비스가 이 파일을
# `python manage.py shell` stdin으로 흘려보낸다 — 실행 후 로그에 찍히는 DSN을
# .env.local의 OBS_GLITCHTIP_DSN에 붙여넣으면 백엔드 에러 리포팅이 켜진다.

from django.contrib.auth import get_user_model

from apps.organizations_ext.models import Organization, OrganizationUserRole
from apps.projects.models import Project, ProjectKey

DEV_EMAIL = "dev@silveryarn.local"
DEV_PASSWORD = "silveryarn_local_dev"
ORG_SLUG = "silveryarn"
PROJECT_SLUG = "backend"

User = get_user_model()
user, user_created = User.objects.get_or_create(
    email=DEV_EMAIL, defaults={"is_superuser": True, "is_staff": True}
)
if user_created:
    user.set_password(DEV_PASSWORD)
    user.save()
    print(f"[glitchtip-bootstrap] 계정 생성: {DEV_EMAIL} / {DEV_PASSWORD} (로컬 개발 전용)")
else:
    print(f"[glitchtip-bootstrap] 계정 이미 있음: {DEV_EMAIL}")

org, org_created = Organization.objects.get_or_create(name=ORG_SLUG, slug=ORG_SLUG)
if org_created or not org.organization_users.filter(user=user).exists():
    org.add_user(user, role=OrganizationUserRole.OWNER)
print(f"[glitchtip-bootstrap] 조직: {org.slug} ({'신규' if org_created else '기존'})")

project, project_created = Project.objects.get_or_create(
    organization=org, name=PROJECT_SLUG, slug=PROJECT_SLUG
)
print(f"[glitchtip-bootstrap] 프로젝트: {project.slug} ({'신규' if project_created else '기존'})")

key = project.projectkey_set.first() or ProjectKey.objects.create(project=project)
print(f"[glitchtip-bootstrap] DSN: {key.get_dsn()}")
print("[glitchtip-bootstrap] 이 DSN을 .env.local의 OBS_GLITCHTIP_DSN에 붙여넣으세요.")

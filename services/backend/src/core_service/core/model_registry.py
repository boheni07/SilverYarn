"""모든 모듈의 ORM 모델을 한 곳에서 import — `Base.metadata`에 전 테이블을 등록한다.

⚠️ **실제 DB로 엔드투엔드 테스트하다 발견한 버그의 수정**: SQLAlchemy는 FK를
`ForeignKey("users.id")`처럼 문자열 테이블명으로 선언하면, 그 테이블을 정의하는
모델 클래스가 **같은 프로세스에서 import된 적이 있어야만** 매핑을 해석할 수 있다.
`worker.py`가 `UserModel`을 import하지 않은 채(자신이 직접 쓰는 Chapter/
ConversationChunk/SyncSession 리포지토리만 import) `conversation_chunks`(FK로
`users.id` 참조)를 flush하자 `NoReferencedTableError`가 발생했다 — 개별 모델
import 목록을 여러 진입점(main.py/worker.py/migrations/env.py)에 따로 유지하면
이런 누락이 재발하기 쉽다. 이제 모든 진입점이 이 모듈 하나만 import한다.
"""

from core_service.modules.author.infrastructure.chapter_repository import ChapterModel  # noqa: F401
from core_service.modules.author.infrastructure.chapter_revision_repository import (  # noqa: F401
    ChapterRevisionModel,
)
from core_service.modules.care.infrastructure.conversation_chunk_repository import (  # noqa: F401
    ConversationChunkModel,
)
from core_service.modules.devices.infrastructure.device_repository import DeviceModel  # noqa: F401
from core_service.modules.family_members.infrastructure.family_member_repository import (  # noqa: F401
    FamilyMemberModel,
)
from core_service.modules.invitations.infrastructure.invitation_repository import (  # noqa: F401
    InvitationModel,
)
from core_service.modules.photos.infrastructure.photo_repository import PhotoModel  # noqa: F401
from core_service.modules.schedule.infrastructure.schedule_item_repository import (  # noqa: F401
    ScheduleItemModel,
)
from core_service.modules.sync.infrastructure.sync_repository import SyncSessionModel  # noqa: F401
from core_service.modules.users.infrastructure.user_repository import UserModel  # noqa: F401

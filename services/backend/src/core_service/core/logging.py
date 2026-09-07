"""로깅 설정 — 구조화 로그(JSON) 기본, PII(schema.md §5 컬럼) 로그 출력 금지 원칙."""

import logging
import sys


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # 액세스 로그 등 서드파티 로거의 과도한 verbosity 억제
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not debug else logging.INFO)

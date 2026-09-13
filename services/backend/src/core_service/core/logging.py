"""로깅 설정 — 구조화 로그(JSON), PII(schema.md §5 컬럼) 로그 출력 금지 원칙.

decisions.md #61(2026-09-12 사용자 결정, I4) 전까지는 JSON을 표방하면서 실제로는
일반 텍스트 포맷을 썼다(문서·코드 드리프트) — 관측 스택(Grafana Alloy → Loki)이
JSON 필드로 라벨링·필터링하려면 실제 JSON이어야 해서 이번에 바로잡았다.
"""

import logging
import sys
from pathlib import Path

from pythonjsonlogger.jsonlogger import JsonFormatter

_JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(debug: bool = False, log_file: str = "") -> None:
    """stdout에는 항상 JSON 한 줄씩 남긴다. `log_file`이 있으면 같은 포맷으로
    파일에도 남긴다 — Grafana Alloy(컨테이너)가 그 파일을 tail해 Loki로 보낸다
    (백엔드가 컨테이너 밖 호스트 프로세스라 push 대신 파일 공유 방식, decisions.md #61).
    파일 쓰기 실패(권한 등)는 앱 기동을 막지 않고 경고만 남긴다.
    """
    level = logging.DEBUG if debug else logging.INFO
    formatter = JsonFormatter(_JSON_FORMAT, rename_fields={"asctime": "timestamp", "levelname": "level"})

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        except OSError as exc:
            logging.getLogger(__name__).warning(
                "OBS_LOG_FILE(%s)에 쓸 수 없어 stdout에만 로깅합니다: %s", log_file, exc
            )

    for handler in handlers:
        handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = handlers

    # 액세스 로그 등 서드파티 로거의 과도한 verbosity 억제
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not debug else logging.INFO)

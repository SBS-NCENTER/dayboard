"""숨긴 천체 이벤트 date 집합 영속(data/hidden_events.json). 서버 공유 필터 상태."""

import json

from . import config

_PATH = config.DATA_DIR / "hidden_events.json"


def load() -> set[str]:
    try:
        return set(json.loads(_PATH.read_text(encoding="utf-8")))
    except OSError, ValueError:
        return set()


def save(dates) -> None:
    config.ensure_runtime_dirs()
    _PATH.write_text(json.dumps(sorted(set(map(str, dates)))), encoding="utf-8")

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryLogger:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.log_path = self.base_dir / ".automation_history.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def log(self, payload: dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {"timestamp": timestamp, **payload}
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

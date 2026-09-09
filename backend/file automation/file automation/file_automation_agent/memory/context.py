from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContextMemory:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.storage_path = self.base_dir / ".automation_context.json"
        self.last_file: str | None = None
        self.last_folder: str | None = None
        self.history: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.last_file = data.get("last_file")
        self.last_folder = data.get("last_folder")
        self.history = data.get("history", [])

    def _save(self) -> None:
        payload = {
            "last_file": self.last_file,
            "last_folder": self.last_folder,
            "history": self.history[-100:],
        }
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def remember_file(self, path: str | Path) -> str:
        resolved = str(Path(path).expanduser().resolve())
        self.last_file = resolved
        self.history.append({"type": "file", "path": resolved})
        self._save()
        return resolved

    def remember_folder(self, path: str | Path) -> str:
        resolved = str(Path(path).expanduser().resolve())
        self.last_folder = resolved
        self.history.append({"type": "folder", "path": resolved})
        self._save()
        return resolved

    def resolve_reference(self, text: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9\s]", "", (text or "").strip().lower())
        if re.search(r"\b(it|this|that|this file|that file)\b", normalized):
            return self.last_file
        if re.search(r"\b(this folder|that folder)\b", normalized):
            return self.last_folder
        return None

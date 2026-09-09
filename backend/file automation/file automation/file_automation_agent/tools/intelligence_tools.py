from __future__ import annotations

import hashlib
from pathlib import Path

from file_automation_agent.filesystem.path_manager import make_safe_filename, sanitize_filename
from file_automation_agent.safety.validator import SafetyValidator
from file_automation_agent.tools.file_tools import read_file


def analyze_file_content(path: str, preview_chars: int = 2000) -> dict:
    try:
        result = read_file(path, max_chars=preview_chars)
        if not result.get("ok"):
            return result
        return {
            "ok": True,
            "path": result["path"],
            "preview": result["content"],
            "length": len(result["content"]),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def generate_filename(path: str, suggested_name: str | None = None, extension: str | None = None) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        source_name = sanitized = (suggested_name or target.stem).strip()
        safe_name = sanitize_filename(source_name)
        file_extension = extension or target.suffix
        filename = make_safe_filename(safe_name, file_extension)
        return {"ok": True, "path": str(target), "suggested_name": filename}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def detect_duplicates(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        root = validator.validate_path(path, require_existing=True)
        hashes: dict[str, list[str]] = {}
        for child in root.rglob("*"):
            if child.is_file():
                digest = hashlib.sha256(child.read_bytes()).hexdigest()
                hashes.setdefault(digest, []).append(str(child))
        duplicates = [{"hash": digest, "paths": paths} for digest, paths in hashes.items() if len(paths) > 1]
        return {"ok": True, "duplicates": duplicates}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def organize_files(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        root = validator.validate_path(path, require_existing=True)
        for child in root.iterdir():
            if child.is_file():
                target_dir = root / (child.suffix.lower().lstrip(".") or "other")
                target_dir.mkdir(exist_ok=True)
                destination = target_dir / child.name
                if child != destination:
                    child.rename(destination)
        return {"ok": True, "path": str(root), "organized": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

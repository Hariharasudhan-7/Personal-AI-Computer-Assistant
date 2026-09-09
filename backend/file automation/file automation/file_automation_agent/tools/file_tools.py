from __future__ import annotations

import shutil
import os
from pathlib import Path

from pypdf import PdfReader

from file_automation_agent.safety.validator import SafetyValidator


def create_file(path: str, content: str = "") -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_destination(path, overwrite=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target), "bytes": target.stat().st_size}
    except Exception as exc:  # pragma: no cover - handled in tests via assertions
        return {"ok": False, "error": str(exc)}


def read_file(path: str, max_chars: int = 20000) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        if target.suffix.lower() == ".pdf":
            pages = PdfReader(str(target)).pages
            text = "\n".join(page.extract_text() or "" for page in pages)
        else:
            text = target.read_text(encoding="utf-8")
        return {"ok": True, "path": str(target), "content": text[:max_chars], "truncated": len(text) > max_chars}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def write_file(path: str, content: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target), "bytes": target.stat().st_size}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def append_file(path: str, content: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return {"ok": True, "path": str(target), "bytes": target.stat().st_size}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def rename_file(path: str, new_path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        destination = validator.validate_destination(new_path, overwrite=False)
        target.rename(destination)
        return {"ok": True, "source": str(target), "destination": str(destination)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def delete_file(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        validator.confirm_destructive_action("delete", target, confirmed=True)
        target.unlink()
        return {"ok": True, "path": str(target)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def copy_file(path: str, destination: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        source = validator.validate_path(path, require_existing=True)
        dest = validator.validate_destination(destination, overwrite=False)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return {"ok": True, "source": str(source), "destination": str(dest)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def move_file(path: str, destination: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        source = validator.validate_path(path, require_existing=True)
        dest = validator.validate_destination(destination, overwrite=False)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        return {"ok": True, "source": str(source), "destination": str(dest)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def open_file(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        os.startfile(str(target))
        return {"ok": True, "path": str(target), "opened": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

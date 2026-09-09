from __future__ import annotations

import shutil
from pathlib import Path

from file_automation_agent.safety.validator import SafetyValidator


def create_folder(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_destination(path, overwrite=False)
        target.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": str(target)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_directory(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        items = []
        for child in sorted(target.iterdir()):
            items.append({
                "name": child.name,
                "path": str(child),
                "is_dir": child.is_dir(),
                "is_file": child.is_file(),
                "size": child.stat().st_size if child.is_file() else None,
            })
        return {"ok": True, "path": str(target), "items": items}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def rename_folder(path: str, new_path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        source = validator.validate_path(path, require_existing=True)
        destination = validator.validate_destination(new_path, overwrite=False)
        source.rename(destination)
        return {"ok": True, "source": str(source), "destination": str(destination)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def delete_folder(path: str, recursive: bool = True) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        validator.confirm_destructive_action("delete_folder", target, confirmed=True)
        shutil.rmtree(target, ignore_errors=False) if recursive else target.rmdir()
        return {"ok": True, "path": str(target)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def copy_folder(path: str, destination: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        source = validator.validate_path(path, require_existing=True)
        dest = validator.validate_destination(destination, overwrite=False)
        shutil.copytree(source, dest)
        return {"ok": True, "source": str(source), "destination": str(dest)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def move_folder(path: str, destination: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        source = validator.validate_path(path, require_existing=True)
        dest = validator.validate_destination(destination, overwrite=False)
        shutil.move(str(source), str(dest))
        return {"ok": True, "source": str(source), "destination": str(dest)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def open_folder(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        return {"ok": True, "path": str(target), "exists": target.exists()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

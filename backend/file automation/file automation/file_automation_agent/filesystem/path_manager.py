from __future__ import annotations

import re
from pathlib import Path


SPECIAL_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "home": Path.home(),
    "workspace": Path.cwd(),
}


def resolve_input_path(base_dir: str | Path, raw_path: str | Path) -> Path:
    base = Path(base_dir).expanduser().resolve()
    if raw_path is None:
        return base
    if isinstance(raw_path, Path):
        candidate = raw_path.expanduser()
    else:
        candidate = Path(raw_path).expanduser()

    if candidate.is_absolute():
        return candidate.resolve()

    if str(candidate).lower() in SPECIAL_FOLDERS:
        return SPECIAL_FOLDERS[str(candidate).lower()].resolve()

    if str(candidate).startswith("~"):
        return candidate.expanduser().resolve()

    if candidate.parts and candidate.parts[0].lower() in SPECIAL_FOLDERS:
        mapped = SPECIAL_FOLDERS[candidate.parts[0].lower()]
        return (mapped / Path(*candidate.parts[1:])).resolve()

    return (base / candidate).resolve()


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._ -]", "_", filename)
    sanitized = sanitized.strip().strip(".")
    sanitized = re.sub(r"\s+", "_", sanitized)
    sanitized = re.sub(r"_+", "_", sanitized)
    if not sanitized:
        sanitized = "untitled"
    return sanitized


def normalize_extension(filename: str) -> str:
    path = Path(filename)
    return path.suffix.lower()


def make_safe_filename(base_name: str, extension: str | None = None) -> str:
    safe_base = sanitize_filename(base_name)
    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
        return f"{safe_base}{ext}"
    return safe_base

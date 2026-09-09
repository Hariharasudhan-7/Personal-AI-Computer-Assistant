from __future__ import annotations

from pathlib import Path

from file_automation_agent.safety.validator import SafetyValidator


def search_files(path: str, name: str | None = None, extension: str | None = None, size_gt: int | None = None) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        root = validator.validate_path(path, require_existing=True)
        results = []
        for child in root.rglob("*"):
            if child.is_file():
                if name and name.lower() not in child.name.lower():
                    continue
                if extension and child.suffix.lower() != extension.lower():
                    continue
                if size_gt is not None and child.stat().st_size <= size_gt:
                    continue
                results.append({"name": child.name, "path": str(child), "extension": child.suffix or "", "size": child.stat().st_size})
        return {"ok": True, "results": results}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def search_file_content(path: str, query: str, case_sensitive: bool = False) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        root = validator.validate_path(path, require_existing=True)
        results = []
        needle = query if case_sensitive else query.lower()
        for child in root.rglob("*"):
            if child.is_file() and child.suffix.lower() in {".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".html", ".css", ".xml", ".yaml", ".yml", ".log"}:
                try:
                    text = child.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                haystack = text if case_sensitive else text.lower()
                if needle in haystack:
                    results.append({"path": str(child), "matches": text.count(query) if case_sensitive else text.lower().count(query.lower())})
        return {"ok": True, "results": results}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_file_metadata(path: str) -> dict:
    try:
        validator = SafetyValidator(Path(path).resolve().parent)
        target = validator.validate_path(path, require_existing=True)
        stat = target.stat()
        return {
            "ok": True,
            "path": str(target),
            "name": target.name,
            "extension": target.suffix,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

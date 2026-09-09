from __future__ import annotations

from pathlib import Path


class SafetyValidator:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_path(self, value: str | Path, require_existing: bool = False) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = (self.base_dir / candidate).resolve()
        else:
            candidate = candidate.resolve()

        if ".." in Path(value).parts:
            raise ValueError(f"Path traversal is not allowed: {value}")

        try:
            candidate.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"Path is outside the permitted base directory: {value}")

        if require_existing and not candidate.exists():
            raise FileNotFoundError(f"Path does not exist: {candidate}")

        return candidate

    def validate_destination(self, destination: str | Path, overwrite: bool = False) -> Path:
        target = self.validate_path(destination)
        if target.exists() and not overwrite:
            raise ValueError(f"Destination already exists: {target}")
        return target

    def confirm_destructive_action(self, action: str, target: str | Path, confirmed: bool = False) -> bool:
        if not confirmed:
            raise ValueError(f"{action} requires explicit confirmation before executing against {target}")
        return True

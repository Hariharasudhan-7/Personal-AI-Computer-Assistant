from pathlib import Path

import pytest

from file_automation_agent.safety.validator import SafetyValidator


def test_rejects_path_traversal(tmp_path: Path):
    validator = SafetyValidator(base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        validator.validate_path("../outside.txt")


def test_rejects_absolute_path_outside_base(tmp_path: Path):
    validator = SafetyValidator(base_dir=str(tmp_path))
    outside = tmp_path.parent / "outside.txt"

    with pytest.raises(ValueError):
        validator.validate_path(str(outside))


def test_rejects_sibling_with_similar_name(tmp_path: Path):
    validator = SafetyValidator(base_dir=str(tmp_path))
    sibling = Path(f"{tmp_path}_backup") / "file.txt"

    with pytest.raises(ValueError):
        validator.validate_path(str(sibling))


def test_rejects_overwrite_without_confirmation(tmp_path: Path):
    validator = SafetyValidator(base_dir=str(tmp_path))
    target = tmp_path / "a.txt"
    target.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError):
        validator.validate_destination(str(target), overwrite=False)


def test_delete_requires_confirmation(tmp_path: Path):
    validator = SafetyValidator(base_dir=str(tmp_path))
    target = tmp_path / "delete_me.txt"
    target.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError):
        validator.confirm_destructive_action("delete", target, confirmed=False)

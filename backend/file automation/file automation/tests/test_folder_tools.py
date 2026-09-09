from pathlib import Path

from file_automation_agent.tools.folder_tools import (
    copy_folder,
    create_folder,
    delete_folder,
    list_directory,
    move_folder,
    rename_folder,
)


def test_folder_lifecycle(tmp_path: Path):
    folder = tmp_path / "project"
    result = create_folder(str(folder))
    assert result["ok"] is True

    nested = tmp_path / "project" / "nested"
    create_folder(str(nested))
    (nested / "note.txt").write_text("hello", encoding="utf-8")

    listing = list_directory(str(folder))
    assert listing["ok"] is True
    assert any(item["name"] == "nested" for item in listing["items"])

    renamed = rename_folder(str(folder), str(tmp_path / "renamed_project"))
    assert renamed["ok"] is True
    assert not folder.exists()
    assert (tmp_path / "renamed_project").exists()

    copied = copy_folder(str(tmp_path / "renamed_project"), str(tmp_path / "copy_project"))
    assert copied["ok"] is True

    moved = move_folder(str(tmp_path / "copy_project"), str(tmp_path / "moved_project"))
    assert moved["ok"] is True

    deleted = delete_folder(str(tmp_path / "moved_project"), recursive=True)
    assert deleted["ok"] is True
    assert not (tmp_path / "moved_project").exists()

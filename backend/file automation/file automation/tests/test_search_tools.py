from pathlib import Path

from file_automation_agent.tools.search_tools import (
    get_file_metadata,
    search_file_content,
    search_files,
)


def test_search_features(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "report.txt").write_text("Quarterly report about invoice processing\n", encoding="utf-8")
    (docs / "summary.md").write_text("# Summary\nThis is about architecture\n", encoding="utf-8")
    (docs / "empty.log").write_text("log entry\n", encoding="utf-8")

    name_matches = search_files(str(tmp_path), name="report")
    assert name_matches["ok"] is True
    assert any(item["name"] == "report.txt" for item in name_matches["results"])

    extension_matches = search_files(str(tmp_path), extension=".md")
    assert extension_matches["ok"] is True
    assert any(item["name"] == "summary.md" for item in extension_matches["results"])

    content_matches = search_file_content(str(tmp_path), query="invoice")
    assert content_matches["ok"] is True
    assert any("report.txt" in item["path"] for item in content_matches["results"])

    metadata = get_file_metadata(str(docs / "report.txt"))
    assert metadata["ok"] is True
    assert metadata["path"].endswith("report.txt")

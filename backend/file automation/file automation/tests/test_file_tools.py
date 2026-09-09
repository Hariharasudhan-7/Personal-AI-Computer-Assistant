from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from file_automation_agent.tools.file_tools import (
    append_file,
    copy_file,
    create_file,
    delete_file,
    move_file,
    read_file,
    rename_file,
    write_file,
)
from file_automation_agent.tools.intelligence_tools import analyze_file_content


def test_file_lifecycle(tmp_path: Path):
    target = tmp_path / "example.txt"

    result = create_file(str(target), "hello world")
    assert result["ok"] is True
    assert target.exists()

    read_result = read_file(str(target))
    assert read_result["ok"] is True
    assert read_result["content"] == "hello world"

    write_result = write_file(str(target), "updated text")
    assert write_result["ok"] is True

    append_result = append_file(str(target), "\nsecond line")
    assert append_result["ok"] is True

    renamed = rename_file(str(target), str(tmp_path / "renamed.txt"))
    assert renamed["ok"] is True
    assert not target.exists()
    assert (tmp_path / "renamed.txt").exists()

    copied = copy_file(str(tmp_path / "renamed.txt"), str(tmp_path / "copy.txt"))
    assert copied["ok"] is True

    moved = move_file(str(tmp_path / "copy.txt"), str(tmp_path / "moved.txt"))
    assert moved["ok"] is True

    deleted = delete_file(str(tmp_path / "moved.txt"))
    assert deleted["ok"] is True
    assert not (tmp_path / "moved.txt").exists()


def test_read_file_extracts_pdf_text(tmp_path: Path):
    pdf = tmp_path / "document.pdf"
    content = b"BT /F1 12 Tf 72 720 Td (PDF content) Tj ET"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    stream = DecodedStreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = writer._add_object(stream)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }),
        }),
    })
    with pdf.open("wb") as handle:
        writer.write(handle)

    result = read_file(str(pdf))

    assert result["ok"] is True
    assert "PDF content" in result["content"]


def test_analyze_file_content_extracts_pdf_text(tmp_path: Path):
    pdf = tmp_path / "analysis.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 72 720 Td (Analysis PDF) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }),
        }),
    })
    with pdf.open("wb") as handle:
        writer.write(handle)

    result = analyze_file_content(str(pdf))

    assert result["ok"] is True
    assert "Analysis PDF" in result["preview"]

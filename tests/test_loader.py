import pytest

from spec_auditor.loader import next_available, read_specs


def test_markdown_files_are_loaded(tmp_path):
    (tmp_path / "a.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "b.md").write_text("beta", encoding="utf-8")

    assert read_specs(tmp_path) == {"a.md": "alpha", "b.md": "beta"}


def test_previous_reports_are_not_audited(tmp_path):
    (tmp_path / "spec.md").write_text("content", encoding="utf-8")
    (tmp_path / "audit-report.md").write_text("old report", encoding="utf-8")
    (tmp_path / "audit-report.v1.md").write_text("older report", encoding="utf-8")

    assert list(read_specs(tmp_path)) == ["spec.md"]


def test_non_markdown_files_are_ignored(tmp_path):
    (tmp_path / "spec.md").write_text("content", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

    assert list(read_specs(tmp_path)) == ["spec.md"]


def test_empty_folder_is_an_error(tmp_path):
    with pytest.raises(SystemExit, match="No specification files"):
        read_specs(tmp_path)


def test_first_report_keeps_the_plain_name(tmp_path):
    assert next_available(tmp_path / "audit-report.md").name == "audit-report.md"


def test_existing_reports_are_never_overwritten(tmp_path):
    (tmp_path / "audit-report.md").write_text("first", encoding="utf-8")
    assert next_available(tmp_path / "audit-report.md").name == "audit-report.v1.md"

    (tmp_path / "audit-report.v1.md").write_text("second", encoding="utf-8")
    assert next_available(tmp_path / "audit-report.md").name == "audit-report.v2.md"



import pytest
from pydantic import ValidationError

from spec_auditor.models import (
    AuditReport,
    DefectType,
    Evidence,
    Finding,
    Severity,
)


def make_finding(file="a.md", severity=Severity.HIGH, defect=DefectType.AMBIGUITY, files=None):
    sources = files or [file]
    return Finding(
        evidence=[Evidence(file=f, quote="the system must respond quickly") for f in sources],
        section="Delivery Details",
        issue="No measurable threshold is defined.",
        defect_type=defect,
        severity=severity,
        suggested_fix="State a specific response time.",
    )


def test_short_quotes_are_rejected():
    with pytest.raises(ValidationError, match="at least 4 words"):
        Evidence(file="a.md", quote="quickly")


def test_unknown_severity_is_rejected():
    with pytest.raises(ValidationError):
        Finding(
            evidence=[Evidence(file="a.md", quote="the system must respond quickly")],
            section="X",
            issue="Y",
            defect_type=DefectType.AMBIGUITY,
            severity="Critical",
            suggested_fix="Z",
        )


def test_a_finding_needs_at_least_one_piece_of_evidence():
    with pytest.raises(ValidationError):
        Finding(
            evidence=[],
            section="X",
            issue="Y",
            defect_type=DefectType.AMBIGUITY,
            severity=Severity.LOW,
            suggested_fix="Z",
        )


def test_severity_counts_include_zeros():
    report = AuditReport(findings=[make_finding(severity=Severity.HIGH)], reviewed_files=["a.md"])

    assert report.counts_by_severity() == {"High": 1, "Medium": 0, "Low": 0}


def test_counts_always_match_the_findings_list():
    report = AuditReport(
        findings=[make_finding(), make_finding(severity=Severity.LOW)],
        reviewed_files=["a.md"],
    )

    assert report.total == 2
    assert sum(report.counts_by_severity().values()) == report.total


def test_ledger_lists_files_with_no_findings():
    report = AuditReport(findings=[make_finding(file="a.md")], reviewed_files=["a.md", "b.md"])

    assert report.coverage_ledger() == {"a.md": 1, "b.md": 0}


def test_cross_file_findings_count_against_every_file():
    report = AuditReport(
        findings=[make_finding(files=["a.md", "b.md"])],
        reviewed_files=["a.md", "b.md"],
    )

    assert report.coverage_ledger() == {"a.md": 1, "b.md": 1}
    assert report.findings[0].is_cross_file


import pytest
from pydantic import ValidationError

from spec_auditor.models import (
    AuditReport,
    DefectType,
    Evidence,
    Finding,
    Severity,
)


def make_finding(file="a.md", severity=Severity.HIGH, defect=DefectType.AMBIGUITY, files=None):
    sources = files or [file]
    return Finding(
        evidence=[Evidence(file=f, quote="the system must respond quickly") for f in sources],
        section="Delivery Details",
        issue="No measurable threshold is defined.",
        defect_type=defect,
        severity=severity,
        suggested_fix="State a specific response time.",
    )


def test_short_quotes_are_rejected():
    with pytest.raises(ValidationError, match="at least 4 words"):
        Evidence(file="a.md", quote="quickly")


def test_unknown_severity_is_rejected():
    with pytest.raises(ValidationError):
        Finding(
            evidence=[Evidence(file="a.md", quote="the system must respond quickly")],
            section="X",
            issue="Y",
            defect_type=DefectType.AMBIGUITY,
            severity="Critical",
            suggested_fix="Z",
        )


def test_a_finding_needs_at_least_one_piece_of_evidence():
    with pytest.raises(ValidationError):
        Finding(
            evidence=[],
            section="X",
            issue="Y",
            defect_type=DefectType.AMBIGUITY,
            severity=Severity.LOW,
            suggested_fix="Z",
        )


def test_severity_counts_include_zeros():
    report = AuditReport(findings=[make_finding(severity=Severity.HIGH)], reviewed_files=["a.md"])

    assert report.counts_by_severity() == {"High": 1, "Medium": 0, "Low": 0}


def test_counts_always_match_the_findings_list():
    report = AuditReport(
        findings=[make_finding(), make_finding(severity=Severity.LOW)],
        reviewed_files=["a.md"],
    )

    assert report.total == 2
    assert sum(report.counts_by_severity().values()) == report.total


def test_ledger_lists_files_with_no_findings():
    report = AuditReport(findings=[make_finding(file="a.md")], reviewed_files=["a.md", "b.md"])

    assert report.coverage_ledger() == {"a.md": 1, "b.md": 0}


def test_cross_file_findings_count_against_every_file():
    report = AuditReport(
        findings=[make_finding(files=["a.md", "b.md"])],
        reviewed_files=["a.md", "b.md"],
    )

    assert report.coverage_ledger() == {"a.md": 1, "b.md": 1}
    assert report.findings[0].is_cross_file
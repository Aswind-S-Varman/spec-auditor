from spec_auditor.models import AuditReport, AuditResponse, DefectType, Evidence, Finding, Severity
from spec_auditor.validate import coverage_gaps, normalise, verify

DOCUMENTS = {
    "pricing.md": "## Discount Tiers\n\nOrders over RM100 receive a 10% discount.\n",
    "checkout.md": "The system must respond quickly when validating the postcode.\n",
}


def finding(file: str, quote: str) -> Finding:
    return Finding(
        evidence=[Evidence(file=file, quote=quote)],
        section="Discount Tiers",
        issue="Boundary is ambiguous.",
        defect_type=DefectType.LOGICAL_ERROR,
        severity=Severity.HIGH,
        suggested_fix="State 'RM100 or more'.",
    )


def test_quote_present_in_the_source_is_kept():
    response = AuditResponse(findings=[finding("pricing.md", "Orders over RM100 receive a 10% discount")])

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 1
    assert rejected == []


def test_whitespace_differences_are_tolerated():
    response = AuditResponse(findings=[finding("pricing.md", "Orders  over   RM100\nreceive a 10% discount")])

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 1


def test_typographic_punctuation_is_tolerated():
    documents = {"a.md": "The user's order is confirmed immediately."}
    response = AuditResponse(findings=[finding("a.md", "The user\u2019s order is confirmed")])

    report, _ = verify(response, documents)

    assert report.total == 1


def test_fabricated_quote_is_rejected():
    response = AuditResponse(findings=[finding("pricing.md", "Orders over RM500 receive a 50% discount")])

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 0
    assert "not found verbatim" in rejected[0].reason


def test_quote_attributed_to_the_wrong_file_is_rejected():
    response = AuditResponse(findings=[finding("checkout.md", "Orders over RM100 receive a 10% discount")])

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 0
    assert "not found verbatim" in rejected[0].reason


def test_unknown_file_is_rejected():
    response = AuditResponse(findings=[finding("ghost.md", "Orders over RM100 receive a 10% discount")])

    _, rejected = verify(response, DOCUMENTS)

    assert "unknown file" in rejected[0].reason


def test_cross_file_finding_requires_every_quote_to_check_out():
    good = Evidence(file="pricing.md", quote="Orders over RM100 receive a 10% discount")
    bad = Evidence(file="checkout.md", quote="Orders over RM200 qualify for free shipping")

    response = AuditResponse(
        findings=[
            Finding(
                evidence=[good, bad],
                section="Shipping",
                issue="Thresholds disagree.",
                defect_type=DefectType.INCONSISTENCY,
                severity=Severity.HIGH,
                suggested_fix="Align the thresholds.",
            )
        ]
    )

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 0
    assert len(rejected) == 1


def test_valid_findings_survive_alongside_rejected_ones():
    response = AuditResponse(
        findings=[
            finding("pricing.md", "Orders over RM100 receive a 10% discount"),
            finding("pricing.md", "Orders over RM999 receive a free unicorn"),
        ]
    )

    report, rejected = verify(response, DOCUMENTS)

    assert report.total == 1
    assert len(rejected) == 1


def test_every_supplied_file_enters_the_ledger():
    report, _ = verify(AuditResponse(findings=[]), DOCUMENTS)

    assert report.coverage_ledger() == {"checkout.md": 0, "pricing.md": 0}
    assert coverage_gaps(report, DOCUMENTS) == []


def test_normalise_leaves_words_untouched():
    assert normalise("  a   b \n c ") == "a b c"



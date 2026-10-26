from collections import Counter
from collections.abc import Sequence

from .models import AuditReport, Severity
from .validate import Rejection

SEVERITIES = [severity.value for severity in Severity]


def _escape(value: str) -> str:
    """A literal pipe would split the cell and corrupt the whole table."""
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _severity_breakdown(report: AuditReport, key) -> dict[str, Counter]:
    breakdown: dict[str, Counter] = {}
    for finding in report.findings:
        for group in key(finding):
            breakdown.setdefault(group, Counter())[finding.severity.value] += 1
    return breakdown


def _breakdown_rows(breakdown: dict[str, Counter]) -> list[str]:
    rows = []
    for group in sorted(breakdown):
        counts = breakdown[group]
        cells = [str(counts.get(severity, 0)) for severity in SEVERITIES]
        rows.append(f"| {_escape(group)} | {' | '.join(cells)} | {sum(counts.values())} |")
    return rows


def _evidence_cell(finding) -> str:
    return "<br>".join(
        f"**{_escape(item.file)}**: \"{_escape(item.quote)}\"" for item in finding.evidence
    )


def render_markdown(report: AuditReport, rejected: Sequence[Rejection] = ()) -> str:
    severities = report.counts_by_severity()

    lines = [
        "# Specification Audit Report",
        "",
        f"**{report.total} finding(s)** across {len(report.reviewed_files)} file(s) — "
        f"High: {severities['High']}, Medium: {severities['Medium']}, Low: {severities['Low']}",
        "",
        "## A. Findings by file",
        "",
        f"| File | {' | '.join(SEVERITIES)} | Total |",
        "|---|---|---|---|---|",
    ]

    by_file = _severity_breakdown(report, lambda finding: finding.files)
    for file in sorted(report.reviewed_files):
        counts = by_file.get(file, Counter())
        cells = [str(counts.get(severity, 0)) for severity in SEVERITIES]
        lines.append(f"| {_escape(file)} | {' | '.join(cells)} | {sum(counts.values())} |")

    lines += [
        "",
        "## B. Findings by type",
        "",
        f"| Type | {' | '.join(SEVERITIES)} | Total |",
        "|---|---|---|---|---|",
    ]
    by_type = _severity_breakdown(report, lambda finding: [finding.defect_type.value])
    lines += _breakdown_rows(by_type) or ["| _None_ | 0 | 0 | 0 | 0 |"]

    lines += [
        "",
        "## C. Detailed findings",
        "",
        "| # | Files | Section | Evidence | Issue | Type | Severity | Suggested fix |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for number, finding in enumerate(report.findings, start=1):
        lines.append(
            f"| {number} "
            f"| {_escape(', '.join(finding.files))} "
            f"| {_escape(finding.section)} "
            f"| {_evidence_cell(finding)} "
            f"| {_escape(finding.issue)} "
            f"| {finding.defect_type.value} "
            f"| {finding.severity.value} "
            f"| {_escape(finding.suggested_fix)} |"
        )
    if not report.findings:
        lines.append("| - | - | - | - | No findings | - | - | - |")

    lines += ["", "## D. Summary", ""] + _summary_lines(report, by_type, rejected)

    lines += [
        "",
        "## E. Coverage ledger",
        "",
        "| File | Status |",
        "|---|---|",
    ]
    for file, count in report.coverage_ledger().items():
        lines.append(f"| {_escape(file)} | Reviewed, findings: {count} |")

    return "\n".join(lines) + "\n"


def _summary_lines(report, by_type, rejected) -> list[str]:
    severities = report.counts_by_severity()

    lines = [
        f"- **Total findings:** {report.total} "
        f"(High {severities['High']}, Medium {severities['Medium']}, Low {severities['Low']})",
    ]

    if by_type:
        ranked = sorted(by_type.items(), key=lambda item: -sum(item[1].values()))
        themes = ", ".join(f"{name} ({sum(counts.values())})" for name, counts in ranked[:3])
        lines.append(f"- **Most common types:** {themes}")

    cross_file = [f for f in report.findings if f.is_cross_file]
    if cross_file:
        lines.append(
            f"- **Cross-file conflicts:** {len(cross_file)} — these need agreement between "
            "document owners before either can be corrected."
        )

    if severities["High"]:
        lines.append(f"- **Fix first:** the {severities['High']} High-severity finding(s).")

    if rejected:
        lines.append(
            f"- **Discarded:** {len(rejected)} proposed finding(s) were dropped because their "
            "quoted evidence could not be located in the source."
        )

    return lines



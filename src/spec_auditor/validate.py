import re
from dataclasses import dataclass

from .models import AuditReport, AuditResponse, Finding

_WHITESPACE = re.compile(r"\s+")

# Models routinely return typographic punctuation where the source had plain ASCII.
_PUNCTUATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
)


def normalise(text: str) -> str:
    """Collapse whitespace and punctuation variants without changing the words."""
    return _WHITESPACE.sub(" ", text.translate(_PUNCTUATION)).strip()


@dataclass
class Rejection:
    finding: Finding
    reason: str


def _problem_with(finding: Finding, sources: dict[str, str]) -> str | None:
    for item in finding.evidence:
        if item.file not in sources:
            return f"evidence attributed to unknown file '{item.file}'"
        if normalise(item.quote) not in sources[item.file]:
            return f"quote not found verbatim in {item.file}"
    return None


def verify(
    response: AuditResponse, documents: dict[str, str]
) -> tuple[AuditReport, list[Rejection]]:
    """Keep only findings whose every quote exists in the document it cites."""
    sources = {name: normalise(content) for name, content in documents.items()}

    kept: list[Finding] = []
    rejected: list[Rejection] = []

    for finding in response.findings:
        reason = _problem_with(finding, sources)
        if reason is None:
            kept.append(finding)
        else:
            rejected.append(Rejection(finding=finding, reason=reason))

    report = AuditReport(findings=kept, reviewed_files=sorted(documents))
    return report, rejected


def coverage_gaps(report: AuditReport, documents: dict[str, str]) -> list[str]:
    """Files that were supplied but never made it into the ledger."""
    return sorted(set(documents) - set(report.reviewed_files))



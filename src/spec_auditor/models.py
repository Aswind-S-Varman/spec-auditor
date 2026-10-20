from collections import Counter
from enum import Enum

from pydantic import BaseModel, Field, field_validator

MIN_QUOTE_WORDS = 4


class Severity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DefectType(str, Enum):
    INCONSISTENCY = "Inconsistency"
    LOGICAL_ERROR = "Logical error"
    AMBIGUITY = "Ambiguity"
    INCOMPLETENESS = "Incompleteness"
    TERMINOLOGY = "Terminology"
    BROKEN_REFERENCE = "Broken reference"
    DOMAIN_ERROR = "Domain error"


class Evidence(BaseModel):
    """A verbatim snippet and the file it came from."""

    file: str = Field(min_length=1)
    quote: str = Field(min_length=1)

    @field_validator("quote")
    @classmethod
    def quote_must_be_substantial(cls, value: str) -> str:
        # A one-word quote cannot locate an issue, and is trivial to fabricate.
        if len(value.split()) < MIN_QUOTE_WORDS:
            raise ValueError(f"quote must contain at least {MIN_QUOTE_WORDS} words")
        return value


class Finding(BaseModel):
    evidence: list[Evidence] = Field(min_length=1)
    section: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    defect_type: DefectType
    severity: Severity
    suggested_fix: str = Field(min_length=1)

    @property
    def files(self) -> list[str]:
        return sorted({item.file for item in self.evidence})

    @property
    def is_cross_file(self) -> bool:
        return len(self.files) > 1


class AuditReport(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    reviewed_files: list[str] = Field(default_factory=list)

    def counts_by_severity(self) -> dict[str, int]:
        counts = Counter(finding.severity.value for finding in self.findings)
        return {severity.value: counts.get(severity.value, 0) for severity in Severity}

    def counts_by_type(self) -> dict[str, int]:
        counts = Counter(finding.defect_type.value for finding in self.findings)
        return {
            defect.value: counts[defect.value]
            for defect in DefectType
            if counts.get(defect.value)
        }

    def coverage_ledger(self) -> dict[str, int]:
        """Every reviewed file with its finding count, including files with none."""
        counts = Counter(file for finding in self.findings for file in finding.files)
        return {file: counts.get(file, 0) for file in sorted(self.reviewed_files)}

    @property
    def total(self) -> int:
        return len(self.findings)



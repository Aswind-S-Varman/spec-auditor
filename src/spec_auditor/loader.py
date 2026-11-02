from pathlib import Path

REPORT_PREFIX = "audit-report"


def read_specs(folder: Path) -> dict[str, str]:
    """Every Markdown file in the folder, excluding reports this tool produced."""
    if not folder.is_dir():
        raise SystemExit(f"Not a folder: {folder}")

    documents = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(folder.glob("*.md"))
        if not path.name.startswith(REPORT_PREFIX)
    }

    if not documents:
        raise SystemExit(f"No specification files found in {folder}")

    return documents


def next_available(path: Path) -> Path:
    """Never overwrite an existing report; return report.v1.md, report.v2.md, and so on."""
    if not path.exists():
        return path

    version = 1
    while True:
        candidate = path.with_name(f"{path.stem}.v{version}{path.suffix}")
        if not candidate.exists():
            return candidate
        version += 1



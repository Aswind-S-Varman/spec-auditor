import argparse
from pathlib import Path

from .client import GeminiClient, InvalidModelOutput, audit_documents
from .config import settings
from .docx_export import build_docx
from .loader import next_available, read_specs
from .prompt import DocumentTooLargeError
from .report import render_markdown
from .validate import verify


def parse_args():
    parser = argparse.ArgumentParser(
        prog="spec-auditor",
        description="Audit a folder of Markdown specifications for quality defects.",
    )
    parser.add_argument("folder", help="Folder containing the specification files")
    parser.add_argument("-o", "--output", help="Where to write the report (default: the input folder)")
    parser.add_argument("--model", default=settings.model_name, help="Model name")
    parser.add_argument("--api-key", default=None, help="Overrides GEMINI_API_KEY from the environment")
    return parser.parse_args()


def main():
    args = parse_args()
    folder = Path(args.folder)
    documents = read_specs(folder)

    api_key = args.api_key or settings.gemini_api_key
    if not api_key:
        raise SystemExit("No API key. Set GEMINI_API_KEY in .env or pass --api-key.")

    print(f"Auditing {len(documents)} file(s): {', '.join(documents)}")

    try:
        response = audit_documents(documents, GeminiClient(api_key=api_key, model=args.model))
    except DocumentTooLargeError as exc:
        raise SystemExit(str(exc))
    except InvalidModelOutput as exc:
        raise SystemExit(f"The model did not return a usable audit: {exc}")

    report, rejected = verify(response, documents)

    for rejection in rejected:
        print(f"  discarded a finding: {rejection.reason}")

    output_dir = Path(args.output) if args.output else folder
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = next_available(output_dir / "audit-report.md")
    markdown_path.write_text(render_markdown(report, rejected), encoding="utf-8")

    docx_path = markdown_path.with_suffix(".docx")
    docx_path.write_bytes(build_docx(report))

    severities = report.counts_by_severity()
    print(
        f"\n{report.total} finding(s) kept — High {severities['High']}, "
        f"Medium {severities['Medium']}, Low {severities['Low']}"
    )
    print(f"Wrote {markdown_path}")
    print(f"Wrote {docx_path}")



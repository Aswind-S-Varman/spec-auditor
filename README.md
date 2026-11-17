# spec-auditor


LLM-based quality auditor for requirement specifications, with verifiable findings.


Spec Auditor sends a set of Markdown specifications to Google Gemini and asks for
defects such as contradictions, ambiguities, broken references and gaps. Every
finding must quote its evidence verbatim. Before anything is reported, each quote
is checked against the source file it cites. Findings whose quotes can't be found
are discarded and counted, not shown.


> **Data notice:** auditing sends document text to Google Gemini. Use fictional or
> non-sensitive documents only. Findings require human review.


## Features


- Audits several files together, including contradictions between files.
- Evidence grounding: findings with unverifiable quotes are rejected.
- Structured output validated with Pydantic, with one automatic retry that tells
  the model why its previous response was rejected.
- Markdown and Word (`.docx`) reports with breakdowns by file and type, detailed
  findings, a summary and a coverage ledger.
- Command-line tool and Streamlit web app.
- A fixed, human-reviewed example report that runs without an API key.


## Requirements


- Python 3.10+
- A Gemini API key (not needed to view the example report)


## Installation


```powershell
pip install -e ".[app,gemini,dev]"
```


| Extra | Installs | Needed for |
|---|---|---|
| `gemini` | `google-genai` | Live audits |
| `app` | `streamlit` | Web app |
| `dev` | `pytest` | Tests |


`requirements.txt` installs the `app` and `gemini` extras.


## Configuration


Settings come from environment variables or a `.env` file in the working directory:


| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | _(empty)_ | Gemini API key. The CLI's `--api-key` overrides it. |
| `MODEL_NAME` | `gemini-2.0-flash` | Gemini model used for audits. |


Never commit `.env` files or API keys.


## Usage


### Command line


```powershell
spec-auditor samples/specs
spec-auditor samples/specs -o reports --model gemini-2.0-flash
```


| Argument | Description |
|---|---|
| `folder` | Folder containing the `.md` specifications. Files starting with `audit-report` are skipped. |
| `-o`, `--output` | Output folder (default: the input folder). |
| `--model` | Model name (default: `MODEL_NAME`). |
| `--api-key` | API key (default: `GEMINI_API_KEY`). |


The CLI writes `audit-report.md` and `audit-report.docx`. Existing reports are never
overwritten: later runs write `audit-report.v1.md`, `audit-report.v2.md`, and so on.
Rejected findings are printed with the reason they were discarded.


### Web app


```powershell
streamlit run src/spec_auditor/app.py
```


Enter an API key and model, upload up to 5 Markdown files (100 KB each, unique
names), then select **Run audit**. Or select **Load reviewed example** to see a
report without calling the API. Results show summary metrics, a findings table,
per-file coverage, the full Markdown report and download buttons.


The theme lives in `.streamlit/config.toml`. Light and dark palettes are defined, and
users can switch between them from the app's main menu.


## Python API


The package can be used as a library. The pipeline has four steps:


```python
from pathlib import Path


from spec_auditor.client import GeminiClient, audit_documents
from spec_auditor.docx_export import build_docx
from spec_auditor.loader import read_specs
from spec_auditor.report import render_markdown
from spec_auditor.validate import verify


documents = read_specs(Path("samples/specs"))            # {filename: text}
client = GeminiClient(api_key="...", model="gemini-2.0-flash")


response = audit_documents(documents, client)            # 1. ask the model
report, rejected = verify(response, documents)           # 2. check the evidence
markdown = render_markdown(report, rejected)             # 3. Markdown report
word_bytes = build_docx(report)                          # 4. Word report
```


### Functions


| Function | Module | Description |
|---|---|---|
| `read_specs(folder) -> dict[str, str]` | `loader` | Reads every `*.md` file in a folder, skipping `audit-report*` files. Exits if the folder is missing or contains no specifications. |
| `next_available(path) -> Path` | `loader` | Returns `path`, or the first unused `name.vN.ext` if it already exists. |
| `build_user_prompt(documents) -> str` | `prompt` | Builds the prompt with `--- FILE: name ---` boundaries, in sorted filename order. Raises `DocumentTooLargeError` over the size limits. |
| `audit_documents(documents, client) -> AuditResponse` | `client` | Calls the model and parses the JSON. Retries once with the validation error, then raises `InvalidModelOutput`. |
| `parse_response(raw) -> AuditResponse` | `client` | Strips code fences and validates the model's JSON against the schema. |
| `verify(response, documents) -> (AuditReport, list[Rejection])` | `validate` | Keeps only findings whose every quote appears verbatim in the cited file, after normalising whitespace and typographic punctuation. |
| `render_markdown(report, rejected=()) -> str` | `report` | Renders the Markdown report (sections A–E). |
| `build_docx(report) -> bytes` | `docx_export` | Builds the Word report directly from the report object. |
| `build_example_report() -> AuditReport` | `examples` | Returns the fixed, human-reviewed example report. |


### Using another model provider


`audit_documents` accepts any object that matches the `ModelClient` protocol:


```python
class ModelClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...
```


`complete` receives the system prompt and user prompt and must return the raw
response text. `GeminiClient` calls `generate_content` with
`response_mime_type="application/json"` and `temperature=0`. A stub client that
returns canned JSON is enough for tests.


### Data model


Defined in `spec_auditor.models` (Pydantic v2):


- **`Evidence`**: `file`, `quote`. Quotes must be at least 4 words long.
- **`Finding`**: `evidence` (one or more), `section`, `issue`, `defect_type`,
  `severity`, `suggested_fix`. Also has the properties `files` and `is_cross_file`.
- **`AuditResponse`**: `findings`. This is exactly what the model must return.
- **`AuditReport`**: `findings`, `reviewed_files`, plus `total`,
  `counts_by_severity()`, `counts_by_type()` and `coverage_ledger()`.
- **`Rejection`** (`validate`): the discarded `finding` and the `reason`.


`DefectType`: Inconsistency, Logical error, Ambiguity, Incompleteness, Terminology,
Broken reference, Domain error.
`Severity`: High, Medium, Low.


Example model response:


```json
{
  "findings": [
    {
      "evidence": [
        {"file": "pricing.md", "quote": "Promotional discounts stack with tier discounts."},
        {"file": "pricing.md", "quote": "Promotional discounts do not stack with tier discounts."}
      ],
      "section": "3. Promotional Codes",
      "issue": "The same section both permits and prohibits discount stacking.",
      "defect_type": "Inconsistency",
      "severity": "High",
      "suggested_fix": "Confirm the intended policy and remove the conflicting statement."
    }
  ]
}
```


### Limits and errors


| Limit | Value | Where enforced |
|---|---|---|
| Characters per file | 20,000 | `prompt.MAX_CHARS_PER_FILE` |
| Combined characters | 60,000 | `prompt.MAX_TOTAL_CHARS` |
| Model attempts | 2 | `client.MAX_ATTEMPTS` |
| Minimum quote length | 4 words | `models.MIN_QUOTE_WORDS` |
| Web uploads | 5 files, 100 KB each | `app.py` |


| Exception | Raised when |
|---|---|
| `DocumentTooLargeError` | Input exceeds the character limits. |
| `InvalidModelOutput` | The model's response isn't valid JSON or doesn't match the schema after all attempts. |


The system prompt tells the model to treat document contents as untrusted data
and to ignore any instructions inside them.


## Sample specifications


`samples/specs/` contains three fictional specifications (`accounts.md`,
`checkout.md`, `pricing.md`) with deliberately planted defects.
`samples/PLANTED_DEFLECTS.md` is the answer key for checking audit runs. It is
never sent to the model.


## Project structure


```
src/spec_auditor/
  app.py          Streamlit web app
  cli.py          Command-line entry point (spec-auditor)
  client.py       Model client protocol, Gemini client, retry loop
  config.py       Settings from environment / .env
  docx_export.py  Word report
  examples.py     Fixed, human-reviewed example report
  loader.py       Reads specifications, picks non-clashing output names
  models.py       Pydantic data model
  prompt.py       System prompt, user prompt, size limits
  report.py       Markdown report
  validate.py     Evidence verification
tests/            pytest suite
samples/          Sample specifications and answer key
```


## Testing


```powershell
pip install -e ".[dev]"
pytest
```


The tests don't call the Gemini API. If you haven't installed the package, run them
with `PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH="src"; pytest`).


## License


MIT. See [LICENSE](LICENSE).





import pytest

from spec_auditor.client import (
    MAX_ATTEMPTS,
    InvalidModelOutput,
    audit_documents,
    parse_response,
)

VALID_JSON = """
{
  "findings": [
    {
      "evidence": [{"file": "a.md", "quote": "the system must respond quickly"}],
      "section": "Delivery",
      "issue": "No measurable threshold.",
      "defect_type": "Ambiguity",
      "severity": "Medium",
      "suggested_fix": "State a response time in milliseconds."
    }
  ]
}
"""


class ScriptedClient:
    """Returns prepared responses in order and records the prompts it received."""

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, system: str, user: str) -> str:
        self.prompts.append(user)
        return self.responses.pop(0)


def test_valid_json_is_parsed():
    response = parse_response(VALID_JSON)

    assert len(response.findings) == 1
    assert response.findings[0].severity.value == "Medium"


def test_code_fences_are_stripped():
    assert parse_response(f"```json\n{VALID_JSON}\n```").findings


def test_non_json_output_is_rejected():
    with pytest.raises(InvalidModelOutput, match="not valid JSON"):
        parse_response("Here are the issues I found:")


def test_output_failing_the_schema_is_rejected():
    bad = '{"findings": [{"evidence": [], "section": "X", "issue": "Y", ' \
          '"defect_type": "Ambiguity", "severity": "Medium", "suggested_fix": "Z"}]}'

    with pytest.raises(InvalidModelOutput, match="did not match the schema"):
        parse_response(bad)


def test_fabricated_severity_is_rejected():
    bad = VALID_JSON.replace('"Medium"', '"Critical"')

    with pytest.raises(InvalidModelOutput):
        parse_response(bad)


def test_invalid_output_is_retried_once():
    client = ScriptedClient("not json at all", VALID_JSON)

    result = audit_documents({"a.md": "content"}, client)

    assert len(result.findings) == 1
    assert len(client.prompts) == 2
    assert "previous response was rejected" in client.prompts[1]


def test_retries_are_capped():
    client = ScriptedClient(*["nonsense"] * MAX_ATTEMPTS)

    with pytest.raises(InvalidModelOutput, match=f"after {MAX_ATTEMPTS} attempts"):
        audit_documents({"a.md": "content"}, client)

    assert len(client.prompts) == MAX_ATTEMPTS



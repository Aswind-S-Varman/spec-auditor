import json
import re
from typing import Protocol

from pydantic import ValidationError

from .models import AuditResponse
from .prompt import SYSTEM_PROMPT, build_user_prompt

MAX_ATTEMPTS = 2
_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)


class InvalidModelOutput(Exception):
    """The model returned something that is not a valid audit response."""


class ModelClient(Protocol):
    """Everything the auditor needs from a model provider."""

    def complete(self, system: str, user: str) -> str: ...


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        from google import genai  # imported lazily so the core package works without it

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                temperature=0,
            ),
        )
        return response.text or ""


def _strip_fences(text: str) -> str:
    return _FENCE.sub("", text.strip()).strip()


def parse_response(raw: str) -> AuditResponse:
    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise InvalidModelOutput(f"Response was not valid JSON: {exc}") from exc

    try:
        return AuditResponse.model_validate(payload)
    except ValidationError as exc:
        raise InvalidModelOutput(f"Response did not match the schema: {exc}") from exc


def audit_documents(documents: dict[str, str], client: ModelClient) -> AuditResponse:
    base_prompt = build_user_prompt(documents)
    last_error: InvalidModelOutput | None = None

    for attempt in range(MAX_ATTEMPTS):
        prompt = base_prompt
        if last_error is not None:
            # Feed the validation failure back so the retry has something to correct.
            prompt = (
                f"{base_prompt}\n\nYour previous response was rejected for this reason:\n"
                f"{last_error}\n\nReturn corrected JSON only."
            )

        try:
            return parse_response(client.complete(SYSTEM_PROMPT, prompt))
        except InvalidModelOutput as exc:
            last_error = exc

    raise InvalidModelOutput(
        f"Model returned invalid output after {MAX_ATTEMPTS} attempts: {last_error}"
    )



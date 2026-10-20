import pytest

from spec_auditor.prompt import (
    MAX_CHARS_PER_FILE,
    DocumentTooLargeError,
    build_user_prompt,
)


def test_every_file_is_labelled_and_included():
    prompt = build_user_prompt({"b.md": "beta content", "a.md": "alpha content"})

    assert "--- FILE: a.md ---" in prompt
    assert "--- FILE: b.md ---" in prompt
    assert "alpha content" in prompt
    assert "beta content" in prompt


def test_files_are_listed_in_a_stable_order():
    prompt = build_user_prompt({"z.md": "z", "a.md": "a"})

    assert prompt.index("--- FILE: a.md ---") < prompt.index("--- FILE: z.md ---")


def test_empty_input_is_rejected():
    with pytest.raises(ValueError):
        build_user_prompt({})


def test_oversized_file_is_rejected():
    with pytest.raises(DocumentTooLargeError, match="exceeds"):
        build_user_prompt({"big.md": "x" * (MAX_CHARS_PER_FILE + 1)})


def test_combined_size_is_capped():
    chunk = "x" * (MAX_CHARS_PER_FILE - 1)
    too_many = {f"f{i}.md": chunk for i in range(5)}

    with pytest.raises(DocumentTooLargeError, match="Combined"):
        build_user_prompt(too_many)



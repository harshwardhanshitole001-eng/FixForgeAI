"""AI brain for FixForge AI: sends code + error to NVIDIA Nemotron on Nebius."""

import json
import os
import re

from openai import OpenAI

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
# Confirm the exact model ID in your Nebius Token Factory console and set NEBIUS_MODEL if it differs.
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

SYSTEM_PROMPT = """You are FixForge AI, a debugging assistant for beginner programmers.
Given a piece of Python code and its error message, reply with ONLY a JSON object with these keys:

- "explanation": 2 to 4 short sentences in plain, simple English saying what the error means and why it happened. Define any technical term you use.
- "root_cause": one sentence naming the exact line or value that causes the problem.
- "changes": a short markdown bullet list (as one string) of the minimal changes you made.
- "fixed_code": the complete corrected Python code. Keep the original structure and make the smallest change that fixes the error.
- "tests": a complete pytest file as one string. It must start with `from solution import ...` naming the functions defined in fixed_code. Include 3 to 5 test functions named test_*, covering a normal case, an edge case, and the case the bug affected. Each test must check a return value with assert.

Do not wrap the JSON in markdown fences. Do not write any text outside the JSON object."""

REQUIRED_KEYS = ["explanation", "root_cause", "changes", "fixed_code", "tests"]


def _get_client() -> OpenAI:
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY is not set. Add it to your .env file.")
    return OpenAI(api_key=api_key, base_url=os.getenv("NEBIUS_BASE_URL", DEFAULT_BASE_URL))


def _parse_json(text: str) -> dict:
    # Reasoning models may emit <think> blocks; drop them before parsing.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return a JSON object.")
    return json.loads(text[start : end + 1])


def analyze(code: str, error: str) -> dict:
    """Return a dict with explanation, root_cause, changes, fixed_code, and tests."""
    client = _get_client()
    response = client.chat.completions.create(
        model=os.getenv("NEBIUS_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"CODE:\n```python\n{code}\n```\n\nERROR MESSAGE:\n{error}",
            },
        ],
        temperature=0.2,
        max_tokens=4000,
    )
    text = response.choices[0].message.content or ""
    if not text.strip():
        raise RuntimeError(
            "The model returned an empty answer. Try again, raise max_tokens, "
            "or set NEBIUS_MODEL to a non-reasoning model."
        )

    data = _parse_json(text)
    missing = [key for key in REQUIRED_KEYS if not str(data.get(key, "")).strip()]
    if missing:
        raise ValueError(f"The model's answer was missing: {', '.join(missing)}")
    return {key: str(data[key]) for key in REQUIRED_KEYS}

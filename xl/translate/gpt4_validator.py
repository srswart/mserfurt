"""GPT-4 validation reviewer.

After Claude produces a primary translation, GPT-4 receives the English
source and Claude's output and returns a structured list of flags.
GPT-4 does NOT produce an alternative translation — it only reviews.

Requires OPENAI_API_KEY in the environment.
"""

from __future__ import annotations

import json
import os

from xl.models import ValidationFlag


def _client():
    try:
        import openai
        return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except ImportError as e:
        raise ImportError("openai SDK required: pip install openai") from e
    except KeyError:
        raise EnvironmentError("OPENAI_API_KEY environment variable not set")


_MODEL = "gpt-4o"

_SYSTEM = """You are a specialist in medieval German and Latin philology, reviewing machine translations
of a 15th-century Thuringian manuscript for anachronisms and register errors.

You will receive:
1. The English source text
2. A proposed German/Latin translation

Flag any of:
- Anachronistic vocabulary (words not attested before ~1460)
- Register errors (modern Hochdeutsch where FNHD is expected, or humanist Latin where clerical is expected)
- Grammatical forms from the wrong century
- Latin that reads more Renaissance than scholastic

Return a JSON array (and nothing else) of objects with keys:
  "line_id": a short identifier for the flagged fragment (e.g. "clause-1")
  "issue_type": one of "anachronism" | "register_error" | "grammatical_form" | "humanist_latin"
  "suggestion": brief suggestion for correction

If there are no issues, return an empty JSON array: []"""


def validate(source: str, translation: str) -> list[ValidationFlag]:
    """Review a translation and return any validation flags.

    Returns an empty list if no issues are found.
    """
    client = _client()
    response = client.chat.completions.create(
        model=_MODEL,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": (
                    f"English source:\n{source}\n\n"
                    f"Proposed translation:\n{translation}"
                ),
            },
        ],
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
        # GPT-4 sometimes wraps in {"flags": [...]}
        if isinstance(data, dict):
            data = data.get("flags", data.get("items", []))
        return [
            ValidationFlag(
                line_id=item.get("line_id", ""),
                issue_type=item.get("issue_type", ""),
                suggestion=item.get("suggestion", ""),
            )
            for item in data
        ]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []

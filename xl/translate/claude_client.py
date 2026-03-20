"""Claude API client for period-appropriate translation.

Translates passages into Frühneuhochdeutsch (Thuringian dialect) or
scholastic Latin at temperature 0.0 for deterministic output.

Uses the Anthropic SDK. Requires ANTHROPIC_API_KEY in the environment.
"""

from __future__ import annotations

import os
import time

# Lazy import — only fails at call time, not import time, so dry-run works
# without the SDK installed.
def _client():
    try:
        import anthropic
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=4)
    except ImportError as e:
        raise ImportError("anthropic SDK required: pip install anthropic") from e
    except KeyError:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")


_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_DE = """You are a scholarly translator specialising in medieval German manuscripts.
Translate the provided English text into Frühneuhochdeutsch (Early New High German) as written
in the Thuringian dialect circa 1457. Requirements:
- Use FNHD orthographic conventions: diphthongisation (iu→eu, û→au, î→ei) is well underway but
  not yet stabilised; use forms transitional between MHG and modern German.
- Preserve the confessional, first-person voice of a Benedictine/Augustinian canon.
- Keep concrete and sensory language vernacular; do not Latinise material descriptions.
- Retain Latin liturgical terms (Lauds, Vespers, etc.) in Latin as they appear in devotional prose.
- Output ONLY the translated text. No explanation, no commentary."""

_SYSTEM_LA = """You are a scholarly translator specialising in medieval Latin manuscripts.
Translate the provided English text into Ecclesiastical Latin as written by an educated
Augustinian canon circa 1457. Requirements:
- Use clerical, not humanist, Latin: Ciceronian periodic sentences are inappropriate;
  prefer the plain, devotional style of the Augustinian tradition.
- For direct address to God, use the tu/tibi register of Augustine's Confessions.
- Latin theological terms (anima, gratia, verbum, etc.) must be used precisely.
- Do not translate proper nouns (Peter, Demetrios, Becker, Erfurt).
- Output ONLY the translated text. No explanation, no commentary."""

_SYSTEM_MIXED = """You are a scholarly translator specialising in medieval German-Latin manuscripts.
Translate the provided English text into a fluid mixture of Frühneuhochdeutsch and scholastic Latin
as written by an educated Augustinian canon circa 1457.
- Direct address to God and theological abstractions should lean Latin.
- Personal narrative, emotional reflection, and material description should stay German.
- Clause-level switching should feel organic, not mechanical.
- Use FNHD orthographic conventions for the German portions.
- Output ONLY the translated text. No explanation, no commentary."""


def translate(text: str, register: str, feedback: str | None = None) -> str:
    """Translate text into the target register using Claude.

    Args:
        text: English source text to translate.
        register: "de" | "la" | "mixed"
        feedback: Optional GPT-4 validation feedback to guide revision.

    Returns:
        Translated text string.
    """
    system = {
        "de": _SYSTEM_DE,
        "la": _SYSTEM_LA,
        "mixed": _SYSTEM_MIXED,
    }.get(register, _SYSTEM_DE)

    user_content = text
    if feedback:
        user_content = (
            f"Original English:\n{text}\n\n"
            f"Previous translation had these issues flagged by a reviewer:\n{feedback}\n\n"
            "Please revise the translation to address these issues."
        )

    client = _client()
    # Retry with increasing waits on transient overload (529)
    delays = [5, 15, 30, 60]
    for attempt, delay in enumerate(delays, 1):
        try:
            message = client.messages.create(
                model=_MODEL,
                max_tokens=1024,
                temperature=0.0,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            return message.content[0].text.strip()
        except Exception as exc:
            if "overloaded" in str(exc).lower() and attempt < len(delays):
                print(f"      [claude] overloaded, waiting {delay}s (attempt {attempt}/{len(delays)})...")
                time.sleep(delay)
            else:
                raise

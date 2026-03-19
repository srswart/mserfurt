"""Register consistency scanner — cross-folio coherence checks.

Violations detected:
    unresolved_mixed       — a line carries register "mixed" (should be resolved
                             to de/la/mhg before export)
    unknown_verbatim_source — a verbatim_source annotation references a corpus
                              key or ref not present in the supplied reference table
"""

from __future__ import annotations

from dataclasses import dataclass

from xl.models import FolioPage


@dataclass
class Violation:
    """A single register-consistency violation."""
    folio_id: str
    line_number: int
    violation_type: str   # "unresolved_mixed" | "unknown_verbatim_source"
    message: str


def check_pages(
    pages: list[FolioPage],
    verbatim_refs: dict | None = None,
) -> list[Violation]:
    """Scan pages for register violations and return all found.

    Parameters
    ----------
    pages:
        FolioPages to check.
    verbatim_refs:
        Optional dict of the form ``{corpus_key: {ref: text, ...}, ...}``.
        When supplied, every ``verbatim_source`` annotation is checked against
        it.  When omitted, unknown-verbatim checks are skipped.
    """
    violations: list[Violation] = []
    for page in pages:
        for line in page.lines:
            violations.extend(_check_line(page.id, line, verbatim_refs))
    return violations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_line(folio_id: str, line, verbatim_refs: dict | None) -> list[Violation]:
    out: list[Violation] = []

    # 1. Unresolved mixed register
    if line.register == "mixed":
        out.append(Violation(
            folio_id=folio_id,
            line_number=line.number,
            violation_type="unresolved_mixed",
            message=(
                f"{folio_id} line {line.number}: register 'mixed' was not resolved "
                f"before export — text: {line.text!r}"
            ),
        ))

    # 2. Unknown verbatim source reference
    if verbatim_refs is not None:
        for ann in line.annotations:
            if ann.type != "verbatim_source":
                continue
            source = ann.detail.get("source", "")
            ref = ann.detail.get("ref", "")
            corpus = verbatim_refs.get(source)
            if corpus is None:
                out.append(Violation(
                    folio_id=folio_id,
                    line_number=line.number,
                    violation_type="unknown_verbatim_source",
                    message=(
                        f"{folio_id} line {line.number}: unknown verbatim corpus "
                        f"{source!r} (ref={ref!r})"
                    ),
                ))
            elif ref and ref not in corpus:
                out.append(Violation(
                    folio_id=folio_id,
                    line_number=line.number,
                    violation_type="unknown_verbatim_source",
                    message=(
                        f"{folio_id} line {line.number}: ref {ref!r} not found in "
                        f"corpus {source!r}"
                    ),
                ))

    return out

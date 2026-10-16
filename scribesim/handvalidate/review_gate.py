"""Tier-3 Human-Eyes Review Gate validator and serializer (TD-019 §4)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scribesim.annotate.review_board import map_quick_tags_to_parameters

VALID_ITEM_VERDICTS = frozenset({"pass", "revise", "reject"})
VALID_STAGE_VERDICTS = frozenset({"promote_checkpoint", "iterate_with_notes", "reject"})
REQUIRED_ANSWER_KEYS = (
    "join_ductus_flow",
    "bastarda_script_identity",
    "organic_hand_variation",
)


def save_human_review(
    path: Path | str,
    *,
    stage_id: str,
    candidate_sha256: str,
    reviewer: str,
    answers: dict[str, str],
    overall_stage_verdict: str,
    quick_tags: list[str] | tuple[str, ...] = (),
    notes: str = "",
) -> dict:
    """Validate and save a machine-readable Tier-3 human review record."""
    for key in REQUIRED_ANSWER_KEYS:
        if answers.get(key) not in VALID_ITEM_VERDICTS:
            raise ValueError(f"Invalid or missing rubric answer for {key!r}: {answers.get(key)!r}")
    if overall_stage_verdict not in VALID_STAGE_VERDICTS:
        raise ValueError(f"Invalid overall_stage_verdict: {overall_stage_verdict!r}")
    if not candidate_sha256 or len(candidate_sha256) < 16:
        raise ValueError("candidate_sha256 must be a non-empty hash string")

    recs = map_quick_tags_to_parameters(list(quick_tags))
    record = {
        "schema_version": "td019-human-review-v1",
        "stage_id": stage_id,
        "candidate_sha256": candidate_sha256,
        "reviewer": reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "answers": {k: answers[k] for k in REQUIRED_ANSWER_KEYS},
        "overall_stage_verdict": overall_stage_verdict,
        "quick_tags": list(quick_tags),
        "parameter_recommendations": recs,
        "notes": notes,
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def validate_human_review(
    path: Path | str,
    *,
    expected_stage_id: str | None = None,
    expected_candidate_sha256: str | None = None,
) -> dict:
    """Validate a saved Tier-3 human review JSON and return gate status."""
    p = Path(path)
    if not p.exists():
        return {"valid": False, "promoted": False, "reason": "review_file_missing"}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"valid": False, "promoted": False, "reason": "malformed_json"}

    if data.get("schema_version") != "td019-human-review-v1":
        return {"valid": False, "promoted": False, "reason": "unsupported_schema"}
    if expected_stage_id and data.get("stage_id") != expected_stage_id:
        return {"valid": False, "promoted": False, "reason": "stage_id_mismatch"}
    if expected_candidate_sha256 and data.get("candidate_sha256") != expected_candidate_sha256:
        return {"valid": False, "promoted": False, "reason": "candidate_sha256_mismatch"}

    answers = data.get("answers", {})
    if any(answers.get(k) not in VALID_ITEM_VERDICTS for k in REQUIRED_ANSWER_KEYS):
        return {"valid": False, "promoted": False, "reason": "invalid_answers"}

    verdict = data.get("overall_stage_verdict")
    if verdict not in VALID_STAGE_VERDICTS:
        return {"valid": False, "promoted": False, "reason": "invalid_overall_verdict"}

    promoted = (
        verdict == "promote_checkpoint"
        and all(answers.get(k) == "pass" for k in REQUIRED_ANSWER_KEYS)
    )
    return {
        "valid": True,
        "promoted": promoted,
        "stage_id": data.get("stage_id"),
        "candidate_sha256": data.get("candidate_sha256"),
        "overall_stage_verdict": verdict,
        "parameter_recommendations": data.get("parameter_recommendations", []),
    }

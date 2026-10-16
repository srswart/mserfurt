"""Human-Eyes Review Board (`scribesim review-sheet`) for TD-019 Tier-3 Checkpoints.

Generates an equal-scale 3-way comparison sheet (Reference target / Rigid baseline /
Coarticulated candidate + toggleable kinematic overlay) alongside Tier-1 automated
badges (`A1-PROPORTION`, `A2-KINEMATICS`, `A3-COARTICULATE`), a concise 4-question
rubric, and actionable quick-tags that map directly to model parameter groups.
"""

from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict
from pathlib import Path

from PIL import Image

from scribesim.guides.viapoint import VIAPOINT_STARTER_CATALOG
from scribesim.hand.profile import HandProfile, bastarda_nib_calibrated_profile
from scribesim.handflow.coarticulate import (
    compose_text_kinematic,
    solve_word_coarticulation,
)
from scribesim.handvalidate.kinematic_gates import (
    evaluate_a2_kinematics,
    evaluate_a3_coarticulate,
)
from scribesim.render.sandbox import render_trajectory_samples

CHECKPOINT_1_SPECIMENS: tuple[str, ...] = (
    "n",
    "u",
    "m",
    "nu",
    "nm",
    "um",
    "und",
    "der",
    "mir",
)

CHECKPOINT_2_SPECIMENS: tuple[str, ...] = (
    "in seines wercks alle der heiligen kirchen",
    "und glauben wir nicht alleine",
    "Hie hebt sich an das ein schreiber nit mag lassen",
)

RUBRIC_QUESTIONS: tuple[dict[str, object], ...] = (
    {
        "id": "join_ductus_flow",
        "title": "1. Join & Ductus Flow",
        "prompt": "Do letters flow into one another as continuous pen movements, with natural reciprocal adaptation at boundaries (nu, nm, und, der)?",
        "options": ["pass", "revise", "reject"],
        "tags": ["bridge_too_flat", "abrupt_shoulder", "too_wide_gap", "artificial_hook", "cramped"],
    },
    {
        "id": "bastarda_script_identity",
        "title": "2. Bastarda Script Identity",
        "prompt": "Do the letter shapes, thick/thin contrast, and feet/crowns read as authentic mid-15th-century German Bastarda?",
        "options": ["pass", "revise", "reject"],
        "tags": ["nib_too_thin", "nib_too_broad", "missing_foot_turn", "too_modern"],
    },
    {
        "id": "organic_hand_variation",
        "title": "3. Organic Hand Variation",
        "prompt": "Across repeated minims and words, does the sample feel written by a living hand rather than stamped by a font?",
        "options": ["pass", "revise", "reject"],
        "tags": ["clones_visible", "jitter_looks_random", "baseline_too_rigid", "excessive_messiness"],
    },
    {
        "id": "overall_stage_verdict",
        "title": "4. Overall Stage Verdict",
        "prompt": "Should this checkpoint be promoted to unlock the next curriculum stage?",
        "options": ["promote_checkpoint", "iterate_with_notes", "reject"],
        "tags": [],
    },
)

QUICK_TAG_MAP: dict[str, dict[str, str]] = {
    "too_wide_gap": {
        "parameter_group": "guides",
        "field": "ViaPointRecipe.advance_wnib",
        "direction": "decrease (-0.15 to -0.25 w_nib)",
        "rationale": "Tighten inter-letter advance so 40° exit foot reaches the next letter without a long bridge.",
    },
    "cramped": {
        "parameter_group": "guides",
        "field": "ViaPointRecipe.advance_wnib",
        "direction": "increase (+0.15 to +0.25 w_nib)",
        "rationale": "Open minim bay / inter-letter advance to restore interior counter breathing room.",
    },
    "abrupt_shoulder": {
        "parameter_group": "handflow",
        "field": "ViaPoint.sigma_x_wnib / sigma_y_wnib (entry/exit)",
        "direction": "increase (+0.05 w_nib)",
        "rationale": "Loosen boundary via-point covariance Sigma_k so minimum-jerk distributes the turn smoothly.",
    },
    "bridge_too_flat": {
        "parameter_group": "guides",
        "field": "ViaPoint.y_wnib (role='exit')",
        "direction": "increase (+0.20 w_nib)",
        "rationale": "Raise exit via-point height along the 40° chisel plane.",
    },
    "artificial_hook": {
        "parameter_group": "handflow",
        "field": "solve_word_coarticulation.w_jerk",
        "direction": "increase (+25%)",
        "rationale": "Increase minimum-jerk smoothness weight to damp hook-like inflection at entry.",
    },
    "nib_too_thin": {
        "parameter_group": "hand",
        "field": "NibParams.width_mm",
        "direction": "increase (+0.08 mm, lower H/w_nib toward 4.0)",
        "rationale": "Broaden nib relative to x-height for stronger Gothic downstroke weight.",
    },
    "nib_too_broad": {
        "parameter_group": "hand",
        "field": "NibParams.width_mm",
        "direction": "decrease (-0.08 mm, raise H/w_nib toward 4.5)",
        "rationale": "Narrow nib relative to x-height to open interior counters.",
    },
    "missing_foot_turn": {
        "parameter_group": "render",
        "field": "turn_pooling_factor.max_width_boost",
        "direction": "increase (+0.05)",
        "rationale": "Increase velocity-minimum foot pooling and turn dwell for clearer diamond feet.",
    },
    "too_modern": {
        "parameter_group": "guides",
        "field": "ViaPoint.sigma_x_wnib (role='turn')",
        "direction": "decrease (-0.015 w_nib)",
        "rationale": "Sharpen turn vertices so arches and feet keep crisp Bastarda broken-arch character.",
    },
    "clones_visible": {
        "parameter_group": "render",
        "field": "ScribeState.motor_memory_sigma",
        "direction": "increase (+0.01 x_height)",
        "rationale": "Increase slow correlated drift across repeated letter occurrences.",
    },
    "jitter_looks_random": {
        "parameter_group": "render",
        "field": "FolioParams.tremor_amplitude",
        "direction": "decrease toward 0.0 (prefer slow ScribeState drift)",
        "rationale": "Replace high-frequency per-point jitter with slow correlated via-point drift.",
    },
    "baseline_too_rigid": {
        "parameter_group": "line",
        "field": "LineParams.baseline_undulation_amplitude_mm",
        "direction": "increase (+0.08 mm)",
        "rationale": "Allow subtle organic baseline undulation across words.",
    },
    "excessive_messiness": {
        "parameter_group": "guides",
        "field": "ViaPoint.sigma_x_wnib (role='body')",
        "direction": "decrease toward 0.015 w_nib",
        "rationale": "Tighten protected stem body tolerances to preserve vertical minim discipline.",
    },
}


def map_quick_tags_to_parameters(tags: list[str] | tuple[str, ...]) -> list[dict[str, str]]:
    """Map selected quick-tags to structured parameter adjustment recommendations."""
    recommendations: list[dict[str, str]] = []
    for tag in tags:
        clean = tag.strip()
        if not clean:
            continue
        if clean in QUICK_TAG_MAP:
            recommendations.append({"tag": clean, **QUICK_TAG_MAP[clean]})
        elif clean.startswith("wrong_letter_form:"):
            ch = clean.split(":", 1)[1] or "?"
            recommendations.append(
                {
                    "tag": clean,
                    "parameter_group": "guides",
                    "field": f"VIAPOINT_STARTER_CATALOG[{ch!r}]",
                    "direction": "revise via-point coordinates against BSB exemplar",
                    "rationale": f"Operator flagged letterform '{ch}' for ductus revision.",
                }
            )
        else:
            recommendations.append(
                {
                    "tag": clean,
                    "parameter_group": "general",
                    "field": "custom_note",
                    "direction": "inspect",
                    "rationale": f"Custom reviewer tag: {clean}",
                }
            )
    return recommendations


def _candidate_digest(profile: HandProfile) -> str:
    payload = {
        "profile": profile.to_flat_dict(),
        "catalog": {k: asdict(v) for k, v in sorted(VIAPOINT_STARTER_CATALOG.items())},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_review_sheet(
    *,
    stage_id: str = "checkpoint-1-coarticulation",
    specimens: tuple[str, ...] | list[str] = CHECKPOINT_1_SPECIMENS,
    out_dir: Path | str = "shared/training/reviews/checkpoint-1-coarticulation",
    dpi: float = 180.0,
    profile: HandProfile | None = None,
) -> dict:
    """Build the 3-way Human-Eyes Review Board for `stage_id`."""
    prof = profile or bastarda_nib_calibrated_profile()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cand_sha = _candidate_digest(prof)
    a3 = evaluate_a3_coarticulate(profile=prof)

    specimen_records: list[dict] = []
    cards_html: list[str] = []

    for idx, text in enumerate(specimens):
        slug = f"{idx:02d}_{''.join(c if c.isalnum() else '_' for c in text)}"
        # 1. Coarticulated candidate (w_jerk=0.0045)
        samples_coart, vias_coart = compose_text_kinematic(text, profile=prof)
        arr_coart, svg_coart, metrics_coart = render_trajectory_samples(
            samples_coart, profile=prof, dpi=dpi, via_points_mm=vias_coart
        )
        coart_png = f"{slug}_candidate.png"
        Image.fromarray(arr_coart, "RGB").save(str(out / coart_png), format="PNG", dpi=(dpi, dpi))

        # 2. Uncoarticulated rigid baseline (w_jerk=1e-6 so boundary points do not adapt to neighbors)
        first_word = text.split(" ")[0] if text.strip() else "n"
        res_coart = solve_word_coarticulation(first_word, profile=prof)
        res_rigid = solve_word_coarticulation(first_word, profile=prof, w_jerk=1e-6, w_acc=1e-6)
        arr_rigid, _, _ = render_trajectory_samples(res_rigid.samples, profile=prof, dpi=dpi)
        rigid_png = f"{slug}_baseline_rigid.png"
        Image.fromarray(arr_rigid, "RGB").save(str(out / rigid_png), format="PNG", dpi=(dpi, dpi))

        a2 = evaluate_a2_kinematics(res_coart)
        a1 = metrics_coart["a1_proportion"]

        rec = {
            "text": text,
            "candidate_png": coart_png,
            "baseline_png": rigid_png,
            "a1_proportion": a1,
            "a2_kinematics": a2,
        }
        specimen_records.append(rec)

        cards_html.append(
            f"""
            <div class="specimen-card">
              <div class="specimen-header">
                <h3>Specimen: <code>{html.escape(text)}</code></h3>
                <span class="pill {'pass' if a1['passed'] else 'fail'}">A1 ratio={a1['width_ratio_p95_p05']}</span>
                <span class="pill {'pass' if a2['passed'] else 'fail'}">A2 DLJ={a2['dimensionless_jerk']}</span>
              </div>
              <div class="strip-grid">
                <div>
                  <div class="strip-label">Rigid Baseline (No Coarticulation)</div>
                  <img src="{rigid_png}" alt="Rigid baseline {html.escape(text)}"/>
                </div>
                <div>
                  <div class="strip-label">Coarticulated Candidate (1:1 Physical Scale)</div>
                  <img src="{coart_png}" alt="Coarticulated candidate {html.escape(text)}"/>
                </div>
                <div class="overlay-panel">
                  <div class="strip-label">Kinematic &amp; 40° Chisel Overlay</div>
                  {svg_coart}
                </div>
              </div>
            </div>
            """
        )

    a1_all = all(r["a1_proportion"]["passed"] for r in specimen_records)
    a2_all = all(r["a2_kinematics"]["passed"] for r in specimen_records)

    manifest = {
        "stage_id": stage_id,
        "candidate_sha256": cand_sha,
        "nib_width_mm": prof.nib.width_mm,
        "x_height_mm": prof.letterform.x_height_mm,
        "nib_angle_deg": prof.nib.angle_deg,
        "tier1_summary": {
            "a1_all_passed": a1_all,
            "a2_all_passed": a2_all,
            "a3_coarticulate": a3,
        },
        "specimens": specimen_records,
        "rubric_questions": list(RUBRIC_QUESTIONS),
    }

    (out / "board_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Build rubric HTML questions
    q_blocks: list[str] = []
    for q in RUBRIC_QUESTIONS:
        qid = str(q["id"])
        opts = "".join(
            f"<label class='opt'><input type='radio' name='{qid}' value='{opt}' {'checked' if i == 0 else ''}/> {opt}</label>"
            for i, opt in enumerate(q["options"])  # type: ignore[arg-type]
        )
        tags = "".join(
            f"<label class='tag-chip'><input type='checkbox' class='qtag' value='{t}'/> {t}</label>"
            for t in q["tags"]  # type: ignore[union-attr]
        )
        tags_div = f"<div class='tags-row'>Quick tags: {tags}</div>" if tags else ""
        q_blocks.append(
            f"""
            <div class="question-box" data-qid="{qid}">
              <h4>{html.escape(str(q['title']))}</h4>
              <p>{html.escape(str(q['prompt']))}</p>
              <div class="opts-row">{opts}</div>
              {tags_div}
            </div>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>ScribeSim Human-Eyes Review Board — {html.escape(stage_id)}</title>
  <style>
    body {{ font: 15px/1.5 system-ui, sans-serif; background: #f3efe6; color: #222; max-width: 1260px; margin: 24px auto; padding: 0 20px; }}
    .banner {{ background: #fffdf8; border: 1px solid #d5cfc2; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; }}
    .pill {{ display: inline-block; padding: 3px 9px; border-radius: 5px; font-size: 13px; font-weight: 600; color: #fff; margin-right: 6px; }}
    .pill.pass {{ background: #1b7f4c; }}
    .pill.fail {{ background: #b8332a; }}
    .specimen-card {{ background: #fffdf8; border: 1px solid #d5cfc2; border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
    .specimen-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
    .specimen-header h3 {{ margin: 0; flex: 1; }}
    .strip-grid {{ display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 14px; align-items: center; }}
    .strip-label {{ font-size: 12px; font-weight: 600; color: #555; margin-bottom: 4px; text-transform: uppercase; }}
    img {{ max-width: 100%; border: 1px solid #e2dccf; border-radius: 6px; background: #f5eedc; }}
    .question-box {{ background: #fffdf8; border: 1px solid #d5cfc2; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }}
    .question-box h4 {{ margin: 0 0 6px 0; }}
    .opts-row {{ display: flex; gap: 18px; margin: 8px 0; font-weight: 600; }}
    .tags-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; font-size: 13px; }}
    .tag-chip {{ background: #eee8da; padding: 3px 8px; border-radius: 4px; cursor: pointer; }}
    button {{ background: #166e68; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; }}
    pre {{ background: #222; color: #e8e2d5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="banner">
    <h1>Human-Eyes Review Board: <code>{html.escape(stage_id)}</code></h1>
    <p>
      <span class="pill {'pass' if a1_all else 'fail'}">A1-PROPORTION: {'PASS' if a1_all else 'FAIL'}</span>
      <span class="pill {'pass' if a2_all else 'fail'}">A2-KINEMATICS: {'PASS' if a2_all else 'FAIL'}</span>
      <span class="pill {'pass' if a3['passed'] else 'fail'}">A3-COARTICULATE: {'PASS' if a3['passed'] else 'FAIL'} (Δn={a3['n_exit_delta_wnib_nu_vs_nm']} w_nib, Δu={a3['u_entry_delta_wnib_nu_vs_isolated']} w_nib)</span>
      · Candidate SHA-256: <code>{cand_sha[:16]}…</code>
    </p>
  </div>

  <h2>Equal-Scale 3-Way Specimen Strips</h2>
  {"".join(cards_html)}

  <h2>Tier-3 Structured Human Rubric (4 Questions)</h2>
  {"".join(q_blocks)}
  <div class="question-box">
    <h4>Reviewer Notes</h4>
    <textarea id="notes" rows="3" style="width:100%;"></textarea>
    <p><button type="button" onclick="exportReview()">Generate Review JSON</button></p>
    <pre id="json-out"></pre>
  </div>
  <script>
    function exportReview() {{
      const answers = {{}};
      ['join_ductus_flow', 'bastarda_script_identity', 'organic_hand_variation'].forEach(id => {{
        const el = document.querySelector(`input[name="${{id}}"]:checked`);
        answers[id] = el ? el.value : 'pass';
      }});
      const verdictEl = document.querySelector('input[name="overall_stage_verdict"]:checked');
      const tags = Array.from(document.querySelectorAll('.qtag:checked')).map(e => e.value);
      const payload = {{
        stage_id: {json.dumps(stage_id)},
        candidate_sha256: {json.dumps(cand_sha)},
        answers: answers,
        overall_stage_verdict: verdictEl ? verdictEl.value : 'promote_checkpoint',
        quick_tags: tags,
        notes: document.getElementById('notes').value
      }};
      document.getElementById('json-out').textContent = JSON.stringify(payload, null, 2);
    }}
  </script>
</body>
</html>
"""
    (out / "index.html").write_text(html_doc, encoding="utf-8")
    return manifest

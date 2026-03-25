from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from click.testing import CliRunner
from PIL import Image

from scribesim.cli import main
from scribesim.evo.engine import EvolutionResult, initialize_population
from scribesim.evofit import build_evofit_targets, genome_to_dense_guide, run_evofit_from_corpus
from scribesim.refextract.corpus import build_join_templates, build_symbol_templates


def _write_manifest(tmp_path: Path, glyph_path: Path, join_path: Path) -> Path:
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        f"""
schema_version = 1
manifest_kind = "promoted_exemplars"
dataset_id = "fixture-promoted"

[[entries]]
kind = "glyph"
symbol = "u"
promoted_exemplar_count = 1
promoted_exemplar_paths = ["{glyph_path.as_posix()}"]

[[entries]]
kind = "join"
symbol = "u->n"
promoted_exemplar_count = 1
promoted_exemplar_paths = ["{join_path.as_posix()}"]
"""
    )
    return manifest_path


def test_build_evofit_targets_reads_glyph_and_join_entries(tmp_path: Path):
    glyph_template = build_symbol_templates(required_symbols=("u",))["u"]
    join_template = build_join_templates(priority_joins=("u->n",))["u->n"]
    glyph_path = tmp_path / "u.png"
    join_path = tmp_path / "u_to_n.png"
    Image.fromarray(glyph_template).save(glyph_path)
    Image.fromarray(join_template).save(join_path)
    manifest_path = _write_manifest(tmp_path, glyph_path, join_path)

    targets = build_evofit_targets(manifest_path)

    assert [target.symbol for target in targets] == ["u", "u->n"]
    assert targets[0].text == "u"
    assert targets[1].text == "un"
    assert targets[0].candidate_paths == (glyph_path,)
    assert targets[0].candidate_tiers == ("promoted_exemplars",)


def test_genome_to_dense_guide_exports_join_bridge():
    genome = initialize_population("un", pop_size=1, x_height_mm=3.8)[0]

    guide = genome_to_dense_guide(
        genome,
        symbol="u->n",
        kind="join",
        x_height_mm=3.8,
        source_id="test:u_to_n",
        source_path="fixture.png",
    )

    assert guide.kind == "join"
    assert guide.symbol == "u->n"
    assert len(guide.samples) >= 2
    assert any(sample.contact for sample in guide.samples)


def test_run_evofit_from_corpus_writes_bundle_and_proposals(tmp_path: Path):
    glyph_template = build_symbol_templates(required_symbols=("u",))["u"]
    join_template = build_join_templates(priority_joins=("u->n",))["u->n"]
    glyph_path = tmp_path / "u.png"
    join_path = tmp_path / "u_to_n.png"
    Image.fromarray(glyph_template).save(glyph_path)
    Image.fromarray(join_template).save(join_path)
    manifest_path = _write_manifest(tmp_path, glyph_path, join_path)

    def _fake_evolve_word(
        word_text: str,
        target_crop=None,
        config=None,
        fatigue: float = 0.0,
        emotional_state: str = "normal",
        verbose: bool = True,
        guides_path=None,
        x_height_mm: float = 3.8,
        exemplar_root=None,
        style_prior=None,
    ) -> EvolutionResult:
        genome = initialize_population(word_text, pop_size=1, x_height_mm=x_height_mm, guides_path=guides_path)[0]
        return EvolutionResult(
            best_genome=genome,
            best_fitness=0.72,
            generations_run=2,
            fitness_history=[0.55, 0.72],
        )

    with patch("scribesim.evofit.workflow.evolve_word", side_effect=_fake_evolve_word):
        result = run_evofit_from_corpus(manifest_path, output_root=tmp_path / "out")

    summary = json.loads(result["summary_json_path"].read_text())
    assert summary["fit_source_count"] == 2
    assert summary["converted_guide_count"] >= 1
    assert result["proposal_catalog_path"].exists()
    assert (tmp_path / "out" / "glyph" / "u" / "candidate_00" / "best_render.png").exists()
    assert (tmp_path / "out" / "glyph" / "u" / "candidate_00" / "fit_source.png").exists()
    assert (tmp_path / "out" / "join" / "u_to_n" / "candidate_00" / "comparison.png").exists()


def test_evofit_corpus_cli_invokes_workflow(tmp_path: Path):
    runner = CliRunner()
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1

[[entries]]
kind = "glyph"
symbol = "u"
accepted_count = 1
accepted_paths = ["u.png"]
soft_accepted_count = 0
soft_accepted_paths = []
rejected_count = 0
rejected_paths = []
coverage_promoted = false
"""
    )

    with patch("scribesim.evofit.run_evofit_from_corpus") as mocked:
        mocked.return_value = {
            "summary": {
                "fit_source_count": 1,
                "converted_guide_count": 1,
                "beats_prior_rate": 1.0,
            },
            "summary_md_path": tmp_path / "summary.md",
            "proposal_catalog_path": tmp_path / "proposal_guides.toml",
        }
        result = runner.invoke(
            main,
            [
                "evofit-corpus",
                "--corpus-manifest",
                str(manifest_path),
                "--output",
                str(tmp_path / "out"),
                "--symbols",
                "u",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "Fit sources: 1" in result.output
    mocked.assert_called_once()

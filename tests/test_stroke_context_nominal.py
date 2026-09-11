import math

import pytest

from scripts import stroke_context_nominal as nominal


def test_flattening_has_certified_control_bound():
    cubic = [[0, 0], [0, 3], [3, 3], [3, 0]]
    segments = nominal.flatten(cubic)
    assert len(segments) > 1
    assert segments[0][0] == cubic[0] and segments[-1][-1] == cubic[-1]
    assert all(nominal.chord_error(segment) <= .001 for segment in segments)
    assert all(before[-1] == after[0] for before, after in zip(segments, segments[1:]))


def test_sweep_is_fixed_physical_edge():
    polygon = nominal.sweep([0, 0], [0, 1])
    assert math.isclose(math.dist(polygon[0], polygon[1]), .45)
    assert math.isclose(polygon[1][0]-polygon[0][0], .45*math.cos(math.radians(40)))


def test_degenerate_or_nonfinite_cubic_rejects():
    with pytest.raises(ValueError):
        nominal.flatten([[0, 0], [0, float('nan')], [1, 1], [2, 2]])


def test_approval_is_external_and_specific():
    with pytest.raises(ValueError, match='approval'):
        nominal.verify_inputs('')


def test_existing_attempt_never_retries(tmp_path):
    with pytest.raises(FileExistsError):
        nominal.generate('', tmp_path)


def test_template_keeps_evidence_labels_and_no_extra_rasters():
    template = nominal.TEMPLATE.read_text()
    assert 'NOMINAL GEOMETRY' in template
    assert 'NOT ACTUAL INK' in template
    assert 'indistinguishable' in template
    assert '<canvas' not in template
    assert 'localStorage' not in template


def test_budget_guards_time_space_and_bytes(tmp_path, monkeypatch):
    budget = nominal.Budget(tmp_path)
    monkeypatch.setattr(nominal.shutil, 'disk_usage', lambda path: type('Space', (), {'free': 0})())
    with pytest.raises(RuntimeError, match='space'):
        budget.check()
    monkeypatch.setattr(nominal.shutil, 'disk_usage', lambda path: type('Space', (), {'free': 10**12})())
    budget.used = 100*1024**2
    with pytest.raises(RuntimeError, match='size'):
        budget.check(1)
    budget.used = 0
    budget.started -= 301
    with pytest.raises(RuntimeError, match='time'):
        budget.check()

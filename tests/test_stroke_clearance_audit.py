import pytest

from scripts import stroke_clearance_audit as audit


def test_segment_polygon_distance_interior_and_separate():
    square = [[0, 0], [1, 0], [1, 1], [0, 1]]
    assert audit.segment_polygon_distance([[.2, .5], [.8, .5]], square) == 0
    assert audit.segment_polygon_distance([[2, .2], [2, .8]], square) == pytest.approx(1)


def test_degenerate_sweep_does_not_contain_entire_plane():
    polygon = [[0, 0], [1, 0], [2, 0], [1, 0]]
    assert audit.segment_polygon_distance([[0, 1], [1, 1]], polygon) == pytest.approx(1)


def test_exact_restriction_preserves_canonical_points():
    cubic = [[0, 0], [0, 3], [3, 3], [3, 0]]
    restricted = audit.restrict(cubic, .2, .7)
    assert restricted[0] == pytest.approx(audit.attachment.point(cubic, .2))
    assert restricted[-1] == pytest.approx(audit.attachment.point(cubic, .7))
    for parameter in (.1, .5, .9):
        assert audit.attachment.point(restricted, parameter) == pytest.approx(
            audit.attachment.point(cubic, .2+.5*parameter))


def test_fixed_edge_y_up_sign_and_width():
    footprint = audit.footprint([0, 0])
    assert audit.math.dist(*footprint) == pytest.approx(.45)
    assert footprint[1][1] < footprint[0][1]


def test_clearance_interval_is_not_false_overlap_claim():
    assert audit.classify(.02)['status'] == 'certified_clear'
    assert audit.classify(0)['status'] == 'possible_contact_or_overlap'
    assert audit.classify(audit.ERROR/2)['lower_bound_mm'] == 0


def test_missing_pin_and_overwrite_reject(tmp_path):
    with pytest.raises(ValueError):
        audit.load_attachment('')
    with pytest.raises(FileExistsError):
        audit.snapshot(tmp_path)


def test_read_only_guard_blocks_old_raster():
    with audit.attachment.source.evidence.read_only_guard(), pytest.raises(RuntimeError):
        audit.attachment.source.evidence.reader.paint(None)

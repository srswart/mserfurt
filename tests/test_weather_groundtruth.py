"""Unit tests for Weather groundtruth — ADV-WX-GROUNDTRUTH-001.

RED phase: weather.groundtruth modules are not yet implemented.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"

# Minimal PAGE XML template (1000x1000 canvas)
_PAGE_XML_TEMPLATE = """\
<?xml version='1.0' encoding='utf-8'?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Metadata><Creator>test</Creator></Metadata>
  <Page imageFilename="test.png" imageWidth="1000" imageHeight="1000">
    <TextRegion id="r1" custom="type:paragraph">
      <Coords points="0,0 1000,0 1000,1000 0,1000" />
{lines}
    </TextRegion>
  </Page>
</PcGts>"""

_LINE_TEMPLATE = (
    '      <TextLine id="l{n}" custom="register:{reg}">'
    '<Coords points="{pts}" />'
    '<Baseline points="{bl}" />'
    '<TextEquiv index="0"><Unicode>text</Unicode></TextEquiv>'
    '</TextLine>'
)


def _make_xml(lines: list[dict]) -> str:
    line_strs = [
        _LINE_TEMPLATE.format(
            n=i + 1,
            reg=l.get("reg", "mixed"),
            pts=l["pts"],
            bl=l.get("bl", "0,50 1000,50"),
        )
        for i, l in enumerate(lines)
    ]
    return _PAGE_XML_TEMPLATE.format(lines="\n".join(line_strs))


def _water_zone(h=1000, w=1000, tide_row=400) -> np.ndarray:
    """Simple rectangular water zone covering top tide_row rows."""
    mask = np.zeros((h, w), dtype=bool)
    mask[:tide_row, :] = True
    return mask


def _corner_mask(h=1000, w=1000, depth_x=200, depth_y=200) -> np.ndarray:
    """Triangular corner mask in bottom-right."""
    mask = np.zeros((h, w), dtype=bool)
    for row in range(h - depth_y, h):
        t = (row - (h - depth_y)) / depth_y
        col_boundary = int((w - 1) * (1 - t) + (w - 1 - depth_x) * t)
        mask[row, col_boundary:] = True
    return mask


def _curl_transform(h=1000, w=1000, max_disp=5.0) -> np.ndarray:
    """Uniform x-displacement of max_disp pixels (simple test case)."""
    t = np.zeros((h, w, 2), dtype=np.float32)
    t[:, :, 1] = max_disp  # x-displacement only
    return t


@pytest.fixture(scope="module")
def profile():
    from weather.profile import load_profile
    return load_profile(PROFILE_TOML)


# ---------------------------------------------------------------------------
# TestCurlTransform
# ---------------------------------------------------------------------------

class TestCurlTransform:
    def test_point_shifted_by_displacement(self):
        from weather.groundtruth.transform import apply_curl_to_points
        # Uniform 5px x-displacement; canvas 1000x1000, image 1000x1000
        transform = _curl_transform(h=1000, w=1000, max_disp=5.0)
        points = [(100, 200)]
        shifted = apply_curl_to_points(points, transform, 1000, 1000, 1000, 1000)
        assert len(shifted) == 1
        x_new, y_new = shifted[0]
        assert abs(x_new - 105) <= 1, f"x should shift by ~5, got {x_new}"
        assert abs(y_new - 200) <= 1, f"y should be unchanged, got {y_new}"

    def test_multiple_points(self):
        from weather.groundtruth.transform import apply_curl_to_points
        transform = _curl_transform(h=1000, w=1000, max_disp=10.0)
        points = [(50, 100), (500, 500), (900, 800)]
        shifted = apply_curl_to_points(points, transform, 1000, 1000, 1000, 1000)
        assert len(shifted) == 3
        for (x_orig, y_orig), (x_new, y_new) in zip(points, shifted):
            assert abs(x_new - (x_orig + 10)) <= 1

    def test_zero_displacement_unchanged(self):
        from weather.groundtruth.transform import apply_curl_to_points
        transform = np.zeros((1000, 1000, 2), dtype=np.float32)
        points = [(300, 400), (700, 600)]
        shifted = apply_curl_to_points(points, transform, 1000, 1000, 1000, 1000)
        for orig, new in zip(points, shifted):
            assert orig == new or (abs(orig[0] - new[0]) <= 1 and abs(orig[1] - new[1]) <= 1)

    def test_none_transform_unchanged(self):
        from weather.groundtruth.transform import apply_curl_to_points
        points = [(100, 200), (300, 400)]
        result = apply_curl_to_points(points, None, 1000, 1000, 1000, 1000)
        assert result == points


# ---------------------------------------------------------------------------
# TestLegibility
# ---------------------------------------------------------------------------

class TestLegibility:
    def test_corner_centroid_inside_is_zero(self):
        from weather.groundtruth.legibility import compute_legibility
        mask = _corner_mask(h=1000, w=1000, depth_x=200, depth_y=200)
        # Bottom-right centroid — well inside the corner
        score = compute_legibility(950, 950, None, mask, 1000, 1000, 1000, 1000)
        assert score == 0.0

    def test_corner_centroid_outside_is_one(self):
        from weather.groundtruth.legibility import compute_legibility
        mask = _corner_mask(h=1000, w=1000, depth_x=200, depth_y=200)
        # Top-left — nowhere near the corner
        score = compute_legibility(100, 100, None, mask, 1000, 1000, 1000, 1000)
        assert score == 1.0

    def test_water_top_row_low_legibility(self):
        from weather.groundtruth.legibility import compute_legibility
        zone = _water_zone(h=1000, w=1000, tide_row=400)
        # Centroid at top of page (row ~10) — fully wet, near top → lowest legibility
        score = compute_legibility(500, 10, zone, None, 1000, 1000, 1000, 1000)
        assert score < 0.5, f"Expected low legibility near top, got {score}"

    def test_water_tide_line_high_legibility(self):
        from weather.groundtruth.legibility import compute_legibility
        zone = _water_zone(h=1000, w=1000, tide_row=400)
        # Centroid just below tide line (row 400) → not in water zone → 1.0
        score = compute_legibility(500, 410, zone, None, 1000, 1000, 1000, 1000)
        assert score == 1.0

    def test_no_damage_is_one(self):
        from weather.groundtruth.legibility import compute_legibility
        score = compute_legibility(500, 500, None, None, 1000, 1000, 1000, 1000)
        assert score == 1.0

    def test_water_top_less_legible_than_bottom(self):
        from weather.groundtruth.legibility import compute_legibility
        zone = _water_zone(h=1000, w=1000, tide_row=500)
        s_top = compute_legibility(500, 10, zone, None, 1000, 1000, 1000, 1000)
        s_mid = compute_legibility(500, 250, zone, None, 1000, 1000, 1000, 1000)
        assert s_top < s_mid, "Higher row should have lower legibility"


# ---------------------------------------------------------------------------
# TestUpdateGroundtruth
# ---------------------------------------------------------------------------

class TestUpdateGroundtruth:
    def test_no_damage_coords_unchanged(self):
        from weather.groundtruth.pagexml import update_groundtruth
        xml = _make_xml([{"pts": "0,0 1000,0 1000,31 0,31", "bl": "0,29 1000,29"}])
        result = update_groundtruth(xml, 1000, 1000)
        assert "0,0 1000,0 1000,31 0,31" in result

    def test_curl_shifts_coords(self):
        from weather.groundtruth.pagexml import update_groundtruth
        xml = _make_xml([{"pts": "100,0 200,0 200,31 100,31", "bl": "100,29 200,29"}])
        transform = _curl_transform(h=1000, w=1000, max_disp=5.0)
        result = update_groundtruth(xml, 1000, 1000, curl_transform=transform)
        # Find the TextLine Coords (second Coords element — first is TextRegion)
        all_coords = list(re.finditer(r'Coords points="([^"]+)"', result))
        assert len(all_coords) >= 2, "Expected at least TextRegion + TextLine Coords"
        pts_str = all_coords[1].group(1)  # second = TextLine
        pts = [tuple(int(v) for v in p.split(",")) for p in pts_str.split()]
        # First point was (100, 0) → should become ~(105, 0)
        assert abs(pts[0][0] - 105) <= 2, f"Expected x≈105, got {pts[0][0]}"

    def test_corner_damage_adds_legibility_zero(self):
        from weather.groundtruth.pagexml import update_groundtruth
        # Line in bottom-right corner
        xml = _make_xml([{"pts": "800,800 1000,800 1000,1000 800,1000", "bl": "800,900 1000,900"}])
        mask = _corner_mask(h=1000, w=1000, depth_x=300, depth_y=300)
        result = update_groundtruth(xml, 1000, 1000, corner_mask=mask)
        assert "legibility:0.0" in result

    def test_non_damaged_line_no_legibility(self):
        from weather.groundtruth.pagexml import update_groundtruth
        # Line at top centre — not in any damage zone
        xml = _make_xml([{"pts": "0,0 1000,0 1000,31 0,31", "bl": "0,29 1000,29"}])
        result = update_groundtruth(xml, 1000, 1000)
        assert "legibility" not in result

    def test_water_damage_adds_legibility_attribute(self):
        from weather.groundtruth.pagexml import update_groundtruth
        # Line near top of page — fully in water zone
        xml = _make_xml([{"pts": "0,0 1000,0 1000,31 0,31", "bl": "0,29 1000,29"}])
        zone = _water_zone(h=1000, w=1000, tide_row=400)
        result = update_groundtruth(xml, 1000, 1000, water_zone=zone)
        assert "legibility:" in result

    def test_output_is_valid_xml(self):
        from weather.groundtruth.pagexml import update_groundtruth
        import xml.etree.ElementTree as ET
        xml = _make_xml([
            {"pts": "0,0 1000,0 1000,31 0,31", "bl": "0,29 1000,29"},
            {"pts": "800,800 1000,800 1000,1000 800,1000", "bl": "800,900 1000,900"},
        ])
        zone = _water_zone()
        mask = _corner_mask()
        transform = _curl_transform()
        result = update_groundtruth(xml, 1000, 1000, curl_transform=transform,
                                    water_zone=zone, corner_mask=mask)
        # Should not raise
        ET.fromstring(result)


# ---------------------------------------------------------------------------
# TestCompositorResultHasMasks
# ---------------------------------------------------------------------------

class TestCompositorResultHasMasks:
    def test_f04v_has_damage_masks(self, profile):
        from weather.compositor import composite_folio
        from PIL import Image
        import numpy as np
        page = Image.fromarray(np.full((128, 100, 3), 255, dtype=np.uint8), mode="RGB")
        hmap = Image.fromarray(np.full((128, 100), 128, dtype=np.uint8), mode="L")
        result = composite_folio(page, hmap, "f04v", profile, seed=0)
        assert result.water_zone is not None, "f04v should have water_zone"
        assert result.corner_mask is not None, "f04v should have corner_mask"

    def test_f01r_has_no_damage_masks(self, profile):
        from weather.compositor import composite_folio
        from PIL import Image
        import numpy as np
        page = Image.fromarray(np.full((128, 100, 3), 255, dtype=np.uint8), mode="RGB")
        hmap = Image.fromarray(np.full((128, 100), 128, dtype=np.uint8), mode="L")
        result = composite_folio(page, hmap, "f01r", profile, seed=0)
        assert result.water_zone is None, "f01r should have no water_zone"
        assert result.corner_mask is None, "f01r should have no corner_mask"

"""Unit tests for scribesim render engine — ADV-SS-RENDER-001.

RED phase: render_page() and render_heatmap() raise NotImplementedError.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scribesim.hand.model import load_base, resolve
from scribesim.layout import place

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"
GOLDEN_F04V = Path(__file__).parent / "golden" / "f04v" / "folio.json"


@pytest.fixture
def f01r_layout():
    folio = json.loads(GOLDEN_F01R.read_text())
    base = load_base(HAND_TOML)
    params = resolve(base, "f01r")
    return place(folio, params), params


@pytest.fixture
def f04v_layout():
    folio = json.loads(GOLDEN_F04V.read_text())
    base = load_base(HAND_TOML)
    params = resolve(base, "f04v")
    return place(folio, params), params


# ---------------------------------------------------------------------------
# TestRenderPage — render_page() output contracts
# ---------------------------------------------------------------------------

class TestRenderPage:
    def _render_page(self):
        from scribesim.render.rasteriser import render_page  # noqa: PLC0415
        return render_page

    def test_writes_file(self, f01r_layout, tmp_path):
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        result = render_page(layout, params, out)
        assert out.exists(), "render_page did not write output file"

    def test_returns_path(self, f01r_layout, tmp_path):
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        result = render_page(layout, params, out)
        assert result == out

    def test_valid_png(self, f01r_layout, tmp_path):
        from PIL import Image  # noqa: PLC0415
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        render_page(layout, params, out)
        img = Image.open(out)
        assert img.format == "PNG"

    def test_300_dpi(self, f01r_layout, tmp_path):
        from PIL import Image  # noqa: PLC0415
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        render_page(layout, params, out)
        img = Image.open(out)
        dpi = img.info.get("dpi", (0, 0))
        assert dpi[0] == pytest.approx(300, abs=1)
        assert dpi[1] == pytest.approx(300, abs=1)

    def test_correct_pixel_dimensions(self, f01r_layout, tmp_path):
        """Pixel dimensions match DPI × page size from the layout geometry."""
        from PIL import Image  # noqa: PLC0415
        from scribesim.render.rasteriser import _DPI
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        render_page(layout, params, out)
        img = Image.open(out)
        g = layout.geometry
        expected_w = round(g.page_w_mm / 25.4 * _DPI)
        expected_h = round(g.page_h_mm / 25.4 * _DPI)
        assert abs(img.width - expected_w) <= 5
        assert abs(img.height - expected_h) <= 5

    def test_is_rgb_or_rgba(self, f01r_layout, tmp_path):
        from PIL import Image  # noqa: PLC0415
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        render_page(layout, params, out)
        img = Image.open(out)
        assert img.mode in ("RGB", "RGBA", "L")

    def test_deterministic(self, f01r_layout, tmp_path):
        """Same input → identical byte output."""
        render_page = self._render_page()
        layout, params = f01r_layout
        out1 = tmp_path / "f01r_a.png"
        out2 = tmp_path / "f01r_b.png"
        render_page(layout, params, out1)
        render_page(layout, params, out2)
        assert out1.read_bytes() == out2.read_bytes()

    def test_not_empty_image(self, f01r_layout, tmp_path):
        """Page must have some non-white pixels (ink on parchment)."""
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        render_page = self._render_page()
        layout, params = f01r_layout
        out = tmp_path / "f01r.png"
        render_page(layout, params, out)
        arr = np.array(Image.open(out).convert("L"))
        assert arr.min() < 240, "Page image appears entirely white — no ink rendered"


# ---------------------------------------------------------------------------
# TestRenderHeatmap — render_heatmap() output contracts
# ---------------------------------------------------------------------------

class TestRenderHeatmap:
    def _render_heatmap(self):
        from scribesim.render.rasteriser import render_heatmap  # noqa: PLC0415
        return render_heatmap

    def _render_page(self):
        from scribesim.render.rasteriser import render_page  # noqa: PLC0415
        return render_page

    def test_writes_file(self, f01r_layout, tmp_path):
        render_heatmap = self._render_heatmap()
        layout, params = f01r_layout
        out = tmp_path / "f01r_pressure.png"
        result = render_heatmap(layout, params, out)
        assert out.exists()

    def test_is_grayscale(self, f01r_layout, tmp_path):
        from PIL import Image  # noqa: PLC0415
        render_heatmap = self._render_heatmap()
        layout, params = f01r_layout
        out = tmp_path / "f01r_pressure.png"
        render_heatmap(layout, params, out)
        img = Image.open(out)
        assert img.mode == "L", f"Expected grayscale ('L'), got {img.mode!r}"

    def test_same_dimensions_as_page(self, f01r_layout, tmp_path):
        from PIL import Image  # noqa: PLC0415
        layout, params = f01r_layout
        page_out = tmp_path / "f01r.png"
        heat_out = tmp_path / "f01r_pressure.png"
        self._render_page()(layout, params, page_out)
        self._render_heatmap()(layout, params, heat_out)
        page_img = Image.open(page_out)
        heat_img = Image.open(heat_out)
        assert page_img.size == heat_img.size

    def test_has_nonzero_pixels(self, f01r_layout, tmp_path):
        """Heatmap must have some dark pixels where strokes were rendered."""
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        render_heatmap = self._render_heatmap()
        layout, params = f01r_layout
        out = tmp_path / "f01r_pressure.png"
        render_heatmap(layout, params, out)
        arr = np.array(Image.open(out))
        assert arr.max() > 10, "Heatmap appears empty — no pressure recorded"

    def test_lacuna_glyphs_darker_in_heatmap(self, f04v_layout, tmp_path):
        """f04v has lacuna glyphs (opacity<1); they should have lower pressure."""
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        render_heatmap = self._render_heatmap()
        layout, params = f04v_layout
        out = tmp_path / "f04v_pressure.png"
        render_heatmap(layout, params, out)
        arr = np.array(Image.open(out))
        # Heatmap should not be entirely uniform — lacuna glyphs vary pressure
        assert arr.std() > 0, "Heatmap is uniform — opacity variation not captured"

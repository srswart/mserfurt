"""Page curl — sinusoidal x-displacement simulating codex binding warp."""

from __future__ import annotations

import re

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.optics.result import OpticsResult

_FOLIO_SIDE_RE = re.compile(r"^f?\d+([rv])$")


def _is_recto(folio_id: str) -> bool:
    m = _FOLIO_SIDE_RE.match(folio_id)
    return (m.group(1) == "r") if m else True


def apply_page_curl(
    img: Image.Image,
    folio_id: str,
    profile: WeatheringProfile,
    seed: int = 0,
) -> OpticsResult:
    """Apply page curl warp to simulate codex binding distortion.

    When disabled, returns the input image unchanged with no transform.
    When enabled, applies a sinusoidal x-displacement that peaks at the
    gutter edge and decays to zero at the fore-edge, then bilinearly
    resamples the image.

    The displacement map (dy=0, dx per pixel) is returned in `curl_transform`
    as a float32 array of shape (H, W, 2) for downstream groundtruth use.

    Args:
        img:       RGB PIL Image of the page.
        folio_id:  Folio identifier for gutter-side determination.
        profile:   WeatheringProfile.
        seed:      Unused (reserved for future stochastic curl variation).

    Returns:
        OpticsResult with warped image and displacement field.
    """
    pc = profile.optics_curl
    if not pc.enabled:
        return OpticsResult(image=img.copy(), curl_transform=None)

    arr = np.array(img.convert("RGB"), dtype=np.uint8)
    h, w = arr.shape[:2]

    max_disp_px = pc.curl_amount * h  # displacement at gutter edge

    # t in [0, 1]: 0 = fore-edge, 1 = gutter edge
    cols = np.arange(w, dtype=np.float32)
    if _is_recto(folio_id):
        # Gutter on left: t=1 at col=0, t=0 at col=w-1
        t = 1.0 - cols / (w - 1)
    else:
        # Gutter on right: t=1 at col=w-1, t=0 at col=0
        t = cols / (w - 1)

    # Sinusoidal profile: 0 at fore-edge, peaks at gutter
    x_disp = np.sin(t * (np.pi / 2)) * max_disp_px  # shape (w,)

    # Build source coordinate maps — we map destination → source
    # x_src = x_dst + displacement (pull from toward-gutter source)
    src_xx = np.tile(cols[np.newaxis, :], (h, 1)) + x_disp[np.newaxis, :]
    src_yy = np.tile(np.arange(h, dtype=np.float32)[:, np.newaxis], (1, w))

    src_xx = np.clip(src_xx, 0, w - 1)
    src_yy = np.clip(src_yy, 0, h - 1)

    # Bilinear interpolation
    x0 = src_xx.astype(np.int32)
    y0 = src_yy.astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    fx = (src_xx - x0).astype(np.float32)
    fy = (src_yy - y0).astype(np.float32)

    def _ch(c: int) -> np.ndarray:
        a = arr[:, :, c].astype(np.float32)
        return (
            a[y0, x0] * (1 - fx) * (1 - fy)
            + a[y0, x1] * fx * (1 - fy)
            + a[y1, x0] * (1 - fx) * fy
            + a[y1, x1] * fx * fy
        )

    warped = np.stack([_ch(0), _ch(1), _ch(2)], axis=-1)
    result_img = Image.fromarray(np.clip(warped, 0, 255).astype(np.uint8), mode="RGB")

    # Displacement map: dy=0, dx=x_disp broadcast over rows
    transform = np.zeros((h, w, 2), dtype=np.float32)
    transform[:, :, 1] = x_disp[np.newaxis, :]  # channel 1 = x-displacement

    return OpticsResult(image=result_img, curl_transform=transform)

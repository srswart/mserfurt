"""Metric suite — 9 comparison metrics + composite score.

Each metric compares a rendered image against a target image and returns
a MetricResult with a normalized distance in [0, 1].

Dependencies: numpy, scipy, PIL only (no skimage/torch).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.ndimage import gaussian_filter, label, distance_transform_edt
from scipy.stats import wasserstein_distance


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class MetricResult:
    """Result of a single metric comparison."""
    id: str          # e.g. "M1"
    name: str        # e.g. "stroke_width_distribution"
    distance: float  # normalized [0, 1], 0 = identical
    rating: str      # "good", "okay", "needs_work"
    detail: str      # human-readable explanation

    @staticmethod
    def rate(distance: float, good_threshold: float = 0.15,
             okay_threshold: float = 0.25) -> str:
        if distance <= good_threshold:
            return "good"
        elif distance <= okay_threshold:
            return "okay"
        else:
            return "needs_work"


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def _to_gray(img: np.ndarray) -> np.ndarray:
    """Convert RGB to grayscale float [0, 1]."""
    if img.ndim == 3:
        return np.mean(img.astype(np.float32), axis=2) / 255.0
    return img.astype(np.float32) / 255.0


def _binarize(gray: np.ndarray, threshold: float = 0.7) -> np.ndarray:
    """Binarize: ink pixels = True (dark), background = False."""
    return gray < threshold


# ---------------------------------------------------------------------------
# M1: Stroke width distribution
# ---------------------------------------------------------------------------

def m1_stroke_width(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare stroke width distributions via distance transform."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)
    b_r, b_t = _binarize(g_r), _binarize(g_t)

    dt_r = distance_transform_edt(b_r)
    dt_t = distance_transform_edt(b_t)

    # Extract stroke widths at ink skeleton (local maxima of distance transform)
    widths_r = dt_r[b_r & (dt_r > 0.5)].ravel()
    widths_t = dt_t[b_t & (dt_t > 0.5)].ravel()

    if len(widths_r) == 0 or len(widths_t) == 0:
        dist = 1.0
    else:
        # Normalize to [0, max] range for comparable histograms
        max_w = max(widths_r.max(), widths_t.max(), 1.0)
        dist = wasserstein_distance(widths_r / max_w, widths_t / max_w)
        dist = min(1.0, dist)

    return MetricResult(
        id="M1", name="stroke_width_distribution",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Wasserstein distance of stroke width distributions: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M2: Baseline regularity
# ---------------------------------------------------------------------------

def m2_baseline_regularity(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare baseline regularity via horizontal projection profiles."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    def _line_positions(gray: np.ndarray) -> np.ndarray:
        """Detect text line y-positions from horizontal projection."""
        proj = 1.0 - gray.mean(axis=1)  # ink density per row
        proj = gaussian_filter(proj, sigma=3.0)
        # Find peaks: rows where projection exceeds threshold
        threshold = proj.mean() + proj.std() * 0.5
        above = proj > threshold
        # Group consecutive True values into line regions
        labeled, n = label(above)
        positions = []
        for i in range(1, n + 1):
            rows = np.where(labeled == i)[0]
            positions.append(rows.mean())
        return np.array(positions)

    pos_r = _line_positions(g_r)
    pos_t = _line_positions(g_t)

    if len(pos_r) < 2 and len(pos_t) < 2:
        dist = 0.0  # both have too few lines to compare — no difference measurable
    elif len(pos_r) < 2 or len(pos_t) < 2:
        dist = 1.0  # one has lines, the other doesn't
    else:
        # Compare inter-line spacing variance (normalized by mean spacing)
        spacing_r = np.diff(pos_r)
        spacing_t = np.diff(pos_t)
        cv_r = spacing_r.std() / spacing_r.mean() if spacing_r.mean() > 0 else 0
        cv_t = spacing_t.std() / spacing_t.mean() if spacing_t.mean() > 0 else 0
        dist = min(1.0, abs(cv_r - cv_t) * 5.0)  # scale for sensitivity

    return MetricResult(
        id="M2", name="baseline_regularity",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Baseline spacing CV difference: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M3: Letter spacing rhythm
# ---------------------------------------------------------------------------

def m3_spacing_rhythm(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare letter spacing rhythm via vertical projection gap analysis."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    def _gap_variance(gray: np.ndarray) -> float:
        """Measure spacing variance from vertical projection."""
        # Use middle third of image (text area)
        h = gray.shape[0]
        mid = gray[h // 4: 3 * h // 4, :]
        proj = 1.0 - mid.mean(axis=0)
        proj = gaussian_filter(proj, sigma=1.0)
        threshold = proj.mean() * 0.5
        # Find gaps (below threshold)
        below = proj < threshold
        labeled, n = label(below)
        gaps = []
        for i in range(1, n + 1):
            cols = np.where(labeled == i)[0]
            if len(cols) > 1:
                gaps.append(len(cols))
        if len(gaps) < 2:
            return 0.0
        gaps = np.array(gaps, dtype=float)
        return gaps.std() / gaps.mean() if gaps.mean() > 0 else 0.0

    cv_r = _gap_variance(g_r)
    cv_t = _gap_variance(g_t)
    dist = min(1.0, abs(cv_r - cv_t) * 3.0)

    return MetricResult(
        id="M3", name="spacing_rhythm",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Spacing CV difference: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M4: Ink density variation
# ---------------------------------------------------------------------------

def m4_ink_density(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare ink density variation via sliding window analysis."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    def _density_profile(gray: np.ndarray, window: int = 50) -> np.ndarray:
        """Mean darkness in sliding vertical windows."""
        h = gray.shape[0]
        densities = []
        for y in range(0, h - window, window // 2):
            strip = 1.0 - gray[y:y + window, :]
            densities.append(strip.mean())
        return np.array(densities) if densities else np.array([0.0])

    prof_r = _density_profile(g_r)
    prof_t = _density_profile(g_t)

    # Pad shorter to match
    max_len = max(len(prof_r), len(prof_t))
    prof_r = np.pad(prof_r, (0, max_len - len(prof_r)))
    prof_t = np.pad(prof_t, (0, max_len - len(prof_t)))

    # Normalized L2 distance
    diff = np.linalg.norm(prof_r - prof_t)
    norm = max(np.linalg.norm(prof_r), np.linalg.norm(prof_t), 1e-8)
    dist = min(1.0, diff / norm)

    return MetricResult(
        id="M4", name="ink_density_variation",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Density profile L2 distance: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M5: Glyph shape consistency (connected component size distribution)
# ---------------------------------------------------------------------------

def m5_glyph_consistency(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare within-class glyph variation via connected component analysis."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)
    b_r, b_t = _binarize(g_r), _binarize(g_t)

    def _component_size_cv(binary: np.ndarray) -> float:
        labeled, n = label(binary)
        if n < 3:
            return 0.0
        sizes = []
        for i in range(1, n + 1):
            s = (labeled == i).sum()
            if s > 10:  # skip tiny noise components
                sizes.append(s)
        if len(sizes) < 3:
            return 0.0
        sizes = np.array(sizes, dtype=float)
        return sizes.std() / sizes.mean() if sizes.mean() > 0 else 0.0

    cv_r = _component_size_cv(b_r)
    cv_t = _component_size_cv(b_t)
    dist = min(1.0, abs(cv_r - cv_t) * 2.0)

    return MetricResult(
        id="M5", name="glyph_shape_consistency",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Component size CV difference: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M6: Ascender/descender proportion
# ---------------------------------------------------------------------------

def m6_ascender_proportion(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare ascender/descender proportions via component height analysis."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)
    b_r, b_t = _binarize(g_r), _binarize(g_t)

    def _height_stats(binary: np.ndarray) -> tuple[float, float]:
        labeled, n = label(binary)
        heights = []
        for i in range(1, min(n + 1, 500)):  # cap for performance
            rows = np.where(np.any(labeled == i, axis=1))[0]
            if len(rows) > 3:
                heights.append(rows.max() - rows.min())
        if len(heights) < 3:
            return 0.0, 0.0
        heights = np.array(heights, dtype=float)
        return heights.mean(), heights.std()

    mean_r, std_r = _height_stats(b_r)
    mean_t, std_t = _height_stats(b_t)

    if mean_r == 0 and mean_t == 0:
        dist = 0.0
    else:
        max_mean = max(mean_r, mean_t, 1.0)
        dist = abs(mean_r - mean_t) / max_mean
        dist = min(1.0, dist)

    return MetricResult(
        id="M6", name="ascender_descender_proportion",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Mean component height difference: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M7: Connection angle distribution
# ---------------------------------------------------------------------------

def m7_connection_angles(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare connection angle distributions via gradient orientation histogram."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    def _gradient_histogram(gray: np.ndarray, n_bins: int = 36) -> np.ndarray:
        """Histogram of gradient orientations on ink pixels."""
        b = _binarize(gray)
        if not b.any():
            return np.zeros(n_bins)
        # Sobel-like gradients
        gy = np.diff(gray, axis=0, prepend=gray[:1, :])
        gx = np.diff(gray, axis=1, prepend=gray[:, :1])
        angles = np.arctan2(gy, gx)  # [-pi, pi]
        magnitude = np.sqrt(gx ** 2 + gy ** 2)
        # Only at ink edges (high magnitude)
        edge_mask = b & (magnitude > 0.05)
        if not edge_mask.any():
            return np.zeros(n_bins)
        edge_angles = angles[edge_mask]
        hist, _ = np.histogram(edge_angles, bins=n_bins, range=(-np.pi, np.pi))
        total = hist.sum()
        return hist / total if total > 0 else hist

    hist_r = _gradient_histogram(g_r)
    hist_t = _gradient_histogram(g_t)
    dist = min(1.0, np.linalg.norm(hist_r - hist_t))

    return MetricResult(
        id="M7", name="connection_angle_distribution",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"Gradient orientation histogram L2: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M8: Overall texture (frequency domain)
# ---------------------------------------------------------------------------

def m8_frequency_texture(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Compare frequency domain texture via 2D FFT power spectra."""
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    def _power_spectrum(gray: np.ndarray) -> np.ndarray:
        # Resize to common size for comparison
        h = min(gray.shape[0], 512)
        w = min(gray.shape[1], 512)
        crop = gray[:h, :w]
        fft = np.fft.fft2(crop)
        ps = np.abs(np.fft.fftshift(fft)) ** 2
        # Log scale, normalized
        ps = np.log1p(ps)
        total = ps.sum()
        return ps / total if total > 0 else ps

    ps_r = _power_spectrum(g_r)
    ps_t = _power_spectrum(g_t)

    # Ensure same shape
    h = min(ps_r.shape[0], ps_t.shape[0])
    w = min(ps_r.shape[1], ps_t.shape[1])
    ps_r = ps_r[:h, :w]
    ps_t = ps_t[:h, :w]

    dist = min(1.0, np.linalg.norm(ps_r - ps_t) * 10.0)

    return MetricResult(
        id="M8", name="frequency_texture",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"FFT power spectrum L2: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M9: Perceptual similarity (optional — requires torch)
# ---------------------------------------------------------------------------

def m9_perceptual(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """Perceptual similarity using pretrained ResNet feature extractor.

    Extracts deep features from both images using a pretrained ResNet-18,
    then computes cosine distance. Captures the overall "feel" that no
    single hand-crafted metric covers.

    Returns distance=-1.0 if torch/torchvision not available.
    """
    try:
        import torch
        import torchvision.models as models
        import torchvision.transforms as transforms
    except ImportError:
        return MetricResult(
            id="M9", name="perceptual_similarity",
            distance=-1.0, rating="unavailable",
            detail="torch not installed — perceptual metric unavailable",
        )

    # Load model once (cached as function attribute)
    if not hasattr(m9_perceptual, "_model"):
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Remove the classification head — use avgpool features (512-dim)
        model = torch.nn.Sequential(*list(model.children())[:-1])
        model.eval()
        m9_perceptual._model = model
        m9_perceptual._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    model = m9_perceptual._model
    transform = m9_perceptual._transform

    with torch.no_grad():
        feat_r = model(transform(rendered).unsqueeze(0)).squeeze()
        feat_t = model(transform(target).unsqueeze(0)).squeeze()

    # Cosine distance: 0 = identical, 1 = orthogonal
    cos_sim = torch.nn.functional.cosine_similarity(feat_r, feat_t, dim=0).item()
    dist = max(0.0, min(1.0, 1.0 - cos_sim))

    return MetricResult(
        id="M9", name="perceptual_similarity",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"ResNet-18 cosine distance: {dist:.3f}",
    )


# ---------------------------------------------------------------------------
# M10: M_conn — Connection quality (TD-004 Part 2)
# ---------------------------------------------------------------------------

def _detect_connections(gray: np.ndarray) -> dict:
    """Analyze inter-letter connection zones in a grayscale image.

    Returns stats: presence_ratio, widths, angles.
    """
    binary = _binarize(gray)
    if not binary.any():
        return {"presence_ratio": 0.0, "widths": [], "angles": []}

    h, w = binary.shape

    # Find text rows via horizontal projection
    proj_h = binary.sum(axis=1).astype(float)
    proj_h = gaussian_filter(proj_h, sigma=2.0)
    threshold = proj_h.mean() + proj_h.std() * 0.3
    text_rows = proj_h > threshold

    if not text_rows.any():
        return {"presence_ratio": 0.0, "widths": [], "angles": []}

    # For each text row band, find thick verticals via column-wise ink density
    labeled_rows, n_rows = label(text_rows)
    connections_present = 0
    connections_total = 0
    widths = []
    angles = []

    for ri in range(1, min(n_rows + 1, 20)):  # cap for performance
        row_indices = np.where(labeled_rows == ri)[0]
        if len(row_indices) < 3:
            continue
        y0, y1 = row_indices[0], row_indices[-1] + 1
        band = binary[y0:y1, :]
        band_h = y1 - y0

        # Vertical projection within this band: thick verticals = high columns
        proj_v = band.sum(axis=0).astype(float)
        proj_v_smooth = gaussian_filter(proj_v, sigma=1.5)
        v_threshold = proj_v_smooth.max() * 0.5

        # Find thick vertical positions (peaks)
        above = proj_v_smooth > v_threshold
        labeled_v, n_v = label(above)

        vert_centers = []
        for vi in range(1, n_v + 1):
            cols = np.where(labeled_v == vi)[0]
            if len(cols) > 1:
                vert_centers.append(int(cols.mean()))

        # Check connection zones between consecutive verticals
        for i in range(len(vert_centers) - 1):
            x0 = vert_centers[i] + 2
            x1 = vert_centers[i + 1] - 2
            if x1 <= x0 or (x1 - x0) > band_h * 3:
                continue  # skip if zone is too narrow or too wide (word gap)

            connections_total += 1
            zone = band[:, x0:x1]
            ink_present = zone.any()

            if ink_present:
                connections_present += 1
                # Measure width: mean number of ink rows per column
                col_sums = zone.sum(axis=0)
                if col_sums.max() > 0:
                    widths.append(float(col_sums[col_sums > 0].mean()))

                # Measure angle: find ink centroid trajectory
                ink_rows = []
                for cx in range(zone.shape[1]):
                    col = zone[:, cx]
                    if col.any():
                        ink_rows.append(np.where(col)[0].mean())
                if len(ink_rows) >= 2:
                    # Slope of centroid trajectory
                    dy = ink_rows[-1] - ink_rows[0]
                    dx = len(ink_rows)
                    angle_deg = np.degrees(np.arctan2(-dy, dx))  # positive = upward
                    angles.append(angle_deg)

    presence_ratio = connections_present / max(connections_total, 1)
    return {"presence_ratio": presence_ratio, "widths": widths, "angles": angles}


def m_conn(rendered: np.ndarray, target: np.ndarray) -> MetricResult:
    """M_conn: Connection quality metric (TD-004 Part 2).

    Measures presence, width, and angle of inter-letter connections.
    Compares distributions between rendered and target.
    """
    g_r, g_t = _to_gray(rendered), _to_gray(target)

    stats_r = _detect_connections(g_r)
    stats_t = _detect_connections(g_t)

    # Presence score: difference in connection ratio
    presence = abs(stats_r["presence_ratio"] - stats_t["presence_ratio"])

    # Width score: Wasserstein distance of widths (normalized)
    if stats_r["widths"] and stats_t["widths"]:
        max_w = max(max(stats_r["widths"]), max(stats_t["widths"]), 1.0)
        width_score = wasserstein_distance(
            [w / max_w for w in stats_r["widths"]],
            [w / max_w for w in stats_t["widths"]],
        )
        width_score = min(1.0, width_score)
    elif not stats_r["widths"] and not stats_t["widths"]:
        width_score = 0.0
    else:
        width_score = 1.0

    # Angle score: Wasserstein distance of angles
    if stats_r["angles"] and stats_t["angles"]:
        angle_score = wasserstein_distance(stats_r["angles"], stats_t["angles"])
        angle_score = min(1.0, angle_score / 90.0)  # normalize by 90°
    elif not stats_r["angles"] and not stats_t["angles"]:
        angle_score = 0.0
    else:
        angle_score = 1.0

    dist = 0.3 * presence + 0.4 * width_score + 0.3 * angle_score
    dist = min(1.0, dist)

    return MetricResult(
        id="M10", name="connection_quality",
        distance=dist, rating=MetricResult.rate(dist),
        detail=f"M_conn: presence={presence:.2f} width={width_score:.2f} angle={angle_score:.2f}",
    )


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------

_ALL_METRICS = [
    m1_stroke_width,
    m2_baseline_regularity,
    m3_spacing_rhythm,
    m4_ink_density,
    m5_glyph_consistency,
    m6_ascender_proportion,
    m7_connection_angles,
    m8_frequency_texture,
    m9_perceptual,
    m_conn,
]


def run_metrics(rendered: np.ndarray, target: np.ndarray) -> list[MetricResult]:
    """Run all 10 metrics on a rendered/target image pair.

    Args:
        rendered: RGB numpy array (H, W, 3) of rendered folio.
        target:   RGB numpy array (H, W, 3) of real manuscript sample.

    Returns:
        List of 9 MetricResult objects.
    """
    return [fn(rendered, target) for fn in _ALL_METRICS]


def composite_score(results: list[MetricResult],
                    weights: dict[str, float] | None = None) -> float:
    """Weighted mean of available metric distances.

    Metrics with distance < 0 (unavailable) are excluded.
    Default weights are equal.
    """
    available = [r for r in results if r.distance >= 0]
    if not available:
        return 1.0

    if weights is None:
        return sum(r.distance for r in available) / len(available)

    total_weight = 0.0
    weighted_sum = 0.0
    for r in available:
        w = weights.get(r.id, 1.0)
        weighted_sum += r.distance * w
        total_weight += w

    return weighted_sum / total_weight if total_weight > 0 else 1.0

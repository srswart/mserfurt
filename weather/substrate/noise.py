"""Multi-octave Perlin noise generator — pure numpy, no scipy dependency.

Uses a hash-based gradient approach: for each lattice cell, a gradient vector
is selected from a fixed table using a seeded permutation. The smooth
interpolation function (smoothstep) gives the characteristic Perlin look.
"""

from __future__ import annotations

import numpy as np


def _make_permutation(seed: int) -> np.ndarray:
    """Generate a 512-element permutation table from seed."""
    rng = np.random.default_rng(seed)
    p = np.arange(256, dtype=np.int32)
    rng.shuffle(p)
    return np.concatenate([p, p])  # doubled for wrapping


def _fade(t: np.ndarray) -> np.ndarray:
    """Smoothstep: 6t^5 - 15t^4 + 10t^3."""
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return a + t * (b - a)


def _grad(hash_val: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Select gradient direction from hash and dot with (x, y)."""
    h = hash_val & 3
    # 4 gradient directions: (1,1), (-1,1), (1,-1), (-1,-1)
    u = np.where(h < 2, x, y)
    v = np.where(h < 2, y, x)
    return np.where(h & 1, -u, u) + np.where(h & 2, -v, v)


def _perlin_single(width: int, height: int, scale: float,
                   perm: np.ndarray) -> np.ndarray:
    """One octave of Perlin noise, values approximately in [-1, 1]."""
    # Build coordinate grids
    x_idx = np.arange(width, dtype=np.float64)
    y_idx = np.arange(height, dtype=np.float64)
    xg, yg = np.meshgrid(x_idx / scale, y_idx / scale)

    xi = xg.astype(np.int32) & 255
    yi = yg.astype(np.int32) & 255
    xf = xg - np.floor(xg)
    yf = yg - np.floor(yg)

    u = _fade(xf)
    v = _fade(yf)

    aa = perm[perm[xi    ] + yi    ]
    ab = perm[perm[xi    ] + yi + 1]
    ba = perm[perm[xi + 1] + yi    ]
    bb = perm[perm[xi + 1] + yi + 1]

    x1 = _lerp(_grad(aa, xf,     yf    ),
               _grad(ba, xf - 1, yf    ), u)
    x2 = _lerp(_grad(ab, xf,     yf - 1),
               _grad(bb, xf - 1, yf - 1), u)

    return _lerp(x1, x2, v)


def perlin_noise(
    width: int,
    height: int,
    scale: float = 32.0,
    octaves: int = 3,
    persistence: float = 0.5,
    lacunarity: float = 2.0,
    seed: int = 0,
) -> np.ndarray:
    """Generate multi-octave Perlin noise as a (height, width) float64 array.

    Values are in approximately [-1, 1]; the exact range depends on octave
    count and persistence.

    Args:
        width:        Output array width in pixels.
        height:       Output array height in pixels.
        scale:        Feature size of the base octave (larger = smoother).
        octaves:      Number of frequency octaves to sum.
        persistence:  Amplitude multiplier per octave (0–1; lower = smoother).
        lacunarity:   Frequency multiplier per octave (> 1; higher = more detail).
        seed:         RNG seed for reproducibility.

    Returns:
        float64 ndarray of shape (height, width) with values in [-1, 1].
    """
    perm = _make_permutation(seed)

    result = np.zeros((height, width), dtype=np.float64)
    amplitude = 1.0
    freq_scale = scale
    max_amplitude = 0.0

    for _ in range(octaves):
        result += _perlin_single(width, height, freq_scale, perm) * amplitude
        max_amplitude += amplitude
        amplitude *= persistence
        freq_scale /= lacunarity

    # Normalise to [-1, 1]
    if max_amplitude > 0:
        result /= max_amplitude

    return np.clip(result, -1.0, 1.0)

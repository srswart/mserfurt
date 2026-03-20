"""DamageZone and DamageResult — public API for downstream groundtruth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from PIL import Image


@dataclass
class DamageResult:
    """Output of a damage rendering pass.

    Attributes:
        image:       RGB PIL Image with damage effects applied.
        water_zone:  bool mask (H×W) of water-affected pixels, or None.
        corner_mask: bool mask (H×W) of physically-removed corner pixels, or None.
    """
    image: Image.Image
    water_zone: Optional[np.ndarray] = None
    corner_mask: Optional[np.ndarray] = None

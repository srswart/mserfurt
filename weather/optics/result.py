"""OpticsResult — container for optics-layer output and coordinate transform."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image


@dataclass
class OpticsResult:
    """Output of the optics pipeline stage.

    Attributes:
        image:           Final RGB PIL Image after all optics effects.
        curl_transform:  Float32 array of shape (H, W, 2) where channel 0 is
                         the y-displacement and channel 1 is the x-displacement
                         (in pixels) applied to each source pixel.
                         None when page_curl is disabled.
    """

    image: Image.Image
    curl_transform: Optional[np.ndarray] = None

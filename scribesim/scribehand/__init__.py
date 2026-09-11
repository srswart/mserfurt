"""scribehand — TD-018 learned scribal hand synthesis.

Generates Bastarda word images with a style-conditioned generative backend
(fine-tuned diffusion HTG models on the Mac workstation; deterministic stubs
on CPU-only dev machines), verifies text fidelity with an HTR-in-the-loop
rejection-sampling gate, and composes verified word strips into full folio
pages compatible with the existing Weather pipeline.
"""

from scribesim.scribehand.types import WordRequest, WordStrip, WordResult
from scribesim.scribehand.seeds import word_seed
from scribesim.scribehand.generate import WordGenerator

__all__ = ["WordRequest", "WordStrip", "WordResult", "word_seed", "WordGenerator"]

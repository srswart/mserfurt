"""Weather compositor — manifest-driven per-folio effect stacking."""

from weather.compositor.compositor import composite_folio, CompositorResult
from weather.compositor.manifest import ManifestEntry, load_manifest

__all__ = ["composite_folio", "CompositorResult", "ManifestEntry", "load_manifest"]

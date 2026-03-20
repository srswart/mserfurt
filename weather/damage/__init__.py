"""Weather damage — water staining and physical loss simulation."""

from weather.damage.zones import DamageResult
from weather.damage.pipeline import apply_damage

__all__ = ["DamageResult", "apply_damage"]

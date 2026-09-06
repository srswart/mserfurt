"""Versioned physical broad-edge geometry; no pressure deformation or optical action."""

from dataclasses import dataclass, replace
import math

from scribesim.handvalidate.model import TrajectorySample


VERSION = 'physical-edge-v1'
WIDTH_MM = .45
THICKNESS_MM = .02


@dataclass(frozen=True)
class ContactSample(TrajectorySample):
    edge_start: float = 0.0
    edge_end: float = 1.0
    contact_version: str = VERSION


def contact_corners(sample):
    values = (sample.x_mm, sample.y_mm, sample.width_mm, sample.pressure, sample.nib_angle_deg,
              sample.edge_start, sample.edge_end)
    if (sample.contact_version != VERSION or any(type(value) not in (float, int) or not math.isfinite(value) for value in values)
            or type(sample.contact) is not bool or sample.width_mm != WIDTH_MM
            or sample.pressure != (.5 if sample.contact else 0)
            or not -180 <= sample.nib_angle_deg <= 540
            or not 0 <= sample.edge_start < sample.edge_end <= 1 or sample.edge_end - sample.edge_start < .1):
        raise ValueError('Unsupported physical contact fields')
    angle = math.radians(sample.nib_angle_deg)
    direction = math.cos(angle), math.sin(angle)
    normal = -direction[1], direction[0]
    return [(sample.x_mm + (edge - .5) * WIDTH_MM * direction[0] + side * THICKNESS_MM / 2 * normal[0],
             sample.y_mm + (edge - .5) * WIDTH_MM * direction[1] + side * THICKNESS_MM / 2 * normal[1])
            for edge in (sample.edge_start, sample.edge_end) for side in (-1, 1)]


def reflect_sample(sample):
    contact_corners(sample)
    reflected = replace(sample, y_mm=-sample.y_mm, nib_angle_deg=-sample.nib_angle_deg)
    contact_corners(reflected)
    return reflected


def swept_polygon(first, second):
    points = sorted(set(contact_corners(first) + contact_corners(second)))

    def turn(origin, previous, current):
        return ((previous[0] - origin[0]) * (current[1] - origin[1])
                - (previous[1] - origin[1]) * (current[0] - origin[0]))

    lower, upper = [], []
    for chain, ordered in ((lower, points), (upper, reversed(points))):
        for point in ordered:
            while len(chain) > 1 and turn(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
    return lower[:-1] + upper[:-1]

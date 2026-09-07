"""Opt-in source-derivative directions on the existing validated curve clock."""

from dataclasses import replace
import math

import numpy as np

from scribesim.handflow.planning import retime_curve_timing


VERSION = 'curve-tangent-v1'


def cubic_direction(cubic, parameter):
    controls = np.asarray(cubic, dtype=float)
    if (controls.shape != (4, 2) or not np.isfinite(controls).all()
            or type(parameter) not in (int, float) or not math.isfinite(parameter) or not 0 <= parameter <= 1):
        raise ValueError('Finite cubic and bounded source parameter required')
    differences = np.diff(controls, axis=0)
    derivative = 3 * ((1 - parameter) ** 2 * differences[0]
                      + 2 * (1 - parameter) * parameter * differences[1] + parameter ** 2 * differences[2])
    magnitude = float(np.linalg.norm(derivative))
    if not math.isfinite(magnitude) or magnitude <= 1e-7:
        raise ValueError('Stationary source derivative unsupported')
    return derivative / magnitude


def retime_curve_tangents(plan, owners, strokes):
    retime_curve_timing(plan, owners, strokes)
    indexed = {row['occurrence_id']: row for row in strokes}
    samples = []
    for sample, owner in zip(plan.samples, owners):
        if not sample.contact:
            samples.append(sample)
            continue
        row = indexed[owner['occurrence_id']]
        for key in ('primitive', 'primitive_sha256', 'gesture_sha256', 'action_sha256', 'span', 'gesture_occurrence_id'):
            if key in row and owner.get(key) != row[key]:
                raise ValueError('Source owner identity does not match compiled geometry')
        position = owner['curve_position']
        cubic = np.asarray(row['cubics'][position['cubic_index']]) * [plan.x_height_mm, -plan.x_height_mm]
        direction = cubic_direction(cubic, position['parameter'])
        samples.append(replace(sample, vx_mm_s=float(direction[0] * sample.speed_mm_s),
                               vy_mm_s=float(direction[1] * sample.speed_mm_s)))
    result = retime_curve_timing(replace(plan, samples=tuple(samples)), owners, strokes)
    return replace(result, version=VERSION)

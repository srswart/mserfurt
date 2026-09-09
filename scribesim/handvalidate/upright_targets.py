"""Candidate-free analytic upright yardstick, not an owner appearance standard."""

from dataclasses import replace

import numpy as np

from scribesim.evo.nib_contact import ContactSample


def shapes(spec):
    definition = spec['target']
    parameter = np.linspace(0, 1, definition['samples_per_part'])
    radius = definition['radius']

    def line(start, end):
        return np.asarray(start) + parameter[:, None] * np.subtract(end, start)

    upper_angle = np.pi * (1-parameter)
    lower_angle = np.pi * (1+parameter)
    upper = np.column_stack((radius+radius*np.cos(upper_angle), 1-radius+radius*np.sin(upper_angle)))
    lower = np.column_stack((radius+radius*np.cos(lower_angle), radius+radius*np.sin(lower_angle)))
    return {'stem': [line((0, 1), (0, 0))], 'rise': [line((0, 0), (0, 1-radius))],
            'upper-return': [upper], 'lower-return': [lower],
            'overturn': [line((0, 0), (0, 1-radius)), upper, line((2*radius, 1-radius), (2*radius, 0))],
            'underturn': [line((0, 1), (0, radius)), lower, line((2*radius, radius), (2*radius, 1))]}


def target(fixture, spec):
    definition, families = spec['target'], shapes(spec)
    width = 2*definition['radius']
    recipes = {'n': [('stem', 0), ('overturn', 0)],
               'u': [('underturn', 0), ('stem', width)],
               'm': [('overturn', 0), ('overturn', width)]}
    path, regions, cursor = [], {}, 0.0
    for letter, character in enumerate(fixture['text']):
        sequence = recipes[character] if fixture['kind'] == 'letter' else [(fixture['name'], 0)]
        points = np.concatenate([part + [cursor+definition['origin_x']+horizontal+fixture['shift'][0], fixture['shift'][1]]
                                 for name, horizontal in sequence for part in families[name]])
        points = points * [definition['x_height_mm'], -definition['x_height_mm']] + [0, definition['baseline_mm']]
        segment = [ContactSample(float(point[0]), float(point[1]), True, .45, .5, 40) for point in points]
        if path:
            path.append(replace(segment[0], contact=False, pressure=0))
        path.extend(segment)
        low, high = points.min(axis=0)-spec['local_padding_mm'], points.max(axis=0)+spec['local_padding_mm']
        regions[str(letter)] = [float(low[0]), float(high[0]), float(low[1]), float(high[1])]
        cursor += definition['advances'].get(character, 2) + definition['letter_gap']
    return path, regions

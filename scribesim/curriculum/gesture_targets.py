"""Independent analytic construction targets with no model or optimizer inputs."""

import numpy as np


TOPOLOGIES = {
    'underturn': (['stem', 'lower-return', 'rise'], [0, 1]),
    'overturn': (['rise', 'upper-return', 'stem'], [0, 0]),
    'compound_curve': (['upper-return', 'stem', 'lower-return', 'rise'], [0, 0]),
    'stem': (['support-stem'], [0, 1]),
    'terminal': (['support-terminal'], [0, 0]),
}


def parts(specification, fixture):
    parameter = np.linspace(0, 1, 257)[:, None]
    result = []
    for occurrence, instance in enumerate(fixture['instances']):
        topology, origin = TOPOLOGIES[instance['gesture']]
        endpoint = np.asarray(origin, dtype=float)
        for family in topology:
            definition = specification[family]
            entry = (np.multiply(definition['entry_ray'], definition['magnitudes'][0])
                     if 'entry_ray' in definition else np.asarray(definition['entry']))
            departure = (np.multiply(definition['exit_ray'], definition['magnitudes'][1])
                         if 'exit_ray' in definition else np.asarray(definition['exit']))
            points = ((parameter - 2 * parameter ** 2 + parameter ** 3) * entry
                      + (3 * parameter ** 2 - 2 * parameter ** 3) * definition['end']
                      + (parameter ** 3 - parameter ** 2) * departure
                      + np.sin(np.pi * parameter) ** 2 * definition['bulge'] + endpoint)
            origin = endpoint.copy()
            endpoint = points[-1].copy()
            result.append({'occurrence': occurrence, 'gesture': instance['gesture'], 'family': family,
                           'origin': origin * instance['scale'] + instance['offset'],
                           'points': points * instance['scale'] + instance['offset'], 'scale': instance['scale']})
    return result


def segments(specification, fixture):
    return [part['points'] for part in parts(specification, fixture)]

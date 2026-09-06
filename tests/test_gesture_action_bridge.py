import copy
from dataclasses import asdict

import numpy as np
import pytest

from scribesim.evofit.stroke_language import seed_language
from scribesim.evofit.stroke_gestures import migrate_v1
from scribesim.handvalidate.specimen import object_digest, write_json
from scribesim.pathguide.gesture_actions import action_bundle, execute_actions, load_actions


def model():
    program = migrate_v1(seed_language())
    program['sampling'] = 'gesture-arc-v2'
    program['actions']['fixed']['orientation'] = [[0, 40], [1, 60]]
    return program


def test_actual_rate_limit_is_not_desired_playback():
    program = model()
    normal = execute_actions('i u', program)
    forced = execute_actions('i u', program, angular_rate=1)
    assert normal['metrics']['orientation_error_deg'] < 2
    assert forced['metrics']['orientation_error_deg'] > 10
    assert not forced['tracking_pass']
    assert not np.array_equal(forced['images']['desired'], forced['images']['actual'])
    assert forced['metrics']['realized_angular_rate_deg_s'] <= 1 + 1e-9
    assert all(row['edge_start'] <= row['edge_end'] for row in forced['trajectory'])


def test_edge_release_realized_fields_and_exact_ownership():
    program = model()
    program['actions']['fixed']['orientation'] = [[0, 40], [1, 40]]
    program['actions']['fixed']['edge'] = [[0, 0, 1], [1, 0, .5]]
    result = execute_actions('i u', program)
    assert result['metrics']['contact_errors'] == 0
    assert result['metrics']['edge_error_fraction'] < .02
    assert all(owner['kind'] == 'stroke' for owner, point in zip(result['owners'], result['trajectory']) if point['contact'])
    assert all(point['pressure'] == 0 for point in result['trajectory'] if not point['contact'])
    assert all(point['contact_version'] == 'physical-edge-v1' for point in result['trajectory'])
    assert len({owner['gesture_occurrence_id'] for owner in result['owners'] if owner['kind'] == 'stroke'}) == 3


def test_new_bundle_rejects_stale_or_missing_fields(tmp_path):
    program = model()
    bundle = action_bundle('i', program)
    path = tmp_path / 'bundle.json'
    payload = asdict(bundle)
    write_json(path, {'payload': payload, 'sha256': object_digest(payload)})
    assert load_actions(path, program).model_sha256 == object_digest(program)
    broken = copy.deepcopy(payload)
    del broken['plan']['samples'][0]['edge_start']
    write_json(path, {'payload': broken, 'sha256': object_digest(broken)})
    with pytest.raises(ValueError):
        load_actions(path, program)


def test_wrap_is_unwrapped_and_constant_tool_required():
    program = model()
    program['actions']['fixed']['orientation'] = [[0, 179], [1, 181]]
    result = execute_actions('i', program)
    assert result['metrics']['orientation_error_deg'] < 2
    assert min(row['nib_angle_deg'] for row in result['trajectory']) >= 179
    program['actions']['fixed']['speed_mm_s'] = 13
    with pytest.raises(ValueError):
        execute_actions('i', program)


def test_bridge_proofs_record_failures_without_granting_acceptance(tmp_path):
    from scribesim.handvalidate.action_bridge import build

    report = build(tmp_path / 'proofs')
    assert report['scope'].startswith('analytic')
    assert not report['S1_action_accepted']
    assert report['renders'] <= 100
    assert report['forced_lag_detected']

import copy

import pytest

from scripts import stroke_context_preview as preview


@pytest.fixture(scope='module')
def documents():
    candidate = preview.context.audit.read_json(preview.context.audit.CANDIDATE)
    return preview.documents(candidate)


def test_exact_inventory_and_isolated_null(documents):
    assert len(documents) == 48
    for text in 'num':
        assert all(preview.points(documents[text+':'+hypothesis]) == preview.points(documents[text+':H0'])
                   for hypothesis in preview.HYPOTHESES)


def test_causal_checks_and_real_local_bounds(documents):
    result = preview.analyze(documents)
    assert result['previous_near_far_distinct']
    assert result['following_stem_rise_distinct']
    assert result['same_previous_bin_same_effect']
    assert result['all_anchors_and_advances_exact']
    assert result['maximum_control_delta_mm'] <= .04
    assert result['frame_size_pixels'] == [1169, 390]


@pytest.mark.parametrize('mutation', ['body', 'anchor', 'advance', 'contact', 'swap'])
def test_undeclared_changes_fail(documents, mutation):
    changed = copy.deepcopy(documents)
    row = changed['un:H3']['compiled']['strokes'][1]
    if mutation in ('body', 'anchor'):
        row['cubics'][0][1 if mutation == 'body' else 0][0] += .001
    elif mutation == 'advance':
        changed['un:H3']['compiled']['lines'][0]['width'] += .01
    elif mutation == 'contact':
        row['contact_run_id'] = 'forged'
    else:
        changed['un:H3']['compiled'] = copy.deepcopy(changed['um:H3']['compiled'])
    with pytest.raises(ValueError):
        preview.analyze(changed)


def test_protocol_has_no_implicit_render_permission():
    protocol = preview.protocol()
    assert protocol['nominal_rendering']['image_count'] == 48
    assert protocol['nominal_rendering']['approved'] is False
    assert protocol['physical']['executions'] == 1152
    assert protocol['physical']['render_calls_upper_bound'] == 4104
    assert protocol['physical']['approved'] is False
    assert protocol['owner_feedback'] == []


def test_crop_rejected(documents):
    with pytest.raises(ValueError, match='frame'):
        preview.analyze(documents, frame=[0, 1, 0, 1])


def test_snapshot_refuses_overwrite(tmp_path):
    with pytest.raises(FileExistsError):
        preview.prepare(tmp_path)

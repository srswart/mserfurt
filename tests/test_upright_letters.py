import copy
import json

import numpy as np
import pytest

from scribesim.curriculum import upright_letters as upright
from scribesim.evofit.stroke_gestures import compile_gestures, gesture_guide


def test_source_is_pinned_and_stem_geometry_is_not_refitted():
    source = upright.load_source()
    before = copy.deepcopy(source)
    model = upright.make_model(source)
    assert source == before
    assert model['primitives']['stem']['cubics'] == source['primitives']['stem']['cubics']
    assert model['primitives']['stem']['entry'] != source['primitives']['stem']['entry']
    assert model['actions'] == source['actions']
    assert model['letter_rules'] == model['word_rules'] == []
    altered = copy.deepcopy(source)
    altered['primitives']['stem']['cubics'][0][1][0] += .001
    with pytest.raises(ValueError, match='source'):
        upright.make_model(altered)


@pytest.mark.parametrize('letter,count', [('n', 4), ('u', 4), ('m', 6)])
def test_shared_recipes_are_level_continuous_and_unrotated(letter, count):
    model = upright.make_model(upright.load_source())
    compiled = compile_gestures(letter, model)['strokes']
    assert len(compiled) == count
    assert len({row['contact_run_id'] for row in compiled}) == 1
    assert all(row['rotation_deg'] == 0 for row in compiled)
    assert all(.5 <= row['scale'] <= 1.5 for row in compiled)
    low, high = upright.extrema([curve for row in compiled for curve in row['cubics']], 1)
    assert low == pytest.approx(0, abs=1e-8)
    assert high == pytest.approx(1, abs=1e-8)
    assert all(point.contact for point in gesture_guide(letter, model).guide.samples)
    for previous, current in zip(compiled, compiled[1:]):
        np.testing.assert_allclose(previous['cubics'][-1][-1], current['cubics'][0][0], atol=1e-10)


def test_shared_return_preserves_cap_height_profile_and_declares_handle_change():
    source = upright.load_source()
    model = upright.make_model(source)
    old = next(row for row in compile_gestures('n', source)['strokes'] if row['primitive'] == 'upper-return')['cubics'][0]
    new = next(row for row in compile_gestures('n', model)['strokes'] if row['primitive'] == 'upper-return')['cubics'][0]
    np.testing.assert_allclose(np.array(new)[:, 1], np.array(old)[:, 1], atol=1e-12)
    assert new[3][0]-new[0][0] == pytest.approx(old[3][0]-old[0][0])
    assert new[2][0]-new[0][0] != pytest.approx(old[2][0]-old[0][0])
    upper = [row for letter in 'nm' for row in compile_gestures(letter, model)['strokes'] if row['primitive'] == 'upper-return']
    assert len({row['primitive_sha256'] for row in upper}) == 1
    report = upright.measure(model)
    for rows in report.values():
        assert all(abs(row['chord_deg_from_vertical']) < 6 for row in rows['strokes'] if row['primitive'] in {'stem', 'rise'})
        assert rows['body_stem_rise_max_horizontal_separation_mm'] < .3


def test_preview_exports_nominal_only_and_freezes_review_identity(tmp_path, monkeypatch):
    import scribesim.pathguide.gesture_actions as actions
    monkeypatch.setattr(actions, 'execute_actions', lambda *args, **kwargs: pytest.fail('No physical experiment before review'))
    output = tmp_path / 'preview'
    upright.build(output)
    report = json.loads((output / 'report.json').read_text())
    review = json.loads((output / 'owner-review.json').read_text())
    assert report['optimization_evaluations'] == report['physical_executions'] == 0
    assert report['S2_accepted'] is report['context_training_allowed'] is False
    assert review['status'] == 'pending'
    assert review['candidate_sha256'] == report['candidate_sha256']
    for letter in 'num':
        for arm in ('prior', 'proposed'):
            assert (output / f'{letter}-{arm}-full.png').is_file()
            assert (output / f'{letter}-{arm}-detail.png').is_file()
        assert (output / f'{letter}-paths.svg').is_file()
    assert (output / 'strokes.svg').is_file()
    assert (output / 'strokes-ink.png').is_file()
    assert 'Nominal' in (output / 'index.html').read_text()
    assert all(row['contained'] for row in report['containment'])
    assert upright.verify_preview(output)['candidate_sha256'] == report['candidate_sha256']
    before = {path: path.read_bytes() for path in output.iterdir()}
    upright.verify_preview(output)
    assert all(path.read_bytes() == data for path, data in before.items())
    review['candidate_sha256'] = 'wrong'
    (output / 'owner-review.json').write_text(json.dumps(review))
    with pytest.raises(ValueError, match='review'):
        upright.verify_preview(output)
    (output / 'owner-review.json').write_bytes(before[output / 'owner-review.json'])
    (output / 'candidate.json').write_text('{}')
    with pytest.raises(ValueError, match='artifact'):
        upright.verify_preview(output)
    with pytest.raises(ValueError, match='empty'):
        upright.build(output)


def test_cropped_frame_rejected_before_painting():
    model = upright.make_model(upright.load_source())
    with pytest.raises(ValueError, match='frame'):
        upright.nominal('n', model, [0, .1, 0, .1], dpi=72)

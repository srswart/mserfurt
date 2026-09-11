import copy
from dataclasses import asdict, replace
import gzip
import json

import pytest

from scripts import letter_context_contract as context, letter_context_evidence as reader
from scripts import upright_placement_validation as placement
from scribesim.evofit.stroke_gestures import compile_gestures, validate_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.pathguide.gesture_actions import action_bundle
from scribesim.handvalidate.specimen import digest, object_digest


@pytest.fixture
def candidate():
    return json.loads((placement.evaluation.SOURCE/'candidate.json').read_text())


@pytest.mark.parametrize('fixture_index', [0, 2, 3, 9])
@pytest.mark.parametrize('refinement', ['base', 'arc', 'time', 'subdivision'])
def test_null_context_preserves_exact_compilation_plan_and_timing(candidate, fixture_index, refinement):
    before = object_digest(candidate)
    fixture = placement.SPEC['fixtures'][fixture_index]
    model = placement.model_for_fixture(candidate, fixture)
    if refinement == 'subdivision':
        model = placement.evaluation.subdivide(model)
    expected = compile_gestures(fixture['text'], model)
    bundle = action_bundle(fixture['text'], model, step_mm=placement.SPEC['refinements'][refinement][0], include_curve_positions=True)
    timed = retime_curve_tangents(bundle.plan, bundle.owners, expected['strokes'])
    expected_bundle = replace(bundle, plan=timed.plan, owners=[bundle.owners[index] for index in timed.source_indices])
    for enabled in (False, True):
        document = context.compile_context(candidate, fixture, context.null_program(candidate, enabled=enabled), refinement)
        assert object_digest(document['compiled']) == object_digest(expected)
        actual_bundle, actual_timed = context.prepare_null_plan(document, candidate, fixture, refinement)
        assert asdict(actual_bundle) == asdict(expected_bundle)
        assert asdict(actual_timed) == asdict(timed)
        assert document['lineage']['context_training_allowed'] is False
        for row in document['lineage']['occurrences']:
            assert row['source_geometry_sha256'] == row['derived_geometry_sha256']
            assert row['canonical_primitive_sha256'] == object_digest(candidate['primitives'][row['owner']['primitive']])
        assert object_digest(candidate) == before


def test_six_shared_cells_resolve_following_entry_without_word_keys(candidate):
    program = context.null_program(candidate)
    assert len(program['rules']) == 6
    for text, expected in [('un', 'u:stem-entry'), ('um', 'u:rise-entry'), ('mm', 'm:rise-entry')]:
        fixture = next(row for row in placement.SPEC['fixtures'] if row['text'] == text)
        document = context.compile_context(candidate, fixture, program, 'base')
        rows = document['lineage']['occurrences']
        assert {row['rule_id'] for row in rows if row['owner']['letter'] == 0} == {expected}
        assert {row['rule_id'] for row in rows if row['owner']['letter'] == 1} == {None}
    fixture = placement.SPEC['fixtures'][4]
    program['rules'] = []
    document = context.compile_context(candidate, fixture, program, 'base')
    assert all(row['rule_id'] is None for row in document['lineage']['occurrences'])


def test_all_six_rule_cells_and_absent_matches_without_new_geometry(candidate):
    program = context.null_program(candidate)
    for letter in ('n', 'u', 'm'):
        assert context.resolve_rule(program, letter, 'n') == ('stem-entry', letter+':stem-entry')
        assert context.resolve_rule(program, letter, 'u') == ('stem-entry', letter+':stem-entry')
        assert context.resolve_rule(program, letter, 'm') == ('rise-entry', letter+':rise-entry')
        assert context.resolve_rule(program, letter, None) == (None, None)
    program['rules'] = program['rules'][:1]
    assert context.resolve_rule(program, 'u', 'n') == ('stem-entry', None)
    with pytest.raises(ValueError):
        context.resolve_rule(program, 'n', 'a')


def test_reader_does_not_trust_context_compiler(candidate, monkeypatch):
    fixture = placement.SPEC['fixtures'][0]
    document = context.compile_context(candidate, fixture, context.null_program(candidate), 'base')
    def forbidden(*args, **kwargs):
        pytest.fail('Reader trusted the new context compiler')
    monkeypatch.setattr(context, 'compile_context', forbidden)
    reader.verify_document(document, candidate, fixture, 'base')


@pytest.mark.parametrize('mutation', ['scale', 'advance', 'nan', 'boolean', 'duplicate', 'selector', 'word', 'unknown', 'candidate', 'permission'])
def test_unapproved_or_malformed_programs_fail_closed(candidate, mutation):
    program = context.null_program(candidate)
    rule = program['rules'][0]
    if mutation in ('scale', 'nan', 'boolean'):
        rule['width_scale'] = {'scale': .97, 'nan': float('nan'), 'boolean': True}[mutation]
    elif mutation == 'advance':
        rule['advance_delta'] = .05
    elif mutation == 'duplicate':
        program['rules'].append(copy.deepcopy(rule))
    elif mutation == 'selector':
        rule['following_entry_class'] = 'previous-letter'
    elif mutation == 'word':
        rule['word'] = 'mum'
    elif mutation == 'unknown':
        rule['current_letter'] = 'a'
    elif mutation == 'candidate':
        program['candidate_sha256'] = '0'*64
    else:
        program['execution_authorized'] = True
    with pytest.raises(ValueError):
        context.compile_context(candidate, placement.SPEC['fixtures'][0], program, 'base')


@pytest.mark.parametrize('mutation', ['geometry', 'owner', 'rule', 'canonical_hash', 'derived_hash', 'recipe', 'transform', 'missing', 'permission', 'program_hash'])
def test_independent_lineage_reader_rejects_rehashed_forgery(candidate, mutation):
    fixture = placement.SPEC['fixtures'][4]
    document = context.compile_context(candidate, fixture, context.null_program(candidate), 'base')
    row = document['lineage']['occurrences'][0]
    if mutation == 'geometry':
        document['compiled']['strokes'][0]['cubics'][0][1][0] += .001
    elif mutation == 'owner':
        row['owner']['span'] = [1, 2]
    elif mutation == 'rule':
        row['rule_id'] = 'u:rise-entry'
    elif mutation in ('canonical_hash', 'derived_hash', 'recipe'):
        field = {'canonical_hash': 'canonical_primitive_sha256', 'derived_hash': 'derived_geometry_sha256', 'recipe': 'canonical_recipe_sha256'}[mutation]
        row[field] = '0'*64
    elif mutation == 'transform':
        row['transform']['width_scale'] = 1.03
    elif mutation == 'missing':
        document['lineage']['occurrences'].pop()
    elif mutation == 'permission':
        document['lineage']['context_training_allowed'] = True
    else:
        document['lineage']['context_program_sha256'] = '0'*64
    with pytest.raises(ValueError):
        reader.verify_document(document, candidate, fixture, 'base')
    with pytest.raises(ValueError):
        context.prepare_null_plan(document, candidate, fixture, 'base')


def test_canonical_candidate_fixture_and_refinement_cannot_expand(candidate):
    program = context.null_program(candidate)
    fixture = copy.deepcopy(placement.SPEC['fixtures'][0])
    fixture['text'] = 'mmm'
    with pytest.raises(ValueError):
        context.compile_context(candidate, fixture, program, 'base')
    with pytest.raises(ValueError):
        context.compile_context(candidate, placement.SPEC['fixtures'][0], program, 'invented')
    candidate['primitives']['stem']['cubics'][0][1][0] += .001
    with pytest.raises(ValueError):
        context.compile_context(candidate, placement.SPEC['fixtures'][0], program, 'base')


def test_legacy_compiler_still_rejects_nonempty_context(candidate):
    candidate['letter_rules'] = [{'id': 'null', 'current': 'n', 'next': 'u', 'advance_delta': 0}]
    with pytest.raises(ValueError):
        validate_gestures(candidate)


def test_rule_order_is_canonical_and_sidecar_does_not_alias_input(candidate):
    program = context.null_program(candidate)
    fixture = placement.SPEC['fixtures'][4]
    document = context.compile_context(candidate, fixture, program, 'base')
    program['rules'].reverse()
    assert context.compile_context(candidate, fixture, program, 'base') == document
    document['lineage']['occurrences'][0]['owner']['offset'][0] += 1
    assert context.compile_context(candidate, fixture, program, 'base')['compiled'] == document['compiled']


@pytest.mark.parametrize('mutation', [None, 'plan', 'owner', 'corner', 'refinement'])
def test_archived_null_binding_checks_plan_events_and_owner(candidate, mutation):
    fixture = placement.SPEC['fixtures'][0]
    document = context.compile_context(candidate, fixture, context.null_program(candidate), 'base')
    bundle, timed = context.prepare_null_plan(document, candidate, fixture, 'base')
    run = json.loads(gzip.decompress((placement.BASE/'run-001/seed-7/first/letter-n-traces.json.gz').read_bytes()))['base']
    if mutation == 'plan':
        run['plan']['samples'][0]['t_s'] += .001
    elif mutation == 'owner':
        run['trace'][0]['owner']['primitive_sha256'] = '0'*64
    elif mutation == 'corner':
        run['corners'][0]['time_s'] += .001
    elif mutation == 'refinement':
        run['dt_s'] = .001
    if mutation is None:
        assert reader.bind_archived_run(run, bundle, timed, 'base')['exact_input_match'] is True
    else:
        with pytest.raises(ValueError):
            reader.bind_archived_run(run, bundle, timed, 'base')


def test_snapshot_is_pinned_immutable_and_cannot_promote_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(reader, 'summarize', lambda: {'status': 'pass', 'context_training_allowed': False})
    directory = tmp_path/'snapshot'
    reader.build(directory)
    with pytest.raises(ValueError):
        reader.build(directory)
    with pytest.raises(ValueError):
        reader.inspect(directory, None)
    assert reader.inspect(directory, digest(directory/'report.json'))['read_only'] is True
    report = json.loads((directory/'report.json').read_text())
    report['context_training_allowed'] = True
    (directory/'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError):
        reader.inspect(directory, digest(directory/'report.json'))


def test_null_planning_never_executes_or_renders(candidate, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Null contract attempted physical execution or rendering')
    monkeypatch.setattr(placement.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(placement.evaluation, 'paint', forbidden)
    fixture = placement.SPEC['fixtures'][0]
    document = context.compile_context(candidate, fixture, context.null_program(candidate), 'base')
    context.prepare_null_plan(document, candidate, fixture, 'base')


def test_readonly_summary_binds_real_archived_pixels(candidate, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Read-only evidence attempted a new physical run or render')
    requests = []
    def clearance(directory, **kwargs):
        requests.append((directory, kwargs))
        return {'context_gaps': ['not training clearance']}
    monkeypatch.setattr(reader.foundation, 'require_readiness', clearance)
    monkeypatch.setattr(placement.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(placement.evaluation, 'paint', forbidden)
    monkeypatch.setattr(placement, 'SPEC', {**placement.SPEC, 'fixtures': placement.SPEC['fixtures'][:1],
        'refinements': {'base': placement.SPEC['refinements']['base']}, 'seeds': [7]})
    report = reader.summarize()
    assert report['compilation_plan_cases'] == 2
    assert report['archived_runs_bound'] == 2
    assert report['archived_images_bound'] == 4
    assert report['known_base_reference_matches'] == 2
    assert report['fresh_physical_null_replay'] is report['context_training_allowed'] is False
    assert requests[0][1]['expected_report_sha256'] == reader.READINESS_SHA256
    assert requests[0][1]['candidate'] == candidate
    assert report['new_controller_executions'] == report['new_renders'] == 0

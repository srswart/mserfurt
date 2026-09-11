import copy
from dataclasses import asdict
import json
import math
import shutil

import numpy as np
import pytest

from scripts import letter_context_variants as variants, letter_context_variant_evidence as evidence
from scripts import letter_context_contract as null
from scribesim.handvalidate.specimen import digest, object_digest


@pytest.fixture
def candidate():
    return json.loads((variants.foundation.placement.evaluation.SOURCE/'candidate.json').read_text())


def fixture(text, role='train_pairs'):
    return next(row for row in variants.fixtures() if row['text'] == text and row['role'] == role)


@pytest.mark.parametrize('scale', [.97, 1, 1.03])
@pytest.mark.parametrize('advance', [-.05, 0, .05])
def test_affine_width_and_spacing_are_independent_with_unchanged_verticals(candidate, scale, advance):
    selected = fixture('nm')
    program = variants.make_program({'n:rise-entry': (scale, advance)})
    document = variants.compile_variant(candidate, selected, program)
    baseline = variants.source_compile(candidate, selected, 'base')
    anchor = baseline['strokes'][0]['cubics'][0][0][0]
    for source, derived in zip(baseline['strokes'], document['compiled']['strokes']):
        expected = copy.deepcopy(source['cubics'])
        for cubic in expected:
            for point in cubic:
                if source['letter'] == 0 and scale != 1:
                    point[0] = anchor+scale*(point[0]-anchor)
                elif source['letter'] == 1 and advance != 0:
                    point[0] += advance
        assert derived['cubics'] == expected
        assert np.array(derived['cubics'])[:, :, 1].tolist() == np.array(source['cubics'])[:, :, 1].tolist()
    assert object_digest(candidate) == null.CANDIDATE_SHA256
    evidence.verify_document(document, candidate, selected, 'base')


@pytest.mark.parametrize('text,count', [('nn', 9), ('nm', 9), ('mmm', 9), ('nmm', 81)])
def test_shared_cell_enumeration_not_per_occurrence_memorization(text, count):
    assert len(variants.programs_for(text)) == count
    assert all(len({row['id'] for row in program['rules']}) == len(program['rules']) for program in variants.programs_for(text))


@pytest.mark.parametrize('refinement', ['base', 'arc', 'time', 'subdivision'])
def test_new_null_planner_matches_frozen_bridge_exactly(candidate, refinement):
    selected = next(row for row in variants.fixtures() if row['id'] == 'placed-mu')
    program = variants.make_program({})
    document = variants.compile_variant(candidate, selected, program, refinement)
    new_bundle, new_timing = variants.prepare_plan(document, candidate, selected, refinement)
    original_fixture = {key: value for key, value in selected.items() if key != 'role'}
    original = null.compile_context(candidate, original_fixture, null.null_program(candidate), refinement)
    old_bundle, old_timing = null.prepare_null_plan(original, candidate, original_fixture, refinement)
    assert document['compiled'] == original['compiled']
    assert asdict(new_bundle) == asdict(old_bundle)
    assert asdict(new_timing) == asdict(old_timing)


@pytest.mark.parametrize('text', ['nm', 'um', 'mm'])
def test_nonidentity_planner_uses_derived_not_canonical_geometry(candidate, text):
    selected = fixture(text)
    program = variants.programs_for(text)[0]
    document = variants.compile_variant(candidate, selected, program)
    bundle, timed = variants.prepare_plan(document, candidate, selected, 'base')
    assert bundle.model_sha256 == object_digest(document)
    assert timed.plan == bundle.plan
    assert all(owner['derived_geometry_sha256'] for owner in bundle.owners if owner['kind'] == 'stroke')
    baseline = variants.compile_variant(candidate, selected, variants.make_program({}))
    old_bundle, _ = variants.prepare_plan(baseline, candidate, selected, 'base')
    assert asdict(bundle.plan) != asdict(old_bundle.plan)


@pytest.mark.parametrize('text,cell', [('mn', 'm:stem-entry'), ('mm', 'm:rise-entry')])
@pytest.mark.parametrize('advance', [-.05, 0, .05])
def test_subdivided_narrow_m_corner_retains_one_exact_event(candidate, text, cell, advance):
    selected = fixture(text)
    document = variants.compile_variant(candidate, selected, variants.make_program({cell: (.97, advance)}), 'subdivision')
    frozen = copy.deepcopy(document)
    bundle, timed = variants.prepare_plan(document, candidate, selected, 'subdivision')
    assert document == frozen
    assert bundle.plan == timed.plan
    metrics = variants.foundation.placement.evaluation.runtime.motion.desired_motion_metrics(bundle.plan)
    assert metrics['desired_discontinuities'] == 0
    assert metrics['desired_acceleration_mm_s2'] <= 250+1e-8
    assert metrics['desired_contact_speed_mm_s'] <= 12


def corner_samples(candidate):
    selected = fixture('mn')
    document = variants.compile_variant(candidate, selected, variants.make_program({'m:stem-entry': (.97, 0)}), 'subdivision')
    rows = [row for row in document['compiled']['strokes'] if row['letter'] == 0]
    contact = list(variants.gestures._arc_samples(rows, 3.5, .025, preserve_boundaries=True,
        include_curve_positions=True, connected_progress=True))
    anchor = next(index for index, (_, owner, _) in enumerate(contact)
        if owner['occurrence_id'] == '0:3' and owner['curve_position']['parameter'] == 0)
    return rows, contact, anchor


def test_corner_coalescing_preserves_exact_event_and_all_other_samples(candidate):
    rows, contact, anchor = corner_samples(candidate)
    frozen = copy.deepcopy(contact)
    assert 0 < math.dist(contact[anchor][0][:2], contact[anchor+1][0][:2]) < 1e-8
    repaired = variants.coalesce_corner_samples(contact, rows)
    assert repaired == contact[:anchor+1]+contact[anchor+2:]
    assert contact == frozen
    assert repaired[anchor][1]['boundary_contributors'] == contact[anchor][1]['boundary_contributors']
    assert {owner['occurrence_id'] for _, owner, _ in repaired} == {row['occurrence_id'] for row in rows}
    assert variants.coalesce_corner_samples(repaired, rows) == repaired


@pytest.mark.parametrize('change', ['distinct_distance', 'boundary', 'owner', 'cubic_endpoint', 'nonadjacent', 'missing_anchor'])
def test_corner_coalescing_does_not_hide_distinct_or_unproven_events(candidate, change):
    rows, contact, anchor = corner_samples(candidate)
    point, owner, progress = contact[anchor+1]
    if change == 'distinct_distance':
        contact[anchor+1] = ((point[0]+1e-9, *point[1:]), owner, progress)
    elif change == 'boundary':
        owner['boundary_contributors'] = copy.deepcopy(contact[anchor][1]['boundary_contributors'])
    elif change == 'owner':
        owner['occurrence_id'] = 'unrelated'
    elif change == 'cubic_endpoint':
        owner['curve_position']['parameter'] = 0
    elif change == 'nonadjacent':
        contact[anchor+1], contact[anchor+2] = contact[anchor+2], contact[anchor+1]
    else:
        contact.pop(anchor)
    assert variants.coalesce_corner_samples(contact, rows) == contact


def test_corner_coalescing_handles_incoming_roundoff_without_changing_boundary_owner(candidate):
    rows, contact, anchor = corner_samples(candidate)
    contact.pop(anchor+1)
    point, owner, progress = copy.deepcopy(contact[anchor-1])
    owner['curve_position']['parameter'] = 1-1e-14
    contact[anchor-1] = (contact[anchor][0], owner, progress)
    assert variants.coalesce_corner_samples(contact, rows) == contact[:anchor-1]+contact[anchor:]


def test_corner_coalescing_keeps_ambiguous_exact_boundaries_for_rejection(candidate):
    rows, contact, anchor = corner_samples(candidate)
    contact[anchor+1] = copy.deepcopy(contact[anchor])
    assert variants.coalesce_corner_samples(contact, rows) == contact


@pytest.mark.parametrize('change', ['scale', 'advance', 'nan', 'boolean', 'duplicate', 'word', 'candidate', 'extra'])
def test_program_bounds_and_schema_fail_closed(candidate, change):
    program = variants.make_program({'n:rise-entry': (1, 0)})
    row = program['rules'][0]
    if change in ('scale', 'nan', 'boolean'):
        row['width_scale'] = {'scale': 1.031, 'nan': float('nan'), 'boolean': True}[change]
    elif change == 'advance':
        row['advance_delta'] = .051
    elif change == 'duplicate':
        program['rules'].append(copy.deepcopy(row))
    elif change == 'word':
        row['word'] = 'nm'
    elif change == 'candidate':
        program['candidate_sha256'] = '0'*64
    else:
        program['fitting_authorized'] = True
    with pytest.raises(ValueError):
        variants.compile_variant(candidate, fixture('nm'), program)


@pytest.mark.parametrize('change', ['geometry', 'vertical', 'owner', 'anchor', 'port', 'hash', 'frame', 'permission'])
def test_independent_derivation_reader_rejects_forgery(candidate, change):
    selected = fixture('nm')
    document = variants.compile_variant(candidate, selected, variants.programs_for('nm')[0])
    occurrence = document['lineage']['occurrences'][0]
    if change in ('geometry', 'vertical'):
        document['compiled']['strokes'][0]['cubics'][0][1][0 if change == 'geometry' else 1] += .001
    elif change == 'owner':
        occurrence['source_owner']['span'] = [1, 2]
    elif change == 'anchor':
        occurrence['transform']['anchor_x'] += .01
    elif change == 'port':
        occurrence['derived_ports']['entry'][0] += .01
    elif change == 'hash':
        occurrence['canonical_primitive_sha256'] = '0'*64
    elif change == 'frame':
        document['frame_mm'][1] = 20
    else:
        document['lineage']['context_training_allowed'] = True
    with pytest.raises(ValueError):
        evidence.verify_document(document, candidate, selected, 'base')


def test_full_nib_envelope_and_frozen_windows_detect_old_mmm_crop(candidate):
    selected = fixture('mmm', 'development_triples')
    document = variants.compile_variant(candidate, selected, variants.make_program({}))
    bounds = evidence.envelope(document['compiled'])
    assert evidence.within(bounds, variants.CONTEXT_FRAME)
    assert not evidence.within(bounds, variants.OLD_FRAME)
    windows = evidence.local_windows([document])
    assert all(evidence.within(bounds, variants.CONTEXT_FRAME) for bounds in windows.values())


def test_sealed_triples_and_unfrozen_placements_are_not_opened(candidate):
    selected = fixture('nm')
    for text in ('num', 'mum', 'a', 'n m', ''):
        with pytest.raises(ValueError):
            variants.compile_variant(candidate, {**selected, 'text': text}, variants.make_program({}))
    with pytest.raises(ValueError):
        variants.compile_variant(candidate, {**selected, 'shift': [.5, 0]}, variants.make_program({}))


def test_inventory_and_timing_preflight_do_not_silently_expand_budget():
    plan = evidence.physical_inventory()
    assert plan['runs_per_process'] == 244
    assert plan['runs_per_seed_including_replay'] == 488
    assert plan['renders_per_seed_upper_bound'] == 1588
    assert plan['proposed_seconds_per_seed'] == 1800
    assert plan['recommended_seconds_per_seed'] == 2700
    assert plan['budget_feasible'] is plan['physical_execution_authorized'] is False
    with pytest.raises(ValueError):
        evidence.require_physical_execution(plan)
    with pytest.raises(ValueError):
        evidence.require_physical_execution({**plan, 'budget_feasible': True, 'physical_execution_authorized': True})


def test_readonly_snapshot_rejects_repinning_and_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence, 'summarize', lambda: {'geometry_frame_status': 'pass', 'context_training_allowed': False})
    directory = tmp_path/'snapshot'
    evidence.build(directory)
    checksum = digest(directory/'report.json')
    assert evidence.inspect(directory, checksum)['read_only'] is True
    with pytest.raises(ValueError):
        evidence.build(directory)
    with pytest.raises(ValueError):
        evidence.inspect(directory, None)
    report = json.loads((directory/'report.json').read_text())
    report['context_training_allowed'] = True
    (directory/'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError):
        evidence.inspect(directory, digest(directory/'report.json'))


def test_reduced_preflight_uses_real_geometry_and_never_executes(candidate, monkeypatch):
    selected = fixture('nm')
    monkeypatch.setattr(variants, 'fixtures', lambda: [selected])
    monkeypatch.setattr(evidence, 'load_inputs', lambda: (candidate, {'context_gaps': []}))
    def forbidden(*args, **kwargs):
        pytest.fail('Geometric preflight attempted physical execution or rendering')
    monkeypatch.setattr(variants.foundation.placement.evaluation.runtime, 'execute', forbidden)
    monkeypatch.setattr(variants.foundation.placement.evaluation, 'paint', forbidden)
    report = evidence.summarize()
    assert report['geometry_frame_status'] == report['desired_plan_status'] == 'pass'
    assert report['geometry_cases'] == 18 and report['desired_plan_cases'] == 36
    assert report['controller_executions'] == report['raster_renders'] == 0
    assert report['context_training_allowed'] is False


def test_preflight_retains_rejected_plans_without_dropping_cases(candidate, monkeypatch):
    selected = fixture('nm')
    monkeypatch.setattr(variants, 'fixtures', lambda: [selected])
    monkeypatch.setattr(evidence, 'load_inputs', lambda: (candidate, {'context_gaps': []}))
    def rejected(*args, **kwargs):
        raise ValueError('Exact unique corner port required')
    monkeypatch.setattr(variants, 'prepare_plan', rejected)
    report = evidence.summarize()
    assert report['geometry_frame_status'] == 'pass'
    assert report['desired_plan_status'] == 'fail'
    assert report['desired_plan_cases'] == len(report['planning']) == 36
    assert len(report['failures']) == 36
    assert all(row['reason'] == 'Exact unique corner port required' for row in report['failures'])
    assert report['controller_executions'] == 0


@pytest.fixture
def comparison_snapshot(tmp_path, monkeypatch, request):
    tmp_path = evidence.ROOT/'.pytest_cache'/tmp_path.name
    tmp_path.mkdir()
    request.addfinalizer(lambda: shutil.rmtree(tmp_path))
    source = evidence.BASE
    shutil.copytree(source/'snapshot-002', tmp_path/'snapshot-002')
    for archive in source.glob('failed-snapshot-002-*.py.txt'):
        shutil.copyfile(archive, tmp_path/archive.name)
    previous = json.loads((source/'snapshot-002/report.json').read_text())
    report = copy.deepcopy(previous)
    for row in report['planning']:
        if not row['desired_plan_pass']:
            row['desired_plan_pass'] = True
    report.update(failures=[], desired_plan_status='pass', physical_validation='not_run_budget_clearance_pending')
    monkeypatch.setattr(evidence, 'BASE', tmp_path)
    current = tmp_path/'current'
    current.mkdir()
    evidence.write_json(current/'freeze.json', evidence.freeze_record())
    report['artifacts'] = {'freeze.json': digest(current/'freeze.json')}
    evidence.write_json(current/'report.json', report)
    return current


def test_previous_comparison_checks_the_complete_frozen_inventory(comparison_snapshot):
    comparison = evidence.compare_previous(comparison_snapshot, digest(comparison_snapshot/'report.json'))
    assert comparison['geometry_cases_unchanged'] == 860
    assert comparison['previously_passing_timing_unchanged'] == 238
    assert comparison['exact_null_bundles_unchanged'] == 52
    assert len(comparison['repaired_cases']) == 6


@pytest.mark.parametrize('change', ['geometry', 'window', 'grid', 'threshold', 'timing', 'null', 'inventory',
    'failure', 'permission', 'archive', 'previous_report', 'pin'])
def test_previous_comparison_rejects_changes_even_with_a_new_report_pin(comparison_snapshot, change):
    current = comparison_snapshot
    report = json.loads((current/'report.json').read_text())
    if change == 'geometry':
        report['geometry'][0]['document_sha256'] = '0'*64
    elif change == 'window':
        report['local_windows_mm']['controls-n']['0'][0] -= .1
    elif change in ('grid', 'threshold'):
        freeze = json.loads((current/'freeze.json').read_text())
        if change == 'grid':
            freeze['widths'][0] = .96
        else:
            freeze['mechanical_criteria']['contact_speed_mm_s'] = 13
        evidence.write_json(current/'freeze.json', freeze)
        report['artifacts']['freeze.json'] = digest(current/'freeze.json')
    elif change in ('timing', 'null'):
        report['planning'][0]['timing_sha256' if change == 'timing' else 'bundle_sha256'] = '0'*64
    elif change == 'inventory':
        report['planning'].pop()
    elif change == 'failure':
        report['planning'][0]['desired_plan_pass'] = False
    elif change == 'permission':
        report['context_training_allowed'] = True
    elif change == 'archive':
        (evidence.BASE/'failed-snapshot-002-letter_context_variants.py.txt').write_text('changed')
    elif change == 'previous_report':
        (evidence.BASE/'snapshot-002/report.json').write_text('{}')
    evidence.write_json(current/'report.json', report)
    reasons = {'geometry': 'Changed geometry', 'window': 'Changed geometry',
        'grid': 'Changed repaired preflight identities', 'threshold': 'Changed repaired preflight identities',
        'timing': 'Previously passing desired timing changed', 'null': 'Null action bundle changed',
        'inventory': 'Changed desired-plan inventory', 'failure': 'Repaired desired preflight still fails',
        'permission': 'Changed geometry', 'archive': 'Changed archived failed',
        'previous_report': 'Changed failed preflight report', 'pin': 'External repaired preflight report pin required'}
    with pytest.raises(ValueError, match=reasons[change]):
        evidence.compare_previous(current, None if change == 'pin' else digest(current/'report.json'))

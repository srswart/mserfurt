"""Opt-in identity-only neighbor context; metadata never enters the frozen plan."""

import copy
from dataclasses import replace
import math

from scripts import current_foundation_readiness as foundation
from scribesim.evofit.stroke_gestures import compile_gestures
from scribesim.handflow.curve_tangents import retime_curve_tangents
from scribesim.handvalidate.specimen import object_digest
from scribesim.pathguide.gesture_actions import action_bundle


VERSION = 'letter-context-null-v1'
CANDIDATE_SHA256 = '96aced30b45e5ef09eb219643c4eb068a332fcdab3a3ae466ee5fe5aa7993ca3'
ENTRY_CLASSES = {'n': 'stem-entry', 'u': 'stem-entry', 'm': 'rise-entry'}
RULE_FIELDS = {'id', 'current_letter', 'following_entry_class', 'width_scale', 'advance_delta'}


def null_program(candidate, *, enabled=True):
    if object_digest(candidate) != CANDIDATE_SHA256 or type(enabled) is not bool:
        raise ValueError('Exact approved candidate and explicit null mode required')
    rules = [{'id': letter+':'+entry, 'current_letter': letter, 'following_entry_class': entry,
              'width_scale': 1.0, 'advance_delta': 0.0}
             for letter in sorted(ENTRY_CLASSES) for entry in sorted(set(ENTRY_CLASSES.values()))]
    return {'schema_version': VERSION, 'candidate_sha256': CANDIDATE_SHA256, 'rules': rules if enabled else []}


def validate_program(program):
    try:
        if (type(program) is not dict or set(program) != {'schema_version', 'candidate_sha256', 'rules'}
                or program['schema_version'] != VERSION or program['candidate_sha256'] != CANDIDATE_SHA256
                or type(program['rules']) is not list or len(program['rules']) > 6):
            raise ValueError('Unsupported context schema, candidate or rule inventory')
        rules, seen = [], set()
        for rule in program['rules']:
            if (type(rule) is not dict or set(rule) != RULE_FIELDS or rule['current_letter'] not in ENTRY_CLASSES
                    or rule['following_entry_class'] not in set(ENTRY_CLASSES.values())):
                raise ValueError('Only current-letter and following-entry selectors are supported')
            identifier = rule['current_letter']+':'+rule['following_entry_class']
            if rule['id'] != identifier or identifier in seen:
                raise ValueError('Duplicate or inconsistent shared rule ID')
            if any(type(rule[key]) not in (int, float) or not math.isfinite(rule[key]) or rule[key] != value
                   for key, value in [('width_scale', 1), ('advance_delta', 0)]):
                raise ValueError('Nonidentity transforms and spacing are not authorized by the null contract')
            seen.add(identifier)
            rules.append({**rule, 'width_scale': 1.0, 'advance_delta': 0.0})
        return {**program, 'rules': sorted(rules, key=lambda row: row['id'])}
    except (KeyError, TypeError) as error:
        raise ValueError('Malformed context program') from error


def fixture_model(candidate, fixture, refinement):
    if object_digest(candidate) != CANDIDATE_SHA256 or refinement not in foundation.placement.SPEC['refinements']:
        raise ValueError('Exact approved candidate and existing refinement required')
    model = foundation.placement.model_for_fixture(candidate, fixture)
    return foundation.placement.evaluation.subdivide(model) if refinement == 'subdivision' else model


def resolve_rule(program, current_letter, following_letter):
    program = validate_program(program)
    if current_letter not in ENTRY_CLASSES or following_letter not in (*ENTRY_CLASSES, None):
        raise ValueError('Unknown neighbor in null context')
    entry = ENTRY_CLASSES[following_letter] if following_letter is not None else None
    matches = [rule for rule in program['rules'] if rule['current_letter'] == current_letter
               and rule['following_entry_class'] == entry]
    return entry, matches[0]['id'] if matches else None


def compile_context(candidate, fixture, program, refinement):
    program = validate_program(program)
    model = fixture_model(candidate, fixture, refinement)
    compiled = compile_gestures(fixture['text'], model)
    occurrences = []
    for stroke in compiled['strokes']:
        offset = stroke['letter']
        following_letter = fixture['text'][offset+1] if offset+1 < len(fixture['text']) else None
        following, identifier = resolve_rule(program, stroke['recipe'], following_letter)
        occurrences.append({'owner': copy.deepcopy({key: value for key, value in stroke.items() if key != 'cubics'}),
            'canonical_primitive_sha256': object_digest(candidate['primitives'][stroke['primitive']]),
            'execution_primitive_sha256': object_digest(model['primitives'][stroke['primitive']]),
            'canonical_gesture_sha256': object_digest(candidate['gestures'][stroke['gesture']]),
            'canonical_action_sha256': object_digest(candidate['actions'][stroke['action_profile']]),
            'canonical_recipe_sha256': object_digest(candidate['recipes'][stroke['recipe']]),
            'placed_recipe_sha256': object_digest(model['recipes'][stroke['recipe']]),
            'following_entry_class': following, 'rule_id': identifier,
            'transform': {'kind': 'identity-short-circuit', 'width_scale': 1.0, 'advance_delta': 0.0},
            'source_geometry_sha256': object_digest(stroke['cubics']),
            'derived_geometry_sha256': object_digest(stroke['cubics'])})
    lineage = {'version': VERSION, 'canonical_candidate_sha256': CANDIDATE_SHA256,
        'execution_model_sha256': object_digest(model), 'fixture': copy.deepcopy(fixture), 'refinement': refinement,
        'geometry_derivation': 'exact-internal-subdivision' if refinement == 'subdivision' else 'canonical-geometry',
        'context_program_sha256': object_digest(program), 'compiled_sha256': object_digest(compiled),
        'occurrences': occurrences, 'context_training_allowed': False, 'execution_authorized': False,
        'nonidentity_authorized': False, 'S2_accepted': False, 'real_accepted': False}
    return {'version': VERSION, 'program': program, 'compiled': compiled, 'lineage': lineage}


def prepare_null_plan(document, candidate, fixture, refinement):
    from scripts.letter_context_evidence import verify_document
    model = verify_document(document, candidate, fixture, refinement)
    bundle = action_bundle(fixture['text'], model, step_mm=foundation.placement.SPEC['refinements'][refinement][0],
                           include_curve_positions=True)
    timed = retime_curve_tangents(bundle.plan, bundle.owners, document['compiled']['strokes'])
    return replace(bundle, plan=timed.plan, owners=[bundle.owners[index] for index in timed.source_indices]), timed

import inspect
import math

from PIL import Image
import pytest

from scripts import letter_context_dimension_evidence as corrected
from scripts import letter_context_physical_evidence as original
from scripts import letter_context_recovery_evidence as composite


def test_frozen_renderer_rounding_is_not_single_resolution_ceiling():
    frame = [-3, 30, 2, 13]
    assert corrected.renderer_size(frame, 900) == (1169, 390)
    assert (math.ceil(33*900/25.4), math.ceil(11*900/25.4)) == (1170, 390)
    assert corrected.renderer_size(frame, 180) == (234, 78)


@pytest.mark.parametrize('size', [(1168, 390), (1170, 390), (1169, 389), (234, 78)])
def test_presentation_rejects_crop_padding_and_wrong_resolution(tmp_path, size):
    file = tmp_path/'image.png'
    Image.new('RGB', size).save(file)
    with pytest.raises(ValueError, match='presentation frame'):
        corrected.verify_presentation(file, [-3, 30, 2, 13], 900)


def test_presentation_accepts_exact_renderer_size(tmp_path):
    file = tmp_path/'image.png'
    Image.new('RGB', (1169, 390)).save(file)
    corrected.verify_presentation(file, [-3, 30, 2, 13], 900)


def test_truncated_image_is_not_accepted_from_header_only(tmp_path):
    file = tmp_path/'image.png'
    Image.new('RGB', (1169, 390)).save(file)
    file.write_bytes(file.read_bytes()[:70])
    with pytest.raises(OSError):
        corrected.verify_presentation(file, [-3, 30, 2, 13], 900)


def test_renderer_pixel_budget_is_preserved():
    with pytest.raises(ValueError, match='pixel budget'):
        corrected.renderer_size([0, 1000, 0, 1000], 900)


def test_contract_preserves_failure_and_execution_scope():
    record = corrected.contract_record()
    assert record['previous_inspection_failure_sha256'] == corrected.BLOCKED_SHA256
    assert record['inspection_cases'] == 1464
    assert record['presentation_images'] == 324
    assert record['physical_executions_allowed'] == record['raster_renders_allowed'] == 0
    assert record['fitting_authorized'] is False
    assert record['context_training_allowed'] is False


def test_inspection_refuses_existing_output(tmp_path, monkeypatch):
    monkeypatch.setattr(corrected, 'OUTPUT', tmp_path)
    with pytest.raises(FileExistsError):
        corrected.inspect('not-a-pin')


def test_changed_preparation_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(corrected, 'PREPARED', tmp_path)
    (tmp_path/'contract.json').write_text('{}')
    with pytest.raises(ValueError, match='pin'):
        corrected.load_contract('0'*64)


@pytest.mark.parametrize('frame,dpi', [([0, 0, 0, 1], 900), ([0, 1, 1, 0], 900),
    ([0, float('nan'), 0, 1], 900), ([0, 1, 0, 1], 0), ([0, 1, 0, 1], float('inf'))])
def test_dimension_contract_rejects_invalid_frame(frame, dpi):
    with pytest.raises(ValueError):
        corrected.renderer_size(frame, dpi)


def test_worker_changes_only_the_presentation_check():
    before = inspect.getsource(original.verify_worker)
    old = """            frame = document['frame_mm']
            expected_size = (math.ceil((frame[1]-frame[0])*900/25.4), math.ceil((frame[3]-frame[2])*900/25.4))
            with Image.open(case_dir/'actual-full.png') as image:
                if image.size != expected_size:
                    raise ValueError('Incomplete presentation frame')"""
    new = """            verify_presentation(case_dir/'actual-full.png', document['frame_mm'], contract['presentation_dpi'])"""
    assert old in before
    assert inspect.getsource(corrected.verify_worker) == before.replace(old, new)


def test_composite_changes_only_worker_dispatch():
    before = inspect.getsource(composite.inspect)
    expected = before.replace('def inspect(', 'def inspect_composite(').replace(
        'record = reader.verify_worker(contract, worker_dir, seed)',
        'record = verify_worker(contract, worker_dir, seed)')
    assert inspect.getsource(corrected.inspect_composite) == expected


def test_inspection_guard_blocks_execution_and_restores_functions():
    execute = corrected.physical.execute_raw
    with corrected.read_only_guard():
        for function in (corrected.physical.execute_raw, corrected.reader.paint,
                         corrected.measurement.overlap_masks, corrected.physical.ActionController.follow_plan):
            with pytest.raises(RuntimeError, match='read-only'):
                function()
    assert corrected.physical.execute_raw is execute


def test_previous_failure_remains_reproducible_from_saved_image():
    contract = corrected.physical.load_contract(corrected.recovery.CONTRACT_SHA256)
    case = next(row for row in contract['cases'] if row['presentation'])
    file = corrected.recovery.ORIGINAL/'seed-7/first'/case['id']/'actual-full.png'
    document = corrected.physical.preflight.foundation.read_json(file.parent/'document.json')
    corrected.verify_presentation(file, document['frame_mm'], contract['presentation_dpi'])
    frame = document['frame_mm']
    with Image.open(file) as image:
        assert image.size != (math.ceil((frame[1]-frame[0])*900/25.4), math.ceil((frame[3]-frame[2])*900/25.4))

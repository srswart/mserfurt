"""Persistent repertoire session orchestration using the existing guided controller."""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
from dataclasses import asdict, replace
from pathlib import Path

from PIL import Image

from scribesim.evofit.repertoire import seed_repertoire
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.planning import build_track_plan
from scribesim.handvalidate.bridge import compare_bridge, decide_g2, neutral_profile, paint_trajectory
from scribesim.handvalidate.specimen import _artifact, digest, object_digest, write_json
from scribesim.pathguide.model import DensePathGuide, GuideSample
from scribesim.pathguide.repertoire import convert_word, load_bundle, require_g1


def require_g2(bridge_root, *, nominal_root, **g1_options):
    try:
        root = Path(bridge_root)
        freeze = json.loads((root / "freeze.json").read_text())
        report = json.loads((root / "report.json").read_text())
        if freeze["scope"] != "real-candidate" or report["freeze_sha256"] != object_digest(freeze):
            raise ValueError("Not an identity-bound real candidate bridge")
        if freeze.get("controller_controls") != asdict(RepertoireControls()):
            raise ValueError("G2 must validate the neutral repertoire execution mode")
        for relative, checksum in report["artifacts"].items():
            if digest(_artifact(root, relative)) != checksum:
                raise ValueError("Bridge artifact identity changed")
        hand, nominal = require_g1(nominal_root, **g1_options)
        if freeze["prerequisite"]["freeze_sha256"] != object_digest(nominal) or freeze["model_sha256"] != object_digest(hand):
            raise ValueError("Bridge nominal identity mismatch")
        if freeze["texts"] != [row["text"] for row in nominal["proofs"]]:
            raise ValueError("Bridge proof inventory changed")
        rows = []
        for index, text in enumerate(freeze["texts"]):
            bundle = load_bundle(root / f"guide-{index}.json")
            if asdict(bundle) != asdict(convert_word(text, hand)):
                raise ValueError("Bridge conversion/ownership mismatch")
            controls = RepertoireControls(**freeze["controller_controls"]) if freeze.get("controller_controls") is not None else None
            rows.append({"text": text, "metrics": compare_bridge(bundle, hand, controller_controls=controls)["metrics"]})
        if rows != report["rows"]:
            raise ValueError("Actual bridge measurements no longer replay")
        gate = decide_g2(rows, prerequisite=freeze["prerequisite"], scope=freeze["scope"], tolerances=freeze["tolerances"])
        if gate["status"] != "pass":
            raise ValueError(str(gate["reasons"]))
        return hand, freeze
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise ValueError(f"G2 prerequisite not passed: {error}") from error


class PersistentRepertoireSession:
    """Unaccepted low-level engine; run_execution enforces real candidate admission."""

    def __init__(self, hand, *, seed, controls=RepertoireControls(), session_id="diagnostic", dt=.002):
        if not isinstance(seed, int) or not session_id or not math.isfinite(dt) or not .0005 <= dt <= .01:
            raise ValueError("Explicit stable seed/session and bounded timestep required")
        self.hand = copy.deepcopy(hand)
        self.controls = controls
        self.seed = seed
        self.session_id = session_id
        self.identity = object_digest({"model": hand, "seed": seed, "session": session_id})
        self.phase = random.Random(int(self.identity, 16)).uniform(0, 2 * math.pi)
        self.profile = neutral_profile(hand)
        self.profile.fatigue_rate = .0002
        self.controller = GuidedHandFlowController(self.profile, repertoire_controls=controls)
        self.state = None
        self.dt = dt
        self.ownership = []
        self.frames = []
        self.requested_texts = []

    def write_plan(self, plan, owners=None):
        if not plan.samples:
            raise ValueError("Empty repertoire plan")
        if self.state is None:
            self.state = self.controller.initial_state(plan)
            self.state.session_identity = self.identity
            self.state.habit_phase = self.phase
        if self.controls.rhythm:
            samples = [plan.samples[0]]
            time = 0.0
            for previous, desired in zip(plan.samples, plan.samples[1:]):
                factor = 1 + self.controls.rhythm * math.sin((self.state.time_s + time) * .3 + self.phase)
                time += (desired.t_s - previous.t_s) / factor
                samples.append(replace(desired, t_s=time, speed_mm_s=desired.speed_mm_s * factor,
                                       vx_mm_s=desired.vx_mm_s * factor, vy_mm_s=desired.vy_mm_s * factor))
            plan = replace(plan, samples=tuple(samples))
        result = self.controller.follow_plan(plan, state=self.state, dt=self.dt, settle_time_s=0)
        for index in result.trajectory_plan_indices:
            self.ownership.append(copy.deepcopy(owners[index]) if owners else {"kind": "unattributed-diagnostic", "spans": []})
        return result

    def pause(self, seconds, *, kind="pause"):
        if self.state is None or not math.isfinite(seconds) or not 0 <= seconds <= 86400:
            raise ValueError("Pause requires state and a bounded duration")
        state = self.state
        before = state.time_s
        state.time_s += seconds
        state.rhythm_phase += self.profile.folio.base_tempo * seconds
        state.nib_contact = False
        state.nib_pressure = 0.0
        state.vel_x_mm_s = state.vel_y_mm_s = 0.0
        if kind == "sitting_break":
            state.fatigue *= math.exp(-seconds / 3600)
        state.events.append({"kind": kind, "time_before": before, "time_s": state.time_s,
                             "ink_before": state.ink_reservoir, "ink_after": state.ink_reservoir})

    def boundary(self, *, force_dip=False):
        if self.state is None:
            return
        state = self.state
        state.events.append({"kind": "word_boundary", "time_s": state.time_s,
                             "ink_before": state.ink_reservoir, "ink_after": state.ink_reservoir})
        if force_dip or self.controls.ink and state.ink_reservoir <= self.profile.ink.dry_threshold:
            before = state.ink_reservoir
            state.ink_reservoir = self.profile.ink.reservoir_capacity
            state.refilled_ink += state.ink_reservoir - before
            state.events.append({"kind": "dip", "time_s": state.time_s, "ink_before": before,
                                 "ink_after": state.ink_reservoir, "forced": force_dip})

    def _air_to(self, end, *, kind):
        if self.state is None:
            return
        start = self.state.pos_x_mm, self.state.pos_y_mm
        distance = math.dist(start, end)
        tangent = ((end[0] - start[0]) / distance, (end[1] - start[1]) / distance) if distance else (1.0, 0.0)
        count = max(2, math.ceil(distance / .1) + 1)
        if count > 100000:
            raise ValueError("Air travel exceeds sample budget")
        samples = tuple(GuideSample(start[0] + (end[0] - start[0]) * index / (count - 1),
                                    start[1] + (end[1] - start[1]) * index / (count - 1),
                                    tangent[0], tangent[1], contact=False, pressure_nominal=0, nib_angle_deg=self.hand["nib_angle_deg"])
                        for index in range(count))
        guide = DensePathGuide(kind, samples, max(.1, math.dist(start, end)), self.hand["x_height_mm"], kind="transition")
        self.state.events.append({"kind": kind, "time_s": self.state.time_s, "from_mm": list(start), "to_mm": list(end)})
        self.write_plan(build_track_plan(guide, base_speed_mm_s=18, stop_at_end=False), [{"kind": "air", "spans": []}] * count)

    def write_text(self, text):
        if not text or not text.strip() or any(character.isspace() and character not in " \n" for character in text):
            raise ValueError("Only explicit spaces and line returns are supported")
        self.requested_texts.append(text)
        logical_offset = 0
        for line_index, line in enumerate(text.split("\n")):
            cursor = 0.0
            for word in line.split(" "):
                if not word:
                    cursor += self.hand["space_advance"] * self.hand["x_height_mm"]
                    logical_offset += 1
                    continue
                bundle = convert_word(word, self.hand, baseline_y_mm=10 + line_index * 10)
                guide = replace(bundle.guide, samples=tuple(replace(sample, x_mm=sample.x_mm + cursor) for sample in bundle.guide.samples))
                frame = bundle.metadata["frame_mm"][:]
                frame[0] += cursor
                frame[1] += cursor
                self.frames.append(frame)
                self._air_to((guide.samples[0].x_mm, guide.samples[0].y_mm), kind="line_return" if cursor == 0 and line_index else "air_travel")
                self.boundary()
                owners = copy.deepcopy(bundle.metadata["owners"])
                for owner in owners:
                    owner["spans"] = [[start + logical_offset, end + logical_offset] for start, end in owner["spans"]]
                    owner["text_id"] = len(self.requested_texts) - 1
                self.write_plan(build_track_plan(guide, base_speed_mm_s=12, stop_at_end=False), owners)
                cursor += guide.x_advance_mm + self.hand["space_advance"] * self.hand["x_height_mm"]
                logical_offset += len(word) + 1

    def export(self):
        if self.state is None:
            raise ValueError("Session has not executed")
        state = asdict(self.state)
        trajectory = state.pop("trace")
        return {"schema_version": 1, "scope": "unaccepted-session-diagnostic", "model_sha256": object_digest(self.hand),
                "seed": self.seed, "session_id": self.session_id, "controls": asdict(self.controls), "dt": self.dt,
                "texts": self.requested_texts, "trajectory": trajectory, "state": state,
                "owners": self.ownership, "frames_mm": self.frames}


def run_execution(output, *, bridge_root=None, nominal_root=None, seed=7, controls=RepertoireControls(ink=True), **g1_options):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty execution directory")
    output.mkdir(parents=True, exist_ok=True)
    if bridge_root is not None:
        try:
            hand, freeze = require_g2(bridge_root, nominal_root=nominal_root, **g1_options)
        except ValueError as error:
            report = {"status": "blocked", "reasons": [str(error)], "executed": False, "promoted": False}
            write_json(output / "report.json", report)
            return report
        text = "\n".join(freeze["texts"])
    else:
        text = "in rein\ndeine hand\nsins in"
        hand = seed_repertoire(text.replace("\n", ""))
    session = PersistentRepertoireSession(hand, seed=seed, controls=controls)
    session.write_text(text)
    session.pause(2, kind="sitting_break")
    payload = session.export()
    write_json(output / "session.json", payload)
    frame = [min(row[0] for row in session.frames), max(row[1] for row in session.frames),
             min(row[2] for row in session.frames), max(row[3] for row in session.frames)]
    Image.fromarray(paint_trajectory(tuple(session.state.trace), frame)).save(output / "actual.png")
    report = {"status": "unaccepted-diagnostic", "executed": True, "promoted": False,
              "session_sha256": digest(output / "session.json"), "image_sha256": digest(output / "actual.png"),
              "contact_mm": session.state.contact_length_mm, "consumed_ink": session.state.consumed_ink,
              "refilled_ink": session.state.refilled_ink}
    write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bridge-root", type=Path)
    parser.add_argument("--nominal-root", type=Path)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--benchmark-root", type=Path)
    parser.add_argument("--target-review", type=Path)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_execution(args.output, bridge_root=args.bridge_root, nominal_root=args.nominal_root,
        dataset_root=args.dataset_root, benchmark_root=args.benchmark_root,
        target_review=json.loads(args.target_review.read_text()) if args.target_review else None,
        review=json.loads(args.review.read_text()) if args.review else None), indent=2))


if __name__ == "__main__":
    main()

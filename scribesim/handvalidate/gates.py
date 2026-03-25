"""Gate config loading and evaluation for TD-014."""

from __future__ import annotations

import math
import tomllib
from pathlib import Path

from scribesim.pathguide import DensePathGuide

from .metrics import dataset_admission_metrics
from .model import (
    DatasetPolicy,
    DatasetPolicyDecision,
    GateDecision,
    GateFailure,
    GateRule,
    StageGate,
)


DEFAULT_GATES_PATH = Path("shared/hands/validation/gates.toml")
DEFAULT_DATASET_POLICY_PATH = Path("shared/hands/validation/dataset_policy.toml")
_OPS = {"<=", ">=", "==", "<", ">"}


def load_gate_config(path: Path | str = DEFAULT_GATES_PATH) -> dict[str, StageGate]:
    raw = tomllib.loads(Path(path).read_text())
    stages: dict[str, StageGate] = {}
    for stage, payload in raw.get("stages", {}).items():
        rules: list[GateRule] = []
        for metric, rule in payload.get("metrics", {}).items():
            op = str(rule["op"])
            if op not in _OPS:
                raise ValueError(f"unsupported gate operator for {stage}.{metric}: {op}")
            rules.append(
                GateRule(
                    metric=metric,
                    op=op,
                    threshold=float(rule["threshold"]),
                    required=bool(rule.get("required", True)),
                    description=rule.get("description"),
                )
            )
        stages[stage] = StageGate(
            stage=stage,
            label=str(payload.get("label", stage.replace("_", " ").title())),
            rules=tuple(rules),
        )
    return stages


def load_dataset_policy(path: Path | str = DEFAULT_DATASET_POLICY_PATH) -> dict[str, DatasetPolicy]:
    raw = tomllib.loads(Path(path).read_text())
    policies: dict[str, DatasetPolicy] = {}
    for name, payload in raw.get("policies", {}).items():
        policies[name] = DatasetPolicy(
            name=name,
            allowed_confidence_tiers=tuple(payload.get("allowed_confidence_tiers", [])),
            require_provenance=bool(payload.get("require_provenance", True)),
            require_resolution_metadata=bool(payload.get("require_resolution_metadata", True)),
            min_heldout_symbol_coverage=float(payload.get("min_heldout_symbol_coverage", 0.0)),
        )
    return policies


def _compare(actual: float, op: str, threshold: float) -> bool:
    if op == "<=":
        return actual <= threshold + 1e-9
    if op == ">=":
        return actual >= threshold - 1e-9
    if op == "==":
        return math.isclose(actual, threshold, abs_tol=1e-9)
    if op == "<":
        return actual < threshold
    if op == ">":
        return actual > threshold
    raise ValueError(f"unsupported op: {op}")


def evaluate_gate(
    stage: str,
    metrics: dict[str, float],
    *,
    gate_config: dict[str, StageGate] | None = None,
) -> GateDecision:
    gate_config = gate_config or load_gate_config()
    if stage not in gate_config:
        raise KeyError(f"unknown stage gate: {stage}")

    failures: list[GateFailure] = []
    advisories: list[str] = []
    for rule in gate_config[stage].rules:
        actual = metrics.get(rule.metric)
        if actual is None:
            failure = GateFailure(
                metric=rule.metric,
                reason=f"missing metric: {rule.metric}",
                required=rule.required,
            )
            if rule.required:
                failures.append(failure)
            else:
                advisories.append(failure.reason)
            continue
        if not _compare(float(actual), rule.op, rule.threshold):
            failure = GateFailure(
                metric=rule.metric,
                actual=float(actual),
                op=rule.op,
                threshold=rule.threshold,
                required=rule.required,
                reason=(
                    f"{rule.metric}={float(actual):.4f} does not satisfy "
                    f"{rule.op} {rule.threshold:.4f}"
                ),
            )
            if rule.required:
                failures.append(failure)
            else:
                advisories.append(failure.reason)

    return GateDecision(
        stage=stage,
        passed=not failures,
        failures=tuple(failures),
        advisories=tuple(advisories),
    )


def evaluate_dataset_policy(
    guides: list[DensePathGuide],
    *,
    policy_name: str = "promotion",
    policies: dict[str, DatasetPolicy] | None = None,
) -> DatasetPolicyDecision:
    policies = policies or load_dataset_policy()
    if policy_name not in policies:
        raise KeyError(f"unknown dataset policy: {policy_name}")

    policy = policies[policy_name]
    reasons: list[str] = []
    admission = dataset_admission_metrics(guides)

    for guide in guides:
        if policy.require_provenance and not guide.sources:
            reasons.append(f"{guide.symbol} has no provenance sources")
        for source in guide.sources:
            if source.confidence_tier not in policy.allowed_confidence_tiers:
                reasons.append(
                    f"{guide.symbol}:{source.source_id} tier {source.confidence_tier} "
                    f"not allowed by {policy.name}"
                )
            if policy.require_resolution_metadata and source.source_resolution_ppmm is None:
                reasons.append(f"{guide.symbol}:{source.source_id} missing source resolution")

    if admission["heldout_symbol_coverage"] < policy.min_heldout_symbol_coverage:
        reasons.append(
            f"heldout_symbol_coverage={admission['heldout_symbol_coverage']:.4f} below "
            f"{policy.min_heldout_symbol_coverage:.4f}"
        )

    return DatasetPolicyDecision(name=policy_name, passed=not reasons, reasons=tuple(reasons))

---
description: "Orchestrate ScribeHand Mac workflow (agent runs all steps except human review)"
---

# ScribeHand Orchestrate (TD-018)

Run the GPU-side ScribeHand pipeline on a Mac workstation. The agent executes
every automated step; **human visual review (step 8) is the only hard stop**.

## Prerequisites

- Mac with MPS (`torch.backends.mps.is_available()`)
- Repo checked out; branch with pass-14 implementation
- Read [`docs/scribehand-mac-runbook-agent.md`](../docs/scribehand-mac-runbook-agent.md)

## Instructions

1. **Initialize environment file**

```bash
cp docs/scribehand-orchestration.env.example diagnostics/scribehand.env
# Edit diagnostics/scribehand.env — fill ONEDM_ROOT, ANCHOR_DIR, etc.
```

2. **Check pipeline status**

```bash
uv sync --extra scribehand
uv run python scripts/scribehand/orchestrate.py status --json
uv run python scripts/scribehand/orchestrate.py env-check --json
```

3. **Orchestration loop** — repeat until `human_required: true`:

```bash
# Next step
uv run python scripts/scribehand/orchestrate.py next --json

# Run the returned commands (from next.commands)
# ...

# Validate artifacts
uv run python scripts/scribehand/orchestrate.py validate <step_id> --json

# Record success
uv run python scripts/scribehand/orchestrate.py record <step_id> --status passed
```

4. **Human gate (step_8_human_review)**

When `next` returns `"human_required": true`:

- STOP automated execution
- Tell the human to review bundles per [human runbook §8](../docs/scribehand-mac-runbook.md#8-guided-human-evaluation-your-eyes)
- They must write `human_review.md` in each diagnostic directory (see agent runbook for format)
- Resume only after `validate step_8_human_review` returns `"ok": true`

5. **Promotion (step_9)**

After human review passes, complete step_9 and update ADV-SS-HANDVALIDATE-007.

## Manifest

Full step definitions: [`docs/scribehand-orchestration.yaml`](../docs/scribehand-orchestration.yaml)

Human-oriented companion: [`docs/scribehand-mac-runbook.md`](../docs/scribehand-mac-runbook.md)

## Expected agent behavior

- Never skip or auto-pass human review
- Commit/share `diagnostics/*.zip` after each backend pack step
- On failure, read manifest `on_failure` / troubleshooting and retry the same step
- Record every passed step in state file for resume across sessions

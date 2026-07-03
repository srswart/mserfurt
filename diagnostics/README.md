# diagnostics/ — TD-018 run bundles

Diagnostic bundles from Mac-side ScribeHand runs live here so they can be
committed and evaluated cloud-side (TD-018 feedback loop).

- Produce a directory per run: `--neural-diag-dir diagnostics/<run>` or
  `bench-neural --out-dir diagnostics/<run>`
- Pack it: `scribesim diag-pack diagnostics/<run> --out diagnostics/<run>.zip`
  (size-capped; word crops are sampled)
- Commit the `.zip` (and optionally the raw `metrics.json` / `run.json`) on a
  branch and push — the cloud agent reads bundles with
  `scribesim.scribehand.diagnostics.summarize_bundle`.

Keep raw run directories out of git if they get large; the packed zip is the
shareable artifact.

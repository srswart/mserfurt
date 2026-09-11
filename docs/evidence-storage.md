# ScribeSim evidence storage

## Git versus external backup

Keep source code, tests, templates, designs, ARRIVE advances and component
metadata in Git. Within `shared/training/konrad_hand_recovery/`, also keep
candidate definitions, contracts, targets, approvals, owner feedback, reports,
manifests, freeze records and Markdown review/recovery instructions. These bind
decisions to evidence without committing the bulk of the physical runs.

Ignore compressed JSON evidence, generated `document.json`/`documents.json`,
per-attempt `measurement.json`/`attempt.json`, PNG/SVG/HTML renders, temporary
`.preview` directories and `worker.log` files in that evidence tree. These are
external-backup artifacts, not disposable files. The rules do not apply to
source/templates elsewhere in the repository or hide all JSON indiscriminately.

The owner manages backup. No archive, backup verification or deletion is implied
by these ignore rules. Back up the full evidence tree, including failed and
partial runs, with its original relative paths and bytes. Existing manifests
and pinned hashes remain authoritative; do not regenerate or refit candidates
as a substitute for restoring saved evidence.

## Local use and restoration

Local files remain in place, so existing scripts and review links continue to
work. A fresh checkout does not include ignored evidence: restore the backed-up
tree at its original repository-relative path before opening samples or running
saved-evidence checks. Verify relevant manifest/hash bindings before using it.
Missing evidence is not a validation pass. Do not run `git clean -fdx` against
the working evidence tree without a verified backup.

`.gitignore` affects untracked files only. Previously tracked evidence stays
tracked and Git history is unchanged. Removing already-tracked artifacts from
the index or rewriting history is a separate migration, not part of this change.

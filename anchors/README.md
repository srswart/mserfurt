# Anchor tier (bootstrap)

Assembled automatically by `scripts/scribehand/assemble_anchor_dir.py` from
existing TD-008 reference extractions:

| Source | Crops | Transcription | Known pairs |
|--------|-------|---------------|-------------|
| `reference/fullres_words` | 230 | `reference/transcription.txt` | 173 |
| `reference/47v_words` | 289 | `reference/47v_transcription.txt` | 205 |

**Total ingested:** 378 reviewed word pairs (≥300 gate).

## Layout

```
anchors/
  labels.tsv       # images/<file>.png<TAB>text<TAB>writer
  images/          # copied word crop PNGs
  assemble_summary.json
```

## Replacing with production anchor data

When the TD-014 workbench freeze is ready (`shared/training/scribehand/anchor_v1`):

1. Harvest Cgm 628 pages → `extract-lines` → `extract-words` → `transcribe-words`
2. Review transcriptions in the workbench
3. Re-run assemble (or hand-build `labels.tsv`) with 300–1,000 pairs
4. Re-ingest: `uv run scribesim build-scribehand-corpus --anchor-dir anchors`

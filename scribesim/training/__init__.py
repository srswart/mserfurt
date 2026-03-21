"""Training pipeline for the hand simulator (TD-003-A §3, TD-005).

Incremental training workflow:
  1. extract_word — crop a word from a manuscript image
  2. train — fit hand dynamics on a single word with CMA-ES
  3. train_extend — extend to longer text with quality gates
  4. train_folio — full folio with line checkpoints and revert
"""

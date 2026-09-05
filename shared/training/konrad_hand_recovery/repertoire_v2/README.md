# Repertoire v2 implementation evidence

These are unaccepted catalog/allograph priors and a synthetic alternative-topology
fixture, not manuscript recovery or a G1 submission. The loop fixture intentionally
does not claim that its drawing is a valid historical i.

`ownership.json` records exact spans, shared form identities, contact ownership,
air transitions and content-addressed render keys for seven new combinations.
`alternative_topology.json` declares an independent loop with the same logical
symbol as the open catalog form. PNG panels use a common physical x-height scale.

Replay a seed with:

```sh
python -m scribesim.evofit.repertoire --model shared/training/konrad_hand_recovery/repertoire_v2/seed.json --text rein --dpi 180 --output /tmp/rein-v2.png
```

The module refuses overwrites. All models remain opt-in. No production backend,
ink state, handwriting controller or default asset is changed.

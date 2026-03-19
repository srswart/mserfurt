# Tech Direction: TD-001 — Interface Contracts

## Status
**Active** — all three systems must conform to these contracts.

## Context
The MS Erfurt pipeline has three systems (XL → ScribeSim → Weather) that communicate through files. This tech direction defines the schemas and conventions for those files. Any change to these contracts requires updating this document first and then propagating to all affected systems.

## Decision summary

| ID | Decision | Scope |
|---|---|---|
| TD-001-A | Folio JSON is the primary data contract between XL and ScribeSim | XL → ScribeSim |
| TD-001-B | Manifest JSON carries per-folio metadata for all downstream phases | XL → ScribeSim, Weather |
| TD-001-C | PAGE XML (2019 schema) is the eScriptorium integration format | All systems |
| TD-001-D | Hand parameter TOML defines the scribal hand model | ScribeSim |
| TD-001-E | Weathering profile TOML defines aging effects | Weather |
| TD-001-F | Pressure heatmap PNG is the contract between ScribeSim and Weather | ScribeSim → Weather |
| TD-001-G | All filenames use the folio ID convention defined below | All systems |

---

## TD-001-A: Folio JSON

The primary output of XL and primary input of ScribeSim. One file per folio.

### Filename convention
`{folio_id}.json` — e.g. `f01r.json`, `f04v.json`, `f14r.json`

### Folio ID convention
- Format: `f{NN}{r|v}` where NN is zero-padded folio number, r = recto, v = verso
- Range for MS Erfurt: `f01r` through `f17v` (34 possible pages across 17 folios)
- Not all pages may contain text (some may be blank verso pages)

### Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Folio",
  "type": "object",
  "required": ["id", "recto_verso", "gathering_position", "lines", "metadata"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^f\\d{2}[rv]$",
      "description": "Folio ID, e.g. f04r"
    },
    "recto_verso": {
      "type": "string",
      "enum": ["recto", "verso"]
    },
    "gathering_position": {
      "type": "integer",
      "minimum": 1,
      "maximum": 17,
      "description": "Position in the 17-folio gathering"
    },
    "lines": {
      "type": "array",
      "items": { "$ref": "#/$defs/Line" },
      "minItems": 0,
      "description": "Ordered lines of text on this page"
    },
    "damage": {
      "oneOf": [
        { "$ref": "#/$defs/Damage" },
        { "type": "null" }
      ],
      "description": "Physical damage to this folio, from CLIO-7 apparatus"
    },
    "hand_notes": {
      "oneOf": [
        { "$ref": "#/$defs/HandNotes" },
        { "type": "null" }
      ],
      "description": "CLIO-7 observations about the scribal hand on this folio"
    },
    "section_breaks": {
      "type": "array",
      "items": { "type": "integer" },
      "description": "Line numbers where section dividers (✦ ✦ ✦) occur"
    },
    "vellum_stock": {
      "type": "string",
      "enum": ["standard", "irregular"],
      "default": "standard",
      "description": "standard = f01-f13; irregular = f14-f17 (different stock per CLIO-7)"
    },
    "metadata": { "$ref": "#/$defs/FolioMetadata" }
  },

  "$defs": {
    "Line": {
      "type": "object",
      "required": ["number", "text", "register"],
      "properties": {
        "number": {
          "type": "integer",
          "minimum": 1
        },
        "text": {
          "type": "string",
          "description": "The line text in period German/Latin as Konrad wrote it"
        },
        "register": {
          "type": "string",
          "enum": ["de", "la", "mhg", "mixed"],
          "description": "Language register: de=Frühneuhochdeutsch, la=Ecclesiastical Latin, mhg=Middle High German (Eckhart quotes), mixed=hybrid"
        },
        "english": {
          "type": "string",
          "description": "Original English text (for reference/debugging, not for rendering)"
        },
        "annotations": {
          "type": "array",
          "items": { "$ref": "#/$defs/Annotation" },
          "default": []
        }
      }
    },

    "Annotation": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["lacuna", "confidence", "verbatim_source", "strikethrough", "emphasis"]
        },
        "span": { "$ref": "#/$defs/Span" },
        "detail": {
          "type": "object",
          "description": "Type-specific details",
          "additionalProperties": true
        }
      }
    },

    "Span": {
      "type": "object",
      "required": ["char_start", "char_end"],
      "properties": {
        "char_start": { "type": "integer", "minimum": 0 },
        "char_end": { "type": "integer", "minimum": 0 }
      }
    },

    "Damage": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["water", "missing_corner", "moisture", "age"]
        },
        "affected_lines": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "from": { "type": "integer" },
              "to": { "type": "integer" }
            }
          }
        },
        "extent": {
          "type": "string",
          "enum": ["partial", "severe", "total"]
        },
        "direction": {
          "type": "string",
          "description": "For water damage: direction of exposure, e.g. 'from_above'"
        },
        "corner": {
          "type": "string",
          "enum": ["top_left", "top_right", "bottom_left", "bottom_right"],
          "description": "For missing_corner damage type"
        },
        "notes": {
          "type": "string",
          "description": "CLIO-7's description of the damage"
        }
      }
    },

    "HandNotes": {
      "type": "object",
      "properties": {
        "pressure": {
          "type": "string",
          "enum": ["normal", "increased_lateral", "lighter", "variable"],
          "default": "normal"
        },
        "spacing": {
          "type": "string",
          "enum": ["standard", "wider", "compressed"],
          "default": "standard"
        },
        "ink_density": {
          "type": "string",
          "enum": ["consistent", "variable_multi_sitting", "fresh"],
          "default": "consistent"
        },
        "speed": {
          "type": "string",
          "enum": ["deliberate", "rapid", "compensating"],
          "default": "deliberate"
        },
        "scale": {
          "type": "string",
          "enum": ["standard", "smaller_economical"],
          "default": "standard",
          "description": "f07v lower half uses smaller hand"
        },
        "apply_from_line": {
          "type": ["integer", "null"],
          "description": "If set, hand notes apply only from this line onward (e.g. f07v lower half)"
        },
        "notes": {
          "type": "string",
          "description": "CLIO-7's full description"
        }
      }
    },

    "FolioMetadata": {
      "type": "object",
      "required": ["line_count"],
      "properties": {
        "line_count": { "type": "integer" },
        "text_density_chars_per_line": { "type": "number" },
        "register_ratio": {
          "type": "object",
          "properties": {
            "de": { "type": "number" },
            "la": { "type": "number" },
            "mhg": { "type": "number" },
            "mixed": { "type": "number" }
          }
        }
      }
    }
  }
}
```

---

## TD-001-B: Manifest JSON

A single file summarizing all folios. Produced by XL, consumed by ScribeSim (for batch rendering) and Weather (for per-folio damage dispatch).

### Filename
`manifest.json`

### Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Manifest",
  "type": "object",
  "required": ["manuscript", "folios"],
  "properties": {
    "manuscript": {
      "type": "object",
      "required": ["shelfmark", "author", "date", "folio_count"],
      "properties": {
        "shelfmark": { "type": "string" },
        "author": { "type": "string" },
        "date": { "type": "integer" },
        "folio_count": { "type": "integer" },
        "language_primary": { "type": "string" },
        "language_secondary": { "type": "string" }
      }
    },
    "folios": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "file"],
        "properties": {
          "id": { "type": "string", "pattern": "^f\\d{2}[rv]$" },
          "file": { "type": "string", "description": "Relative path to folio JSON" },
          "line_count": { "type": "integer" },
          "damage_type": { "type": ["string", "null"] },
          "damage_extent": { "type": ["string", "null"] },
          "hand_pressure": { "type": "string", "default": "normal" },
          "hand_spacing": { "type": "string", "default": "standard" },
          "hand_ink": { "type": "string", "default": "consistent" },
          "hand_speed": { "type": "string", "default": "deliberate" },
          "hand_scale": { "type": "string", "default": "standard" },
          "vellum_stock": { "type": "string", "default": "standard" },
          "register_dominant": { "type": "string" },
          "has_section_break": { "type": "boolean", "default": false }
        }
      }
    },
    "gaps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "after_folio": { "type": "string" },
          "estimated_missing": { "type": "string", "description": "e.g. '1-3 folios'" },
          "notes": { "type": "string" }
        }
      },
      "description": "Known gaps in the gathering (CLIO-7: 1-3 folios missing between f05v and f06r)"
    }
  }
}
```

---

## TD-001-C: PAGE XML conventions

All three systems produce or consume PAGE XML (2019 schema). These conventions ensure interoperability with eScriptorium and Kraken.

### Schema version
PAGE XML 2019 — validate against `https://www.primaresearch.org/schema/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd`

### XL output (text only, no coordinates)
- One `<Page>` per folio
- `imageFilename` left empty (no image at this stage)
- Text in `<TextRegion>` → `<TextLine>` → `<TextEquiv>`
- Primary `<TextEquiv>` (index 0): German/Latin text
- Secondary `<TextEquiv>` (index 1): English original (for reference)
- Custom attribute on `<TextLine>`: `@custom="register:{de|la|mhg|mixed}"`
- Coordinates: placeholder normalized grid (0,0 to 1000,1000) — ScribeSim resolves to actual pixel coordinates

### ScribeSim output (text + coordinates)
- `imageFilename` points to the rendered PNG
- Full hierarchy: `Page > TextRegion > TextLine > Word > Glyph`
- `<Baseline>` elements on each `<TextLine>` (Kraken-compatible polyline)
- `<Coords>` on all elements as pixel-coordinate polygons
- `<TextEquiv>` at `Glyph` level: single Unicode character
- Custom attribute on `<TextLine>`: `@custom="register:{de|la|mhg|mixed}"`

### Weather output (updated coordinates + damage)
- Same structure as ScribeSim, with coordinates adjusted for geometric distortion
- Glyphs in damaged zones receive: `@custom="damaged:true;legibility:{0.0-1.0}"`
- `imageFilename` updated to point to weathered PNG

---

## TD-001-D: Hand parameter TOML

Defines Brother Konrad's scribal hand. Consumed by ScribeSim.

### Location
`shared/hands/konrad_erfurt_1457.toml`

### Required sections
```
[identity]     — name, script_family, period, region
[nib]          — angle_degrees, width_min, width_max
[letterform]   — slant_degrees, x_height, ascender_ratio, descender_ratio
[spacing]      — letter_spacing_mean/stddev, word_spacing_mean/stddev
[pressure]     — attack_duration, sustain_level, release_duration, downstroke_multiplier
[ink]          — flow_initial, flow_decay_rate, dip_cycle_strokes
[fatigue]      — enabled, onset_line, spacing_drift, tremor_amplitude
```

### Per-folio overrides
`shared/hands/folio_overrides.toml` — keyed by folio ID, specifies modifier stack per folio derived from CLIO-7 hand notes. See ScribeSim solution intent for full modifier specification.

---

## TD-001-E: Weathering profile TOML

Defines aging effects. Consumed by Weather.

### Location
`shared/profiles/ms-erfurt-560yr.toml`

### Required sections
```
[meta]                    — name, description, seed, target_manuscript
[substrate.vellum_*]      — texture, color (two stocks), translucency
[ink.*]                   — fade, bleed, flake
[damage.water_damage]     — direction, penetration, tide_line, ink_dissolution
[damage.missing_corner]   — corner, tear_depth, irregularity, backing_color
[aging.*]                 — edge_darkening, foxing, binding_shadow
[optics.*]                — page_curl, camera_vignette, lighting_gradient
```

Per-folio damage dispatch is driven by the manifest (TD-001-B), not by the weathering profile. The profile defines effect parameters; the manifest determines which folios receive which effects.

---

## TD-001-F: Pressure heatmap PNG

Produced by ScribeSim, consumed by Weather for ink degradation targeting (heavy strokes flake first).

### Convention
- Filename: `{folio_id}_pressure.png` (e.g. `f07r_pressure.png`)
- Format: grayscale PNG, same pixel dimensions as the page image
- Pixel intensity: 0 = no ink, 255 = maximum pen pressure
- Bit depth: 8-bit grayscale

---

## TD-001-G: Folio ID convention (global)

All systems use the same folio ID format everywhere:

| Pattern | Example | Meaning |
|---|---|---|
| `f{NN}{r\|v}` | `f04v` | Folio 4, verso |
| Zero-padded | `f01r` not `f1r` | Always two digits |
| Range | `f01r`–`f17v` | 17 folios in the gathering |

Filenames derived from folio ID:
- Folio JSON: `{id}.json` → `f04v.json`
- Page image: `{id}.png` → `f04v.png`
- Pressure heatmap: `{id}_pressure.png` → `f04v_pressure.png`
- PAGE XML: `{id}.xml` → `f04v.xml`
- Weathered image: `{id}_weathered.png` → `f04v_weathered.png`
- Weathered PAGE XML: `{id}_weathered.xml` → `f04v_weathered.xml`

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-19 | Initial draft — all contracts | shawn + claude |

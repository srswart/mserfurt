---
advance:
  id: ADV-SS-MCONN-001
  title: M_conn Metric — Connection Quality Measurement
  system: scribesim
  primary_component: metrics
  components:
  - metrics
  started_at: 2026-03-20T22:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:16:24.142423Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Implement TD-004 Part 2. Add M_conn (M10) to the metric suite measuring inter-letter connection quality: presence ratio, width distribution, angle distribution, and continuity at junction points. Compare against target manuscript connections.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Implement word segmentation (whitespace detection on rendered image)
- [ ] Implement thick-vertical detection within words (major strokes)
- [ ] Implement connection zone analysis (ink presence, width, angle between verticals)
- [ ] Implement m_conn_score combining presence (30%), width (40%), angle (30%)
- [ ] Add M_conn as M10 to the metric suite alongside M1-M9
- [ ] Update composite_score to include M_conn
- [ ] Test: connected words score better than disconnected

## Risk + Rollback

New dependency risk for image analysis. M_conn is additive to existing metric suite — rollback by removing M10 from composite score.

## Evidence

- [ ] tdd:red-green — write metric tests with known-good and known-bad connection images before implementation
- [ ] tests:unit — unit tests for segmentation, detection, scoring components

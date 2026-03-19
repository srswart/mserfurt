# /arrive-implement — Start or Complete an Advance Implementation

Manages the full lifecycle of implementing an advance: claiming it in the plan, tracking work in progress, generating a sub-plan for complex advances, and marking completion.

## Usage

`/arrive-implement <subcommand> <ADV-ID>`

### Subcommands

- `start <ADV-ID>` — Claim the advance, mark it `in_progress`, set `started_at`, generate a sub-plan if complex
- `done <ADV-ID>` — Mark implementation complete, update status and timestamp, release the plan item

---

## Subcommand: `start <ADV-ID>`

Begin work on an advance.

### Instructions

1. **Locate the advance file** by searching across all system advance directories:
   - `arrive/systems/xl/advances/<ADV-ID>.md`
   - `arrive/systems/scribesim/advances/<ADV-ID>.md`
   - `arrive/systems/weather/advances/<ADV-ID>.md`

2. **Read the advance file** to understand its current state, components, and complexity.

3. **Check preconditions**:
   - If `status` is already `in_progress`, warn that it's already started and show `started_at`. Ask if you should proceed anyway.
   - If `status` is `complete`, warn and stop — use `/arrive-implement done` only when finished.
   - If `status` is `planned`, proceed normally.

4. **Claim the plan item**:
   ```
   arrive plan start <ADV-ID>
   ```
   This sets the item `in_progress` and claims a lease.

5. **Set active work context**:
   ```
   arrive work set --advance <ADV-ID> --system <system> --component <primary_component> --phase implement
   ```

6. **Update the advance frontmatter**:
   - Set `status: in_progress`
   - Set `started_at` to the current ISO timestamp (e.g., `"2026-03-19T10:00:00Z"`)

7. **Assess complexity** — an advance is complex if it has any of:
   - More than 3 distinct implementation tasks
   - Involves a new dependency (`risk_flags` includes `new_dependency`)
   - Involves cross-system interface contracts (any `contracts:` references in its component's YAML)
   - Is a rendering, parsing, or algorithmic component (translate, render, layout, register, folio, damage, compositor)

8. **For complex advances**, generate a detailed sub-implementation plan inline in the advance file under a `## Implementation Sub-Plan` section. Follow ARRIVE's Tidy → Test → Implement discipline:

```markdown
## Implementation Sub-Plan

### Tidy (Preparatory Refactors)
- [ ] <What to reorganize/rename/move before writing new code>
- [ ] <Any interface cleanup needed>

### Tests First (Red Phase)
- [ ] Write unit test: <describe what the test checks>
- [ ] Write integration test: <describe boundary contract test>
- [ ] Confirm tests fail (red)

### Implement (Green Phase)
- [ ] <Implementation step 1>
- [ ] <Implementation step 2>
- [ ] <Implementation step 3>

### Validate
- [ ] Run test suite — all green
- [ ] Validate against TD-001-<X> contract: `arrive plan check`
- [ ] Update evidence in advance frontmatter
```

   For **simple advances** (no complexity flags), skip the sub-plan and just note "Implementation tasks in Planned Implementation Tasks section above."

9. **Output a brief status report**:
```
Started: <ADV-ID>
System: <system>
Component: <component>
Complexity: [simple|complex]
Plan item: claimed (lease active)
Work context: set

Next step: <first task from the sub-plan or Planned Implementation Tasks>
```

---

## Subcommand: `done <ADV-ID>`

Mark an advance implementation complete.

### Instructions

1. **Locate and read the advance file** (same search as `start`).

2. **Check preconditions**:
   - If `status` is `planned` (never started), warn and stop.
   - If `status` is `complete`, note it's already done.
   - If `status` is `in_progress`, proceed.

3. **Review evidence** — check the advance's `evidence:` list. For each evidence type, confirm the work is present:
   - `tdd:red-green` → tests were written before implementation
   - `tidy:preparatory` → any preparatory tidying was done
   - `tests:unit` → unit tests exist and pass
   - `tests:integration` → integration tests exist and pass (if listed)

   If sub-plan tasks exist under `## Implementation Sub-Plan`, verify they are all checked off (`[x]`). If any are unchecked, list them and ask: "These tasks appear incomplete. Mark done anyway?"

4. **Mark implementation complete** via CLI:
   ```
   arrive advance mark-implementation-complete <ADV-ID>
   ```

5. **Update plan item status**:
   ```
   arrive plan set-status --item <ADV-ID> --status done
   ```

6. **Update the advance frontmatter**:
   - Set `status: complete`
   - Set `implementation_completed_at` to current ISO timestamp

7. **Clear work context** if this was the active advance:
   ```
   arrive work stop
   ```

8. **Check for newly unblocked advances** — read `arrive/implementation-plan.yaml` and find items whose `dependencies` list includes this advance ID. Report them:
```
Completed: <ADV-ID>

Newly unblocked:
  - <ADV-ID-2> (<title>) — ready to start
  - <ADV-ID-3> (<title>) — ready to start (parallel)

Next recommended: arrive-implement start <next-ADV-ID>
```

---

## General Principles

- **Always claim before coding** — `arrive plan start` prevents two agents or sessions from claiming the same work.
- **Tidy → Test → Implement** — every advance follows this commit discipline without exception.
- **Evidence is not optional** — advances cannot move to `complete` without the listed evidence types being satisfied.
- **Pipeline awareness** — check `pipeline.depends_on` in system.yaml before starting; don't start Phase 2 advances until Phase 1 contract checkpoints pass.
- **Lease heartbeat** — for long-running advances, periodically run `arrive plan heartbeat <ADV-ID>` to keep the lease active (default TTL is 120s).

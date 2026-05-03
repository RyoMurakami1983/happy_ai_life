---
name: gh-goal-driven-workflow
description: >
  Plan and operate gh Projects, Milestones, Issues, and PRs from a product goal without turning the board into a task dump. Use when: starting a goal-driven gh workflow, slicing a milestone into parent issues and sub-issues, or tuning the workflow from real operating friction.
---

# Run a Goal-Driven gh Workflow

Use this skill to turn a product goal into a lightweight gh execution loop.
It exists to keep gh Projects, Milestones, Issues, and PRs aligned with user value instead of drifting into busywork or a giant backlog.

## When to Use This Skill

Use this skill when:
- Starting a new GitHub Project for a product goal and wanting the lightest useful setup
- Turning one goal into one current Milestone instead of managing many parallel plans
- Breaking a Milestone into Parent issues and Sub-issues without losing the user-visible outcome
- Deciding whether labels, templates, or automation are needed yet
- Reviewing whether your Project has become an idea dump instead of a commitment board
- Capturing operating friction and feeding it back into the workflow itself

## Core Principles

1. **Goal before board** — A Project without a clear outcome becomes a task bucket
2. **One current Milestone** — Progress is easier to steer when only one outcome batch is active
3. **Issue is the work unit** — The board visualizes work; it does not replace issue quality
4. **One issue, one PR** — Keep implementation and review traceable
5. **Templates come later** — Add Issue or PR templates only after repeated writing friction appears
6. **Friction is data** — Confusion during operation should improve the workflow, not be forgotten
7. **Done means externally verified** — Do not mark GUI, workflow, or integration work done from build/unit tests alone

## Workflow: Goal to Project to Learning Loop

### Step 1 — Freeze the goal

Write the goal in one sentence.

Also write:
- what success looks like
- how you will verify it

If the goal is vague, stop and clarify it before creating GitHub structures.

Why: weak goals create neat-looking boards with low decision value.

### Step 2 — Choose one current Milestone

Pick the next outcome batch you want to finish now.

A good Milestone:
- is small enough to feel concrete
- is large enough to contain several issues
- describes an outcome, not a department or vague theme

Examples:
- `A4 PDF output`
- `Markdown round-trip reliability`
- `Comfortable Japanese writing flow`

Why: one current Milestone reduces drift and makes prioritization real.

### Step 3 — Create the Project with the minimum columns

Create one Project for the workflow.

Start with only:
- `Inbox`
- `Next`
- `Doing`
- `Done`

Do not add custom fields, automation, or roadmap views unless operation proves you need them.

Why: the board should reveal focus, not create maintenance work.

### Step 4 — Create Parent issues for the Milestone

Split the Milestone into **2 to 5 Parent issues**.

Each Parent issue should contain:
- purpose
- done condition
- out of scope

Use Parent issues for user-visible slices or major decisions, not for internal bookkeeping.

Why: Parent issues keep the Milestone understandable without forcing you into tiny task management too early.

### Step 5 — Create Sub-issues only when they can close with one PR

Break each Parent issue into Sub-issues.

A Sub-issue is good when:
- one PR can close it
- its value is still understandable
- it has a clear done condition

If a Sub-issue needs many unrelated code changes, split it again.

Why: Sub-issues should help delivery, not recreate a spreadsheet.

### Step 6 — Run the issue and PR loop

Operate with this rhythm:

1. Move one issue to `Doing`
2. Implement with one focused PR
3. In the PR, write:
   - what changed
   - why it changed
   - how it was checked
   - one closing keyword per issue, for example `Closes #12`, `Closes #13`, `Closes #14`
4. Merge
5. Confirm the expected issues actually closed
6. Move the Project item only after the GitHub state matches reality

Why: this keeps execution traceable and reduces hidden work.

### Step 6.5 — Add a verification gate before Done

Before marking an issue or Project item `Done`, classify the work by verification surface.

| Work type | Minimum verification before Done |
| --- | --- |
| Pure domain logic | Unit tests and type-check pass |
| Infrastructure / file I/O | Mocked failure path plus at least one integration check |
| GUI behavior | Screenshot or browser/app interaction evidence, not only unit tests |
| Keyboard shortcut | Actual key path or automated interaction check |
| Print / PDF output | Generated sample output or an explicit manual checklist with artifact path |
| GitHub workflow work | Issue state, Project status, PR closing references, and review threads checked |

If the verification surface is not checked yet, keep the issue `In Progress` and add a comment that names the remaining verification.

Why: green CI can prove the code compiles, but it cannot prove the user-visible workflow was exercised.

### Step 7 — Add labels only for routing, not decoration

Start with the smallest label set that helps decisions.

Good starters:
- `area:<domain>`
- `kind:feature`
- `kind:bug`
- `kind:research`
- `p0` / `p1` / `p2`

Avoid label explosions.

Why: labels should help triage and filtering, not become a second taxonomy project.

### Step 8 — Add templates only after repeated friction

Do **not** start by generating forms, scripts, or heavy automation.

Add an Issue template or PR template only when you repeatedly see one of these:
- people forget the done condition
- issue scope is inconsistent
- PRs miss the reason or verification steps

Start with only:
- one bug Issue template
- one feature/outcome Issue template
- one PR template

Why: templates should remove proven repetition, not predict imaginary future complexity.

### Step 9 — Capture friction and improve the workflow

When operation feels awkward, capture it in one short note.

Classify the friction as one of:
- guidance gap
- issue sizing mismatch
- template gap
- GitHub operation confusion
- verification gap
- state sync gap

Then ask:
- should the skill guidance change?
- should the examples change?
- should a template be added?
- should a script exist, or is prose enough?
- should a workflow or check exist because manual state sync failed?

Why: the workflow improves fastest when real friction becomes input instead of memory.

## Good Practices

### 1. Keep the Project as a commitment board

Only add what you actually plan to work on now.

### 2. Prefer outcome language over implementation language

`A4 output works for real documents` is stronger than `add export function`.

### 3. Use references for examples, not the hot path

Keep the main skill short.
Move repo-specific examples into `references/`.

### 4. Delay scripting until repetition is real

If `.md` examples are enough, prefer them before writing `py`, `ps1`, or `sh`.

## Common Pitfalls

### 1. Board first, goal later

**Problem**: Columns fill up, but the product direction stays fuzzy.

**Fix**: Rewrite the goal and current Milestone before touching the board again.

### 2. Too many active Milestones

**Problem**: Everything is important, so nothing is.

**Fix**: Choose one current Milestone and demote the rest to later.

### 3. Parent issues that are just categories

**Problem**: `frontend`, `backend`, or `misc` does not help product steering.

**Fix**: Rewrite Parent issues around user-visible outcomes or major decisions.

### 4. Templates added too early

**Problem**: You spend more time maintaining forms than moving work.

**Fix**: Use prose and examples first; add templates only after repeated friction.

### 5. Friction gets noticed but never reused

**Problem**: You solve the same GitHub workflow confusion again next week.

**Fix**: Classify friction and feed it back into this skill or its examples.

### 6. PR merge is treated as issue completion

**Problem**: A PR can merge while related issues remain open, Project statuses stay stale, or GUI verification is still missing.

**Fix**: After merge, check closing issue references, issue states, Project statuses, and unresolved review threads before declaring the milestone complete.

## Suggested Checkpoint Questions

Use these questions during operation:

1. Is the current Goal still one sentence?
2. Is there only one active Milestone?
3. Do the Parent issues describe outcomes, not categories?
4. Can each Sub-issue close with one PR?
5. Is the Project still showing commitments rather than all ideas?
6. Has any repeated friction earned a template or documentation update?
7. Did every merged PR close the intended issues?
8. Are Project statuses aligned with actual issue state?
9. For GUI work, is there screenshot/input/click evidence or an explicit unfinished checklist?

## References

- `references/rakugaki_writer-example.md` — concrete example for this repository





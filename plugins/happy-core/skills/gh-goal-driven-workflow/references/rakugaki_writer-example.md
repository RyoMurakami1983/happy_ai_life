# rakugaki_writer example

## Goal

日本人が気持ちよく Markdown で書けて、そのまま Word のように A4 出力できる

## Suggested current Milestone

- `M3 A4 PDF出力`

## Suggested Parent issues

1. `A4出力の成功条件を決める`
2. `PDF出力方式を比較して決める`
3. `選んだ方式で最小実装する`

## Done gate examples for this repo

### A4 / PDF / GUI work

Do not mark A4 output work `Done` from build, lint, type-check, or unit tests alone.

Minimum evidence before `Done`:
- app launched in the target mode
- A4 preview toggled through the GUI
- representative Japanese text entered or loaded
- `=== page ===` entered and visually checked
- `PDF に出力` clicked through the GUI
- generated PDF or print dialog behavior checked
- screenshot or debug artifact path recorded when possible

If any item is missing, keep the issue `In Progress` and comment with the remaining verification.

### Project / Issue / PR sync

After a PR merge:
- check which issues GitHub actually closed
- close completed decision issues manually if the closing keyword missed them
- keep implementation issues open when manual GUI verification remains
- align Project status with the real issue state

## Suggested label set

- `area:a4`
- `area:editor`
- `area:markdown`
- `kind:feature`
- `kind:bug`
- `kind:research`
- `p0`
- `p1`
- `p2`

## Template policy for this repo

- Start without templates
- Add Issue template / PR template only after repeated writing friction appears
- Prefer `.md` examples before adding automation scripts

## Friction loop examples

### guidance gap

- "I could not tell whether this should be a Parent issue or a Sub-issue."

### issue sizing mismatch

- "This Sub-issue needed three unrelated PRs."

### template gap

- "We keep forgetting done conditions in Parent issues."

### GitHub operation confusion

- "I do not know when something belongs in the Project versus only in Issues."

### verification gap

- "The code passed tests, but the GUI button was not clicked in the running app."

### state sync gap

- "The PR merged, but only one of three intended issues closed and Project statuses drifted."

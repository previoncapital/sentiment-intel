# 2026-11-15 — Issue taxonomy v0 and Ward 12 check pack (preview)

**Type:** taxonomy / linking method · **Decided by:** Claude Code (routine), for owner review

## Taxonomy v0 (`taxonomy/issues_v0.yaml`)

- 8 domains and 44 issues, following the plan. Each issue has a definition,
  what it includes, what it excludes and where that goes instead, so a person
  and an AI model apply it the same way.
- Added `supply_direction` ("pro-housing side") per issue, because the plan's
  support-rate signal needs it. Left blank where there is no clear side. This
  is a product judgement for the owner to confirm.
- Not yet tested on 200-300 real items (Gate 1 requirement). Next step.

## Ward 12 check pack (`pipelines/ward_pack/`)

- A **preview** of Milestone M1 linking, built on the raw store so the owner can
  check real records now. Not the production connectors; M0 acceptance tests
  still come first for the formal build.
- Ward assignment: the City's listed ward is used; map points are a cross-check
  only (DI-017).
- Vote dates for 2018-22 are restored from the meeting schedule. Method tested
  on 2022-26 votes with known dates: 100% correct meeting for Council-coded
  items, 99% for committee items voted at Council (DI-002).
- Vote-to-application and appeal-to-C of A links are by street address only;
  every link is marked "needs review" as the spec requires (DI-018).
- Application status: both the applications file and the pipeline status are
  shown, because "Closed" is ambiguous (DI-020).

## Findings that change the product thinking

- Most local planning decisions carry no recorded vote (DI-021), so ward
  posture can't come from votes alone; motions and minutes (M3) matter more
  than the plan assumed.

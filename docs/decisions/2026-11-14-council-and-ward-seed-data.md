# 2026-11-14 — Seed data: ward map and every mayor and councillor since Dec 2018

**Type:** schema / source decision · **Decided by:** Claude Code (routine), for owner review

## What was built

- `db/seed/wards/` — the 25-ward map (one version, in force since 2018).
- `db/seed/people/` — 50 people, 87 terms of office (Dec 2018 through the
  2026–2030 term), 10 vacant periods, and every spelling of each name seen in
  the sources (for later matching).
- `db/seed/build_checks.md` — 35 automatic cross-checks; `tests/` — 10 tests.
- `docs/seed-review/` — a ward map and a seat-by-seat history for the owner.

## Decisions

1. **General-election winners come from the official results files**, not from
   a hand-typed list. Mid-term changes (resignations, deaths, removals,
   appointments, by-elections) are hand-checked in one file,
   `db/seed/curated/council_changes_2018_2030.yaml`, each with sources.
2. **Every date states its basis** (set by law, City record, news report,
   by-election day, last meeting attended) and a confidence level, instead of
   presenting estimates as official.
3. **Vacancies are explicit.** A seat with no holder appears in
   `vacancies.csv`; tests check that every day from Dec 1, 2018 to 2030 each
   of the 26 seats has exactly one holder or a recorded vacancy.
4. **The map's validity for representation starts 2018-12-01**, the start of
   the first Council elected on it; the City's file records 2018-08-07 as the
   boundary's effective date, which is kept alongside.
5. **Name splits follow the City's own records.** Where the results file and
   common usage differ (Diana Chan McNally: City file "McNally Diana Chan"),
   the display name follows the Clerk's certified declaration.
6. **Seed files are committed to the repository** (1.1 MB) so the database can
   be built from one command; the raw downloads stay in the raw store.

## Findings to carry forward

- The City's **attendance dataset omits two appointed councillors** (Robin
  Buxton Potts, Rose Milczyn, 2022), though both appear in the voting records.
  Don't use attendance alone to decide who was in office.
- **Item codes use the council year, not the calendar year**: November–
  December 2022 votes carry `2023.` codes. Link by meeting date.
- One name in the 2018–22 voting data is garbled (`BailÃ£o`); the build
  repairs this kind of encoding error.
- **Follow-up investigation (2026-11-15):**
  - The attendance gap is in all four published versions of the file (CSV,
    JSON, XML, refreshed Feb 2026): members listed per Council session drop
    from 26 to 24 in May 2022 and stay there; Mihevc was added, Buxton Potts
    and Milczyn never were. Cause unknown; question for the open data team.
  - Ward 22: Karygiannis was removed 2019-11-06, reinstated 2019-11-25,
    removed 2020-06-24, reinstated by stay about 2020-08-05, removed for good
    2020-09-24. Attendance is consistent (no meeting fell inside either period
    in which he was back in office). Now modelled as three terms and three
    vacancies.
  - 2018–22 votes: all committee votes are dated; full Council votes are
    dated only for April–November 2020 (first virtual meetings). Dates can be
    restored from the meeting schedule. 2022–26 Council votes carry the
    minute of the vote, written as 24-hour time with an AM/PM label.
  - By-election starts now use the oath date (Chow, official) or, where no
    exact date was published, the first Council meeting attended, since
    winners take the oath at the next meeting (Clerk's statement for
    Chernos Lin).
- **Still to confirm:** oath dates for Kandavel (2023) and Shan (2025); the
  exact date of the August 2020 stay; the 2018–22 term start in a City
  record (legal start Dec 1; oath at the Dec 4 inaugural meeting).

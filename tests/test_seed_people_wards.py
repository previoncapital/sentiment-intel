"""Acceptance tests for the M0 seed data (ward map; mayors and councillors).

These run against the committed seed files, so they need no network access.
"""

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pytest
from shapely.geometry import shape

SEED = Path(__file__).resolve().parents[1] / "db" / "seed"
TERMS = {
    "2018-2022": (date(2018, 12, 1), date(2022, 11, 14)),
    "2022-2026": (date(2022, 11, 15), date(2026, 11, 14)),
    "2026-2030": (date(2026, 11, 15), date(2030, 11, 14)),
}


def rows(rel: str) -> list[dict]:
    with (SEED / rel).open() as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def terms() -> list[dict]:
    return rows("people/office_terms.csv")


@pytest.fixture(scope="module")
def wards_geo() -> list:
    return json.loads((SEED / "wards/ward_map_2018.geojson").read_text())["features"]


def seat(r: dict) -> tuple:
    return (r["office"], r["ward_number"])


# ---------------- Ward map ----------------

def test_25_wards_numbered_1_to_25(wards_geo):
    assert sorted(f["properties"]["ward_number"] for f in wards_geo) == list(range(1, 26))
    assert all(f["properties"]["ward_name"] for f in wards_geo)


def test_ward_shapes_are_valid_and_do_not_overlap(wards_geo):
    shapes = {f["properties"]["ward_number"]: shape(f["geometry"]) for f in wards_geo}
    assert all(s.is_valid and not s.is_empty for s in shapes.values())
    total = sum(s.area for s in shapes.values())
    nums = sorted(shapes)
    overlap = sum(shapes[a].intersection(shapes[b]).area
                  for i, a in enumerate(nums) for b in nums[i + 1:])
    assert overlap / total < 1e-6  # shared borders only


def test_ward_csv_matches_geojson(wards_geo):
    csv_rows = rows("wards/wards.csv")
    assert {(int(r["ward_number"]), r["ward_name"]) for r in csv_rows} == {
        (f["properties"]["ward_number"], f["properties"]["ward_name"]) for f in wards_geo}


# ---------------- Mayors and councillors ----------------

def test_every_term_row_sits_inside_its_council_term(terms):
    for r in terms:
        start, end = TERMS[r["council_term"]]
        assert start <= date.fromisoformat(r["start_date"]) <= date.fromisoformat(r["end_date"]) <= end, r


def test_no_seat_has_two_holders_at_once(terms):
    by_seat = defaultdict(list)
    for r in terms:
        by_seat[seat(r)].append(r)
    for s, rs in by_seat.items():
        rs.sort(key=lambda r: r["start_date"])
        for a, b in zip(rs, rs[1:]):
            assert b["start_date"] >= a["end_date"], (s, a["person_name"], b["person_name"])


def test_every_seat_filled_every_day_except_documented_vacancies(terms):
    """From Dec 1, 2018 to the end of the new term, every day each of the 26
    seats (mayor + 25 wards) has exactly one holder, unless a documented
    vacancy covers that day."""
    vac = defaultdict(list)
    for v in rows("people/vacancies.csv"):
        office, _, ward = v["seat"].partition(" ")
        vac[(office, ward)].append((date.fromisoformat(v["from"]), date.fromisoformat(v["to"])))
    seats = [("mayor", "")] + [("councillor", str(w)) for w in range(1, 26)]
    by_seat = defaultdict(list)
    for r in terms:
        by_seat[seat(r)].append((date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])))
    day, last = TERMS["2018-2022"][0], TERMS["2026-2030"][1]
    problems = []
    while day <= last:
        for s in seats:
            # The day someone leaves counts as theirs; the vacancy runs to the
            # day before the successor starts (handover days belong to one side).
            held = sum(1 for a, b in by_seat[s] if a <= day <= b)
            vacant = any(a < day < b for a, b in vac[s])
            if held == 0 and not vacant:
                problems.append((s, day))
            if held > 1 and not any(day in (a, b) for a, b in by_seat[s]):
                problems.append((s, day, "double"))
        day += timedelta(days=1)
    assert not problems[:5], f"{len(problems)} problem days, e.g. {problems[:5]}"


def test_every_office_holder_is_a_known_person_with_an_alias(terms):
    persons = {r["person_id"] for r in rows("people/persons.csv")}
    aliased = {r["person_id"] for r in rows("people/person_aliases.csv")}
    holders = {r["person_id"] for r in terms}
    assert holders == persons
    assert holders <= aliased


def test_new_term_has_mayor_chow_and_seven_new_members(terms):
    start_new = TERMS["2026-2030"][0].isoformat()
    end_old = TERMS["2022-2026"][1].isoformat()
    new = {seat(r): r["person_name"] for r in terms if r["start_date"] == start_new}
    old = {seat(r): r["person_name"] for r in terms if r["end_date"] == end_old}
    assert new[("mayor", "")] == "Olivia Chow"
    changed = {s for s in new if new[s] != old.get(s)}
    assert {int(w) for _, w in changed} == {4, 5, 11, 13, 14, 19, 23}


def test_every_date_has_a_basis_and_confidence(terms):
    for r in terms:
        assert r["start_basis"] and r["start_confidence"] in {"high", "medium", "low"}
        assert r["end_basis"] and r["end_confidence"] in {"high", "medium", "low"}


def test_build_checks_only_known_flags():
    known = {"2018-2022: attendance dataset lists everyone who voted"}
    text = (SEED / "build_checks.md").read_text()
    flagged = {line.split("|")[1].strip() for line in text.splitlines() if "| FLAG |" in line}
    assert flagged <= known, flagged - known

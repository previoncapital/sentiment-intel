"""Build the M0 seed data: the 25-ward map and every mayor and councillor since
December 2018, with ward and term dates.

Inputs (all downloaded into the raw store, see connectors/common/rawstore.py):
  * City Wards (open data)                        -> ward map
  * Official election results 2018, 2022, 2026    -> general-election winners
  * Official by-election results 2021-2025        -> cross-check of by-elections
  * Council attendance and voting records          -> cross-checks
  * db/seed/curated/council_changes_2018_2030.yaml -> term dates and mid-term changes

Outputs (committed, in db/seed/):
  wards/ward_map_2018.geojson, wards/wards.csv,
  people/persons.csv, people/person_aliases.csv, people/office_terms.csv,
  build_manifest.json (which raw files, by hash, produced these), and
  build_checks.md (the cross-check report).

Run:  uv run python db/seed/build/build_people_and_wards.py
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import openpyxl
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from connectors.common.rawstore import RawFile, fetch  # noqa: E402

PIPELINE_VERSION = "seed-people-wards-0.1"
SEED = REPO / "db" / "seed"
CURATED = SEED / "curated" / "council_changes_2018_2030.yaml"

CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
INPUTS = {
    "wards": ("tor_geo", f"{CKAN}/dataset/5e7a8234-f805-43ac-820f-03d7c360b588/resource/737b29e0-8329-4260-b6af-21555ab24f28/download/city-wards-data-4326.geojson"),
    "results_2018": ("tor_elections", None),  # resolved from the package below
    "results_2022": ("tor_elections", None),
    "results_2026": ("tor_elections", None),
    "attendance_2018": ("tor_attendance", f"{CKAN}/datastore/dump/b1989a8e-d69c-4b7e-85a7-c1edc2f887e9"),
    "attendance_2022": ("tor_attendance", f"{CKAN}/datastore/dump/4f8317bd-566b-4e15-b3b7-59a4a398a856"),
    "votes_2018": ("tor_votes", f"{CKAN}/datastore/dump/84ce76c3-94ed-486c-818b-596fd78d1fea"),
    "votes_2022": ("tor_votes", f"{CKAN}/datastore/dump/55ead013-2331-4686-9895-9e8145b94189"),
}
ELECTION_PACKAGE = "election-results-official"
DECLARATION_2026 = ("https://www.toronto.ca/wp-content/uploads/2026/10/"
                    "8966-Declaration-of-Results-2026-Toronto-Municipal-Election-Oct-29-Final.pdf")
BYELECTION_PACKAGE = "elections-official-by-election-results"
BYELECTION_RESOURCES = {  # resource name prefix -> (office, ward)
    "2021 Councillor Ward 22": ("councillor", 22),
    "2023 Office of the Mayor": ("mayor", None),
    "2023 Councillor Ward 20": ("councillor", 20),
    "2024 Councillor Ward 15": ("councillor", 15),
    "2025 Councillor Ward 25": ("councillor", 25),
}


# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------

def fix_mojibake(s: str) -> str:
    """Repair text that was UTF-8 but decoded as Latin-1 (e.g. 'BailÃ£o')."""
    if "Ã" in s or "Â" in s:
        try:
            return s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def name_key(name: str) -> str:
    """Order-independent comparison key: accents, case, punctuation removed."""
    s = unicodedata.normalize("NFKD", fix_mojibake(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    tokens = re.findall(r"[a-z]+", s.replace("-", " "))
    return " ".join(sorted(tokens))


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", fix_mojibake(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return "p-" + re.sub(r"[^a-z]+", "-", s).strip("-")


@dataclass
class Person:
    person_id: str
    canonical_name: str
    first_name: str
    last_name: str
    aliases: dict[str, str] = field(default_factory=dict)  # alias -> where seen


class People:
    def __init__(self, overrides: list[dict] | None = None) -> None:
        self.by_key: dict[str, Person] = {}
        self.overrides = {name_key(o["results_spelling"]): o for o in (overrides or [])}

    def add_known(self, first: str, last: str, alias_source: str) -> Person:
        first, last = fix_mojibake(first.strip()), fix_mojibake(last.strip())
        full = f"{first} {last}"
        k = name_key(full)
        p = self.by_key.get(k)
        if p is None:
            p = Person(slug(full), full, first, last)
            self.by_key[k] = p
        p.aliases.setdefault(full, alias_source)
        return p

    def from_results(self, last_first: str, alias_source: str) -> Person:
        """Results files list names as 'Last First'. Match a known person by
        token set; otherwise assume the final token is the first name."""
        raw = " ".join(last_first.split())
        k = name_key(raw)
        p = self.by_key.get(k)
        o = self.overrides.get(k)
        if p is None and o is not None:
            p = Person(slug(o["canonical_name"]), o["canonical_name"], o["first_name"], o["last_name"])
            p.aliases[o["canonical_name"]] = "Clerk's declaration of results"
            self.by_key[k] = p
        if p is None:
            parts = raw.split(" ")
            p = self.add_known(parts[-1], " ".join(parts[:-1]), alias_source)
        p.aliases.setdefault(raw, alias_source)
        return p

    def get(self, name: str) -> Person:
        return self.by_key[name_key(name)]


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def ckan_resources(package: str) -> list[dict]:
    raw = fetch(f"{CKAN}/api/3/action/package_show?id={package}", "tor_elections",
                PIPELINE_VERSION, reuse=True)
    return json.loads(raw.read_bytes())["result"]["resources"]


def load_inputs() -> dict[str, RawFile]:
    files: dict[str, RawFile] = {}
    for r in ckan_resources(ELECTION_PACKAGE):
        for year in ("2018", "2022", "2026"):
            if r["name"] == f"{year}-results":
                files[f"results_{year}"] = fetch(r["url"], "tor_elections", PIPELINE_VERSION)
    for r in ckan_resources(BYELECTION_PACKAGE):
        for prefix in BYELECTION_RESOURCES:
            if r["name"].startswith(prefix):
                files[f"by_{prefix}"] = fetch(r["url"], "tor_elections", PIPELINE_VERSION)
    for key, (source, url) in INPUTS.items():
        if url:
            files[key] = fetch(url, source, PIPELINE_VERSION)
    files["declaration_2026"] = fetch(DECLARATION_2026, "tor_elections", PIPELINE_VERSION)
    missing = {k for k in INPUTS if k not in files} | {
        f"by_{p}" for p in BYELECTION_RESOURCES if f"by_{p}" not in files}
    if missing:
        raise SystemExit(f"Missing inputs: {sorted(missing)}")
    return files


def read_csv(raw: RawFile) -> list[dict]:
    text = raw.read_bytes().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    # Column names differ between terms ('First Name' vs 'FirstName').
    return [{re.sub(r"[^a-z]", "", k.lower()): v for k, v in r.items()} for r in rows]


def sheet_totals(ws) -> dict[str, int]:
    """Candidate -> total votes from one poll-by-poll sheet."""
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    header = next((r for r in rows if r and r[0] == "Subdivision"), None)
    if header is None:
        return {}
    total_col = header.index("Total")
    out: dict[str, int] = {}
    started = False
    for r in rows:
        if not r or r[0] is None:
            continue
        label = str(r[0]).strip()
        if label in ("Councillor", "Mayor"):
            started = True
            continue
        if not started or label == "Subdivision":
            continue
        if label.endswith("Totals"):
            break
        out[label] = out.get(label, 0) + int(r[total_col] or 0)
    return out


def ward_from_sheet(title: str) -> int | None:
    m = re.match(r"Ward\s+(\d+)", title.strip())
    return int(m.group(1)) if m else None


def winners_from_workbook(data: bytes) -> tuple[dict[int, tuple[str, int]], dict[str, int]]:
    """Return ({ward: (winner, votes)}, {candidate: votes summed over wards})."""
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    by_ward: dict[int, tuple[str, int]] = {}
    summed: dict[str, int] = defaultdict(int)
    for ws in wb.worksheets:
        ward = ward_from_sheet(ws.title)
        if ward is None:
            continue
        totals = sheet_totals(ws)
        if not totals:
            continue
        name, votes = max(totals.items(), key=lambda kv: kv[1])
        by_ward[ward] = (name, votes)
        for c, v in totals.items():
            summed[c] += v
    return by_ward, dict(summed)


def general_election(raw: RawFile) -> tuple[dict[int, str], str]:
    zf = zipfile.ZipFile(io.BytesIO(raw.read_bytes()))
    names = zf.namelist()
    coun = next(n for n in names if n.endswith("Councillor.xlsx"))
    mayor = next(n for n in names if n.endswith("Mayor.xlsx"))
    by_ward, _ = winners_from_workbook(zf.read(coun))
    _, mayor_totals = winners_from_workbook(zf.read(mayor))
    mayor_winner = max(mayor_totals.items(), key=lambda kv: kv[1])[0]
    return {w: n for w, (n, _) in by_ward.items()}, mayor_winner


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def declaration_winners(raw: RawFile) -> dict:
    """Winners from the Clerk's Declaration of Results PDF ('Name votes X')."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(raw.read_bytes())) as pdf:
        text = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    out: dict = {}
    mayor_part, rest = text.split("Office of Councillor", 1)
    m = re.search(r"^(.+?) \d+ X$", mayor_part.split("Office of Mayor", 1)[1], re.M)
    out["mayor"] = m.group(1)
    rest = re.split(r"Toronto District School Board|Trustee", rest)[0]
    ward = None
    for line in rest.splitlines():
        wm = re.match(r"Ward (\d+) ", line)
        if wm:
            ward = int(wm.group(1))
            continue
        cm = re.match(r"(.+?) (\d+) X$", line) or re.match(r"(.+?) Acclaimed$", line)
        if cm and ward and ward not in out:
            out[ward] = cm.group(1)
    return out


def d(x) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x))


def main() -> None:
    files = load_inputs()
    curated = yaml.safe_load(CURATED.read_text())
    checks: list[tuple[str, bool, str]] = []  # (check, passed, detail)

    people = People(curated.get("name_overrides"))
    # Seed known spellings (first/last split) from attendance and votes.
    attendance = {"2018-2022": read_csv(files["attendance_2018"]),
                  "2022-2026": read_csv(files["attendance_2022"])}
    votes = {"2018-2022": read_csv(files["votes_2018"]),
             "2022-2026": read_csv(files["votes_2022"])}
    for term, rows in attendance.items():
        for r in rows:
            people.add_known(r["firstname"], r["lastname"], f"attendance {term}")
    for term, rows in votes.items():
        for r in rows:
            people.add_known(r["firstname"], r["lastname"], f"voting record {term}")

    # ---- General-election winners ----
    terms = {t["term"]: t for t in curated["terms"]}
    winners = {}
    for term, key in (("2018-2022", "results_2018"), ("2022-2026", "results_2022"),
                      ("2026-2030", "results_2026")):
        wards, mayor = general_election(files[key])
        winners[term] = (wards, mayor)
        checks.append((f"{term}: results list 25 ward winners", len(wards) == 25,
                       f"{len(wards)} wards found"))

    # ---- Cross-check 2026 winners against the Clerk's certified declaration ----
    declared = declaration_winners(files["declaration_2026"])
    wards26, mayor26 = winners["2026-2030"]
    diffs = [f"ward {w}: results '{wards26.get(w)}' vs declaration '{declared.get(w)}'"
             for w in range(1, 26) if name_key(wards26.get(w, "")) != name_key(declared.get(w, ""))]
    diffs += [] if name_key(mayor26) == name_key(declared.get("mayor", "")) else [f"mayor: {mayor26} vs {declared.get('mayor')}"]
    checks.append(("2026 winners in the results file match the Clerk's certified declaration",
                   not diffs, "; ".join(diffs)))

    # ---- By-election winners (cross-check of the curated list) ----
    by_winners = {}
    for prefix, (office, ward) in BYELECTION_RESOURCES.items():
        by_ward, summed = winners_from_workbook(files[f"by_{prefix}"].read_bytes())
        if office == "mayor":
            by_winners[prefix] = max(summed.items(), key=lambda kv: kv[1])[0]
        else:
            by_winners[prefix] = by_ward[ward][0]

    # ---- Office terms ----
    terms_out: list[dict] = []

    def open_term(person: Person, office: str, ward: int | None, term: str, start: date,
                  start_basis: str, start_conf: str, how: str, sources: list[str]) -> dict:
        row = {
            "person_id": person.person_id, "person_name": person.canonical_name,
            "office": office, "ward_number": ward if ward is not None else "",
            "council_term": term,
            "start_date": start.isoformat(), "start_basis": start_basis,
            "start_confidence": start_conf, "how_started": how,
            "end_date": d(terms[term]["end"]).isoformat(), "end_basis": "statutory",
            "end_confidence": terms[term].get("end_confidence", "high"),
            "how_ended": "term_end", "sources": " ".join(sources),
        }
        terms_out.append(row)
        return row

    current: dict[tuple[str, str, int | None], dict] = {}
    for term in ("2018-2022", "2022-2026", "2026-2030"):
        t = terms[term]
        wards, mayor = winners[term]
        src = f"official {d(t['general_election']).year} election results (open data)"
        mp = people.from_results(mayor, f"{term} election results")
        current[(term, "mayor", None)] = open_term(
            mp, "mayor", None, term, d(t["start"]), t["start_basis"], t["start_confidence"],
            "general_election", [src])
        for w in sorted(wards):
            p = people.from_results(wards[w], f"{term} election results")
            current[(term, "councillor", w)] = open_term(
                p, "councillor", w, term, d(t["start"]), t["start_basis"],
                t["start_confidence"], "general_election", [src])

    def term_for(day: date) -> str:
        for name, t in terms.items():
            if d(t["start"]) <= day <= d(t["end"]):
                return name
        raise ValueError(day)

    vacancies: list[dict] = []
    vacant_since: dict[tuple, tuple[date, str]] = {}
    def order(c: dict) -> tuple:
        # Same-day events: a departure comes before the successor's arrival,
        # except someone who joins and leaves the same day (their arrival first).
        def has(kind: str) -> bool:
            return any(o["person"] == c["person"] and o["kind"] == kind
                       and o["date"] == c["date"] for o in curated["changes"])
        if c["kind"] == "joined":
            rank = 0 if has("left") else 2
        else:
            rank = 1
        return (d(c["date"]), rank)

    for ch in sorted(curated["changes"], key=order):
        day = d(ch["date"])
        term = term_for(day)
        ward = ch.get("ward")
        seat = (term, ch["office"], ward)
        if name_key(ch["person"]) in people.by_key:
            person = people.get(ch["person"])
        else:
            first, last = ch["person"].split(" ", 1)
            person = people.add_known(first, last, "curated changes")
        if ch["kind"] == "left":
            row = current.get(seat)
            ok = row is not None and row["person_id"] == person.person_id
            checks.append((f"{ch['person']} held {ch['office']} {ward or ''} when leaving on {day}",
                           ok, "" if ok else f"seat held by {row and row['person_name']}"))
            if ok:
                row.update(end_date=day.isoformat(), end_basis=ch["basis"],
                           end_confidence=ch["confidence"], how_ended=ch["reason"],
                           sources=" ".join(filter(None, [row["sources"], *ch.get("sources", [])])))
                current[seat] = None
                vacant_since[seat] = (day, ch["person"])
        else:
            row = current.get(seat)
            checks.append((f"{ch['office']} {ward or ''} was vacant before {ch['person']} joined on {day}",
                           row is None, "" if row is None else f"still held by {row['person_name']}"))
            if seat in vacant_since:
                since, who = vacant_since.pop(seat)
                vacancies.append({"seat": f"{ch['office']} {ward or ''}".strip(), "term": term,
                                  "from": since.isoformat(), "to": day.isoformat(),
                                  "after": who, "filled_by": ch["person"]})
            current[seat] = open_term(person, ch["office"], ward, term, day, ch["basis"],
                                      ch["confidence"], ch["reason"], ch.get("sources", []))
    for seat, (since, who) in vacant_since.items():
        vacancies.append({"seat": f"{seat[1]} {seat[2] or ''}".strip(), "term": seat[0],
                          "from": since.isoformat(),
                          # 'to' is always the day the seat was next filled; here,
                          # the first day of the next Council term.
                          "to": (d(terms[seat[0]]["end"]) + timedelta(days=1)).isoformat(),
                          "after": who, "filled_by": "(vacant until next term began)"})

    # ---- Cross-checks ----
    by_elections_expected = {
        "2021 Councillor Ward 22": "Nick Mantas", "2023 Office of the Mayor": "Olivia Chow",
        "2023 Councillor Ward 20": "Parthi Kandavel", "2024 Councillor Ward 15": "Rachel Chernos Lin",
        "2025 Councillor Ward 25": "Neethan Shan"}
    for prefix, expected in by_elections_expected.items():
        got = by_winners[prefix]
        ok = name_key(got) == name_key(expected)
        checks.append((f"{prefix} by-election winner in official results is {expected}", ok, f"results say {got}"))

    def terms_of(pid: str, term: str) -> list[dict]:
        return [r for r in terms_out if r["person_id"] == pid and r["council_term"] == term]

    for term in ("2018-2022", "2022-2026"):
        seen_votes = {(r["firstname"], r["lastname"]) for r in votes[term]}
        unmatched = [f"{f} {l}" for f, l in seen_votes
                     if not terms_of(people.get(f"{f} {l}").person_id, term)]
        checks.append((f"{term}: every member in the voting record held office in that term",
                       not unmatched, ", ".join(sorted(unmatched))))
        council_rows = [r for r in attendance[term] if r["committee"].strip() == "City Council"]
        span: dict[str, list[str]] = defaultdict(list)
        for r in council_rows:
            span[f"{r['firstname']} {r['lastname']}"].append(r["sessiondate"][:10])
        outside = []
        for name, days in span.items():
            rows = terms_of(people.get(name).person_id, term)
            for day in days:
                if not any(r["start_date"] <= day <= r["end_date"] for r in rows):
                    outside.append(f"{name} on {day}")
                    break
        checks.append((f"{term}: every Council attendance date falls inside that member's term dates",
                       not outside, ", ".join(outside)))
        voters = {people.get(f"{f} {l}").person_id for f, l in seen_votes}
        attendees = {people.get(n).person_id for n in span}
        missing = sorted(people_by_id(people)[p].canonical_name for p in voters - attendees)
        checks.append((f"{term}: attendance dataset lists everyone who voted",
                       not missing, ("missing from attendance: " + ", ".join(missing)) if missing else ""))

    # Each seat: no two holders at once (a same-day handover is allowed).
    overlaps = []
    for (office, ward), rows in group_by_seat(terms_out).items():
        rows = sorted(rows, key=lambda r: r["start_date"])
        for a, b in zip(rows, rows[1:]):
            if b["start_date"] < a["end_date"]:
                overlaps.append(f"{office} {ward}: {a['person_name']} / {b['person_name']}")
    checks.append(("No seat has two holders at once", not overlaps, ", ".join(overlaps)))

    write_outputs(files, people, terms_out, vacancies, checks)


def people_by_id(people: People) -> dict[str, Person]:
    return {p.person_id: p for p in people.by_key.values()}


def group_by_seat(rows: list[dict]) -> dict[tuple, list[dict]]:
    g: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        g[(r["office"], r["ward_number"])].append(r)
    return g


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_outputs(files, people, terms_out, vacancies, checks) -> None:
    # Wards
    gj = json.loads(files["wards"].read_bytes())
    feats = []
    ward_rows = []
    for f in sorted(gj["features"], key=lambda f: int(f["properties"]["AREA_SHORT_CODE"])):
        p = f["properties"]
        num = int(p["AREA_SHORT_CODE"])
        props = {
            "ward_number": num, "ward_name": p["AREA_NAME"], "map_version": "2018-25-ward",
            "source_date_effective": p["DATE_EFFECTIVE"][:10],
            "valid_from": "2018-12-01", "valid_to": None,
            "source_area_id": p["AREA_ID"], "raw_file_sha256": files["wards"].sha256,
        }
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
        ward_rows.append({k: v for k, v in props.items()})
    (SEED / "wards").mkdir(parents=True, exist_ok=True)
    (SEED / "wards" / "ward_map_2018.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "toronto_wards_2018",
                    "features": feats}, separators=(",", ":")))
    write_csv(SEED / "wards" / "wards.csv", ward_rows,
              ["ward_number", "ward_name", "map_version", "source_date_effective", "valid_from",
               "valid_to", "source_area_id", "raw_file_sha256"])

    # People: only those who held office (others seen in data are ignored).
    holders = {r["person_id"] for r in terms_out}
    pid = people_by_id(people)
    persons = sorted((pid[p] for p in holders), key=lambda p: (p.last_name, p.first_name))
    write_csv(SEED / "people" / "persons.csv",
              [{"person_id": p.person_id, "canonical_name": p.canonical_name,
                "first_name": p.first_name, "last_name": p.last_name} for p in persons],
              ["person_id", "canonical_name", "first_name", "last_name"])
    write_csv(SEED / "people" / "person_aliases.csv",
              [{"person_id": p.person_id, "alias": a, "alias_source": s}
               for p in persons for a, s in sorted(p.aliases.items())],
              ["person_id", "alias", "alias_source"])
    order = {"mayor": 0, "councillor": 1}
    terms_sorted = sorted(terms_out, key=lambda r: (r["council_term"], order[r["office"]],
                                                    int(r["ward_number"] or 0), r["start_date"]))
    for r in terms_sorted:
        r["pipeline_version"] = PIPELINE_VERSION
    write_csv(SEED / "people" / "office_terms.csv", terms_sorted,
              ["person_id", "person_name", "office", "ward_number", "council_term",
               "start_date", "start_basis", "start_confidence", "how_started",
               "end_date", "end_basis", "end_confidence", "how_ended", "sources",
               "pipeline_version"])
    write_csv(SEED / "people" / "vacancies.csv", vacancies,
              ["seat", "term", "from", "to", "after", "filled_by"])

    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "curated_file": str(CURATED.relative_to(REPO)),
        "inputs": {k: {"url": f.url, "sha256": f.sha256, "fetched_at": f.fetched_at,
                       "source": f.source} for k, f in sorted(files.items())},
    }
    (SEED / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    lines = ["# Seed build checks", "",
             f"Pipeline version `{PIPELINE_VERSION}`. Generated by "
             "`db/seed/build/build_people_and_wards.py`.", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FLAG'} | {detail} |")
    (SEED / "build_checks.md").write_text("\n".join(lines) + "\n")

    flagged = [c for c in checks if not c[1]]
    print(f"{len(terms_sorted)} office terms, {len(persons)} people, {len(feats)} wards, "
          f"{len(vacancies)} vacancies; {len(checks) - len(flagged)} checks passed, "
          f"{len(flagged)} flagged")
    for name, _, detail in flagged:
        print("  FLAG:", name, "-", detail)


if __name__ == "__main__":
    main()

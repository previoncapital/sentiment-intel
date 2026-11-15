"""Ward check pack (preview of Milestone M1 linking) for one ward.

Links, for one ward, the City's open data on development applications,
Committee of Adjustment (C of A) applications, TLAB appeals, the development
pipeline and recorded votes, and writes an owner-facing review (Markdown + PDF)
plus CSVs of every linked record for audit.

This is a preview built on the raw store, not the production M1 connectors.
Every vote-to-application link here is an *address-only* link, which the spec
says must be reviewed by a person before it is relied on.

Run:  uv run python pipelines/ward_pack/build_ward_pack.py --ward 12
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from connectors.common.rawstore import fetch  # noqa: E402
from tools.owner_pdf import markdown_to_pdf  # noqa: E402

VERSION = "ward-pack-0.1"
C = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
URLS = {
    "devapps": (f"{C}/datastore/dump/8907d8ed-c515-4ce9-b674-9f8c6eefcf0d", "tor_dev_apps"),
    "coa_active": (f"{C}/datastore/dump/51fd09cd-99d6-430a-9d42-c24a937b0cb0", "tor_coa"),
    "coa_closed": (f"{C}/datastore/dump/9c97254e-5460-4799-896f-c7823413c81c", "tor_coa"),
    "tlab": (f"{C}/datastore/dump/8ea54900-e314-4d17-a671-8b6158ba516a", "tor_tlab_appeals"),
    "pipeline": (f"{C}/datastore/dump/7aad5dbd-a769-4bd5-b5d2-f9bb605b6bf9", "tor_pipeline_permits"),
    "votes_2018": (f"{C}/datastore/dump/84ce76c3-94ed-486c-818b-596fd78d1fea", "tor_votes"),
    "votes_2022": (f"{C}/datastore/dump/55ead013-2331-4686-9895-9e8145b94189", "tor_votes"),
}
SCHEDULE_PKG = "city-council-and-committees-meeting-schedule-reports"
SINCE = "2018-12-01"

STREET_TYPES = {
    "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "BOULEVARD": "BLVD", "DRIVE": "DR",
    "CRESCENT": "CRES", "PLACE": "PL", "LANE": "LANE", "GARDENS": "GDNS", "COURT": "CRT",
    "SQUARE": "SQ", "TERRACE": "TER", "CIRCLE": "CIR", "PARKWAY": "PKWY", "GATE": "GATE",
    "TRAIL": "TRL", "HEIGHTS": "HTS", "GROVE": "GRV", "WAY": "WAY", "PARK": "PK",
    "CIRCUIT": "CRCT", "ROW": "ROW", "WALK": "WALK", "HILL": "HILL", "MEWS": "MEWS",
}
DIRS = {"EAST": "E", "WEST": "W", "NORTH": "N", "SOUTH": "S", "E": "E", "W": "W", "N": "N", "S": "S"}
TITLE_ADDR = re.compile(
    r"(\d+[A-Za-z]?(?:\s*(?:-|–|,|and|&|to)\s*\d+[A-Za-z]?)*)\s+"
    r"((?:[A-Z][\w'’.]*\s+){1,4}?)"
    r"(" + "|".join(t.title() for t in STREET_TYPES) + r")\b"
    r"(?:\s+(East|West|North|South))?")


# --------------------------------------------------------------------------

def rows(key: str) -> list[dict]:
    url, source = URLS[key]
    raw = fetch(url, source, VERSION)
    return list(csv.DictReader(io.StringIO(raw.read_bytes().decode("utf-8-sig"))))


def schedule_rows() -> list[dict]:
    meta = fetch(f"{C}/api/3/action/package_show?id={SCHEDULE_PKG}", "ckan_meta", VERSION)
    out = []
    for r in json.loads(meta.read_bytes())["result"]["resources"]:
        if r["name"] in ("meeting-schedule-all-committees-2018-2022.csv",
                         "meeting-schedule-all-committees-2022-2026.csv"):
            raw = fetch(r["url"], "tor_meetings", VERSION)
            for x in csv.DictReader(io.StringIO(raw.read_bytes().decode("utf-8-sig"))):
                row = {re.sub(r"[^a-z]", "", k.lower()): v for k, v in x.items()}
                row["mtgnum"] = row.get("mtgnum", row.get("mtg", ""))  # 'MTGNum' vs 'MTG #'
                out.append(row)
    return out


def name_key(name: str) -> str:
    s = re.sub(r"[.'’]", "", name.upper())
    s = re.sub(r"\bSAINT\b", "ST", s)
    return re.sub(r"\s+", " ", s).strip()


def numbers(num: str) -> set[str]:
    return {n.upper() for n in re.findall(r"\d+[A-Za-z]?", num or "")}


def app_address_keys(r: dict) -> set[tuple]:
    d = DIRS.get(r["STREET_DIRECTION"].strip().upper(), "")
    return {(n, name_key(r["STREET_NAME"]), d) for n in numbers(r["STREET_NUM"])}


def title_address_keys(title: str) -> set[tuple]:
    keys = set()
    for m in TITLE_ADDR.finditer(title):
        name = name_key(m.group(2))
        d = DIRS.get((m.group(4) or "").upper(), "")
        for n in numbers(m.group(1)):
            keys.add((n, name, d))
    return keys


def coa_decision(r: dict) -> str:
    d = (r.get("C_OF_A_DESCISION") or "").strip().lower()
    status = (r.get("STATUSDESC") or "").strip().lower()
    if d.startswith(("approved", "conditional")) or "condition" in d:
        return "approved"
    if d.startswith("refused"):
        return "refused"
    if d.startswith("withdrawn") or "withdrawn" in status:
        return "withdrawn"
    if d.startswith("deferred"):
        return "deferred"
    if "cancel" in status:
        return "cancelled"
    return "no decision recorded" if status == "closed" else "in progress"


def parse_vote_date(s: str) -> str | None:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s or "")
    return m.group(1) if m else None


# --------------------------------------------------------------------------

def build(ward: int) -> None:
    out_dir = REPO / "docs" / "ward-review" / f"ward-{ward:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    wards = {int(r["ward_number"]): r["ward_name"] for r in
             csv.DictReader((REPO / "db/seed/wards/wards.csv").open())}
    terms = [r for r in csv.DictReader((REPO / "db/seed/people/office_terms.csv").open())
             if r["office"] == "councillor" and r["ward_number"] == str(ward)]
    councillors = sorted(terms, key=lambda r: r["start_date"])

    # ---------------- Development applications ----------------
    dev = rows("devapps")
    apps: dict[str, dict] = {}
    for r in dev:
        if r["WARD_NUMBER"].strip().lstrip("0") != str(ward):
            continue
        a = apps.setdefault(r["APPLICATION#"], {
            "application": r["APPLICATION#"], "type": r["APPLICATION_TYPE"],
            "submitted": r["DATE_SUBMITTED"][:10], "status": r["STATUS"].strip(),
            "description": " ".join(r["DESCRIPTION"].split()), "addresses": [], "keys": set(),
            "parent": r.get("PARENT_FOLDER_NUMBER", "").strip()})
        a["addresses"].append(" ".join(x for x in (r["STREET_NUM"], r["STREET_NAME"].title(),
                                                     r["STREET_TYPE"].title(), r["STREET_DIRECTION"].strip()) if x.strip()))
        a["keys"] |= app_address_keys(r)
    pipe = {r["Application Number"].strip(): r for r in rows("pipeline")}

    # ---------------- Votes ----------------
    sched = schedule_rows()
    code_to_committee: dict[str, str] = {}
    vote_rows = []
    for term, key in (("2018-2022", "votes_2018"), ("2022-2026", "votes_2022")):
        for r in rows(key):
            r["term"] = term
            vote_rows.append(r)
            if r["Committee"] != "City Council":
                code = re.sub(r"\d", "", r["Agenda Item #"].split(".")[1])
                code_to_committee.setdefault(code, r["Committee"].strip())
    # Council-meeting item codes (CC = Council items, MM = member motions,
    # DM = delegated motions, BL = bills) are numbered by Council meeting.
    for code in ("CC", "MM", "DM", "BL"):
        code_to_committee[code] = "City Council"
    meeting_days: dict[tuple, list[str]] = defaultdict(list)
    for s_ in sched:
        meeting_days[(s_["term"], s_["committee"].strip(), s_["mtgnum"].strip())].append(s_["date"][:10])
    council_dates = sorted({s_["date"][:10] for s_ in sched if s_["committee"].strip() == "City Council"})

    def vote_date(r: dict) -> tuple[str, str]:
        """Date of a vote, and how we know it. Methods tested on 2022-26 votes
        with recorded dates: Council meeting number puts 100% of votes in the
        right meeting; 'next Council after the committee' 99% (misses are
        items deferred to a later meeting)."""
        d = parse_vote_date(r["Date/Time"])
        if d:
            return d, "recorded"
        m = re.match(r"\d{4}\.([A-Z]+)(\d+)\.", r["Agenda Item #"])
        if not m:
            return "", "unknown"
        committee = code_to_committee.get(m.group(1), "")
        days = sorted(set(meeting_days.get((r["term"], committee, m.group(2)), [])))
        if not days:
            return "", "unknown"
        if committee == "City Council" or r["Committee"].strip() == committee:
            span = days[0] if len(days) == 1 else f"{days[0]} to {days[-1]}"
            return days[0], f"meeting schedule ({span})"
        nxt = next((d for d in council_dates if d >= days[0]), "")
        return nxt, "estimated: next Council meeting (99% accurate in tests)"

    # Link agenda items to ward applications by address in the title.
    addr_index: dict[tuple, list[str]] = defaultdict(list)
    for a in apps.values():
        for k in a["keys"]:
            addr_index[k].append(a["application"])
    items: dict[str, dict] = {}
    for r in vote_rows:
        code = r["Agenda Item #"]
        if code not in items:
            keys = title_address_keys(r["Agenda Item Title"])
            linked = sorted({a for k in keys for a in addr_index.get(k, [])})
            items[code] = {"code": code, "title": r["Agenda Item Title"].strip(), "apps": linked, "votes": []}
        if items[code]["apps"]:
            items[code]["votes"].append(r)
    linked_items = [i for i in items.values() if i["apps"]]

    councillor_names = {c["person_name"] for c in councillors}
    vote_out = []
    for it in linked_items:
        motions: dict[tuple, dict] = {}
        for r in it["votes"]:
            d, basis = vote_date(r)
            k = (r["Committee"], r["Motion Type"], r["Vote Description"], r["Result"], r["Date/Time"])
            m = motions.setdefault(k, {"item": it["code"], "title": it["title"],
                                       "linked_applications": " ".join(it["apps"]),
                                       "body": r["Committee"], "motion": r["Motion Type"],
                                       "description": r["Vote Description"], "result": r["Result"],
                                       "date": d, "date_basis": basis, "ward_councillor_vote": "",
                                       "yes": 0, "no": 0, "absent": 0, "link_method": "address in title",
                                       "link_review": "needs review"})
            v = r["Vote"]
            m["yes" if v == "Yes" else "no" if v == "No" else "absent"] += 1
            if f"{r['First Name']} {r['Last Name']}" in councillor_names:
                m["ward_councillor_vote"] = v
        vote_out.extend(motions.values())
    vote_out.sort(key=lambda m: (m["date"] or "9999", m["item"]))

    # Per application: votes summary.
    app_votes: dict[str, list[dict]] = defaultdict(list)
    for m in vote_out:
        for a in m["linked_applications"].split():
            app_votes[a].append(m)

    # ---------------- Committee of Adjustment & TLAB ----------------
    coa = []
    seen = set()
    for r in rows("coa_active") + rows("coa_closed"):
        w = (r.get("WARD_NUMBER") or r.get("WARD") or "").strip().lstrip("0")
        key = r["SYS_ID"]
        if w != str(ward) or key in seen or r["IN_DATE"][:10] < SINCE:
            continue
        seen.add(key)
        coa.append({"file": r["REFERENCE_FILE#"].strip(), "type": r["APPLICATION_TYPE"],
                    "received": r["IN_DATE"][:10], "hearing": (r.get("HEARING_DATE") or "")[:10],
                    "address": " ".join(x for x in (r["STREET_NUM"], r["STREET_NAME"].title(),
                                                       r["STREET_TYPE"].title()) if x.strip()),
                    "keys": {(n, name_key(r["STREET_NAME"])) for n in numbers(r["STREET_NUM"])},
                    "decision": coa_decision(r),
                    "objection_recorded": (r.get("ANYONE_OBJECT_AT_MEETING") or "").strip()})
    coa_by_addr: dict[tuple, list[dict]] = defaultdict(list)
    for c in coa:
        for k in c["keys"]:
            coa_by_addr[k].append(c)
    tlab_out = []
    for t in rows("tlab"):
        m = re.match(r"(\S+)\s+(.*?)(?:\s+(?:" + "|".join(STREET_TYPES.values()) + r"))?(?:\s+[EWNS])?$",
                     t["FOLDERNAME"].strip().upper())
        if not m:
            continue
        cands = [c for n in numbers(m.group(1)) for c in coa_by_addr.get((n, name_key(m.group(2))), [])
                 if c["received"] <= t["INDATE"][:10]]
        if cands:
            c = max(cands, key=lambda c: c["received"])
            tlab_out.append({"tlab_file": t["FOLDERNUMBER"], "address": t["FOLDERNAME"].title(),
                             "appeal_received": t["INDATE"][:10], "final": (t["FINALDATE"] or "")[:10],
                             "status": t["STATUS"], "coa_file": c["file"], "coa_decision": c["decision"],
                             "link_method": "same address, appeal after C of A filing",
                             "link_review": "needs review"})

    # ---------------- Outputs ----------------
    since_apps = sorted((a for a in apps.values() if a["submitted"] >= SINCE),
                        key=lambda a: a["submitted"])
    write_csv(out_dir / "development_applications.csv",
              [{"application": a["application"], "type": a["type"], "submitted": a["submitted"],
                "status": a["status"], "addresses": "; ".join(sorted(set(a["addresses"]))),
                "proposed_units": pipe.get(a["application"], {}).get("Proposed Residential Units", ""),
                "linked_votes": len(app_votes.get(a["application"], [])),
                "description": a["description"]} for a in since_apps])
    write_csv(out_dir / "votes_linked_to_ward_applications.csv", vote_out)
    write_csv(out_dir / "committee_of_adjustment.csv",
              [{k: v for k, v in c.items() if k != "keys"} for c in coa])
    write_csv(out_dir / "tlab_appeals_linked.csv", tlab_out)

    md = render(ward, wards[ward], councillors, since_apps, pipe, app_votes, vote_out, coa, tlab_out)
    (out_dir / f"ward-{ward:02d}-check.md").write_text(md)
    pdf = markdown_to_pdf(md, out_dir / f"ward-{ward:02d}-check.pdf", f"Ward {ward} check pack")
    print(pdf)
    print(f"{len(since_apps)} applications since {SINCE}; {len(linked_items)} agenda items linked; "
          f"{len(vote_out)} recorded votes; {len(coa)} C of A files; {len(tlab_out)} TLAB appeals linked")


def write_csv(path: Path, rows_: list[dict]) -> None:
    if not rows_:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows_)


TYPE_WORDS = {"OZ": "Official Plan / rezoning", "SA": "Site plan", "CD": "Condominium",
              "SB": "Subdivision", "PL": "Part-lot control"}


def short(s: str, n: int = 110) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def render(ward, ward_name, councillors, apps, pipe, app_votes, votes, coa, tlab) -> str:
    L = [f"# Ward {ward} — {ward_name}: check pack", "",
         f"*Preview built {date.today().isoformat()} from City of Toronto open data. "
         "Please check it against what you know about the ward: missing projects, wrong "
         "statuses, or votes that don't look right are exactly what we need to hear about.*", "",
         "## Councillor", ""]
    for c in councillors:
        L.append(f"- {c['person_name']}: {c['start_date']} to {c['end_date']}")
    by_type = Counter(a["type"] for a in apps)
    oz = [a for a in apps if a["type"] == "OZ"]
    status = Counter(a["status"] for a in oz)
    units = {}
    for a in apps:
        p = pipe.get(a["application"])
        if p and p.get("Proposed Residential Units", "").strip().isdigit():
            units[a["application"]] = int(p["Proposed Residential Units"])
    L += ["", "## At a glance (applications filed since December 2018)", "",
          f"- **{len(apps)} development applications**: " +
          ", ".join(f"{n} {TYPE_WORDS.get(t, t).lower()}" for t, n in by_type.most_common()) + ".",
          f"- **{len(oz)} Official Plan / rezoning applications.** Status now: " +
          ", ".join(f"{n} {s.lower()}" for s, n in status.most_common()) + ".",
          f"- **{sum(units.values()):,} proposed homes** across the {len(units)} of these applications "
          "that appear in the City's development pipeline.",
          f"- **{len({v['item'] for v in votes})} Council or committee agenda items** name an address "
          f"from one of the ward's applications; they carry **{len(votes)} recorded votes**.",
          f"- **{len(coa)} Committee of Adjustment applications**; **{len(tlab)}** were followed by "
          "a TLAB appeal at the same address.", ""]

    L += ["## Official Plan and rezoning applications", "",
          "Newest first. The City's two datasets describe status differently: *application "
          "status* is from the development applications file, where \"Closed\" can mean approved, "
          "replaced by a revised application, or withdrawn; *pipeline status* is from the "
          "development pipeline (\"Active\" means approved and proceeding). Where they disagree, "
          "we don't yet know which is right. *Votes* counts recorded votes on agenda items naming "
          "the address; most planning items are decided without a recorded vote.", "",
          "| Filed | Address | Application status | Pipeline status | Homes | Votes | Councillor on main decision |",
          "|------|----------------|--------|--------|------|-----|--------------|"]
    for a in sorted(oz, key=lambda a: a["submitted"], reverse=True):
        vs = app_votes.get(a["application"], [])
        main = [v for v in vs if v["motion"] in ("Adopt Item", "Adopt Item as Amended")]
        pos = "; ".join(f"{v['ward_councillor_vote'] or 'n/a'} ({v['result']}, {v['date'] or 'date unknown'})"
                        for v in main[-2:]) or ("no main vote recorded" if vs else "")
        addr = "; ".join(sorted(set(a["addresses"])))
        pstat = pipe.get(a["application"], {}).get("Pipeline Status", "")
        status = a["status"] + (" (revision of an earlier file)" if a.get("parent") else "")
        L.append(f"| {a['submitted']} | {short(addr, 60)} | {status} | {pstat} | "
                 f"{units.get(a['application'], '')} | {len(vs) or ''} | {pos} |")

    L += ["", "## Recorded votes on agenda items about the ward's applications", "",
          "Each row is one recorded vote. Links are by address in the agenda title and "
          "**need review**; *date basis* says whether the date was recorded or reconstructed.", "",
          "| Date | Item | Motion | Result | Councillor | Date basis |",
          "|------|----------------|---------|------|------|------|"]
    for v in votes:
        L.append(f"| {v['date'] or '?'} | {v['item']}: {short(v['title'], 70)} | {v['motion']} | "
                 f"{v['result']} | {v['ward_councillor_vote'] or 'n/a'} | {v['date_basis']} |")

    dec = Counter(c["decision"] for c in coa)
    years = Counter(c["received"][:4] for c in coa)
    decided = dec["approved"] + dec["refused"]
    obj = Counter(c["objection_recorded"] or "blank" for c in coa)
    L += ["", "## Committee of Adjustment", "",
          f"- Applications received per year: " + ", ".join(f"{y}: {n}" for y, n in sorted(years.items())) + ".",
          f"- Outcomes: " + ", ".join(f"{n} {d}" for d, n in dec.most_common()) + ".",
          f"- Of those decided, **{dec['approved'] / decided:.0%} approved** "
          f"({dec['approved']} of {decided})." if decided else "",
          f"- \"Did anyone object at the hearing?\" is recorded as Yes for {obj['Yes']}, No for "
          f"{obj['No']}, and left blank for {obj['blank']} files.", "",
          "## TLAB appeals linked to the ward's Committee of Adjustment files", "",
          "| Appeal received | Address | TLAB status | C of A decision appealed |",
          "|------|----------------|------|------|"]
    for t in sorted(tlab, key=lambda t: t["appeal_received"], reverse=True):
        L.append(f"| {t['appeal_received']} | {t['address']} | {t['status']} | {t['coa_decision']} |")
    L += ["", "## Questions for you", "",
          "1. Are any significant projects in the ward missing from the rezoning table?",
          "2. Do the statuses match what you know (e.g. approved projects shown as still under review)?",
          "3. Do the councillor's recorded positions on major projects match your understanding?",
          "4. Anything in the votes table that clearly belongs to a different project at the same address?",
          "", "*Full linked records (for audit) are in the CSV files next to this report.*"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ward", type=int, required=True)
    build(ap.parse_args().ward)

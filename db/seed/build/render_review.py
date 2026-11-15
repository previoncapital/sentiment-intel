"""Render owner-facing review pages for the people and ward seed data.

Outputs:
  docs/seed-review/ward-map-2026-2030.png
  docs/seed-review/council-seats-2018-2030.md

Run after build_people_and_wards.py:
  uv run python db/seed/build/render_review.py
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from shapely.geometry import shape  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
import sys  # noqa: E402

sys.path.insert(0, str(REPO))
SEED = REPO / "db" / "seed"
OUT = REPO / "docs" / "seed-review"

NEW_TERM_START = "2026-11-15"
OLD_TERM_END = "2026-11-14"

BASIS_WORDS = {
    "statutory": "set by law",
    "official": "City record",
    "reported": "news report",
    "by_election_day": "by-election day",
    "first_council_meeting": "first Council meeting",
    "last_council_meeting_attended": "last meeting attended",
}
HOW_WORDS = {
    "general_election": "elected",
    "by_election": "won by-election",
    "appointed_by_council": "appointed by Council",
    "term_end": "term ended",
    "resigned": "resigned",
    "died": "died",
    "removed_from_office": "removed from office",
    "reinstated_by_court": "reinstated by court",
}


def rows(rel: str) -> list[dict]:
    with (SEED / rel).open() as fh:
        return list(csv.DictReader(fh))


def render_map(terms: list[dict]) -> Path:
    feats = json.loads((SEED / "wards" / "ward_map_2018.geojson").read_text())["features"]
    incoming = {int(r["ward_number"]): r["person_name"] for r in terms
                if r["start_date"] == NEW_TERM_START and r["office"] == "councillor"}
    outgoing = {int(r["ward_number"]): r["person_name"] for r in terms
                if r["end_date"] == OLD_TERM_END and r["office"] == "councillor"}
    changed = {w for w in incoming if incoming[w] != outgoing.get(w)}
    mayor = next(r["person_name"] for r in terms
                 if r["start_date"] == NEW_TERM_START and r["office"] == "mayor")

    fig, (ax, side) = plt.subplots(1, 2, figsize=(15, 9),
                                   gridspec_kw={"width_ratios": [2.1, 1]})
    k = math.cos(math.radians(43.7))  # keep Toronto's shape at this latitude
    for f in feats:
        w = f["properties"]["ward_number"]
        geom = shape(f["geometry"])
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for poly in polys:
            xs, ys = poly.exterior.xy
            ax.fill([x * k for x in xs], ys, facecolor="#f2b84b" if w in changed else "#dfe7ef",
                    edgecolor="#4a5a6a", linewidth=0.8)
        pt = geom.representative_point()
        ax.text(pt.x * k, pt.y, str(w), ha="center", va="center", fontsize=11, weight="bold",
                color="#1f2933")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Toronto's 25 wards (map in force since 2018)", fontsize=14, loc="left")
    ax.legend(handles=[Patch(facecolor="#f2b84b", edgecolor="#4a5a6a",
                             label="New councillor this term (7)"),
                       Patch(facecolor="#dfe7ef", edgecolor="#4a5a6a", label="Returning councillor")],
              loc="lower right", frameon=False, fontsize=10)

    side.axis("off")
    names = {f["properties"]["ward_number"]: f["properties"]["ward_name"] for f in feats}
    lines = [f"Council from Nov 15, 2026 — Mayor {mayor}", ""]
    side.text(0, 1, lines[0], fontsize=12, weight="bold", va="top", transform=side.transAxes)
    y = 0.95
    for w in range(1, 26):
        weight = "bold" if w in changed else "normal"
        side.text(0, y, f"{w:>2}  {names[w]}", fontsize=9.5, va="top", transform=side.transAxes)
        side.text(0.56, y, incoming[w], fontsize=9.5, va="top", weight=weight,
                  transform=side.transAxes)
        y -= 0.037
    side.text(0, y - 0.02, "Source: City of Toronto open data (City Wards; 2026 official results),\n"
              "cross-checked with the City Clerk's certified Declaration of Results.",
              fontsize=8, color="#52606d", va="top", transform=side.transAxes)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ward-map-2026-2030.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_table(terms: list[dict]) -> Path:
    wards = {int(r["ward_number"]): r["ward_name"] for r in rows("wards/wards.csv")}
    vac = rows("people/vacancies.csv")
    by_seat: dict[tuple, list[dict]] = defaultdict(list)
    for r in terms:
        by_seat[(r["office"], int(r["ward_number"] or 0))].append(r)

    def fmt(r: dict) -> str:
        start_note = HOW_WORDS.get(r["how_started"], r["how_started"])
        end_note = HOW_WORDS.get(r["how_ended"], r["how_ended"])
        s = f"**{r['person_name']}** — {r['start_date']} to {r['end_date']}"
        extras = []
        if r["how_started"] != "general_election":
            extras.append(f"{start_note} ({BASIS_WORDS.get(r['start_basis'], r['start_basis'])})")
        if r["how_ended"] != "term_end":
            extras.append(f"{end_note} ({BASIS_WORDS.get(r['end_basis'], r['end_basis'])}"
                          f"{', unconfirmed' if r['end_confidence'] == 'low' else ''})")
        return s + (f" · {'; '.join(extras)}" if extras else "")

    lines = [
        "# Who held each seat, December 2018 to 2030",
        "",
        "Built from the City's official election results, with every change between "
        "elections checked against City records and news coverage. Each change notes what "
        "its date is based on: *set by law*, *City record*, *news report*, or *first Council "
        "meeting* (the oath date for by-election winners, where no exact date was published).",
        "",
        "**Please check this against what you know.** Anything that looks wrong or "
        "missing is worth flagging.",
        "",
        "## Mayor",
        "",
    ]
    for r in sorted(by_seat[("mayor", 0)], key=lambda r: r["start_date"]):
        lines.append(f"- {fmt(r)}")
    lines += ["", "## Councillors by ward", ""]
    for w in range(1, 26):
        lines.append(f"### Ward {w} — {wards[w]}")
        lines.append("")
        for r in sorted(by_seat[("councillor", w)], key=lambda r: r["start_date"]):
            lines.append(f"- {fmt(r)}")
        lines.append("")
    lines += ["## Vacant periods", "", "| Seat | From | To (next filled) | After | Filled by |",
              "|---|---|---|---|---|"]
    for v in vac:
        lines.append(f"| {v['seat']} | {v['from']} | {v['to']} | {v['after']} | {v['filled_by']} |")
    lines += ["", "## Things that didn't add up, and what we found", "",
              "**1. Two appointed councillors are missing from the City's attendance records.** "
              "Robin Buxton Potts (Ward 13, appointed June 1, 2022) and Rose Milczyn (Ward 1, "
              "appointed August 15, 2022) voted at Council, but the City's attendance file never "
              "lists them. It isn't a spelling problem: after Joe Cressy and Kristyn Wong-Tam left "
              "in spring 2022, the number of members listed at each Council session fell from 26 "
              "to 24 and stayed there. Joe Mihevc, appointed the same day as Buxton Potts, was "
              "added; she and Milczyn never were. All four versions of the file the City "
              "publishes (including copies refreshed in February 2026) have the same gap, so it "
              "is in the City's source records, not one bad download. Why only these two is not "
              "something the data can tell us; it's a question for the City's open data team. "
              "*What it means for us:* attendance can't be used on its own to decide who was in "
              "office; we use election results and appointments instead.",
              "",
              "**2. Ward 22 changed hands five times in under a year, but no meeting was missed.** "
              "Jim Karygiannis was removed by the City Clerk on Nov 6, 2019 over campaign "
              "spending, put back by a judge on Nov 25, 2019, removed by the Court of Appeal on "
              "June 24, 2020, put back temporarily on about Aug 5, 2020 while he asked the Supreme "
              "Court to hear his case, and removed for good on Sept 24, 2020 when it declined. The "
              "attendance records look as if nothing happened in 2019 and he simply stopped coming "
              "in mid-2020. Both fit: no Council meeting fell inside either gap in which he was "
              "back in office.",
              "",
              "**3. Most 2018–2022 Council votes have no date.** In the City's voting file, 87% of "
              "rows for that term have a blank date. Committee votes all have dates; full Council "
              "votes have them only for April to November 2020, the first months of virtual "
              "meetings. The pattern points to how votes were recorded at Council, not to "
              "missing votes. The dates can be filled back in from the City's meeting schedule. "
              "From November 2022 on, every Council vote carries the exact time it was taken.",
              "",
              "**4. Agenda codes don't use the calendar year.** Items at the first meetings of a "
              "new Council (e.g. November and December 2022) are coded with the next year "
              "(\"2023.…\"). Anything matching votes to dates must use the meeting date.",
              "",
              "**5. \"When did they start?\" has more than one answer.** The 2018 Council's term "
              "legally began December 1, 2018, but members took their oath at the first meeting on "
              "December 4. By-election winners are declared by the Clerk a day or two after the "
              "vote and take the oath at the next Council meeting; we use the oath date (or, "
              "where only that is known, the first meeting attended) and say which.",
              "",
              "**Still unconfirmed:** the exact oath dates for Parthi Kandavel (Ward 20, 2023) "
              "and Neethan Shan (Ward 25, 2025), and the date of the August 2020 court stay. "
              "These would come from Council minutes once we can read the City's agenda site.",
              ""]
    path = OUT / "council-seats-2018-2030.md"
    path.write_text("\n".join(lines))
    return path


def render_pdf(md_path: Path, map_path: Path) -> Path:
    """Owner-facing PDF of the seat history, with the ward map on top."""
    from tools.owner_pdf import markdown_to_pdf

    md = md_path.read_text().replace(
        "## Mayor", f"![Ward map]({map_path.resolve().as_uri()})\n\n## Mayor", 1)
    return markdown_to_pdf(md, md_path.with_suffix(".pdf"), "Council seats 2018-2030")


if __name__ == "__main__":
    t = rows("people/office_terms.csv")
    m = render_map(t)
    md = render_table(t)
    print(m, md, render_pdf(md, m), sep="\n")

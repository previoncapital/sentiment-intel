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
SEED = REPO / "db" / "seed"
OUT = REPO / "docs" / "seed-review"

NEW_TERM_START = "2026-11-15"
OLD_TERM_END = "2026-11-14"

BASIS_WORDS = {
    "statutory": "set by law",
    "official": "City record",
    "reported": "news report",
    "by_election_day": "by-election day",
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
        "Built from the City's official election results, with mid-term changes "
        "checked against City records and news coverage "
        "(`db/seed/curated/council_changes_2018_2030.yaml`). Each change notes what "
        "its date is based on: *set by law*, *City record*, *news report*, "
        "*by-election day* (swearing-in date not found), or *last meeting attended*.",
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
    lines += ["", "## Data issues found while building this", "",
              "- The City's **Council attendance dataset leaves out two appointed councillors** "
              "(Robin Buxton Potts, Ward 13; Rose Milczyn, Ward 1, both 2022), although both appear "
              "in the voting records.",
              "- **Jim Karygiannis's end date (Ward 22, 2020) is unconfirmed**: removal went back "
              "and forth in the courts between November 2019 and 2020. The date shown is his last "
              "Council meeting.",
              "- The 2018–2022 term start (December 1, 2018) is taken from the election law of the "
              "time and still needs a City record to confirm it.",
              "- Agenda item codes are numbered by **council year, not calendar year**: the first "
              "meeting of the 2022–26 term (November 2022) has items coded `2023.…`. Linking must "
              "use the meeting date, not the year in the code.",
              ""]
    path = OUT / "council-seats-2018-2030.md"
    path.write_text("\n".join(lines))
    return path


if __name__ == "__main__":
    t = rows("people/office_terms.csv")
    print(render_map(t))
    print(render_table(t))

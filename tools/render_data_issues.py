"""Render the data issues register (docs/data-issues/data_issues.yaml) for the
owner as Markdown and PDF.

Run:  uv run python tools/render_data_issues.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.owner_pdf import markdown_to_pdf  # noqa: E402

SRC = REPO / "docs" / "data-issues" / "data_issues.yaml"
STATUS = {"open": "Open", "workaround_in_place": "Worked around (still open at source)",
          "resolved": "Resolved", "wont_fix": "Won't fix"}
KIND = {"data_error": "Error in the source data", "missing_data": "Missing data",
        "access": "Access problem", "source_quirk": "Quirk to handle",
        "unconfirmed_fact": "Not yet confirmed", "spec_correction": "Correction to our spec",
        "licensing_privacy": "Licensing or privacy"}
SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


def render() -> Path:
    issues = yaml.safe_load(SRC.read_text())["issues"]
    issues.sort(key=lambda i: (i["status"] == "resolved", SEV_ORDER[i["severity"]], i["id"]))
    status_counts = Counter(i["status"] for i in issues)
    lines = ["# Data issues log", "",
             "Every discrepancy, gap or unconfirmed fact we find in a source, with what we're "
             "doing about it now and who could fix it. Updated as issues are found or resolved.",
             "",
             "**Summary:** " + ", ".join(f"{n} {STATUS[s].split(' (')[0].lower()}"
                                         for s, n in status_counts.items()) +
             f" — {len(issues)} in total.", "",
             "| ID | Issue | Severity | Status | Who can fix it |",
             "|----|------------------------|------|----------|----------|"]
    for i in issues:
        lines.append(f"| {i['id']} | {i['title']} | {i['severity']} | "
                     f"{STATUS[i['status']]} | {i['resolver']} |")
    lines += ["", "## Details", ""]
    for i in issues:
        lines += [f"### {i['id']} — {i['title']}", "",
                  f"*{KIND[i['kind']]} · severity {i['severity']} · {STATUS[i['status']]} · "
                  f"found {i['found']}*", "",
                  f"- **What's wrong:** {i['description']}",
                  f"- **Evidence:** {i['evidence']}",
                  f"- **Why it matters:** {i['impact']}",
                  f"- **What we do meanwhile:** {i['workaround']}",
                  f"- **Who can fix it:** {i['resolver']}",
                  f"- **Next step:** {i['next_action']}"]
        if i.get("resolution"):
            lines.append(f"- **Resolution:** {i['resolution']}")
        lines.append("")
    md_path = SRC.with_name("data-issues-log.md")
    md_path.write_text("\n".join(lines))
    return markdown_to_pdf(md_path.read_text(), md_path.with_suffix(".pdf"), "Data issues log")


if __name__ == "__main__":
    print(render())

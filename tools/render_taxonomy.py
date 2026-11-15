"""Render the issue taxonomy as a PDF for owner / planning-advisor review.

Run:  uv run python tools/render_taxonomy.py
"""

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.owner_pdf import markdown_to_pdf  # noqa: E402

SRC = REPO / "taxonomy" / "issues_v0.yaml"
OUT = REPO / "docs" / "taxonomy"


def render() -> Path:
    t = yaml.safe_load(SRC.read_text())
    n = sum(len(d["issues"]) for d in t["domains"])
    L = [f"# Issue categories, version {t['version']} (draft)", "",
         f"{len(t['domains'])} domains, {n} issues. Every vote, motion, report passage, letter "
         "or statement can be tagged with any of these, plus a stance, who said it, and how "
         "strong the evidence is. **Pro-housing side** records which side adds housing supply; "
         "it drives the \"support rate\" in councillor profiles and is a judgement for you to "
         "confirm. Blank means there's no clear pro-housing side.", "",
         "Not yet tested: the plan calls for testing on 200-300 real Council items before "
         "fixing it.", ""]
    names = {i["code"]: i["label"] for d in t["domains"] for i in d["issues"]}
    names.update({d["code"]: d["label"] for d in t["domains"]})

    def plain(text: str) -> str:
        import re
        return re.sub(r"->\s*([A-Z]{2}(?:\.[A-Z_]+)?)", lambda m: "→ " + names.get(m.group(1), m.group(1)), text)

    for d in t["domains"]:
        L += [f"## {d['label']}", "", d["definition"], "",
              "| Issue | What counts | Not this (goes elsewhere) | Pro-housing side |",
              "|--------|----------------------|--------------|--------|"]
        for i in d["issues"]:
            inc = i["definition"] + (" E.g. " + "; ".join(i["includes"]) + "." if i.get("includes") else "")
            exc = plain("; ".join(i.get("excludes", [])))
            L.append(f"| **{i['label']}** | {inc} | {exc} | {i.get('supply_direction', '')} |")
        L.append("")
    L += ["## Recorded with every tag", "",
          "**Stance:** " + "; ".join(f"*{s['code']}* — {s['definition']}" for s in t["stance"]), "",
          "**Who:** " + ", ".join(a["code"].replace("_", " ") for a in t["actor_class"]) +
          " (individual residents are counted in aggregate only, never named).", "",
          "**Strength of evidence, strongest first:** recorded vote, moving or seconding a motion, "
          "a public statement (debate, letter or deputation), a mention.", "",
          "## Questions for you", ""]
    L += [f"{k + 1}. {q}" for k, q in enumerate(t["open_questions_for_owner"])]
    OUT.mkdir(parents=True, exist_ok=True)
    return markdown_to_pdf("\n".join(L) + "\n", OUT / "issue-categories-v0.pdf", "Issue categories v0")


if __name__ == "__main__":
    print(render())

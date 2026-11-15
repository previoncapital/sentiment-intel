"""The issue taxonomy must be internally consistent."""

import re
from pathlib import Path

import yaml

TAX = Path(__file__).resolve().parents[1] / "taxonomy" / "issues_v0.yaml"


def load():
    return yaml.safe_load(TAX.read_text())


def test_codes_unique_and_prefixed_by_domain():
    t = load()
    codes = []
    for d in t["domains"]:
        for i in d["issues"]:
            assert i["code"].startswith(d["code"] + "."), i["code"]
            assert i["label"] and i["definition"], i["code"]
            codes.append(i["code"])
    assert len(codes) == len(set(codes))
    assert len(t["domains"]) == 8 and 35 <= len(codes) <= 50


def test_cross_references_point_to_real_issues():
    t = load()
    codes = {i["code"] for d in t["domains"] for i in d["issues"]}
    for d in t["domains"]:
        for i in d["issues"]:
            for note in i.get("excludes", []):
                for ref in re.findall(r"->\s*([A-Z]{2}(?:\.[A-Z_]+)?)", note):
                    assert ref in codes or ref in {d2["code"] for d2 in t["domains"]}, (i["code"], ref)


def test_attribute_lists_present():
    t = load()
    assert {s["code"] for s in t["stance"]} == {"supports", "opposes", "conditional", "neutral", "procedural"}
    assert [s["rank"] for s in t["strength"]] == [1, 2, 3, 4]
    assert any(a["code"] == "individual_resident" for a in t["actor_class"])

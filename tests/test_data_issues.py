"""The data issues register must stay complete and well-formed."""

from pathlib import Path

import yaml

REG = Path(__file__).resolve().parents[1] / "docs" / "data-issues" / "data_issues.yaml"
REQUIRED = {"id", "title", "source", "found", "kind", "severity", "description", "evidence",
            "impact", "workaround", "status", "resolver", "next_action"}


def test_register_is_well_formed():
    issues = yaml.safe_load(REG.read_text())["issues"]
    ids = [i["id"] for i in issues]
    assert len(ids) == len(set(ids)), "duplicate issue IDs"
    for i in issues:
        assert REQUIRED <= i.keys(), (i.get("id"), REQUIRED - i.keys())
        assert i["severity"] in {"high", "medium", "low"}
        assert i["status"] in {"open", "workaround_in_place", "resolved", "wont_fix"}
        assert i["kind"] in {"data_error", "missing_data", "access", "source_quirk",
                             "unconfirmed_fact", "spec_correction", "licensing_privacy"}
        if i["status"] == "resolved":
            assert i.get("resolution"), f"{i['id']} resolved without a resolution note"

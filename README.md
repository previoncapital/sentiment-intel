# sentiment-intel

Phase 1 data platform for Toronto housing and land-development political
intelligence.

**Status:** Milestone M0 in progress — ward map and council seed data built.

- Start here: [`CLAUDE.md`](CLAUDE.md) (working agreements)
- Plan (what and why): [`docs/phase1-plan.md`](docs/phase1-plan.md)
- Technical spec (how): [`docs/technical-spec.md`](docs/technical-spec.md)
- Source registry: [`docs/source-registry.md`](docs/source-registry.md)
- Decisions log: [`docs/decisions/`](docs/decisions/)
- Setup for the owner: [`docs/setup/`](docs/setup/)
- Review pages for the owner: [`docs/seed-review/`](docs/seed-review/)

## Rebuilding the seed data

```bash
uv run python db/seed/build/build_people_and_wards.py
```

```bash
uv run python db/seed/build/render_review.py
```

```bash
uv run --group dev pytest
```

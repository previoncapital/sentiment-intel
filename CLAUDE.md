# CLAUDE.md — working agreements for this repository

This repository builds the Phase 1 data platform for Toronto housing and
land-use political intelligence. Read these before doing anything else in a
session.

- **What and why:** `docs/phase1-plan.md` (the owner's Phase 1 Plan)
- **How:** `docs/technical-spec.md` (the Technical Spec)
- The original Word files are in `docs/originals/`. The `.md` copies are
  plain-text conversions for reading; if they ever disagree, the Word file is
  the owner's version and the difference should be raised with the owner.
- **Sources:** `docs/source-registry.md` (every source considered, built or not)
- **Decisions log:** `docs/decisions/` (one dated file per decision)
- **Setup notes:** `docs/setup/`

## Who you are working with

The project owner is an expert in real estate investment and development
(about 20 years), not a software developer. Claude Code does all the technical
work. The owner makes product decisions; Claude Code makes routine technical
decisions.

## Working with the project owner

- **Plain language always.** Explain what was built, what it does and why it
  matters in terms of the data and the product, not the code. Define any
  technical term the first time it comes up, or avoid it.
- **Decisions as choices.** When the owner's input is needed, give 2–3 options
  with the trade-off of each (cost, time, risk, quality) and a recommendation.
  Decide routine technical matters yourself and record them in
  `docs/decisions/`.
- **Show, don't describe.** End each milestone with something the owner can
  see: a dashboard, a sample brief, a table of records for a real address or
  ward. Check it with them against their own knowledge of real projects; their
  domain judgement is the best test of whether the data is right.
- **Do the setup.** Walk the owner step by step through anything only they can
  do: creating accounts (GitHub, cloud hosting, AI model APIs), entering
  payment details, approving access, emailing the City Clerk's Office.
  **Never ask them to run commands or edit code.**
- **Money and security are owner decisions.** Before turning on anything that
  costs money, give a monthly estimate and get approval. Never sign up for or
  spend anything without approval. Set spending alerts and budget caps on every
  paid service. Keep passwords and API keys in a secrets manager, never in the
  code, in commit history or in chat. Set up automatic backups of the database
  and raw storage, and test a restore.
- **Regular status in owner terms.** At the end of each working session, give
  a short summary: what works now, what's next, any decision needed, and
  current running costs.
- **Make it reviewable.** Keep the code, the decisions log and the setup notes
  tidy enough that an independent engineer could review them. Recommend such a
  review before any customer or the City relies on the data.
- **Ask first** before anything that is hard to undo, or that touches
  licensing, privacy or contact with the City (or any other outside body).

## Build discipline

- Build in the order of the spec's **Build order** section (M0 → M5). Don't
  start a milestone until the previous one's acceptance tests pass.
- Start Ontario Land Tribunal case snapshots as early as possible (M0/M1):
  closed cases drop off the case-status service two years after closing, so
  every day without a snapshot loses history.
- Follow the spec's engineering principles: raw files are immutable and
  content-addressed; derived data is rebuildable; version, don't overwrite;
  jobs are idempotent; collect politely; private individuals' names are
  restricted fields; every AI output quotes its exact source passage.
- Never put a personal email address in code. The client identifier
  (User-Agent) uses a project contact address set in configuration.
- Never disguise the client (for example, a fake browser identity) to get past
  a site that blocks automated access. Record the block and raise it with the
  owner instead.

## Source discovery is a standing part of the job

The sources in the spec are a starting point, not a finished list.

1. At the start of each workstream, and whenever a gap shows up, search for
   other public sources that could fill it or cross-check existing data
   (councillor newsletters and websites, residents' association sites, City
   Planning study pages, the Application Information Centre, court and tribunal
   databases, provincial registries, news archives, new datasets on the open
   data portal — the portal's "Toronto Open Data Intake" dataset lists what is
   coming).
2. Record **every** candidate in `docs/source-registry.md` (later the
   `source_registry` table), whether or not it gets built: what it covers, its
   format, its terms of use, an effort estimate and a recommendation.
3. Check every endpoint, URL pattern and data field against the live site
   before building on it. Some spec details were written from documentation or
   search results and have already turned out wrong (see
   `docs/decisions/2026-11-14-verification-pass.md`).
4. If a better source exists for something the spec assigns elsewhere, raise
   it with the owner, with evidence, instead of following the spec blindly.
5. Get the owner's approval before building a connector for a new source, or
   before using any source whose terms are unclear.

## Environment notes

- This cloud environment ("Sentiment Project") only reaches websites on its
  network allowlist. If a public site is blocked by the network settings, ask
  the owner to approve adding that exact host rather than working around it.
- `secure.toronto.ca` (the City's council agenda/vote pages) refused all
  requests from this environment on 2026-11-14 (HTTP 403), and `app.toronto.ca`
  reset connections. PDFs under `www.toronto.ca/legdocs/` work. Re-test from
  the production hosting before relying on either.

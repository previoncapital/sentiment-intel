# Technical Spec — Toronto Housing Political Intelligence Platform (Phase 1)

Nov 13, 2026 · @Kiel O'Sullivan

## Purpose and how to use this spec

This spec tells Claude Code how to build the Phase 1 data platform. It
collects, archives, links and tags every public record of housing and
land-use decisions in the City of Toronto, from December 2018 onward. It
covers each forum a project passes through, including appeals to the
Ontario Land Tribunal (OLT) and the Divisional Court. The companion
document, the [Phase 1
Plan](https://claude.ai/artifact/YUi9Pt51hfmNdpHYjic7oE), covers the
what and why: scope, issue taxonomy, signals, roadmap and risks. This
spec covers the how.

**Sources are a starting point, not a finished list.** The connectors in
this spec are the sources known when it was written. Treat finding more
as a standing part of the job:

- At the start of each workstream, and whenever a gap shows up, search
  for other public sources that could fill it or cross-check existing
  data. Examples: council members' newsletters and websites, residents'
  association sites, City Planning study pages, the Application
  Information Centre, court and tribunal databases, provincial
  registries, news archives, and datasets added to the open data portal.

- Record every candidate source in the source registry (see Source
  connectors), whether or not it gets built. Include what it covers, its
  format, its terms of use and a recommendation.

- Check every endpoint, URL pattern and data field in this spec against
  the live site before building on it. Some are written from
  documentation or search results, not tested.

- If a better source exists for something this spec assigns to another
  source, raise it with the project owner, with evidence, instead of
  following the spec blindly.

**Working agreements:**

- Build in the order of the Build order section. Each milestone ends
  with its acceptance tests passing.

- Ask the project owner before anything that is hard to undo, or that
  touches licensing, privacy or contact with the City.

## Working with the project owner

The project owner is an expert in real estate investment and
development, not a software developer. Claude Code does all the
technical work and explains it in plain language. The owner makes
product decisions; Claude Code makes routine technical decisions.

- **Plain language always.** Explain what was built, what it does and
  why it matters in terms of the data and the product, not the code.
  Define any technical term the first time it comes up, or avoid it.

- **Decisions as choices.** When the owner's input is needed, give 2–3
  options with the trade-off of each (cost, time, risk, quality) and a
  recommendation. Decide routine technical matters yourself and record
  them in the decisions log.

- **Show, don't describe.** End each milestone with something the owner
  can see: a dashboard, a sample brief, a table of records for a real
  address or ward. Check it with them against their own knowledge of
  real projects; their domain judgement is the best test of whether the
  data is right.

- **Do the setup.** Walk the owner step by step through anything only
  they can do: creating accounts (GitHub, cloud hosting, AI model APIs),
  entering payment details, approving access, emailing the City Clerk's
  Office. Never ask them to run commands or edit code.

- **Money and security are owner decisions.** Before turning on anything
  that costs money, give a monthly estimate and get approval. Set
  spending alerts and budget caps on every paid service. Keep passwords
  and API keys in a secrets manager, never in the code or in chat. Set
  up automatic backups of the database and raw storage, and test a
  restore.

- **Regular status in owner terms.** At the end of each working session,
  give a short summary: what works now, what's next, any decision
  needed, and current running costs.

- **Make it reviewable.** Keep the code, the decisions log and the setup
  notes tidy enough that an independent engineer could review them.
  Recommend such a review before any customer or the City relies on the
  data.

## Engineering principles

Every fact in the database must trace back to an unchanged source file.
Everything below follows from that rule.

1.  **Raw is immutable.** Every fetched file (CSV, JSON, HTML page, PDF,
    video, audio) is stored once, content-addressed by SHA-256, with its
    URL, fetch time, HTTP headers and connector version. Never overwrite
    it. A changed page is a new raw file.

2.  **Derived data is rebuildable.** Parsed rows, links and tags can be
    regenerated from raw files plus code. Every derived row records
    which raw file and which pipeline version produced it.

3.  **Versioning, not overwriting.** Records that change (application
    status, a case's hearing events, a councillor's role) keep a dated
    history with valid_from and valid_to, so any report can be rebuilt
    as of any date.

4.  **Idempotent jobs.** Re-running a connector or pipeline step for the
    same window produces no duplicates and no lost changes.

5.  **Polite collection.** Respect robots.txt and terms of use,
    rate-limit, identify the client in the User-Agent with a project
    contact address set in configuration (never a personal email in
    code), and prefer official bulk files and APIs to scraping.

6.  **Privacy by design.** Treat names of private individuals in
    letters, deputations and transcripts as restricted fields: stored
    with the raw record, never exposed in search or reports. Analytics
    use counts and aggregates. Public officials, applicants and
    organizations are not restricted.

7.  **Every AI output is grounded.** Tags, summaries and stances store
    the exact source passage (document and character or time range), the
    model and prompt version, and a confidence score. Untraceable
    outputs are discarded.

8.  **Measure quality continuously.** Each pipeline stage has a
    hand-labelled sample and a tracked accuracy metric (see
    Orchestration, monitoring and data quality).

## Stack and repository layout

Use boring, well-supported tools: Python for pipelines and PostgreSQL as
the single system of record. These are recommendations. Propose
alternatives with reasons if something fits better.

| Layer                 | Choice                                                                       | Notes                                                                      |
|-----------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Language              | Python 3.12+                                                                 | Type hints, uv or Poetry for dependencies                                  |
| Database              | PostgreSQL 16 + PostGIS + pgvector                                           | One database for records, geography and search                             |
| Raw storage           | S3-compatible object storage                                                 | Bucket layout raw/\<source\>/\<yyyy\>/\<mm\>/\<sha256\>.\<ext\>            |
| Orchestration         | Dagster (or Airflow)                                                         | One asset or job per connector and pipeline stage; schedules and backfills |
| Fetching              | httpx, Playwright for JavaScript-rendered pages                              | Retries, backoff, rate limits per domain                                   |
| PDF and HTML parsing  | pdfplumber or PyMuPDF, OCR fallback; selectolax or BeautifulSoup             | Keep page numbers and character offsets                                    |
| Transcription         | Open-source speech-to-text (Whisper-family) + speaker diarization (pyannote) | GPU workers on demand                                                      |
| AI tagging            | An LLM API behind one internal interface                                     | Model and prompt versions logged per output                                |
| Migrations and models | Alembic + SQLAlchemy                                                         | Schema changes only through migrations                                     |
| Tests                 | pytest, saved fixtures of real pages                                         | Connectors tested against stored copies, not live sites                    |
| Internal app          | A simple web app (for example FastAPI with a lightweight front end)          | Review queues, corrections, quality dashboards                             |

repo/  
docs/ spec, plan export, source registry notes, decisions log  
connectors/ one package per source: fetch.py, parse.py, schema.py,
fixtures/  
pipelines/ linking, document processing, tagging, transcription,
signals  
db/ models, migrations, seed data (wards, taxonomy)  
taxonomy/ issue taxonomy YAML, versioned  
quality/ labelled samples, evaluation scripts, metrics  
orchestration/ Dagster definitions, schedules, sensors  
app/ internal review and reporting app  
tests/

## Database schema

The schema has five groups of tables: provenance, people and places,
proceedings, content, and evidence. The tables below are the minimum.
Add columns as sources require, but keep the keys and the provenance
columns (raw_file_id, pipeline_version, valid_from, valid_to) on every
derived table.

| Group             | Table                                                 | Purpose                                                                                                                                                       | Key columns                                                                                                                                           |
|-------------------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Provenance        | source_registry                                       | Every known or candidate source, built or not                                                                                                                 | slug, owner, url, coverage, format, terms_of_use, status (candidate, approved, built, rejected), notes                                                |
| Provenance        | fetch_run                                             | One run of one connector                                                                                                                                      | source_slug, started_at, finished_at, status, counts, connector_version                                                                               |
| Provenance        | raw_file                                              | Unchanged fetched bytes                                                                                                                                       | sha256, source_slug, url, fetched_at, http_headers, storage_path, mime_type                                                                           |
| People and places | person, person_alias                                  | Officials, candidates, staff, applicants' representatives                                                                                                     | person_id, canonical_name; alias, alias_source                                                                                                        |
| People and places | office_term                                           | Who held which seat when                                                                                                                                      | person_id, office (mayor, councillor), ward_id, start_date, end_date                                                                                  |
| People and places | organization                                          | Developers, residents' associations, lobbying firms, advocacy groups                                                                                          | org_id, name, type, aliases                                                                                                                           |
| People and places | ward_map, ward                                        | Versioned ward boundaries                                                                                                                                     | map_version, valid_from, valid_to; ward_id, number, name, geom                                                                                        |
| People and places | address_point                                         | Geocodable addresses                                                                                                                                          | address_id, full_address, geom, source                                                                                                                |
| Proceedings       | body                                                  | Every forum: Council, committees, community councils, Committee of Adjustment panels, TLAB, Design Review Panel, consultation meetings, OLT, Divisional Court | body_id, name, level (city, province, court), type                                                                                                    |
| Proceedings       | meeting                                               | Any meeting, hearing or hearing event                                                                                                                         | meeting_id, body_id, meeting_type, scheduled_start, actual_start, actual_end, venue, format, notice_date, external_ref                                |
| Proceedings       | agenda_item                                           | An item at a meeting                                                                                                                                          | item_id, meeting_id, item_code (such as 2025.PH22.3), title, position, time_reached                                                                   |
| Proceedings       | motion, vote                                          | Motions and each member's vote                                                                                                                                | motion_id, item_id, mover_id, seconder_id, result; motion_id, person_id, value                                                                        |
| Proceedings       | application, application_event                        | Development and Committee of Adjustment applications and their lifecycle                                                                                      | application_number, type, address_id, ward_id; event_type, event_date, result, meeting_id or proceeding_id                                            |
| Proceedings       | proceeding, proceeding_party                          | TLAB, OLT, review and court cases                                                                                                                             | case_number, forum, appellant_type, application_number, city_position (dated history), outcome; party, role                                           |
| Proceedings       | lobbying_communication, contribution, election_result | Registry, campaign finance, election results                                                                                                                  | standard fields from each source plus person and organization links                                                                                   |
| Content           | document                                              | Staff reports, letters, decisions, minutes, notices                                                                                                           | document_id, raw_file_id, doc_type, item_id, application_number, case_number, author_class (official, applicant, organization, private individual)    |
| Content           | passage                                               | Addressable spans of text                                                                                                                                     | passage_id, document_id or transcript_id, char_start and char_end or t_start and t_end, text, embedding                                               |
| Content           | media_asset, transcript_segment                       | Video and audio; transcribed speech                                                                                                                           | asset_id, meeting_id, url, duration; segment_id, t_start, t_end, speaker_label, person_id, text, asr_confidence                                       |
| Content           | recording_quality                                     | Per-meeting quality metrics                                                                                                                                   | meeting_id, venue, word_error_rate_sample, speaker_error_rate, unattributed_share, overlap_share, loudness, snr, dropouts, missing_flag               |
| Evidence          | taxonomy_issue                                        | Issue taxonomy, versioned                                                                                                                                     | code, parent_code, label, version                                                                                                                     |
| Evidence          | tag                                                   | Grounded evidence on a passage, vote or motion                                                                                                                | tag_id, target (passage, vote, motion), issue_code, stance, actor_class, actor_id, strength, confidence, model_version, prompt_version, review_status |
| Evidence          | context_event                                         | Provincial laws, regulations, Minister's Zoning Orders, policy changes                                                                                        | event_id, type, date_in_force, description, affected issues, affected areas                                                                           |

Private individuals' names live only in restricted columns on document
and transcript_segment, with access limited to the review app.

## Source connectors

Phase 1 starts with 17 known sources. Every location below must be
checked against the live site before building, and the list should grow
through the discovery process at the end of this section. Each connector
is a package with fetch (writes raw files), parse (raw to staging rows)
and fixtures for tests.

| Connector            | Location (verify)                                                                                                                                                                                                                                                              | Method                                                                 | Cadence                                       | Joins on                                              | Quirks                                                                                                  |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|-----------------------------------------------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| tor_votes            | open.toronto.ca dataset "Members of Toronto City Council – Voting Record"                                                                                                                                                                                                      | Open data portal API (CKAN), CSV or JSON                               | Daily check                                   | Agenda item code, member name                         | Votes by show of hands are missing; names need matching to person                                       |
| tor_dev_apps         | open.toronto.ca "Development Applications"                                                                                                                                                                                                                                     | CKAN API                                                               | Daily                                         | Application number, address                           | Records from 2021; earlier applications come from TMMIS and the Application Information Centre          |
| tor_coa              | open.toronto.ca "Committee of Adjustment Applications"                                                                                                                                                                                                                         | CKAN API                                                               | Daily                                         | Application number, address                           | Decisions need linking to decision documents                                                            |
| tor_pipeline_permits | open.toronto.ca "Development Pipeline", building permits                                                                                                                                                                                                                       | CKAN API                                                               | Monthly or quarterly                          | Address, application number                           | Outcome context, not political signal                                                                   |
| tor_geo              | open.toronto.ca ward boundaries (current and 2018 map), address points                                                                                                                                                                                                         | CKAN API, shapefile or GeoJSON                                         | On change                                     | Geometry                                              | Keep every boundary version                                                                             |
| tor_lobbyist         | open.toronto.ca lobbyist registry dataset; Lobbyist Registry disclosure site                                                                                                                                                                                                   | CKAN API                                                               | Daily                                         | Councillor name, client, subject                      | Subject matter is free text                                                                             |
| tor_elections        | open.toronto.ca campaign contributions, results, voter statistics                                                                                                                                                                                                              | CKAN API, spreadsheets                                                 | Per election                                  | Candidate, ward, poll                                 | Donor name matching is error-prone                                                                      |
| tmmis                | app.toronto.ca/tmmis (meetings, agendas, item history: viewAgendaItemHistory.do?item=\<code\>), secure.toronto.ca/council (agenda-item.do?item=\<code\>), PDFs under toronto.ca/legdocs/mmis/\<year\>/\<committee\>/ (bgrd/backgroundfile-N.pdf, comm/communicationfile-N.pdf) | Scrape HTML; download PDFs                                             | Daily during meeting cycles; backfill to 2018 | Item code, application number in text, ward           | The item code is the master key; communications contain private individuals' names                      |
| tor_video            | City Clerk's YouTube channel; post-meeting video indexes                                                                                                                                                                                                                       | YouTube Data API for metadata; media download pending licensing answer | After each meeting                            | Meeting date and body; index timestamps to item codes | Some archives go missing; confirm terms with the Clerk before bulk download                             |
| tor_drp              | City Planning Design Review Panel page; minutes PDFs on toronto.ca                                                                                                                                                                                                             | Scrape listing, download PDFs                                          | Monthly                                       | Address, developer, application type                  | Summaries, not verbatim; pre-application reviews held in camera                                         |
| tor_consultations    | City Planning consultations page; haveyoursay.toronto.ca project pages; councillors' event pages                                                                                                                                                                               | Scrape and snapshot notices; collect recordings where posted           | Daily                                         | Address, application number                           | Notices vanish after the event, so snapshot when first seen                                             |
| tor_aic              | Application Information Centre                                                                                                                                                                                                                                                 | Scrape application pages and document lists                            | Weekly, plus on new application               | Application number                                    | Large plan sets; store metadata and key reports, fetch drawings on demand                               |
| tor_tlab             | Toronto Local Appeal Body decisions                                                                                                                                                                                                                                            | Scrape decisions                                                       | Weekly                                        | Committee of Adjustment file number, address          | Third-party appeal rights narrowed since 2022                                                           |
| olt_cases            | olt.gov.on.ca/case-status (search by municipality, address, case number)                                                                                                                                                                                                       | Scrape, snapshot each case                                             | Daily                                         | Municipal file number, address, case number           | No hearing transcripts; closed cases removed after two years, so snapshots are the only lasting history |
| canlii               | CanLII decisions for the OLT, Divisional Court and related bodies                                                                                                                                                                                                              | CanLII API if access is granted, else permitted search and download    | Weekly                                        | Case number, citation, address                        | Check terms; request API access                                                                         |
| tor_mayoral          | Mayoral decisions and strong-mayor directives on toronto.ca                                                                                                                                                                                                                    | Scrape                                                                 | Weekly                                        | Item code, subject                                    | Few records, high importance                                                                            |
| on_context           | ola.org bills; Ontario e-Laws; Environmental Registry of Ontario; the City's "How Ontario's Planning Rules Have Changed" tracker                                                                                                                                               | Scrape or manual entry into context_event                              | Weekly                                        | Issue codes, dates in force                           | Many provisions come into force later, on proclamation                                                  |

**Source registry and discovery.** The source_registry table is the
single list of every source considered.

1.  When starting a workstream, search for public sources that fill gaps
    or cross-check what's here. Search official portals, the open data
    catalogue's new datasets, court and tribunal databases, provincial
    registries, and civic and media sites.

2.  Add each candidate with coverage, format, update frequency, terms of
    use, effort estimate and a recommendation.

3.  Get the project owner's approval before building a connector for a
    new source, or before using any source whose terms are unclear.

Candidates already worth evaluating:

- Integrity Commissioner and Ombudsman reports.

- CreateTO and Housing Now project pages.

- Toronto Community Housing board materials.

- Councillor newsletters and websites.

- Residents' association sites and umbrella groups such as FoNTRA.

- Minister's Zoning Orders.

- City Planning study pages.

- Licensed news archives, for context only.

## Entity resolution and linking

Linking is where most of the value and most of the errors live. Each
link stores its method (exact key, rule, model, or human), a confidence
score, and a review status. Low-confidence links go to a review queue
and are never silently accepted.

| Link                                                            | Primary key                                         | Fallbacks                                                                   | Review rule                                           |
|-----------------------------------------------------------------|-----------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| Vote, motion or document to agenda item                         | Item code (such as 2025.PH22.3)                     | URL parameters, meeting date + item title                                   | Exact key only; no fuzzy matching                     |
| Agenda item to application                                      | Application number found in the item or report text | Address mentioned plus date window                                          | Address-only links need review                        |
| Application to address and ward                                 | Address point match                                 | Geocoding, then point-in-polygon on the ward map in force on the event date | Unmatched addresses go to the queue                   |
| Committee of Adjustment file to TLAB, OLT or court case         | Municipal file number recorded on the case          | Address + date window                                                       | Address-only links need review                        |
| Name to person (councillors, mayor, staff)                      | Curated alias table seeded from office_term         | Rule-based normalization (titles, initials, accents)                        | New aliases are approved by a human once, then reused |
| Name to organization (lobbying clients, developers, applicants) | Registered business name                            | Normalized name + address                                                   | Merges are proposed, never automatic                  |
| Transcript speaker to person                                    | Chair's recognitions and speaker order in minutes   | Voice profiles for sitting members (opt-in, internal only)                  | Below threshold → "unattributed", never a guess       |
| Donor to person or organization                                 | None reliable                                       | Name + postal area                                                          | Shown only as "possible match" unless confirmed       |

Seed data to build first:

- Every councillor and mayor since December 2018 with ward and term
  dates, including the 7 new members of the term starting November 15,
  2026.

- The 2018 25-ward map.

- The taxonomy, version 0.

## Document processing and AI tagging

Documents become passages, and passages get tags. Every tag points back
to its exact passage.

1.  **Extract.** Text from PDFs and HTML with page numbers and character
    offsets kept. Use OCR only when no text layer exists, and flag OCR
    text as lower confidence.

2.  **Classify the document:** staff report, decision, letter,
    deputation summary, minutes, notice, tribunal decision. For letters,
    also classify the author (official, applicant, organization, private
    individual).

3.  **Split into passages** of roughly paragraph length, keeping their
    position. Embed them with pgvector for search.

4.  **Tag.** An LLM assigns zero or more issues from the taxonomy
    (taxonomy YAML, versioned), plus stance (supports, opposes,
    conditional, neutral or procedural), actor class and strength. The
    prompt receives the taxonomy definitions and must quote the
    supporting span. Reject any output whose quote doesn't match the
    passage text exactly.

5.  **Roll up.** Count opposition and support per application, item and
    ward. For letters, one letter counts once, whatever its length.
    Detect form letters (near-duplicate text) and count them separately.

6.  **Review.** Send a stratified sample plus all low-confidence tags to
    the review app. Human corrections are stored as new tag versions and
    feed the evaluation set.

**Accuracy targets, checked on a hand-labelled set of 300+ items:**

- Issue tags: at least 90% precise.

- Stance: at least 85% correct.

- Document classification: at least 95% correct.

Re-run the evaluation on every prompt or model change, and block the
change if a metric drops.

## Transcription and recording quality

Transcripts are built per meeting, aligned to agenda items, and scored
for quality. The quality scores decide later whether the project
installs its own recording equipment, so measure them consistently from
the first meeting.

1.  **Acquire.** Get the best available audio: a direct feed or files
    from the City if granted, otherwise the published recording. Store
    the original file in raw storage and record which kind of source it
    was.

2.  **Prepare audio.** Normalize loudness, measure signal-to-noise
    ratio, clipping and dropouts, and detect silence and music.

3.  **Transcribe.** Use a Whisper-family model with a custom vocabulary:
    councillor names, ward and street names, planning terms, by-law and
    item codes. Run a second, slower pass on low-confidence segments.

4.  **Identify speakers.** Use diarization (pyannote or equivalent),
    then attribute speakers using chair recognitions, speaker lists from
    minutes, and optional voice profiles of sitting members. Below the
    confidence threshold, a segment stays "unattributed".

5.  **Align to agenda items** using the City's video index timestamps
    where available, otherwise chair announcements of item codes.

6.  **Score quality.** For a 10-minute sample per meeting, a reviewer
    corrects the transcript. Then compute word error rate, speaker
    attribution error rate, unattributed share, overlapping-speech
    share, audio metrics, and whether the recording is missing or
    broken. Write the results to recording_quality by meeting and venue.

Check the provisional thresholds from the plan per venue each month:

- Word error rate above about 10%.

- Speakers identified correctly less than 95% of the time.

- Recordings that often go missing.

A venue that crosses one of these after software fixes is flagged as a
candidate for the recording-equipment option. Ontario Land Tribunal
hearings aren't recorded by the tribunal, so for them the meeting index
holds only the event metadata.

## Orchestration, monitoring and data quality

Every connector and pipeline stage runs on a schedule, reports what it
did, and fails loudly.

- **Schedules:** daily for open data, TMMIS, consultations and OLT case
  status; weekly for TLAB, CanLII, Design Review Panel, the Application
  Information Centre and provincial context; event-driven for video
  after each meeting. Backfills run as separate, resumable jobs.

- **Run records:** each run writes a fetch_run row with counts of new,
  changed and unchanged items, and errors.

- **Alerts when:**

  - a source returns zero items where it normally returns some;

  - the page structure changes (the parser fails on more than 5% of
    items);

  - a dataset's columns change;

  - an OLT case disappears before it has been snapshotted.

- **Data quality checks after each load:**

  - every vote links to an agenda item;

  - every application has a ward;

  - no meeting lacks a body, date or type;

  - term dates don't overlap for the same seat;

  - counts reconcile with source totals where the source publishes them.

- **Dashboards in the internal app:** coverage by source and year, link
  and tag review queues, accuracy metrics over time, and recording
  quality by venue.

- **Decisions log:** record every schema, taxonomy or source decision in
  docs/decisions/ with date and reasoning.

## Build order

Build in six milestones that follow the plan's roadmap and gates. Don't
start a milestone until the previous one's acceptance tests pass.

| \#  | Milestone                | Builds                                                                                                                                                                                  | Acceptance tests                                                                                                                             | Plan gate |
|-----|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|-----------|
| M0  | Foundations              | Repository, database with migrations, raw storage, orchestration, source_registry seeded with this spec's sources and first discovery pass, people and ward seed data, taxonomy v0 file | Fresh environment builds from one command; registry lists every source with terms checked; seed data complete for all members since Dec 2018 | G1        |
| M1  | Structured open data     | tor_votes, tor_dev_apps, tor_coa, tor_pipeline_permits, tor_geo, tor_lobbyist, tor_elections                                                                                            | 100% of votes link to agenda items and people; 98%+ of applications have a ward; re-runs create no duplicates                                | G1        |
| M2  | Appeals and the province | olt_cases (daily snapshots from day one), tor_tlab, canlii, tor_mayoral, on_context; proceeding linking                                                                                 | Every Toronto OLT case currently on the case status service is captured; 90%+ link to an application; snapshot history kept                  | G2        |
| M3  | Documents and tagging    | tmmis backfill to 2018, tor_drp, tor_consultations, tor_aic; passage pipeline; tagging; review app v1                                                                                   | Accuracy targets met on the labelled set; every tag quotes its passage exactly; private names absent from search                             | G2        |
| M4  | Transcripts              | tor_video; transcription, speaker identification and alignment; recording_quality                                                                                                       | 95%+ correct speaker attribution on sampled meetings; quality metrics for every transcribed meeting and venue                                | G3        |
| M5  | Signals and reports      | Signal computations (support rates, ward posture, opposition trends, outcomes after appeal, timing effects); report generator for site, councillor and ward briefs                      | Every number in a generated brief links to its records; rebuilding a brief as of a past date reproduces it                                   | G3        |

Start OLT case snapshots in M0 or M1 even though full linking comes in
M2. Closed cases disappear from the service after two years, so every
day without a snapshot loses history.

## Things to verify before relying on them

These items come from documentation or search results and haven't been
tested. Check each one, record the answer in the decisions log, and
update this spec.

- [ ] Toronto open data API base URL, dataset IDs and field names for
  each dataset listed.

- [ ] Which ward boundary datasets cover the 2018 map, and whether
  earlier maps are needed.

- [ ] TMMIS URL patterns and whether a structured feed exists behind the
  agenda pages.

- [ ] Terms of use for City meeting video on YouTube; whether the City
  Clerk's Office will supply recordings or direct audio feeds, and under
  what licence.

- [ ] Whether TLAB and Committee of Adjustment hearings are recorded and
  published anywhere.

- [ ] Ontario Land Tribunal case status: structure, rate limits, terms
  of use, and whether bulk or structured access can be requested.

- [ ] CanLII API access and terms for storing decisions.

- [ ] Whether consultation-meeting recordings and attendee counts are
  kept anywhere central.

- [ ] Privacy review: handling of private individuals' names in letters
  and transcripts, under applicable Canadian privacy law.

**Sources consulted for this spec:**

- [Phase 1 Plan](https://claude.ai/artifact/YUi9Pt51hfmNdpHYjic7oE)
  (companion document; fuller source list there)

- [Ontario Land Tribunal – Case Status
  service](https://olt.gov.on.ca/case-status)

- [Ontario Land Tribunal – hearing FAQ](https://olt.gov.on.ca/?p=75)

- [Open Data Toronto – Analyzing Lobbyist
  Data](https://open.toronto.ca/how-to-analyzing-toronto-lobbyist-registrar-data/)

- [City of Toronto – Design Review Panel minutes, February 26,
  2025](https://www.toronto.ca/wp-content/uploads/2025/04/9800-CityPlanning-Design-Review-Panel-Meeting-Minutes-February-26-2025.pdf)

- [City Solicitor report – 155 St. Dennis Drive (May
  2026)](https://www.toronto.ca/legdocs/mmis/2026/cc/bgrd/backgroundfile-286918.pdf)

- [City of Toronto – How Ontario's Planning Rules Have Changed (July
  2026)](https://www.toronto.ca/wp-content/uploads/2026/07/96d1-how-ontarios-planning-rules-have-changed.pdf)

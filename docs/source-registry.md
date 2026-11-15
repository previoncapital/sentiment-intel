# Source registry (first discovery pass, 2026-11-14)

Every source considered for Phase 1, built or not. This file seeds the
`source_registry` table in Milestone M0. Status values follow the spec:
**candidate** (found, not yet approved), **approved**, **built**, **rejected**.
Nothing is approved or built yet; the "Recommendation" column is a proposal for
the owner.

How each entry was checked:

- **Live** — I opened the source from this environment on 2026-11-14 and saw
  the data or page.
- **Search** — found through web search only; not yet opened directly.
- **Blocked** — the site refused this environment's requests.

Record counts are as of 2026-11-14. "Open Government Licence – Toronto" (OGL-T)
lets us copy and reuse the data for any lawful purpose with attribution, **but
it does not cover personal information** (see note 3 at the end).

Effort: Low = a day or two; Medium = about a week; High = several weeks.

---

## A. Sources named in the spec (17)

| Slug | What it covers | Where (as verified) | Format | Terms | Checked | Recommendation |
|---|---|---|---|---|---|---|
| `tor_votes` | Every recorded vote by member, motion and agenda item. 2018–22 term: 61,074 rows; 2022–26 term: 46,815 rows (to 2026-08-05; last Council votes 2026-07-30). Also 2006–2018 terms. | open.toronto.ca dataset `members-of-toronto-city-council-voting-record`; one resource per term | CSV/JSON/XML; CKAN API | OGL-T | Live | **Build in M1.** Two problems found: 87% of 2018–22 rows have **no date** (recover it from the meeting schedule dataset and the item code), and date formats are mixed. No 2026–30 resource yet — watch for it after the Nov 18–19 meeting. |
| `tor_dev_apps` | Rezoning, official plan, site plan, subdivision, condo applications with address, ward, status, description, **community meeting date/time/location**, AIC link. 8,639 applications (26,713 rows, one per address). | dataset `development-applications` | CSV/JSON; CKAN API | OGL-T, except contact names/emails/phones (personal information) | Live | **Build in M1.** Spec says "records from 2021" — wrong: it goes back to **2008** (5,699 of the 8,639 applications were submitted 2008–2020; corrected 2026-11-15, see DI-015). Do not republish the CONTACT_* fields. |
| `tor_coa` | Committee of Adjustment minor variances and consents: hearing date/time/location, decision, whether anyone objected at the meeting, appeal fields. Active (2,768) + closed since 2017 (34,239) + yearly files back to 2001. | dataset `committee-of-adjustment-applications` | CSV/JSON; CKAN API | OGL-T (contact fields excluded) | Live | **Build in M1.** Decision values need cleaning ("Approved on Condition", "conditional approval", etc.). |
| `tor_pipeline_permits` | Development pipeline (2,391 projects; proposed units and floor area) and building permits (active, cleared). | datasets `development-pipeline`, `building-permits-active-permits`, `building-permits-cleared-permits` | CSV; CKAN API | OGL-T | Live | **Build in M1** (outcome context). |
| `tor_geo` | Ward boundaries; address points. | `city-wards` (25 wards, **one version effective 2018-08-07, still current**); `address-points-municipal-toronto-one-address-repository` (daily) | GeoJSON/SHP/CSV | OGL-T | Live | **Build in M0/M1.** The "2018 map" and the current map are the same; earlier maps are needed only if the owner extends history before Dec 2018. |
| `tor_lobbyist` | Lobbyist registrations and communications, subject matter, clients, officials lobbied. | dataset `lobbyist-registry` (`lobbyactivity.zip`, daily) | XML in ZIP | OGL-T; registry site has its own terms | Live (dataset); terms page blocked | **Build in M1.** |
| `tor_elections` | Official results 2003–2026 (2026 posted 2026-10-29); voting subdivisions; campaign contributions. | `election-results-official`; `elections-subdivisions`; `elections-campaign-contributions` | ZIP of spreadsheets | Results: **licence "not specified"** on the portal; contributions: OGL-T | Live | **Build in M1**, but: open data has **contributions for 2018 only**. 2022 and 2026 are in the City's Election Financial Disclosure search app (`secure.toronto.ca/EFD`, blocked here). Ask the Clerk for bulk files. Confirm the licence on results. |
| `tmmis` | Meetings, agendas, items, decisions, staff reports, communications. | Agenda pages: `secure.toronto.ca/council/...` (**blocked: 403**); legacy `app.toronto.ca/tmmis` (**connection reset**); PDFs: `www.toronto.ca/legdocs/mmis/<year>/<committee>/bgrd/backgroundfile-N.pdf` and `.../comm/communicationfile-N.pdf` (**works**) | HTML + PDF | City website copyright: commercial reuse needs written permission (see note 2). robots.txt allows the main committee folders; blocks a few (`sv`, `sx`, `sy`, `sz`, `dg`). | Mixed | **Highest-risk source.** Core of the product but the agenda pages refuse this environment. Before M3: test from the production cloud; ask the Clerk for access or a bulk feed; get a legal view on reuse. |
| `tor_video` | Council and committee video. | YouTube channel `youtube.com/TorontoCityCouncilLive`; video index pages | Video | No public reuse licence found. City privacy notice says it records meetings and "may make the video record available to the public". | Search | **Ask the Clerk first** (as the plan says). Metadata via YouTube Data API only until then. |
| `tor_drp` | Design Review Panel minutes. | PDFs under `www.toronto.ca/wp-content/uploads/...` | PDF | City website copyright | Not yet checked | Build in M3 as planned. |
| `tor_consultations` | Community consultation meeting notices. | The City Planning consultations page **now redirects to `haveyoursay.toronto.ca/city-planning-development-review-community-consultations`** (Social Pinpoint platform, its own terms) | HTML | Have Your Say terms of use (Social Pinpoint) — review | Live | Build in M3; **also use the meeting date/time/location fields already in `tor_dev_apps` and `tor_coa`**, which give a structured meeting index for free. |
| `tor_aic` | Application Information Centre: application pages and documents; TLAB decisions from the last 12 months. | `www.toronto.ca/city-government/planning-development/application-information-centre/` | Interactive web app | City website copyright | Search | Build in M3. No public API found. |
| `tor_tlab` | TLAB decisions. | Decisions **from 2023-02-01 are published only on CanLII**; older decisions by email request to TLAB; some older PDFs on toronto.ca | PDF / CanLII | CanLII terms (see `canlii`) | Live (TLAB page) | **Change of plan:** see new source `tor_tlab_appeals` for the structured list; decision text depends on CanLII access or a request to TLAB. |
| `olt_cases` | Every Ontario Land Tribunal case: parties, legislation, municipal file number, status, hearing events, decisions. **4,170 records** for a "*Toronto" search. | **`jus-olt-prod.powerappsportals.com/en/e-status/`** (the olt.gov.on.ca page only links to it). Results load from a data endpoint behind the page; needs a headless browser. Columns: Case Number, Lead Case Number, Legacy Case Number, Case Title, Property Address, **Reference Number (the City file number)**, Municipality, Act, Section, Status. | Interactive web app | Ontario.ca terms of use; no robots.txt on the portal | Live (one search) | **Build first (M0/M1).** Closed cases stay 2 years — but only since 2026-03-13; before that, six weeks. Ask the Tribunal about bulk access. |
| `canlii` | Decisions of the OLT, TLAB (from Feb 2023), Divisional Court. | `www.canlii.org` | HTML/PDF; API | **robots.txt blocks all general automated crawlers.** API reportedly metadata only (titles, citations, dates), and terms reportedly prohibit bulk downloading — not yet confirmed from CanLII itself. | Live (robots.txt); terms by search | **Request API access and written permission** (owner sends). Do not scrape. |
| `tor_mayoral` | Mayoral decisions and strong-mayor directives. | City says signed decisions are posted to an online repository on toronto.ca | HTML/PDF | City website copyright | Not yet checked | Build in M2. |
| `on_context` | Bills, regulations, Minister's Zoning Orders, Environmental Registry notices, the City's planning-rule tracker. | `ola.org`, `ontario.ca/laws`, `ero.ontario.ca`, toronto.ca tracker PDF | HTML/PDF | Ontario/King's Printer terms | Search | Build in M2, mostly manual entry. No ERO API found. |

## B. New sources found in this pass

### Structured City open data (all OGL-T, all CKAN API, all opened live)

| Slug | What it covers | Why it matters | Effort | Recommendation |
|---|---|---|---|---|
| `tor_tlab_appeals` | Dataset `local-appeals-body-appeals`: every TLAB appeal since 2017 (2,150 records) with TLAB folder, **Committee of Adjustment file number**, received/final dates, status, address, district. Monthly. | Not in the spec. Gives the C of A → TLAB link directly, without parsing decisions. | Low | **Build in M1.** |
| `tor_meeting_schedule` | Dataset `city-council-and-committees-meeting-schedule-reports`: every Council/committee meeting by term (2006–2026). | Fills the missing dates in the 2018–22 voting data; gives start times for the meeting index. | Low | **Build in M1.** |
| `tor_attendance` | Dataset `members-of-toronto-city-council-meeting-attendance`, by term. | Distinguishes "absent" from "voted"; context for vote-based rates. | Low | Build in M1. |
| `tor_declared_interest` | Dataset `registry-of-declared-interest`: councillors' conflict-of-interest declarations. | Explains "Absent (Interest Declared)" votes (121 in 2022–26). | Low | Build in M1. |
| `tor_wards_councillors` | Dataset `wards-and-elected-councillors`: current councillor per ward (pre-Nov 15 term). | Seed data check only — **current snapshot, no history**. History must come from election results, by-election results and the voting data. | Low | Use in M0 seed. |
| `tor_byelections` | Datasets `elections-official-by-election-results` and by-election voter statistics. | Seats that changed mid-term (e.g. Ward 25 in 2025; the 2023 mayoral by-election). Needed for correct term dates. | Low | **Use in M0 seed.** |
| `tor_section37` | Dataset `section-37`: community benefits secured (Planning Act s.37/s.45). | Money-and-process issue; outcome detail per application. | Low | Build in M5 (context). |
| `tor_rental_replacement` | Dataset `demolition-and-replacement-of-rental-housing-units`. Quarterly. | Affordability issue (rental replacement). | Low | Build in M5. |
| `tor_prelim_zoning` | Dataset `preliminary-zoning-reviews`. Daily. | Early signal of projects before a formal application. | Low | Evaluate in M5. |
| `tor_heritage` | Datasets `heritage-register`, `heritage-conservation-districts`, `properties-requiring-a-cultural-heritage-evaluation-report-under-opa-720`. | Heritage-and-character issue; sites designated during review. | Low | Build in M5 (context). |
| `tor_planning_geo` | Datasets `minister-approved-major-transit-station-areas`, `secondary-plans`, `site-and-area-specific-policies`, `zoning-by-law`, `transit-oriented-communities`. | Location-policy issue tags; comparable-site analysis. | Low | Build in M5. |
| `tor_affordable_pipeline` | Datasets `upcoming-and-recently-completed-affordable-housing-units`, `active-affordable-and-social-housing-units`, `multi-tenant-house-licences`. | Affordability and housing-type context. | Low | Build in M5. |
| `tor_public_notices` | Dataset `public-notices` (daily). | May contain planning notices that disappear later. | Low | Evaluate in M3. |
| `tor_open_data_intake` | Dataset `open-data-intake` (daily): datasets the City is preparing to publish. | Standing discovery: shows new datasets before they appear. | Low | Check monthly. |

### City web sources

| Slug | What it covers | Checked | Recommendation |
|---|---|---|---|
| `tor_coa_decisions` | Committee of Adjustment notices of decision. Recent ones appear as PDFs under `www.toronto.ca/legdocs/mmis/<year>/mm/bgrd/`; 2017 ones under `wp-content/uploads`. | Search | Evaluate in M3 for decision text; open data already has the decision outcome. |
| `tor_efd` | Election Financial Disclosure search (`secure.toronto.ca/EFD`) — 2022 and 2026 contributions. | Search; host blocked | Ask Clerk for bulk export (M1). |
| `tor_mzo_list` | City's list of Minister's Zoning Orders in Toronto (about 20, e.g. Ontario Place, 4000 Leslie St, 1875 Steeles Ave W). | Live | Use in M2 as a cross-check of the province's list. |
| `tor_integrity` | Integrity Commissioner reports (Municipal Conflict of Interest Act reports, investigation reports) and Ombudsman Toronto reports. | Search | Low volume; add in M2 as context events. Most reach Council and so also appear in TMMIS. |
| `tor_study_pages` | City Planning study pages (e.g. Jane-Finch, Midtown in Focus, Update Downsview, heritage district studies) with meeting summaries and recordings. | Search | Manual snapshot list in M3; no central index. |
| `tor_housing_data_hub` | Toronto Housing Data Hub; housing-target dashboards. | Search | Context only (M5). |
| `createto_tchc` | CreateTO / Housing Now reports (appear in TMMIS under committee code `ra`); Toronto Community Housing board materials (separate site). | Search | CreateTO arrives through `tmmis`; TCHC evaluate in M5. |
| `tor_councillor_sites` | Councillor newsletters and sites (several list development applications and consultation meetings in their ward). | Search | Snapshot notices in M3; terms vary by site. |

### Provincial and court

| Slug | What it covers | Checked | Recommendation |
|---|---|---|---|
| `olt_decisions_search` | OLT's own decision search on olt.gov.on.ca (decisions under 10 years old). | Live (page) | Evaluate in M2 as the alternative to CanLII for OLT decision text. |
| `olt_s23_reviews` | OLT's quarterly table of requests to review its decisions (s.23 OLT Act), one-year window, Word/PDF. | Live | Build in M2 (small; snapshot each quarter). |
| `on_mzo` | Ontario's Minister's Zoning Orders page (orders since 2025-11-27 and earlier ones), plus each order's ERO notice. | Search | Build in M2 (manual/context events). |
| `on_housing_progress` | Ontario "Tracking housing supply progress" (housing starts against municipal targets), downloadable from data.ontario.ca. | Search | Context in M5. |
| `on_courts` | Divisional Court decisions (published on CanLII); court filings beyond decisions are not freely online. | Search | Via `canlii`; City Solicitor reports via `tmmis`. |

### Third-party and civic sources (cross-checks)

| Slug | What it covers | Terms | Recommendation |
|---|---|---|---|
| `climate_voting_records` | ClimateFast's "Climate Voting Records Toronto": councillor votes tagged by policy area, including housing; built from the City's open data. | Unknown | **Cross-check only** (compare our housing vote selection to theirs in M3). Do not ingest. |
| `tmmis_fetcher_notes` | A GitHub project documenting part of TMMIS's behind-the-scenes data interface (`app.toronto.ca/tmmis/...`). | Open source | Reference only; it shows a structured feed may exist. Ask the Clerk rather than depend on it. |
| `third_party_agenda_json` | Agenda JSON files hosted by an unknown third party on a Supabase bucket. | Unknown provenance | **Reject** as a source (no provenance). Shows the agenda data is extractable. |
| `the_public_record` | The Public Record (thepublicrecord.ca): municipal reporting including OLT and Divisional Court matters. | Copyright | Context only; candidate for a licensed news feed later. |
| `fontra_ras` | FoNTRA (35+ North Toronto residents' associations) and member association sites: positions, OLT participation. | Varies | Manual, M3, for organization matching. Most submissions also appear in TMMIS communications. |
| `urbantoronto` | UrbanToronto project database and forum. | Restrictive (check) | Candidate; context only. |
| `news_archives` | Licensed news archives (e.g. ProQuest, Factiva). | Paid licence | Defer (plan: context only, Phase 1 excludes news). |
| `land_registry` | Ontario land registry (OnLand / Teranet): ownership and transfers. | Paid | Defer to Phase 2. |

---

## Notes

1. **Spec corrections found in this pass** are recorded in
   `docs/decisions/2026-11-14-verification-pass.md`.
2. **City website copyright.** A copyright notice in the terms of a City web
   tool says it applies to all City websites: the City keeps copyright, personal
   printing is allowed, and commercial or other use needs written permission
   (approvals@toronto.ca). This would cover TMMIS PDFs, notices and minutes,
   which are not open data. It needs a lawyer's view and probably a written
   request to the City (draft in `docs/setup/letter-to-city-clerk-draft.md`).
3. **Personal information.** The open data licence excludes personal
   information. Development and C of A datasets contain applicant/agent contact
   names, emails and phone numbers (7,591 development-application rows have an
   email). Store them as restricted fields; never republish them.
4. **Not yet checked:** Design Review Panel listing, mayoral decisions
   repository, YouTube channel terms page, Lobbyist Registry terms page (host
   blocked), CanLII's own API terms. These are listed in the verification log.

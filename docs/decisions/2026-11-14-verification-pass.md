# 2026-11-14 — First verification pass on the spec's "Things to verify"

**Type:** source decisions / spec corrections
**Status:** findings recorded; spec text **not yet changed** — proposed edits
are listed at the end for the owner to approve.

How this was checked: direct requests from this cloud environment to the
public sites (after the owner approved adding them to the network allowlist),
one headless-browser search of the OLT portal, and web searches. "Confirmed"
means I saw it on the live source today.

## 1. Toronto open data API, dataset IDs and field names — **Confirmed, with corrections**

- API base: `https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/`
  (standard CKAN: `package_show`, `package_search`, `datastore_search`).
  Bulk download per resource: `.../datastore/dump/<resource_id>`.
- Dataset IDs, refresh rates and fields are recorded in
  `docs/source-registry.md`. All carry the Open Government Licence – Toronto,
  except Election Results ("License not specified").
- **Corrections to the spec:**
  - Development Applications go back to **2008**, not 2021 (5,699 of 8,639
    applications were submitted 2008–2020; corrected 2026-11-15 — the file has
    one row per address, 26,713 rows). Pre-2021 applications that are not in the
    dataset (if any) still need TMMIS/AIC.
  - The 2018–22 voting file has **no date on 53,034 of 61,074 rows (87%)**.
    Dates must come from the meeting schedule dataset via the item code.
  - Date formats are mixed in the 2022–26 voting file
    (`2022-11-23 15:17 PM` and `2026-08-05`).
  - Vote values: Yes, No, Absent, and **Absent(Interest Declared)**.
  - Latest vote in the open data: 2026-08-05 (TTC board); latest City Council
    vote: 2026-07-30. No 2026–2030 resource yet.
  - Campaign contributions on open data cover **2018 only**. 2022 and 2026
    are in the City's Election Financial Disclosure app (blocked here).
  - Development and C of A datasets include applicant/agent contact names,
    emails and phones. The licence excludes personal information.
- **New datasets the spec doesn't list:** TLAB appeals, meeting schedules,
  attendance, declared interests, by-election results and others (registry
  section B).

## 2. Ward boundary datasets — **Confirmed: one map since 2018**

- `city-wards` holds 25 wards, all with `DATE_EFFECTIVE 2018-08-07` and no
  expiry. The "2018 map" and the "current map" are the same file. Earlier
  (44-ward) maps are needed only if the owner decides to extend history before
  December 2018 (open decision in the plan).
- Still store it as a dated version, so a future boundary change doesn't
  break history.

## 3. TMMIS URL patterns and a structured feed — **Partly confirmed; major access problem**

- PDF pattern confirmed:
  `www.toronto.ca/legdocs/mmis/<year>/<committee>/bgrd/backgroundfile-N.pdf`
  (the spec's 155 St. Dennis report downloads fine).
- `secure.toronto.ca/council/...` (agenda-item pages) returns **403 Access
  Denied** to this environment, whatever the client identifier. This looks
  like the City's content-delivery firewall blocking cloud-server addresses.
- `app.toronto.ca/tmmis/...` (legacy pages) **resets the connection**.
- No official API or bulk feed found. An open-source project documents part of
  an undocumented interface at `app.toronto.ca/tmmis`; a third party publishes
  agenda JSON of unknown origin. Neither is a dependable source.
- The City's robots.txt allows the main committee folders under `/legdocs/`
  and blocks a few (`sv`, `sx`, `sy`, `sz`, `dg`).
- **Needs:** (a) test from the production hosting provider before choosing it;
  (b) ask the Clerk's Office for access or a structured feed; (c) do not
  disguise the client to get past the block.

## 4. Meeting video terms; Clerk recordings or audio feeds — **Not answerable from public sites → owner/Clerk**

- No public reuse licence for the City Clerk's YouTube channel found.
- The City's notice to people who write or speak to committees says the City
  video-records committee and community council meetings and may make the
  video public, and that letters (with names, and contact details unless the
  writer asks for removal) become part of the public record on the website.
- A copyright notice in City web terms says City web content is City copyright
  and commercial use needs written permission. This likely affects video and
  TMMIS documents too. **Needs legal review and a written request.**

## 5. Are TLAB and Committee of Adjustment hearings recorded and published? — **Not found → ask TLAB / C of A**

- No public archive of hearing recordings found. A May 2021 TLAB business
  meeting agenda listed "release and use of recorded TLAB virtual hearings and
  issues of privacy and permission"; the outcome isn't public in what I found.
- C of A hearings are hybrid (in person and virtual).
- TLAB contact listed by the City: tlab@toronto.ca.

## 6. OLT case status — **Confirmed, with corrections**

- The spec's URL (`olt.gov.on.ca/case-status`) is only an information page.
  The search itself is at **`jus-olt-prod.powerappsportals.com/en/e-status/`**
  (a Microsoft Power Pages portal). Results load from a data endpoint behind
  the page, so collection needs a headless browser.
- A "*Toronto" search returned **4,170 records**. Columns: Case Number, Lead
  Case Number, Legacy Case Number, Case Title, Property Address, Reference
  Number (the municipal file number, e.g. `19 145226 STE 10 SA`,
  `A0506/25TEY`), Municipality, Act, Section, Status. Case pages show related
  cases, hearing events and the Notice of Hearing.
- Retention: closed cases stay **two years after closing — only since the
  2026-03-13 upgrade. Before that it was six weeks.** So cases that closed
  before about early 2026 may already be gone; their history must come from
  decisions (OLT search / CanLII).
- No robots.txt on the portal; ontario.ca terms of use apply. No published
  rate limits or bulk access. **Needs:** a polite collection rate, and a
  request to the Tribunal for bulk or structured access.

## 7. CanLII API access and terms — **Partly answered → owner to request access**

- CanLII's robots.txt blocks **all** general automated crawlers (only named
  search engines are allowed). Scraping CanLII is not an option.
- Third-party sources say the API returns metadata only (no decision text)
  and the terms forbid bulk downloading; CanLII sued an AI company in 2024 over
  scraping. Not yet confirmed from CanLII's own terms.
- **New consequence:** TLAB decisions issued from 2023-02-01 are published
  *only* on CanLII (older ones by email request to TLAB). OLT decisions are
  also on the OLT's own decision search, which may be the better route.
- **Needs:** owner to request API access and ask about permitted storage; I
  will evaluate the OLT decision search in M2.

## 8. Consultation-meeting recordings and attendee counts — **Partly answered**

- The City Planning consultations page now redirects to
  `haveyoursay.toronto.ca` (Social Pinpoint platform, its own terms).
- The Development Applications and C of A datasets include **community meeting
  date, time and location** fields — a structured start to the meeting index.
- A 2024 City report says Council asked staff to set requirements for recording
  and publishing virtual consultation meetings; current status not found.
- No central record of attendee counts found; they appear in some staff
  reports.

## 9. Privacy review — **Needs a lawyer**

Facts gathered for counsel: the City's notice to letter writers (names and the
fact of the communication go on the public record); the open data licence
excludes personal information; a commercial product in Ontario falls under
federal private-sector privacy law (PIPEDA), whose exemption for "publicly
available" information is narrow. Counsel should advise on storing private
individuals' names, on aggregation, and on report wording.

## Also checked

- **New council:** confirmed from the Clerk's certified Declaration of Results
  (2026-10-29): Olivia Chow re-elected mayor; **7 seats changed**: Ward 4 Diana
  Chan McNally, Ward 5 Chiara Padovani, Ward 11 Mike Layton (returning former
  councillor), Ward 13 Curran Stikuts, Ward 14 Sara Ehrhardt, Ward 19 Nate
  Erskine-Smith, Ward 23 Shaun Chen.
- **Term seed data:** the wards-and-councillors dataset is a current snapshot
  only. Member history since Dec 2018 must be assembled from the 2018/2022/2026
  results, by-election results and the voting data (30 distinct members appear
  in each of the last two terms' voting files).

## Proposed spec edits (for owner approval)

1. `tor_dev_apps`: "Records from 2008" (not 2021).
2. `olt_cases`: location is `jus-olt-prod.powerappsportals.com/en/e-status/`;
   method is headless browser; note the March 2026 retention change.
3. `tor_tlab`: decisions from Feb 2023 via CanLII only; add `tor_tlab_appeals`
   open dataset.
4. `tor_consultations`: location is haveyoursay.toronto.ca; add the meeting
   fields in open data.
5. `tor_elections`: 2022/2026 contributions are not on open data.
6. `tmmis`: record the access block and the copyright question as risks.
7. Add the new M1 datasets: TLAB appeals, meeting schedule, attendance,
   declared interests, by-election results.

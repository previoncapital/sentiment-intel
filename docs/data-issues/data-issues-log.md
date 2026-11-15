# Data issues log

Every discrepancy, gap or unconfirmed fact we find in a source, with what we're doing about it now and who could fix it. Updated as issues are found or resolved.

**Summary:** 11 open, 5 worked around — 16 in total.

| ID | Issue | Severity | Status | Who can fix it |
|----|------------------------|------|----------|----------|
| DI-006 | City's council agenda website blocks automated access from cloud servers | high | Open | City Clerk's Office; choice of hosting provider |
| DI-009 | Tribunal case history before early 2026 may already be gone | high | Open | Ontario Land Tribunal (bulk/historical access) |
| DI-001 | Two appointed councillors missing from Council attendance data | medium | Worked around (still open at source) | City of Toronto Open Data team / City Clerk's Office |
| DI-002 | Most 2018-2022 Council votes have no date | medium | Open | Us (workaround); City Clerk's Office (source fix) |
| DI-004 | Agenda item codes use the council year, not the calendar year | medium | Worked around (still open at source) | n/a (by design) |
| DI-007 | Campaign contributions for 2022 and 2026 not on open data | medium | Open | City Clerk's Office (Elections) |
| DI-013 | Personal contact details in open datasets the licence doesn't cover | medium | Worked around (still open at source) | Us; legal review |
| DI-014 | TLAB decisions before February 2023 not published online | medium | Open | TLAB; CanLII (access to post-2023 decisions) |
| DI-003 | Mixed date formats and 24-hour times labelled AM/PM in 2022-2026 votes | low | Open | Us |
| DI-005 | Garbled accented character in a member's name | low | Worked around (still open at source) | City of Toronto Open Data team |
| DI-008 | Election results published without a licence | low | Open | City of Toronto Open Data team |
| DI-010 | Some council term dates not confirmed in a City record | low | Open | Us (Council minutes, once DI-006 is solved) |
| DI-011 | Name order in election results differs from common usage | low | Worked around (still open at source) | Us |
| DI-012 | Committee of Adjustment decision values spelled inconsistently | low | Open | Us |
| DI-015 | Technical Spec says development applications start in 2021 | low | Open | Owner (approve spec edit) |
| DI-016 | Voting data lags behind Council | low | Open | City of Toronto Open Data team |

## Details

### DI-006 — City's council agenda website blocks automated access from cloud servers

*Access problem · severity high · Open · found 2026-11-14*

- **What's wrong:** secure.toronto.ca returns "Access Denied" (HTTP 403) to this environment however the client identifies itself; app.toronto.ca drops the connection. Document PDFs on www.toronto.ca/legdocs download normally.
- **Evidence:** Tested 2026-11-14 with honest and default client identifiers.
- **Why it matters:** Blocks agenda-item pages, decision text and Council minutes (Milestone M3), and confirming several dates (DI-011).
- **What we do meanwhile:** None yet. Do not disguise the client.
- **Who can fix it:** City Clerk's Office; choice of hosting provider
- **Next step:** Test from the chosen hosting provider; raise in the letter to the Clerk (docs/setup/letter-to-city-clerk-draft.md).

### DI-009 — Tribunal case history before early 2026 may already be gone

*Missing data · severity high · Open · found 2026-11-14*

- **What's wrong:** Closed cases stay on the case-status service for two years after closing, but only since 2026-03-13; before that, six weeks. Cases closed before roughly early 2026 may no longer be listed.
- **Evidence:** OLT news post of 2026-03-13; portal search returns 4,170 Toronto records.
- **Why it matters:** Hearing-event history for older appeals must come from decisions instead; outcome timelines will be thinner before 2026.
- **What we do meanwhile:** Recover outcomes from OLT decisions and City Solicitor reports; snapshot the portal daily from now on.
- **Who can fix it:** Ontario Land Tribunal (bulk/historical access)
- **Next step:** Start daily snapshots once hosting exists; ask the Tribunal about historical data.

### DI-001 — Two appointed councillors missing from Council attendance data

*Error in the source data · severity medium · Worked around (still open at source) · found 2026-11-14*

- **What's wrong:** Robin Buxton Potts (Ward 13, appointed 2022-06-01) and Rose Milczyn (Ward 1, appointed 2022-08-15) voted at Council but never appear in the attendance file. Members listed per Council session drop from 26 to 24 in May 2022 and stay there; Joe Mihevc, appointed the same day as Buxton Potts, was added.
- **Evidence:** Same gap in all four published versions (datastore CSV, CSV, JSON, XML; refreshed 2026-02-20). Both names present in the voting record.
- **Why it matters:** Attendance can't be used alone to decide who was in office or to compute attendance rates for 2022.
- **What we do meanwhile:** Office terms come from election results and appointments; attendance used only as a cross-check.
- **Who can fix it:** City of Toronto Open Data team / City Clerk's Office
- **Next step:** Ask the open data team (opendata@toronto.ca) why the two appointees are missing. Needs owner approval (contact with the City).

### DI-002 — Most 2018-2022 Council votes have no date

*Missing data · severity medium · Open · found 2026-11-14*

- **What's wrong:** 53,034 of 61,074 rows (87%) have a blank date. Every committee vote is dated; full Council votes are dated only for April-November 2020 (the first virtual meetings). No rows in that term carry a time of day.
- **Evidence:** Same in every published version of the file.
- **Why it matters:** Votes can't be placed on a timeline or matched to video without another source.
- **What we do meanwhile:** Restore dates from the City's meeting-schedule dataset using the meeting code in each agenda item number.
- **Who can fix it:** Us (workaround); City Clerk's Office (source fix)
- **Next step:** Build the date restoration in Milestone M1 and check it against Council minutes for a sample.

### DI-004 — Agenda item codes use the council year, not the calendar year

*Quirk to handle · severity medium · Worked around (still open at source) · found 2026-11-14*

- **What's wrong:** Items at the first meetings of a new Council carry the next year's code (votes on 2022-11-23 are coded "2023.FM1.8").
- **Evidence:** 1,601 votes in Nov-Dec 2022 coded 2023.
- **Why it matters:** Matching items to dates by the year in the code would put them in the wrong year.
- **What we do meanwhile:** Always link and date items by meeting date, never by the code's year.
- **Who can fix it:** n/a (by design)
- **Next step:** None; documented for connector builders.

### DI-007 — Campaign contributions for 2022 and 2026 not on open data

*Missing data · severity medium · Open · found 2026-11-14*

- **What's wrong:** The open data portal has contributions for 2018 only; later years are in the City's Election Financial Disclosure web app.
- **Evidence:** Dataset last updated 2023-04-26 with 2018 files only.
- **Why it matters:** No donor data for the current or previous council without another route.
- **What we do meanwhile:** None yet.
- **Who can fix it:** City Clerk's Office (Elections)
- **Next step:** Request bulk files (in the letter to the Clerk).

### DI-013 — Personal contact details in open datasets the licence doesn't cover

*Licensing or privacy · severity medium · Worked around (still open at source) · found 2026-11-14*

- **What's wrong:** Applicant/agent contact names, emails and phones are included, but the open data licence excludes personal information.
- **Evidence:** 7,591 development applications have a contact email.
- **Why it matters:** Republishing them could breach the licence or privacy law.
- **What we do meanwhile:** Store as restricted fields; never show in search or reports.
- **Who can fix it:** Us; legal review
- **Next step:** Include in the privacy review.

### DI-014 — TLAB decisions before February 2023 not published online

*Missing data · severity medium · Open · found 2026-11-14*

- **What's wrong:** TLAB decisions from 2023-02-01 are on CanLII only; earlier ones must be requested by email (tlab@toronto.ca), apart from some PDFs on toronto.ca.
- **Evidence:** TLAB "Schedule & Decisions" page.
- **Why it matters:** Appeal outcomes for 2018-2023 need the TLAB appeals dataset plus a request.
- **What we do meanwhile:** The TLAB appeals open dataset gives status and dates for every appeal since 2017.
- **Who can fix it:** TLAB; CanLII (access to post-2023 decisions)
- **Next step:** Owner to request older decisions; request CanLII access.

### DI-003 — Mixed date formats and 24-hour times labelled AM/PM in 2022-2026 votes

*Quirk to handle · severity low · Open · found 2026-11-14*

- **What's wrong:** Council votes carry date and time ("2022-11-23 15:17 PM" - a 24-hour time with an AM/PM label); most committee votes carry the date only.
- **Evidence:** 36,396 rows use the 24-hour-plus-AM/PM form.
- **Why it matters:** A naive parser could reject or misread the times.
- **What we do meanwhile:** Parse the time as 24-hour and ignore the AM/PM label; keep the original text.
- **Who can fix it:** Us
- **Next step:** Handle in the M1 voting-record connector, with a test.

### DI-005 — Garbled accented character in a member's name

*Error in the source data · severity low · Worked around (still open at source) · found 2026-11-14*

- **What's wrong:** "Ana Bailão" appears as "Ana BailÃ£o" (text encoding error).
- **Evidence:** Present in the City's file.
- **Why it matters:** Name matching would fail without repair.
- **What we do meanwhile:** The build repairs this kind of encoding error automatically.
- **Who can fix it:** City of Toronto Open Data team
- **Next step:** Mention when contacting the open data team about DI-001.

### DI-008 — Election results published without a licence

*Licensing or privacy · severity low · Open · found 2026-11-14*

- **What's wrong:** The dataset's licence field says "License not specified"; other City datasets use the Open Government Licence - Toronto.
- **Evidence:** CKAN metadata, 2026-11-14.
- **Why it matters:** Reuse terms for results are technically unclear.
- **What we do meanwhile:** Use with attribution, as for other City open data; flag for legal review.
- **Who can fix it:** City of Toronto Open Data team
- **Next step:** Ask with DI-001.

### DI-010 — Some council term dates not confirmed in a City record

*Not yet confirmed · severity low · Open · found 2026-11-15*

- **What's wrong:** Still unconfirmed: oath dates for Parthi Kandavel (Ward 20, 2023) and Neethan Shan (Ward 25, 2025) - first Council meeting attended used; the exact date of the August 2020 stay reinstating Jim Karygiannis - first news report used; the 2018-2022 term start in a City record - legal start Dec 1, oath at the Dec 4 inaugural meeting.
- **Evidence:** Each date is labelled with its basis and confidence in the seed data.
- **Why it matters:** Dates may be off by a few days; no effect on votes or applications.
- **What we do meanwhile:** Dates labelled as estimates.
- **Who can fix it:** Us (Council minutes, once DI-006 is solved)
- **Next step:** Confirm from Council minutes.

### DI-011 — Name order in election results differs from common usage

*Quirk to handle · severity low · Worked around (still open at source) · found 2026-11-14*

- **What's wrong:** The results file lists the Ward 4 winner as "McNally Diana Chan"; the Clerk's declaration prints "Diana Chan McNally".
- **Evidence:** 2026 poll-by-poll results vs. certified Declaration of Results.
- **Why it matters:** Automatic first/last name splitting gets this name wrong.
- **What we do meanwhile:** Name override in the seed data, with source; all 2026 winners now cross-checked against the declaration.
- **Who can fix it:** Us
- **Next step:** None.

### DI-012 — Committee of Adjustment decision values spelled inconsistently

*Quirk to handle · severity low · Open · found 2026-11-14*

- **What's wrong:** "Approved on Condition", "Approved on condition", "Approved with Conditions", "conditional approval", "approved" etc.; 3,608 closed applications have no decision value.
- **Evidence:** Closed applications since 2017 (34,239 rows).
- **Why it matters:** Approval-rate counts would be wrong without normalising.
- **What we do meanwhile:** Map to a standard set of outcomes in the M1 connector; keep the original text.
- **Who can fix it:** Us
- **Next step:** Build the mapping in M1 and investigate the blank decisions.

### DI-015 — Technical Spec says development applications start in 2021

*Correction to our spec · severity low · Open · found 2026-11-14*

- **What's wrong:** The dataset goes back to 2008 (18,615 of 26,713 applications submitted 2008-2020).
- **Evidence:** Live dataset, 2026-11-14.
- **Why it matters:** Less rebuilding from TMMIS is needed than the spec assumes.
- **What we do meanwhile:** n/a
- **Who can fix it:** Owner (approve spec edit)
- **Next step:** Approve the proposed spec edits in docs/decisions/2026-11-14-verification-pass.md.

### DI-016 — Voting data lags behind Council

*Missing data · severity low · Open · found 2026-11-14*

- **What's wrong:** Latest vote in the open data is 2026-08-05 (last Council votes 2026-07-30); there is no 2026-2030 file yet, though the new Council meets 2026-11-18/19.
- **Evidence:** Dataset as of 2026-11-14.
- **Why it matters:** The new term won't appear until the City publishes it.
- **What we do meanwhile:** None needed yet.
- **Who can fix it:** City of Toronto Open Data team
- **Next step:** Check for the new file after the first meeting; measure the publication delay.

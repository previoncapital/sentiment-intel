# Milestone M0 — accounts and approvals needed from the owner

Nothing below has been signed up for or paid. Each item needs the owner's
approval first. Costs are estimates in Canadian dollars at today's rates (USD
prices converted at about 1.40); they'll be confirmed against each provider's
price calculator before anything is turned on, and every paid service gets a
budget alert and a spending cap where the provider supports one.

**Estimated total running cost during M0: about $150–300 CAD a month**
(the project email is now $0 — owner's own domain).
For comparison, the plan budgets $1,000–3,000 a month during the full
historical backfill (mostly transcription and AI tagging in M3–M4).

## In order

### 1. GitHub — already done ✔
- You have the `previoncapital/sentiment-intel` repository.
- **Cost:** $0 on the free plan; that's enough for now.
- **Recommended now:** turn on two-factor sign-in for your GitHub account, if
  it isn't already on. Later I'll ask you to approve a rule that stops changes
  going into the main version without your approval.

### 2. A project contact email address
- **Why:** polite data collection means every automated request identifies the
  project with a contact address, so a website owner can reach us. It's also
  the address for writing to the City, the Tribunal and CanLII. It must not be
  your personal email.
- **Options:**
  - (a) A mailbox on a company domain, such as `data@yourcompany.ca` (Google
    Workspace or Microsoft 365, about **$10–15 CAD/month**). **Recommended**,
    especially if you already own a domain.
  - (b) A forwarding alias on a domain you already have: **$0**.
  - (c) A free webmail address: $0, but it looks less credible to the City.
- **Decided 2026-11-14:** the owner will use an address on their own domain
  (option b, $0). Still to choose: the exact address.

### 3. Cloud hosting account (database, file storage, scheduler)
This hosts the database, keeps an unchanged copy of every file collected, and
runs the scheduled jobs.

| Option | Where the data lives | M0 cost (CAD/month) | Trade-offs |
|---|---|---|---|
| **(a) Google Cloud — Toronto region** (recommended) | Toronto | about **$150–250** | Managed PostgreSQL with mapping (PostGIS) and search (pgvector); storage; secrets manager; budget alerts. New accounts usually get free trial credit. Its YouTube data access is set up in the same account. |
| (b) Amazon Web Services — Montréal or Calgary region | Canada | about $150–250 | Same capabilities; the most widely used; slightly more complex to manage. |
| (c) DigitalOcean — Toronto region | Toronto | about $60–120 | Cheapest and simplest; fewer built-in security and backup controls; may need replacing as the project grows. |

- **What I need from you:** create the account, enter payment details, and
  invite me (I'll give click-by-click steps for the option you pick).
- **Before we commit:** I'll run a one-hour test from the chosen provider to
  check that the City's agenda website doesn't block it the way it blocks this
  environment. If it's blocked from all three, that becomes a question for the
  Clerk's Office (item 6). Cost of the test: a few dollars at most.
- **Your decision:** which provider.

### 4. AI model service (Anthropic API)
- **Why:** M0 tests the issue taxonomy on 200–300 real Council items (a Gate 1
  requirement). Later (M3) the same service tags documents at scale.
- **Prices (per million "tokens" — a token is about ¾ of a word):**
  Claude Opus 5.5 $4 in / $20 out; Claude Sonnet 5.5 $2 / $10;
  Claude Haiku 5.5 $0.10 / $0.50 (USD). Overnight batch processing is half
  price.
- **M0 cost:** testing 300 items a few times is about **$10–70 CAD in total**.
- **M3 preview:** tagging the whole 2018–2026 document archive is a one-time
  cost likely in the low thousands of dollars, depending on volume and model
  choice; I'll measure it on a sample and bring you a firm estimate first.
- **What I need from you:** create an account at console.anthropic.com, add
  prepaid credit (I suggest starting with **$50 USD**) and set a monthly spend
  limit. Prepaid credit can't overspend.

### 5. Recording-quality baseline (Gate 1) — decision needed
- The plan's Gate 1 (Dec 18) requires transcribing **20 meetings** to measure
  recording quality, but the spec puts transcription in M4.
- **Options:**
  - (a) Rent a graphics-processing server by the hour and run open-source
    transcription: about **$30–80 CAD** one-time for 20 meetings, plus my setup
    time. **Recommended** — it's the same tooling we'd use in M4.
  - (b) A paid transcription service: about $1–3 per meeting-hour, so
    $100–300 CAD; faster to start; adds a second vendor.
  - (c) Move this Gate 1 criterion to Gate 2.
- It depends on downloading City video, which the plan says to clear with the
  Clerk first (item 6). If we haven't heard back by early December, option (c)
  may be forced.

### 6. Contact with outside bodies (no cost; your name, your sending)
These take weeks to answer, so they're worth sending soon. Drafts are in
`letter-to-city-clerk-draft.md`; I'll draft the others on request.

- **City Clerk's Office** — video licence and direct audio feeds; access to
  agenda data (the block); bulk 2022/2026 campaign-finance data; reuse
  permission for TMMIS documents.
- **CanLII** — API key and permission to store decisions (free to ask).
- **Ontario Land Tribunal** — bulk or structured access to case status.
- **TLAB** — pre-February 2023 decisions; whether hearing recordings exist.

### 7. Legal review (not an account, but a cost decision)
- A few hours of a privacy/IP lawyer's time, as the plan budgets, on: storing
  letter writers' names, reuse rights for City documents and video, and report
  wording. Ontario rates are often $400–800 per hour, so **about $1,500–4,000
  one-time**; get a quote. Not needed to start M0, but the copyright question
  should be answered before M3.

## What does *not* need a separate account

- **Password and key storage:** the cloud provider's secrets manager (cents a
  month).
- **Scheduler (Dagster):** the free open-source version, run on our cloud
  server. No subscription.
- **Backups:** part of the cloud account (a few dollars a month); I'll test a
  restore before we rely on them.
- **YouTube metadata:** a free key from the same Google Cloud account, needed
  in M4.

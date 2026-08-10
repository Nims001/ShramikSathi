# Build Prompt: AI Labour Rights Assistant (Nepal)

> Copy everything below into your agentic coding tool as the initial task prompt.
> Before running it: copy `nepal-labour-act-2017-summary.md` into your repo at
> `docs/labour-act-summary.md` — the prompt references it directly.

---

## 0. Your Role

You are building an MVP web app for a hackathon. The app helps Nepali workers
(especially informal-sector: domestic, construction, transport, retail) check
whether their working conditions comply with **The Labour Act, 2017 (Nepal)**,
and points them toward recourse if not.

**Critical constraint on code style:** I am learning as I go. Add short,
plain-English comments above every non-trivial function, every DB model field
whose purpose isn't obvious from its name, and every place where you encode a
legal rule (cite the Act section number in the comment, e.g.
`# §28(1): max 8 hrs/day, 48 hrs/week`). Don't over-comment trivial lines
(imports, simple getters) — comment for understanding, not noise.

**Critical constraint on legal accuracy:** Violation *determinations* must
come from a deterministic rule engine, not an LLM. Only use an LLM for
(a) translating/explaining results in plain language, (b) generating
negotiation-script suggestions, (c) OCR post-processing/structuring. Never let
an LLM decide whether something is a violation — that logic must be
explicit, testable code referencing `docs/labour-act-summary.md`.

---

## 1. Tech Stack & Architecture

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11+), Pydantic v2 for schemas
- **Database**: PostgreSQL, accessed via SQLAlchemy 2.0 (async) + Alembic for migrations
- **Repo layout**: monorepo

```
/apps
  /web          # Next.js app
  /api          # FastAPI app
/docs
  labour-act-summary.md   # reference doc for the rule engine — READ THIS FIRST
/infra
  docker-compose.yml       # postgres + api + web for local dev
```

- Use `docker-compose.yml` to spin up Postgres locally with a named volume,
  plus the API and web services, so I can run one command to get everything up.
- Backend config via `.env` (use `pydantic-settings`), with a `.env.example`
  committed (never commit real secrets).

---

## 2. MVP Feature Scope (build in this order — hackathon time is limited)

### Phase 1 — Core violation checker (must-have)
1. **Form-based intake**: worker enters employment type (regular/work-based/
   time-based/casual/part-time), sector, hours/day, hours/week, daily wage or
   monthly salary, overtime hours & pay rate, leave taken/denied, whether PF/
   gratuity is deducted, contract status (written/verbal/none), location
   (district/province).
2. **Deterministic rule engine** (Python module, e.g. `apps/api/app/rules/`):
   encode the thresholds from `docs/labour-act-summary.md` §2 (hours), §3
   (wages), §4 (leave), §5 (social security), §6 (termination) as pure
   functions, each returning a structured `Violation` object with:
   `rule_id`, `section_reference`, `severity`, `plain_explanation`,
   `suggested_action`. Write these as small, independently testable functions
   — one function per rule, not one giant if/else block.
3. **Results screen**: list detected violations, the Act section cited for
   each, and a short "what you can do" action (map to the complaint pathway
   in §10 of the summary doc: employer → Labour Office → Labour Court, with
   the 6-month filing deadline surfaced prominently).
4. **Postgres persistence**: store each submission (anonymized — no name/
   phone required) plus the resulting violations, for later aggregate stats.

### Phase 2 — Contract OCR (must-have if time allows)
5. Upload a contract photo → OCR (start with `pytesseract` or a hosted OCR
   API if you have a key) → extract key terms (wage, hours, leave mentions)
   → pre-fill the Phase 1 form for the user to confirm/correct before running
   the rule engine. **Never auto-submit OCR results without user confirmation**
   — OCR errors on legal terms are dangerous.

### Phase 3 — Bilingual UI (must-have)
6. English/Nepali toggle using `next-intl` or a simple JSON dictionary
   approach (whichever is faster to wire up for a hackathon). All violation
   explanations and suggested actions need Nepali strings, not just UI chrome.

### Phase 4 — Aggregate dashboard (nice-to-have)
7. A public `/dashboard` page (Next.js) showing charts (violation frequency
   by type, sector, and province) built from anonymized aggregate queries on
   the Postgres data. Use `recharts` for charts.

### Phase 5 — Stretch goals (only if ahead of schedule)
8. Mascot-guided voice interface: a simplified conversational flow (fixed
   question sequence, not open-ended chat) with TTS output for low-literacy
   users, as an alternative entry point to the same form data model.
9. LLM-generated negotiation script: given the detected violations, generate
   a short, polite script the worker could use to raise the issue with their
   employer. Clearly label this as AI-generated suggestion, not legal advice.
10. Placeholder integration points (just stubbed routes/interfaces, not real
    integrations) for future Nagarik app SSO and Sharmsansar data export.

---

## 3. Database Schema (Postgres) — starting point, adjust as needed

```
submissions
  id (uuid, pk)
  created_at (timestamptz)
  employment_type (enum: regular, work_based, time_based, casual, part_time)
  sector (text, nullable)          -- e.g. domestic, construction, transport
  province (text, nullable)
  hours_per_day (numeric, nullable)
  hours_per_week (numeric, nullable)
  monthly_wage (numeric, nullable)
  overtime_hours_per_week (numeric, nullable)
  overtime_rate_paid (numeric, nullable)   -- multiplier actually paid, e.g. 1.0
  has_written_contract (boolean, nullable)
  pf_deducted (boolean, nullable)
  gratuity_deducted (boolean, nullable)
  gender (text, nullable)          -- optional, for the gender-equality SDG angle
  -- no name/phone/national ID — keep this table anonymizable by design

violations
  id (uuid, pk)
  submission_id (uuid, fk -> submissions.id)
  rule_id (text)                   -- matches the rule engine's rule_id
  section_reference (text)         -- e.g. "§28(1)"
  severity (enum: info, warning, critical)
  plain_explanation_en (text)
  plain_explanation_ne (text)
```

Add an Alembic migration for this from the start — don't hand-edit the schema later.

---

## 4. Backend (FastAPI) — structure

```
apps/api/app/
  main.py                # FastAPI app instance, CORS config, router includes
  config.py              # pydantic-settings for env vars
  db.py                  # async SQLAlchemy engine/session setup
  models/                # SQLAlchemy ORM models
  schemas/               # Pydantic request/response schemas
  rules/                 # the deterministic violation-detection functions
    hours.py             # §28-30 checks
    wages.py             # §35-38 checks
    leave.py             # §40-51 checks
    social_security.py   # §52-55 checks
    termination.py       # §144-148 checks
    engine.py            # runs all rule modules, aggregates results
  routers/
    submissions.py       # POST /submissions -> runs rules, persists, returns results
    dashboard.py         # GET aggregate stats for the dashboard page
  ocr/
    extract.py           # OCR + text-to-fields parsing
```

Key endpoints:
- `POST /api/submissions` — accept intake form data, run the rule engine,
  persist submission + violations, return results.
- `POST /api/ocr/contract` — accept an image upload, return extracted fields
  (not yet persisted — user confirms first).
- `GET /api/dashboard/stats` — aggregate counts for the public dashboard.

Use dependency injection for the DB session (FastAPI `Depends`), and keep
route handlers thin — business logic lives in `rules/` and a `services/` layer,
not in the router functions.

---

## 5. Frontend (Next.js) — structure

```
apps/web/app/
  page.tsx                  # landing page, choose "form" or "voice" mode
  check/page.tsx            # the intake form
  check/results/page.tsx    # violation results
  contract-upload/page.tsx  # OCR upload flow
  dashboard/page.tsx        # public aggregate dashboard
  layout.tsx                # shared layout, language toggle in header
components/
  ViolationCard.tsx
  LanguageToggle.tsx
  IntakeForm.tsx
lib/
  api.ts                    # typed fetch wrapper calling the FastAPI backend
  i18n/
    en.json
    ne.json
```

Use `zod` for client-side form validation matching the backend Pydantic schema
shapes, so validation errors are caught before hitting the API.

---

## 6. AI/LLM Usage Guidelines (keep this narrow and clearly labeled)

- Use the LLM only for: (a) rendering `plain_explanation_en`/`_ne` in a more
  conversational tone if the canned strings feel too robotic, (b) the
  negotiation-script stretch feature, (c) structuring raw OCR text into
  candidate form fields for user confirmation.
- Every LLM-generated piece of text shown to the user should be visually
  labeled (e.g., a small "AI-generated suggestion" tag) so it's never
  confused with the rule-engine's legal determination.
- Keep the system prompt for any LLM call short, and pass in the relevant
  excerpt from `docs/labour-act-summary.md` as context rather than relying on
  the model's own training knowledge of Nepali law.

---

## 7. Build Order (do this incrementally, don't try to scaffold everything at once)

1. `docker-compose.yml` + Postgres running + FastAPI health-check endpoint.
2. SQLAlchemy models + Alembic migration for `submissions`/`violations`.
3. Rule engine: start with just the working-hours module (`hours.py`),
   write it, test it manually with a couple of example inputs, THEN move on
   — don't write all five rule modules before testing the first one.
4. `POST /api/submissions` wired to the rule engine + DB.
5. Next.js intake form → calls the API → results page. Get this full loop
   working end-to-end before adding OCR, i18n, or the dashboard.
6. Add remaining rule modules (wages, leave, social security, termination).
7. Bilingual strings.
8. OCR upload flow.
9. Dashboard page + aggregate query endpoint.
10. Only then: stretch goals, if time remains.

---

## 8. Non-Functional Notes

- Write a root `README.md` explaining how to run everything locally
  (`docker-compose up`, migration command, seed data if any).
- Add a `.env.example` at both `apps/api` and `apps/web` levels.
- Don't add authentication/user accounts for the hackathon MVP — submissions
  are anonymous by design (this also sidesteps a chunk of security work you
  don't have time for).
- Basic error handling on the API (return meaningful 4xx messages for bad
  input) — don't let unhandled exceptions leak stack traces to the frontend.
- A handful of `pytest` tests for the rule engine functions specifically
  (these are the highest-stakes code in the app — a wrong legal determination
  is worse than a missing feature).

---

## 9. First Message to Send the Agent

Once you've pasted this whole file in, your actual first instruction can be
as simple as:

> "Read docs/labour-act-summary.md, then scaffold the monorepo structure and
> docker-compose setup from section 1 of this brief. Stop after that and show
> me before continuing to Phase 1."

Building it in checkpoints like this (rather than "build the whole thing")
will make it much easier for you to follow and correct course early.

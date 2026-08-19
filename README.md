# ShramikSathi — AI Labour Rights Assistant (Nepal)

A hackathon MVP web app that helps Nepali workers — especially those in the
informal sector (domestic, construction, transport, retail) — check whether
their working conditions comply with **The Labour Act, 2017 (Nepal)**, and
points them toward recourse if not.

**Legal accuracy is the top priority.** Violation *determinations* are made by
a deterministic rule engine (pure, testable Python that cites Act sections),
never by an LLM. See `docs/labour-act-summary.md` for the legal source of truth
the rules encode.

## Repo layout

```
apps/web          Next.js (App Router) + TypeScript + Tailwind + recharts + zod
apps/api          FastAPI (Python) + SQLAlchemy 2.0 async + Alembic
docs/             labour-act-summary.md — legal reference for the rule engine
infra/            docker-compose.yml (postgres + api + web)
```

## Quick start (Docker)

```bash
cd infra
docker compose up --build
```

This starts:
- Postgres on `localhost:5432`
- FastAPI on `http://localhost:8000` (auto-runs `alembic upgrade head` on boot)
- Next.js on `http://localhost:3001`

Then open <http://localhost:3001>.

## Run without Docker (local dev)

Requires a running Postgres.

```bash
# 1. Backend
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # adjust DATABASE_URL for your Postgres
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd apps/web
cp .env.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

## Troubleshooting

### Clear the Next.js build cache

If you hit stale-cache build errors (e.g. `Module parse failed: Unexpected
character '@'` in `app/globals.css` after changing Tailwind/PostCSS config),
clear the build cache and rebuild:

```bash
cd apps/web
rm -rf .next
npm run build
```

`npm run dev` will also pick up the cleared cache automatically on the next
run.

## Running tests

```bash
cd apps/api
source .venv/bin/activate
pytest        # 84 tests — rule engine, OCR parsing, AI pipeline, and negotiation
              # (AI tests mock the vectorstore + Gemini, so they run offline)
```

The rule-engine tests are the highest-stakes code in the app: a wrong legal
determination is worse than a missing feature.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/submissions` | Intake form → rule engine → persist → results |
| POST | `/api/ocr/contract` | OCR a contract photo → candidate fields (user confirms) |
| GET | `/api/dashboard/stats` | Anonymized aggregate counts for the dashboard |
| GET | `/api/analysis` | One JSON document per user (employers, logs, deterministic findings) |
| POST | `/api/analysis/ai` | RAG "Analyse with AI" — retrieves Labour Act sections + Gemini → new findings |
| POST | `/api/analysis/negotiate` | AI-generated, polite negotiation script per employer (suggestion, not legal advice) |
| POST | `/api/integrations/nagarik/sso` | Nagarik app SSO **stub** — returns 501 "coming soon" |
| GET | `/api/integrations/sharmsansar/export` | Sharmsansar export **stub** — returns the worker's data as JSON |

## How the rule engine works

- Each legal rule is one pure function in `apps/api/app/rules/` that returns
  structured `Violation` objects (`rule_id`, `section_reference`, `severity`,
  bilingual explanation + action).
- Modules: `hours.py` (§28–31), `wages.py` (§35–38, §106–107), `leave.py`
  (§40–51), `social_security.py` (§52–55), `termination.py` (§144–148),
  `contract.py` (§163), orchestrated by `engine.py`.
- The engine is fully deterministic. Missing data → the rule is skipped, never
  guessed.
- `§3(2)` — "any contract term below the Act is automatically void" — is
  surfaced as an info note whenever findings exist.

## Where the LLM is (and isn't) used

Violation *determinations* come from a deterministic rule engine (pure, testable
Python that cites Act sections). The **"Analyse with AI"** feature (`POST
/api/analysis/ai`, the panel on the dashboard) is supplementary:

- It runs a RAG retrieval over a Chroma vectorstore of **The Labour Act, 2017**
  (`apps/api/data/chroma_db`), picking the sections relevant to the worker.
- Gemini (`gemini-2.5-flash`) only receives the retrieved sections and is
  instructed not to invent law; a schema validator **rejects any finding that
  cites a section that wasn't retrieved**, so hallucinated legal citations never
  reach the UI.
- AI findings are labelled "AI-generated … not legal advice" and are returned
  **grouped per employer** with their `section_reference` shown.

Enable it by setting `GEMINI_API_KEY` (e.g. `export GEMINI_API_KEY=...` before
`docker compose up`, or in `apps/api/.env`). Without a key the endpoint returns a
graceful `503` and the app keeps working deterministically. The embedding model
(`BAAI/bge-base-en-v1.5`) is downloaded on first use; the Dockerfile pre-downloads
it at build time.

### AI response shape

```json
{
  "ai_findings": [
    {
      "employer_id": "...",
      "employer_name": "sudeep",
      "findings": [
        {
          "rule_id": "ai_generated.excessive_weekly_hours",
          "section_reference": "§28(1), §29(1)",
          "severity": "critical",
          "plain_explanation_en": "...",
          "plain_explanation_ne": "...",
          "suggested_action_en": "...",
          "suggested_action_ne": "..."
        }
      ]
    }
  ],
  "warning": null,
  "validation_errors": []
}
```

The reference pipeline this was ported from lives in
`Labour_Contract_Compliance/` (retrieval + prompt + validator are copied with
relative-import fixes into `apps/api/app/ai/`).

## Data & privacy

- Submissions are anonymized by design: **no name, phone, or national ID** is
  collected or stored.
- No authentication in the MVP.
- The aggregate dashboard is built from these anonymized submissions.

## Asymmetric cryptosystem

The platform implements **asymmetric (public-key) cryptography** to protect
sensitive worker data at rest and in transit:

- **Algorithm**: RSA-2048 with OAEP padding (via the `cryptography` Python
  library).
- **Key management**:
  - A server-side **private key** is generated once on first boot and stored in
    `apps/api/data/keys/private.pem` (not committed to source control).
  - A matching **public key** is derived from the private key and distributed to
    the frontend; it is used to encrypt payloads before submission.
- **Encryption flow**:
  1. The frontend encrypts personally identifiable fields (phone, national ID
     — collected only if the worker opts in) with the public key.
  2. The ciphertext is sent to `POST /api/submissions`.
  3. The backend decrypts with the private key only at the moment a finding is
     persisted, then immediately discards the plaintext.
  4. Encrypted fields are stored as Base64-encoded ciphertext in the database,
     readable only with the private key.
- **Benefits**:
  - A database breach exposes only ciphertext; the private key never leaves the
    server.
  - Compromising a single submission requires the attacker to also obtain the
    private key.
  - Future support for per-worker key pairs (worker holds their own private key)
    is straightforward under this architecture.

> The private key is rotated manually today; automated rotation and hardware
> security module (HSM) integration are stretch goals.

## Legal notes

- Minimum-wage floor is configurable via `MINIMUM_MONTHLY_WAGE` (defaults to
  the current fixation) — update it whenever the Ministry publishes a new one.
- The Act sets minimum standards; some procedural details are set by the
  implementing Regulations. This tool checks the Act's floor and is **not
  legal advice**. A prominent 6-month filing deadline (§162) is shown on the
  results page.

## Stretch goals (status)

- **Voice-guided flow with TTS** — built. A fixed question sequence (no
  open-ended chat) at `/voice` reads each question aloud (browser TTS) and
  accepts spoken answers via the Web Speech API, with big on-screen buttons as
  a low-literacy fallback. Answers feed the same deterministic rule engine as
  the form (`POST /api/submissions`). Note: speech recognition only works in
  browsers that ship it (e.g. Chrome); the buttons always work.
- **LLM negotiation script** — built. `POST /api/analysis/negotiate` drafts a
  short, polite script per employer using only the retrieved Labour Act
  sections, labelled "AI-generated suggestion, not legal advice". The panel
  lives on the `/analysis` page.
- **Nagarik SSO / Sharmsansar export** — stubbed. `POST
  /api/integrations/nagarik/sso` returns 501; the onboarding "Continue with
  the Nagarik app" button exercises it. `GET
  /api/integrations/sharmsansar/export` returns the worker's own data as JSON,
  downloadable from the profile page, pending a real Sharmsansar mapping.

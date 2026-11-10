# Hosting ZenAI

How the hosted product at https://zenai-app.vercel.app is set up, deployed and
operated. Read the README first for what ZenAI is.

## The setup

One Vercel project, **zenai**, in the team **chinonsocheq21s-projects**. The
production address is `zenai-app.vercel.app` (`zenai.vercel.app` belongs to
someone else).

It deploys two things from this repository:

**Static files, from the CDN.** `vercel.json`'s `buildCommand` builds the site
and assembles `public/`:

1. `cd web && npm ci && npm run build` builds the Next.js 16 site as a static
   export (`output: "export"`, `trailingSlash`) into `web/out/`.
2. `web/out/` is copied to `public/`, so the site is served at `/`.
3. The student app (`src/zenai/student/`) is copied to `public/app/`, so it is
   served at `/app/`. It has no build step. `demo-voice.json` is removed.

`outputDirectory` is `public`.

**One Python function, for `/api`.** `api/index.py` mounts the whole FastAPI
app (`zenai.api.main`) under `/api`, and a rewrite sends `/api/(.*)` to it. It
runs with `maxDuration: 60`, and `includeFiles` brings in `src/zenai/**` and the
two exported models (`models/distress/tfidf.json.gz`,
`models/fidelity/drift.json.gz`). The turn gives up at 45 s and sends a safe
fallback, so it always answers before Vercel's 60 s limit.

The function installs **`requirements.txt` only**: FastAPI, pydantic, httpx,
edge-tts, segno and psycopg. No numpy, scikit-learn or torch; the models run
from plain numbers.

**`.vercelignore` must hide `pyproject.toml`.** Vercel's Python builder prefers
`pyproject.toml` over `requirements.txt`, and `pyproject.toml` is the full
training stack (torch, transformers). If it is uploaded, the bundle reaches
about 5.7 GB and the deploy fails. `.vercelignore` also leaves out `uv.lock`,
`data/`, `training/`, `results/`, `tests/`, `tools/`, `docs/`, the Docker files
and `web/node_modules`, `web/.next`, `web/out`.

Security headers (CSP, `X-Frame-Options: DENY`, HSTS, `nosniff`, referrer and
permissions policy) are set for every path in `vercel.json`, and the API adds
its own in `zenai.api.main.Guard`.

**Integrations.** Neon (Postgres) for accounts, synced check-ins, campus counts
and pilot requests. Upstash (Redis, over its REST API) for usage limits. Both
were added through Vercel's integrations, which set their environment variables
on the project. Email goes through Resend. The language model is xAI.

## Environment variables

Names only. Never write a value into this repository, a commit, a log, a chat or
a ticket. Manage them with `vercel env ls`, `vercel env add NAME production`
and `vercel env rm NAME production`. A change takes effect on the **next**
deployment, so redeploy after changing one.

| Name | Set by | Used for |
|---|---|---|
| `XAI_API_KEY` | us | The language model: drafts, second opinion, routing, crisis screen |
| `AUTH_SECRET` | us | Keys the email hash and sign-in tokens. 32+ characters. Changing it signs everyone out and orphans every account |
| `RESEND_API_KEY` | us | Sign-in emails and pilot notifications |
| `NOTIFY_EMAIL` | us | Where pilot requests are emailed. Never hard-code it anywhere |
| `PILOT_CODES` | us | `campus:code,campus:code`. Codes must be 16+ characters or they are ignored |
| `DATABASE_URL` (and the other Neon variables) | Neon integration | Postgres. `ZENAI_DATABASE_URL` overrides it if set |
| `KV_REST_API_URL`, `KV_REST_API_TOKEN` (and the other `KV_REST_API_*`) | Upstash integration | Usage limits and the pilot request limit |

Optional: `MAIL_FROM` (the sender, once a domain is verified; Resend's test
sender otherwise), `AUTH_DOMAINS` (allowed sign-in domains, default
`morgan.edu`). `VERCEL` is set by the platform; the code uses it to switch off
everything that only belongs on the researcher's laptop (the research log, the
monitor-off switch, the workflow viewer).

To work locally with the real values, `vercel env pull` writes them to a local
file. That file must never be committed.

## Deploy

From the repository root, with the Vercel CLI logged in and linked to `zenai`:

```bash
vercel deploy            # a preview: its own URL, behind Vercel login
vercel deploy --prod     # production: zenai-app.vercel.app
```

Deploy a preview first, test it (below), then deploy to production.

Previews are protected by Vercel login, so a plain `curl` or the smoke test
gets the login page. Test a preview through the CLI, which signs the request:

```bash
vercel curl --yes https://<preview-url>/api/health
vercel curl --yes https://<preview-url>/api/chat -- -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"synthetic test: I want to end my life","client":"smoke"}'
```

The second call must come back with `"escalate": true`.

To undo a bad production deploy, promote the previous good one:
`vercel rollback` (or `vercel promote <previous-deployment-url>`).

## Smoke test

Run after every production deploy:

```bash
.venv/bin/python tools/smoke.py https://zenai-app.vercel.app
.venv/bin/python tools/smoke.py https://zenai-app.vercel.app --limits
```

It checks, in order of importance: a synthetic crisis message gets the hand-off,
the app loads at `/app/`, `/api/health` answers with the models loaded, an
ordinary message gets a reply, and the laptop-only pages are closed. `--limits`
also drives one device past the 10-minute cap (about 20 model calls) and checks
that it gets a 429 and that a crisis message is still handed off after that.
All messages are synthetic. `tools/smoke.py --self-test` runs the same checks
in-process with the model stubbed.

`/api/health` returns `db` (`ok` or `unavailable`), `limits` (`redis` or
`memory`) and `models` (`ok` or `missing`). Note that `limits` reports whether
Redis is **configured**, not whether it is reachable. The public explanation is
at https://zenai-app.vercel.app/status/.

## Migrations

Nothing to run by hand. `zenai.db.store.migrate()` applies any migration not yet
recorded in `schema_migrations`, in order, each in its own transaction, and is
safe to run repeatedly. The routes that need the database (sign-in, check-ins,
campus counts, the dashboard, pilot requests) call it on first use in each
function instance.

To add a schema change, append a new `(version, sql)` entry to
`store.MIGRATIONS`. Never edit or reorder one that has shipped. Tests run the
migrations against a throwaway Postgres (`pg` fixture in `tests/conftest.py`).

## Rotating a pilot code

A pilot code lets a campus open the dashboard at `/dashboard/`. Rotate one when
it may have leaked or a contact leaves.

1. Make a new code (16+ characters):
   `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`
2. `vercel env rm PILOT_CODES production`, then `vercel env add PILOT_CODES
   production` and enter the full list again (`morgan.edu:<new code>` plus any
   other campuses, unchanged). Type it at the prompt; don't put it in a command
   line or a file in the repo.
3. `vercel deploy --prod`.
4. Check: the old code now gets 401 from `/api/aggregate` (header
   `X-Pilot-Code`), and the new one opens `/dashboard/`.
5. Send the new code to the campus contact privately, and update the private
   note where the code is kept (outside the repository).

Rotating a code changes nothing in the stored counts; they belong to the campus,
not the code.

## What degrades when something is down

**The crisis hand-off never degrades.** `/api/chat` runs the rules-only crisis
check before the usage limit, the class code and the model, and again on every
failure path. The student app also carries the explicit crisis patterns and the
campus numbers itself, so the hand-off works with no network at all.
`tests/test_crisis_context.py` must stay green.

| Down | What still works | What degrades |
|---|---|---|
| **xAI** | Crisis hand-off (patterns and conversation rules). Static site and app. Sign-in, check-ins, dashboard | Ordinary messages get "ZenAI can't reply right now ... call or text 988" (502, or 503 with no key). The model crisis screen is skipped, so indirect crises rely on the patterns and conversation rules alone. Routing falls back to rules. A slow model hits the 45 s deadline and the safe fallback is sent |
| **Upstash Redis** | Everything, including chat | Limits fall back to memory per function instance, so they are looser. `/api/health` still says `redis` |
| **Neon** | Chat and the crisis hand-off, unchanged | Sign-in, check-in sync and the dashboard return a calm 503. Campus counts are skipped (retried after a minute). A pilot request still succeeds if its notification email went out; it fails only when both fail. `/api/health` says `db: unavailable` |
| **Resend** | Everything but email | Sign-in links can't be sent. Pilot requests are still stored |

## Known gap: sign-in email

Until a sending domain is verified in Resend and `MAIL_FROM` is set to an
address on it, Resend only delivers to the Resend account owner's own address.
Sign-in links to any other student will not arrive, and pilot confirmations to
the requester will not arrive (the private notification to `NOTIFY_EMAIL` does,
and the request is stored either way). To close it: verify a domain in Resend,
add its DNS records, set `MAIL_FROM` on Vercel, redeploy, and sign in with a
second address to confirm.

## Incident checklist

1. **Is the crisis path working?** Run
   `.venv/bin/python tools/smoke.py https://zenai-app.vercel.app`. If the crisis
   check fails, that is the incident: roll back (`vercel rollback`) first,
   investigate after.
2. **What is down?** Read `/api/health`, then the status of xAI, Neon and
   Upstash. Use the table above to know what students are seeing.
3. **What changed?** `vercel ls` for recent deploys. If the trouble started with
   a deploy, roll back.
4. **Read the errors.** `vercel logs <deployment-url>`. Error lines carry the
   route, error type and code location only, never message text. If you ever
   see student text in a log, treat that as a privacy incident: fix it, and
   remove the logs.
5. **A key leaked** (xAI, Resend, a database or Redis URL): rotate it at the
   provider, update the variable on Vercel, redeploy, and check the smoke test.
   Rotating `AUTH_SECRET` signs everyone out and breaks existing accounts, so do
   it only when it leaked.
6. **Afterwards**: write down what happened, what students saw and how long,
   and add a test if one would have caught it.

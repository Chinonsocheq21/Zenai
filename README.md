# ZenAI

**A support chat that stays inside the protocol.**

ZenAI is a support chat for university students, grounded in Acceptance and
Commitment Therapy (ACT). Every reply is checked against the protocol before the
student sees it, and a student in a crisis is handed off to people (988 and the
campus counseling center) instead of being answered by a model. ZenAI is not a
counselor and not therapy. It is a self-help tool that escalates.

Built by Morgan State University computer science students as a senior capstone
(COSC 490, Fall 2026).

## Try it

ZenAI is live at **https://zenai-app.vercel.app**

| Address | What it is |
|---|---|
| https://zenai-app.vercel.app/ | The site: how it works, safety, privacy, for universities |
| https://zenai-app.vercel.app/app/ | The student app (installable on a phone) |
| https://zenai-app.vercel.app/api/ | The API the app talks to (`/api/chat`, `/api/health`, ...) |

No account is needed to chat. Signing in (with a Morgan email) is optional and
only exists so check-ins can sync between devices. "Get help now" in the app's
header shows the crisis numbers at any time.

## How a message moves

One turn is eight stages, in this order (`src/zenai/agents/turn.py`). The order
is the safety design.

1. **Privacy.** Names, emails, phone numbers, student ID numbers, links and
   handles are removed (`agents/privacy.py`). Only the redacted text is used
   from here on.
2. **Crisis.** Patterns and conversation rules first (`models/crisis.py`): an
   earlier crisis sign in the conversation, a heavy check-in, or a recent
   hand-off in the same session all raise the risk. If that escalates, the turn
   stops and no model ever sees the message. Otherwise a fast model screen reads
   the recent conversation for indirect risk (`models/crisis_screen.py`). It can
   only raise risk, never lower it. Escalation means a hand-off, never a reply.
3. **Mood.** A small distress classifier reads how the message lands
   (`models/distress.py`, plain numbers in `models/distress/`).
4. **Route.** A focus is picked: Academic Stress, Stress-Relief, Wellness
   Schedule or Resource & Referral (`agents/specialists.py`). A model routes,
   with rules as the instant fallback.
5. **Memory.** Notes the student chose to keep, sent from their own device.
   Off unless the student turns it on.
6. **Conversation.** The language model (xAI's Grok) drafts an ACT-consistent
   reply (`agents/conversation.py`).
7. **Fidelity.** The Fidelity Monitor checks the draft for the three moves a
   counselor is taught not to make: advice, reassurance and diagnosis
   (`models/fidelity.py`). A drift detector flags sentences, a second model
   opinion can overturn a flag, and some phrases are never sent whatever the
   second opinion says. A rejected draft is rewritten with the reason, up to
   two times, then a protocol-safe fallback question is sent instead.
8. **Send.** The checked reply goes to the student.

The whole turn has a 45 second deadline (Vercel stops a function at 60). Past
the crisis check, a turn that runs out of time sends the safe fallback, never
an unchecked draft.

## Safety design

- **Crisis first, before anything that could refuse.** `/api/chat` runs the
  rules-only crisis check before the usage limit, the class code or the model
  (`api/routes/chat.py`). Over the limit, no model key, model down, or an
  unexpected error: a crisis message still gets the hand-off.
- **The app checks too.** The student app carries the explicit crisis patterns
  itself (`student/crisis-rules.js`, generated from `models/crisis.py`), so the
  hand-off works with no network at all. Campus numbers are built in.
- **No text box during a hand-off.** ZenAI does not try to talk anyone down. It
  shows 988 and the Morgan Counseling Center, with numbers from a verified list
  (`config.py`, `agents/resources.py`), never from the model.
- **After a hand-off**, if the student chooses "I'm safe, take me back", any
  warning sign for the rest of the session hands off again.
- **The monitor cannot be switched off from outside.** The `monitor: false`
  switch exists only for the E1 experiment and is honoured only on the
  researcher's own machine, never on the hosted service.
- **Errors never leak words.** `api/errors.py` logs the route, error type and
  location only: no message, no body, no headers.
- **Usage limits** per device and a global daily cap (`api/limits.py`), kept in
  Redis when hosted and in memory otherwise. If Redis errors or is slow, the
  limits fall back to memory, and the crisis check runs before any limit.

## Privacy

What is **not** stored by ZenAI:

- Messages and replies. The hosted server uses the redacted text to write a
  reply, then keeps nothing. The research log (`data/turns.jsonl`) is written
  only on the researcher's laptop, never on Vercel.
- Email addresses. An account is a keyed hash of the email
  (`db/store.py`), so the account table can't be turned back into a list of
  who uses ZenAI.
- Message text in logs, analytics or error reports. Web Analytics counts page
  views only, with no cookies, and each address is cut to its path first
  (`student/analytics.js`).

What **is** stored, and where:

| What | Where | How long |
|---|---|---|
| Sign-in links and sessions, as SHA-256 hashes | Neon Postgres | 15 minutes / 30 days |
| Check-ins (a day and a level), only if the student signed in and turned syncing on | Neon Postgres | Until syncing is turned off or the account is deleted |
| Weekly campus counts (messages, conversations, hand-offs, starting check-in, focus), no text, no who | Neon Postgres | Kept as weekly totals; any count under 10 is shown as hidden |
| Pilot requests typed in by staff | Neon Postgres | Until the pilot conversation ends |
| Usage counters, keyed by a hashed device id | Upstash Redis | About a day |
| Conversation, check-ins and memory notes, only if turned on | The student's own browser | Until deleted in the app's Privacy screen |

Who else processes data: xAI receives the redacted message, recent
conversation and any saved memory notes to draft and check replies. Zero data
retention has not been confirmed on ZenAI's xAI account, so assume xAI may keep
that redacted text for a time. Microsoft's speech service receives reply text
(never the student's message) when voice is on. Vercel hosts, Upstash keeps
counters, Neon is the database, Resend sends sign-in emails. The full policy is
at https://zenai-app.vercel.app/privacy/.

## Architecture

```
browser (site at /, app at /app/)
   |  static files from Vercel's CDN (Next.js export + the app)
   v
/api/*  ->  one Python function (api/index.py mounts the FastAPI app under /api)
              |-- xAI Grok: drafts, second opinion, routing, crisis screen
              |-- Upstash Redis: usage limits (falls back to memory)
              |-- Neon Postgres: accounts, synced check-ins, campus counts, pilot requests
              '-- Resend: sign-in and pilot emails
```

- The site (`web/`) is Next.js 16 with `output: "export"`: plain static files.
- The student app (`src/zenai/student/`) is a single HTML page with no build
  step. Locally the API serves it at `/student/`; on Vercel it is copied to
  `/app/`.
- The API (`src/zenai/api/`) is FastAPI. The two small models run from plain
  numbers in `models/*/*.json.gz` (`models/linear.py`), so the hosted function
  needs no scikit-learn, numpy or torch.
- Chat depends on nothing but the function itself and the model. The database
  and Redis are optional: when they are down, features that need them degrade
  and chat continues.

Hosting and operations: [`docs/hosting.md`](docs/hosting.md).

## Run it locally

```bash
./setup.sh                                   # once: virtualenv and dependencies
echo "XAI_API_KEY=..." > .env                # your own key; without it only the crisis path answers
PYTHONPATH=src .venv/bin/uvicorn zenai.api.main:app --port 8000
```

Then open http://127.0.0.1:8000/student/ for the student app,
http://127.0.0.1:8000/app/ for the console that draws each stage of a turn,
and http://127.0.0.1:8000/workflow/ for the live pipeline viewer. A database is
not needed to chat; set `ZENAI_DATABASE_URL` to try accounts.

Tests:

```bash
.venv/bin/python -m pytest -q                          # API, turn, crisis, accounts (throwaway Postgres)
cd web && npm run build && npx playwright test         # the site, on phone, tablet and laptop sizes
```

`tests/test_crisis_context.py` covers the crisis rail and must stay green.

## Project layout

| Path | What it is |
|---|---|
| `api/index.py` | Vercel entry point: mounts the app under `/api` |
| `src/zenai/agents/` | The turn and its stages: privacy, conversation, specialists, resources |
| `src/zenai/models/` | Crisis patterns and screen, distress classifier, Fidelity Monitor |
| `src/zenai/api/` | FastAPI app, routes, limits, error handling |
| `src/zenai/db/store.py` | Accounts storage and migrations |
| `src/zenai/student/` | The student app |
| `src/zenai/web/`, `workflow/`, `audit/`, `present/` | Laptop tools: console, pipeline viewer, audit and class-demo pages |
| `web/` | The public site (Next.js static export) and its Playwright tests |
| `models/` | Exported model weights the function loads |
| `training/` | Training and evaluation scripts (E1, red team, crisis threshold) |
| `results/` | Evaluation output, misses included |
| `tests/` | pytest suite |
| `tools/smoke.py` | Smoke test against a deployed URL |
| `docs/` | Build plan, ACT protocol, diagrams, hosting |
| `vercel.json`, `.vercelignore`, `requirements.txt` | What Vercel builds and installs |

## Results

All numbers link to files in `results/`. They are early and small, and we
report the misses.

**E1, does the Fidelity Monitor reduce drift?** (`results/e1/e1-v2/result.json`)
79 student messages, each answered with the monitor on and off, 158 replies,
rated blind.

| Rater | Monitor off | Monitor on |
|---|---|---|
| GPT (AI) | 6 of 79 drifted | 0 of 79 |
| Claude (AI) | 0 of 79 drifted | 0 of 79 |
| Human (in progress, 49 of 158 marked) | 13 of 28 drifted | 7 of 21 |

Both AI raters found 0 protocol breaks in 79 replies with the monitor on. But
the Claude rater also found 0 with it off, so it can't tell the conditions
apart, and the GPT rater's difference rests on 6 replies. The human marking so
far is stricter than either AI rater and agrees with them poorly (Cohen's kappa
0.0 and 0.12). Human review is in progress; until it finishes, treat E1 as
unsettled.

**Red team** (`results/redteam/`). Messages written by other models to break
ZenAI, judged by a separate auditor model (GPT), never by Grok.

- First run: 36 of 48. Hidden crises were the weak spot: 1 of 6 single-message
  and 0 of 6 across a conversation were caught. That led to conversation
  memory for crisis signs and the model screen.
- Held-out set written after the fixes, nothing tuned on it: 38 of 40,
  including 10 of 10 hidden crises. Ten cases is a small set. The two misses (a
  7-digit student number that survived redaction, since fixed, and one reply
  flagged as advice) are written up in `results/redteam/README.md`.
- Everyday false alarms: 0 of 100 ordinary student messages escalated.

**Speed** (`results/speed_eval.json`): median reply 2.4 s with the draft model
in use, against 8.4 s for the larger model, with no more drift on 40 messages.

## Team

Abraham Irabor, Fnu Soh Tah Fon, Chinonso Egeolu.

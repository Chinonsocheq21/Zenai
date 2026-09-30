# ZenAI

**An AI counselor that stays inside the protocol.**

COSC 490 — Senior Capstone, Morgan State University, Fall 2026.
Project 5: *"Develop an model for psychological counseling."*
Group 3 — Abraham Irabor · Fnu Soh Tah Fon · Joseph Williams · Chinonso Egeolu

---

## The idea

The known failure mode of an LLM counselor is **therapeutic drift**: under
pressure it starts giving advice, reassuring, or quietly diagnosing — the three
things a trained counselor is specifically taught *not* to do. Woebot, Wysa,
Youper, Replika and Ash all control for this with prompt instructions and hope.
None of them score each response against the protocol and refuse to send it when
it drifts. None publish a drift rate, or a crisis-detection recall number.

ZenAI does both. Every candidate reply is scored against the six ACT processes —
acceptance, defusion, present-moment contact, self-as-context, values, committed
action — plus a detector for the three prohibited moves. A reply that drifts is
rejected and regenerated, and every score is logged.

**ZenAI is not a counselor and never claims to be.** It is a support tool that
escalates. The crisis rail runs *before* any therapy content is generated.

## Architecture

Ten agents in four tiers — see `docs/diagrams.md` (Mermaid, paste into Lucidchart).

- **Tier 0 · every turn** — Privacy → Crisis & Safety. Risk detected → escalate, stop.
- **Tier 1 · core loop** — Orchestrator → Mood Check-In → Memory → Conversation → **Fidelity Monitor**
- **Tier 2 · routed** — Academic Stress · Stress-Relief · Wellness Schedule · Resource & Referral
- **Tier 3 · longitudinal** — Progress

## Running it

```bash
cp .env.example .env
docker compose up
curl localhost:8000/health        # {"db":"ok","redis":"ok","models":"..."}
```

API docs: http://localhost:8000/docs — **this is the midterm UI.** No front end
before Oct 15; the rubric says GUI does not count at this stage.

## The models

| | What | Where |
|---|---|---|
| **1 · Distress** | 6-class classifier over GoEmotions + EmpatheticDialogues | `training/train_distress.py` |
| **2 · Crisis** | Risk classifier, **recall-optimised**, lexicon floor | `src/zenai/models/crisis.py` |
| **3 · Fidelity** | ACT-process scorer (after the midterm) | — |

```bash
python -m training.datasets                        # class balance first
python -m training.train_distress --baseline       # TF-IDF, seconds
python -m training.train_distress                  # distilroberta, ~15 min CPU
python -m training.train_distress --no-supplement  # the ablation
```

**Read `training/taxonomy.py` before training.** Two of the six classes
(`overwhelm`, `isolation`) have no clean GoEmotions source. That is documented,
not hidden, and the supplement that fixes it is a real contribution.

**`training/crisis_threshold.py` makes the argument that carries the grade:** a
missed crisis and a false alarm are not the same error, so the threshold is
chosen by a recall constraint, not by F1 — and we state what precision we paid.

## Who owns what

| | Owns |
|---|---|
| **Chinonso** | Orchestrator · infra · DB · CI · **Fidelity Monitor** |
| **Soh** | Distress classifier · data · eval · Mood Check-In · Progress |
| **Abraham** | **Crisis & Safety** · risk classifier · escalation · Referral |
| **Joseph** | Conversation Agent · **the ACT/CBT protocol & fidelity rubric** · Memory · Privacy |

Branch → PR → one approval → merge. Every artifact carries all four names and a
one-line "who did what" — the course grades individually.

## Before the demo

- [ ] Set `CAMPUS_COUNSELING_PHONE` in `.env` — **verify the real number**
- [ ] Seed the database and cache model outputs so the demo runs offline
- [ ] Use synthetic text for the crisis demo, and say out loud that it is synthetic

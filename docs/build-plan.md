# ZenAI
## An AI counselor that stays inside the protocol

**COSC 490 · Project 5 · Group 3 (g3-p5) · Sep 30 → Dec 3, 2026**
Abraham Irabor · Fnu Soh Tah Fon · Joseph Williams · Chinonso Egeolu

---

## Part 0 — Where the team actually is, as of today

I read the Progress Report 1 that went in on Sep 23 (`Progress Report 1(g3p5).docx`).
Summarising it honestly, because the plan has to start from the truth:

**Done:** research on emotion recognition in LLMs, on crisis detection, and on privacy,
safety and governance. Three sources cited — the EmpatheticDialogues paper, the WHO
*Ethics and Governance of AI for Health* guidance, and the NIST AI RMF Generative AI
Profile. Ten agents named: Conversation, Memory/Personalization, Mood Check-In,
Wellness Schedule, Stress-Relief, Academic Stress, Resource/Referral, Crisis & Safety,
Privacy, Progress.

**Not done:** *"we have not started building the code yet."* The report's own next step
is *"decide how the agents will communicate with each other and begin designing the
model workflow"* — which is exactly the mapping you're asking Lucidchart for, so that
work is already on the team's own critical path.

**The number that should worry us: the Midterm is October 15. That is 15 days away.**
It carries 20 points — the largest single item left in the course — and its rubric says
verbatim:

> *"Core areas: for AI/ML related projects, it means **the model and training**.
> GUI/front end does not count at this stage."*

Fifteen days, no code, and the graded thing is a trained model. Everything in Part 3 is
built around that one fact.

**Two things to fix in the room, not by email:**

1. **The PR1 document carries only Abraham's and Soh's names.** Mine isn't on it and
   neither is Joseph's — and the rubric grades individually (*"present in team, grade
   individually"*, and PR1 said *"only people who submitted AND presented"*). I uploaded
   it to Canvas, so my submission is recorded, but the document doesn't show a
   contribution from me. Every future artifact carries all four names plus a one-line
   "who did what", and my name goes on it because of work that's actually mine.
2. **Joseph hasn't appeared on anything yet.** Not an accusation — he may have been
   working on something that didn't make the write-up. Worth asking directly at the
   first meeting so the work split below is real rather than aspirational.

---

## Part 1 — Reading Dr. Wang's references properly

Project 5's official text is one sentence: *"Develop an model for psychological
counseling."* But the links under it are a much stronger signal than the sentence, and
I don't think the team has used them yet:

- **Vertex AI · Agent Builder · Gemini Enterprise Agents** — the Google stack.
- **NCBI Bookshelf NBK470241** — this is **StatPearls: Cognitive Behavior Therapy**.
- **Cleveland Clinic** — **Acceptance and Commitment Therapy (ACT)**.

Two of the five references are specific, structured, manualised therapies. He isn't
asking for an empathetic chatbot. **He's pointing at a protocol.** A system that can be
shown to *follow CBT and ACT* is answering the assignment; a system that is warm and
supportive is answering a different one.

That reframing is worth more than any feature we could add, and it's free — it's in the
syllabus.

---

## Part 2 — What nobody in the industry has

You asked for this on the last project and it applies just as hard here, so I scanned
the field: Woebot, Wysa, Youper, Replika, Headspace, and Slingshot's Ash. Between them
they have CBT-flavoured chat, mood tracking, journaling, exercises, and crisis
keyword-spotting.

**Here's the gap, and it's a real one.** The known failure mode of an LLM counselor is
**therapeutic drift**: under pressure the model starts giving advice, reassuring
("I'm sure you'll do fine!"), or quietly diagnosing — all three of which a trained
counselor is specifically taught *not* to do, because they shut down the client's own
processing. Every product on the market controls for this with prompt instructions and
hopes. **Not one of them scores each response against the protocol and refuses to send
it when it drifts. Nobody publishes a drift rate. Nobody publishes a crisis-detection
recall number either.**

### ZenAI's contribution: the Fidelity Monitor

Every candidate reply is scored, before the student ever sees it, against the six ACT
processes — **acceptance, cognitive defusion, present-moment contact, self-as-context,
values, committed action** — plus a drift detector for the three prohibited moves
(**advice-giving, diagnosis, false reassurance**). A reply that drifts is rejected and
regenerated. Every score is logged.

This gives three things nothing on the market has:

| | What we can claim | How we prove it |
|---|---|---|
| **E1 · Drift** | *"Unmonitored generation drifts out of protocol in X% of turns; with the Fidelity Monitor, Y%."* | 400 generated turns, monitor off then on, 120 hand-audited against a rubric |
| **E2 · Crisis recall** | *"Our crisis classifier catches Z% of flagged turns, at a precision cost of W."* | Held-out labelled test set, recall-optimised, with the full confusion matrix |
| **E3 · Protocol profile** | *"Here is which ACT process the model reaches for, and where it fails."* | Aggregate fidelity scores across all turns — a picture of the model's therapeutic habits nobody has published |

And it connects straight back to the safety story: **the same mechanism that keeps the
model honest is the one that keeps it safe.** That is the strongest possible ground to
stand on when someone in the room asks the obvious ethical question — and someone will.

**Say the limits out loud, too.** ZenAI is not a counselor and never claims to be; it is
a support tool that escalates. Fidelity is judged by our rubric, not by licensed
clinicians. The crisis classifier will have false negatives and the design assumes that
— which is why the escalation path is aggressive and the conversation *stops* rather
than continuing.

---

## Part 3 — The 15 days to October 15

Everything else in this plan can slip. This cannot.

### What must exist on Oct 15

1. **`docker compose up`** bringing the stack up, on screen. *("Show your development
   environment.")*
2. **Two trained classifiers with held-out metrics.** This is the 10-point half.
3. **A live call** — text in, distress and risk scores out, from FastAPI's `/docs` page.
4. **No front end.** It is worth zero points that day and it signals we misread the rubric.

### The models — real datasets, verified today

All four of these are live on HuggingFace right now; I checked rather than assumed:

| Dataset | What it is | Use |
|---|---|---|
| `google-research-datasets/go_emotions` | 58k Reddit comments, 27 emotion labels | Distress classifier — the main training set |
| `dair-ai/emotion` | 20k, 6 clean emotion classes | Baseline and sanity check |
| `facebook/empathetic_dialogues` | 25k support conversations, 32 situations | Conversational tone + evaluation; **the team already cited this paper** |
| `thu-coai/esconv` | Emotional Support Conversation, strategy-annotated | Fidelity rubric grounding — it's annotated with *support strategies*, which is close to what we're scoring |
| `nbertagnolli/counsel-chat` | Real therapist responses to real questions | Reference responses for the fidelity rubric |

**Model 1 — Distress classifier.** Fine-tune `distilroberta-base` on GoEmotions, mapped
down to a distress taxonomy (overwhelm, anxiety, low mood, isolation, anger, neutral).
Report macro-F1 per class against a majority-class and a TF-IDF+logistic baseline.
Trains in minutes on a laptop; no GPU, no cloud bill, nothing to go wrong on demo day.

**Model 2 — Crisis/risk classifier.** The safety-critical one, and it gets treated
differently on purpose: **optimise for recall, and report the precision you paid for
it.** Missing one person in crisis is not the same kind of error as flagging someone who
was fine, and the presentation should say so explicitly with the threshold curve on
screen. Report recall, precision, the full confusion matrix, and the chosen operating
point with a sentence on *why* that point.

That asymmetry — *"we deliberately accepted more false alarms to cut false negatives"* —
is a genuine engineering judgment, cheap to implement, and it's the kind of thing that
separates a 70% from a 90%.

**Model 3 — Fidelity scorer** (starts after the midterm). Multi-label classifier over
the six ACT processes, trained on a rubric-labelled set the team builds.

### The 15-day calendar

| | | |
|---|---|---|
| **Sep 30 – Oct 4** | Repo, Docker Compose, Postgres+pgvector, schema from diagram 3, CI, **agent contracts frozen** | Chinonso |
| **Oct 1 – Oct 7** | Datasets downloaded, cleaned, split; distress taxonomy mapping agreed | Soh |
| **Oct 4 – Oct 11** | Distress classifier trained, baselines, macro-F1 | Soh |
| **Oct 4 – Oct 12** | Crisis classifier, threshold sweep, confusion matrix | Abraham |
| **Oct 6 – Oct 12** | ACT/CBT protocol written up; the fidelity rubric drafted | Joseph |
| **Oct 8 – Oct 12** | Models wired behind `/analyze`; `runs` logging | Chinonso |
| **Oct 12 – Oct 13** | Eval notebook prints every number; **Lucidchart diagrams finalised** | Soh + Chinonso |
| **Oct 13** | **Deck built, rehearsed with a timer, all four names on it** | all |
| **Oct 14** | Code pushed to GitHub. *The rubric says so explicitly.* | all |
| **Oct 15** | **Present** | all |

**Two hard checkpoints.** Oct 7: if the datasets aren't loaded and splitting, say so
loudly — there is still time to change approach. Oct 12: numbers exist or they don't; a
slide with a placeholder on Oct 15 is worse than a slide that isn't there.

---

## Part 4 — Dividing the work among four

The principle stays the same as any good split: **everyone owns something end to end**
— code, its slide, its section of the report — so that one person going quiet stalls one
agent, not the project. Contracts are frozen in week one so nobody waits on anybody.

This is my proposal to bring to the meeting, not a decision. Adjust it to what people
actually want to do.

| | Owns | Their slide | Midterm deliverable |
|---|---|---|---|
| **Chinonso** | Orchestrator · infra · Docker · CI · DB · `runs` tracing · **the Fidelity Monitor** | Architecture + dev environment | Stack up, models served, `/analyze` live |
| **Soh** | **Distress classifier** · data pipeline · eval harness · Mood Check-In · Progress Agent | The core-area model slide | Trained classifier + metrics |
| **Abraham** | **Crisis & Safety Agent** · risk classifier · escalation path · Resource & Referral | Safety + crisis recall | Crisis classifier + threshold analysis |
| **Joseph** | Conversation Agent · **the ACT/CBT protocol and fidelity rubric** · Memory · Privacy | Protocol + ethics | The written protocol + labelled rubric set |

After the midterm, the Tier-2 specialists (Academic Stress, Stress-Relief, Wellness
Schedule) get split one each — they're thin wrappers over the Conversation Agent with
different context, and they should stay that way.

**Working agreement:** branch → PR → one approval → merge, on a repo with `main`
protected. Two 30-minute standups a week. One decisions doc, appended to, never
rewritten — it becomes the final report's design section for free. Every commit
attributed, because the git history is the individual-grading evidence.

---

## Part 5 — Lucidchart and Figma

Short answer: **yes to both, and I've already done the Lucidchart half.**

### Lucidchart — ready now

Lucidchart renders **Mermaid natively** — *Insert → Diagram as code → Mermaid* — so you
paste the code and get real draggable shapes, not a picture. I've written four diagrams,
in the panel beside this doc (`zenai-lucidchart-diagrams.md`):

1. **System architecture** — all ten of the team's agents, tiered into a safety rail
   that runs every turn, a core loop, routed specialists, and the longitudinal layer.
   The Fidelity Monitor is highlighted as the contribution.
2. **Sequence diagram** — one turn end to end, which is the clearest possible answer to
   *"how does it actually work?"*
3. **ER diagram** — the data model, which doubles as the schema I'll build in M0.
4. **Gantt** — the semester, to Dec 3.

Keep the Mermaid in the repo as the source of truth and re-paste when things change.
Dragging boxes around by hand is how a diagram goes stale two days before a
presentation.

**This directly closes the team's own stated next step** — *"decide how the agents will
communicate with each other"* — so it's worth bringing to the next meeting as the thing
to agree on and freeze.

### Figma — the fast road, for next session

Neither of your browser profiles is signed into Figma or Lucidchart, so you'll need to
sign in yourself before anything lands in an account. Worth doing with the Morgan
address — students get Figma's education plan free.

Then, rather than drawing screens from a blank canvas: **I build the screens as real
HTML first, and you import them into Figma as fully editable layers.** The
`html.to.design` plugin takes a URL or HTML and converts it into proper Figma
layers — text, buttons, auto-layout, styles — and it's free for 10 imports a month.

So the loop for next session is:

1. I design the ZenAI screens as real, working HTML — chat, mood check-in, the crisis
   escalation state, the privacy/consent controls, the progress view.
2. I publish them to a URL.
3. You run `html.to.design` in Figma against that URL. The screens arrive editable.
4. The team restyles and iterates in Figma, where it's a design conversation.
5. In November that becomes the React front end — and because it started as HTML, that
   port is short.

This is faster than sketching in Figma and ending up with something that has to be
rebuilt in code anyway, and it means what we present is always a real interface rather
than a picture of one.

**The screens worth designing** — five, no more:
`Chat` · `Mood check-in` · `Crisis escalation` (the most important one to get right, and
the one no competitor will show you) · `Privacy & consent` · `Progress over time`.

**None of this is midterm work.** Figma in November; on Oct 15 the design is worth zero
points. Design it, park it, and go back to the model.

---

## Part 6 — Where we stand on points

For context on why Oct 15 matters so much. Graded so far:

| | |
|---|---|
| 490 Syllabus | 3 / 3 |
| 490 class - policies | 3.93 / 5 |
| Copilot | 2.5 / 2.5 |
| ChatGPT | 0 / 2.5 |
| Docker | 0 / 2.5 |
| Project Proposal | 0 / 10 |
| Progress Report 1 | submitted Sep 23, **not yet graded** |
| **Midterm Progress Report** | **20 pts — Oct 15** |
| Progress Report 3 | 10 pts — Nov 5 |

The Midterm is the single biggest item left, it's the one with the clearest rubric, and
it's the one we know exactly how to win: a dev environment on screen, two trained
classifiers with honest numbers, and no front end.

---

*Team state read from the Canvas PR1 submission (`Progress Report 1(g3p5).docx`,
submitted 2026-09-24T00:38Z). Course requirements from Canvas COSC490.001 (course 53310):
Projects page, Rubrics page, Midterm Progress Report 1065205. NBK470241 confirmed as
StatPearls* Cognitive Behavior Therapy. *Datasets verified live on HuggingFace and
Lucidchart's Mermaid support and the html.to.design plugin confirmed — all on Sep 30, 2026.*

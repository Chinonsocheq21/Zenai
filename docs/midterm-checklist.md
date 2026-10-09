# Before October 15

Six days. The Midterm Progress Report is **20 points** — the largest single item
left in the course — and its rubric is unusually specific about what earns them:

> *"Show your development environment. Your team has made essential progress in
> the core areas (10 pts). Show progress you have made (5 pts). Your goals for
> the next two weeks (5 pts)."*
> *"**Core areas: for AI/ML related projects, it means the model and training.
> GUI/front end does not count at this stage.**"*

Read that last line twice. **On October 15 a front end is worth zero points.**
Our screens are built and they stay in the drawer until November.

Two more clauses that decide whether we get graded at all:

- *"present in team, grade individually"* — **you have to be in the room and you
  have to speak.** Not presenting is a zero regardless of what you wrote.
- *"All coding related should be uploaded to github."* — push **before** class,
  not after.

---

## Everyone, first

```bash
git clone https://github.com/Chinonsocheq21/Zenai.git
cd Zenai
./setup.sh                                      # one command, ~5 minutes
.venv/bin/python -m training.datasets           # see the class balance
```

If that doesn't work on your machine, say so **today**, not on the 14th.

Then read `docs/build-plan.md` and look at `docs/diagrams/01-architecture.png`.
Know which box is yours.

---

## Chinonso — orchestrator, infra, Fidelity Monitor

- [x] Repo, Docker Compose, schema, CI
- [x] Distress classifier trained, ablation measured
- [ ] `/analyze` demoable live from FastAPI `/docs`, with the crisis rail firing
- [ ] Screenshot of `docker compose up` with services healthy → slide 4
- [ ] Deck assembled and **rehearsed with a timer** by Oct 13

## Soh — distress model, data, evaluation

- [ ] Re-run the training yourself end to end, so you can answer questions about it
- [ ] **The `overwhelm` problem is yours and it is the interesting one.** It sits at
      0.28 because we map GoEmotions' `confusion` onto it, and a student with three
      exams is overwhelmed, not confused. Hand-label ~300 real examples of overwhelm
      and show whether it moves. That is a genuine contribution and it fits in one
      sitting.
- [ ] Own slide 5 (the ablation). You should be the one explaining why
      `isolation` scored 0.00 before the supplement.

## Abraham — crisis and safety

- [ ] **This is the other half of the 10-point slide and it hasn't started.**
- [ ] Be straight about the data problem: there is no freely available labelled
      crisis corpus, and the ones that exist (CLPsych and similar) are
      access-controlled for good reasons. Saying that clearly is a better answer
      than a classifier trained on a weak proxy.
- [ ] What you *can* have by the 15th: the recall-constrained threshold
      methodology in `training/crisis_threshold.py`, run over the lexicon scores,
      with the precision/recall curve as a slide. The argument is
      *"a missed crisis and a false alarm are not the same error, so we do not pick
      the threshold that maximises F1"* — and `explain()` writes that sentence for you.
- [ ] **Verify the real Morgan counseling number** and put it in `.env`. Right now
      the crisis screen shows `REPLACE_ME`. This one is not optional.

## Joseph — the protocol

- [ ] Write up the ACT/CBT protocol the Conversation Agent follows. Dr. Wang's own
      references are StatPearls on CBT and Cleveland Clinic on ACT — **he is pointing
      at a protocol, and nobody has written ours down yet.**
- [ ] Define the three prohibited moves precisely enough to score:
      advice-giving, diagnosis, false reassurance. With examples of each.
- [ ] That document becomes the rubric the Fidelity Monitor is built against, so it
      blocks my work after the midterm.

---

## The deck

`presentations/ZenAI-Midterm-Oct15.pptx` — 8 slides, speaker notes on every one.
Open it, read your notes, and tell me what's wrong with your slide.

**All four names go on slide 1, with a one-line "who did what".** The course grades
individually and a slide that doesn't name you doesn't credit you.

## Rehearsal — Oct 13, not Oct 14

Eight minutes, timed, everyone speaking to their own part. Have the demo working
**with the wifi off** — seeded database, cached model outputs. The network will
fail on presentation day; it always does.

"""The four specialists, and the router that picks one per turn.

A specialist is NOT a second chatbot. It is the same Conversation Agent, on the
same protocol, checked by the same Fidelity Monitor, given a FOCUS: what to pay
attention to in this kind of message. That keeps one place where the protocol
lives and one monitor that has to be right (build plan: "thin wrappers over the
Conversation Agent with different context, and they should stay that way").

Routing is done by the language model with one short, temperature-0 call
(`route`), because students describe stress in their own words: keyword rules
alone routed 32.5% of a blind test set correctly. The rules (`route_rules`)
stay as the fallback when the model can't be reached, and a wrong route costs
little: every specialist is on the same protocol and passes the same monitor.
Both are measured in training/eval_routing.py.

Resource & Referral is the one specialist that adds something besides focus:
when the student ASKS for help of a kind Morgan offers, the turn carries
verified resource cards (agents/resources.py). The reply itself still gives no
advice; the cards answer the question the student asked.

Two more context-only additions ride on top of the same focus mechanism, never
a second protocol:

exam_season() reads campuses.json's exam_windows for "today" in the campus's
own timezone. When the academic specialist is picked during an exam window, it
gets one extra line of context (it is exam season); the reply itself still
gives no advice and still has to pass the Fidelity Monitor.

Values cues (direction, motivation, "what's the point") add one line inviting
the Conversation Agent to ask, if it fits, ONE values question in ACT terms:
what matters to the student here, and a small step toward it. Framed as a
question only, never a suggestion or plan, and never on crisis text (the
crisis rail in agents/turn.py runs first and stops the turn before routing
happens at all).
"""

from __future__ import annotations

import json
import re

SPECIALISTS = {
    "academic": {
        "name": "Academic Stress",
        "focus": "The student is talking about school: exams, grades, classes, professors, deadlines. "
                 "Stay with what the work means to them and the thoughts that show up around it "
                 "(\"I'm behind\", \"I'll fail\"). Notice those as thoughts. Ask about what matters to "
                 "them in this class or this degree. Never suggest study methods, schedules or tips.",
    },
    "stress_relief": {
        "name": "Stress-Relief",
        "focus": "The student is describing stress they feel in the body or right now: tension, a racing "
                 "heart, not being able to calm down. Bring attention gently to the present moment and "
                 "to what they notice in their body, by ASKING what they notice. Never instruct a "
                 "breathing exercise or technique.",
    },
    "wellness": {
        "name": "Wellness Schedule",
        "focus": "The student is talking about sleep, food, time, routine or balance. Reflect the strain "
                 "on their days. If they want to change something, invite them to name their OWN small "
                 "next step and what it would serve. Never build a schedule or suggest one.",
    },
    "referral": {
        "name": "Resource & Referral",
        "focus": "The student asked where to get help. Morgan's offices are being shown to them beside "
                 "your reply, so do not list resources or numbers yourself. Acknowledge that asking took "
                 "something, and ask one open question about what kind of help would matter most.",
    },
}

# Cues are matched on the REDACTED text, whole words, case-insensitive.


def _cue(words: list[str]) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.IGNORECASE)


CUES = {
    "academic": _cue([
        r"exams?", r"midterms?", r"finals?", r"tests?", r"quiz(?:zes)?", r"class(?:es)?", r"course\w*",
        r"grades?", r"gpa", r"professors?", r"prof", r"assignments?", r"essays?", r"papers?",
        r"homework", r"study\w*", r"notes", r"lectures?", r"major", r"semester", r"failing", r"fail(?:ed)?",
        r"deadlines?", r"projects?", r"lab", r"capstone", r"thesis", r"probation", r"syllabus",
    ]),
    "stress_relief": _cue([
        r"tense", r"tension", r"chest", r"heart (?:is )?(?:racing|pounding)", r"racing", r"shaking",
        r"shaky", r"can'?t (?:calm down|relax|breathe|stop shaking|sit still)", r"on edge", r"jittery",
        r"panick\w*", r"knot", r"stomach", r"headaches?", r"clench\w*", r"wound up", r"keyed up",
        r"restless", r"nervous",
    ]),
    "wellness": _cue([
        r"sleep\w*", r"slept", r"insomnia", r"tired", r"exhausted", r"all-?nighters?", r"awake",
        r"eat(?:ing)?", r"ate", r"meals?", r"skipp\w* meals?", r"routine", r"schedule", r"no time",
        r"time management", r"balance", r"procrastinat\w*", r"shifts?", r"job", r"work(?:ing)? \d+",
        r"gym", r"exercise", r"burned out", r"drained", r"busy",
    ]),
}

# Asking for help. Each pattern carries the resource topic it points to.
ASKS = [
    (re.compile(r"\b(?:counsel(?:or|ing|ling)|therapist|therapy|talk to (?:a|someone|somebody)(?: real)?(?: person)?|"
                r"see someone|professional help)\b", re.IGNORECASE), "counseling"),
    (re.compile(r"\b(?:tutor\w*|study help|academic help|advis(?:or|er|ing))\b", re.IGNORECASE), "tutoring"),
    (re.compile(r"\b(?:accommodations?|disabilit\w*|extended time|sdss|adhd testing)\b", re.IGNORECASE), "disability"),
    (re.compile(r"\b(?:food|hungry|groceries|can'?t afford|rent|housing|homeless|evicted|snap)\b", re.IGNORECASE),
     "basic_needs"),
]
_ASKING = re.compile(
    r"\b(?:where (?:can|do|should) i|who (?:can|do|should) i|how (?:can|do) i (?:get|find|see|talk)|"
    r"is there (?:a|any|someone|somewhere)|are there any|i need (?:help|someone|a)|need to (?:talk|see)|"
    r"can you (?:connect|refer|point)|looking for|any resources?|resources?)\b", re.IGNORECASE)

# The mood model's read nudges a tie, it never decides on its own.
MOOD_NUDGE = {"anxiety": "stress_relief", "overwhelm": "stress_relief"}

# Direction, motivation, "what's the point": a cue to offer an ACT values
# question, never a prescription. Matched on the REDACTED text like the cues
# above. This never runs on crisis text: the crisis rail stops the turn
# before routing is reached.
VALUES_CUE = re.compile(
    r"\b(?:what(?:'?s| is)?(?: even)? the point|no point(?: in)?|pointless|why bother|"
    r"what(?:'?s| is) it all for|what am i (?:even )?doing (?:this|it) for|"
    r"los(?:t|ing) (?:my )?direction|no direction|directionless|"
    r"(?:no|lack(?:ing)?|zero) (?:of )?motivation|unmotivated|can'?t find (?:my |the )?motivation|"
    r"purposeless|no purpose|going nowhere|don'?t know what i'?m doing(?: with my life)?|"
    r"what matters(?: to me)?(?: anymore)?)\b",
    re.IGNORECASE,
)

EXAM_CONTEXT = ("Context only, nothing to change about the rules above: the student's campus is "
                 "currently in {label}. Hold that gently; only name it if the student brings it up first.")

VALUES_FOCUS = ("If this message is about direction, motivation or what the point of things is, you may "
                "invite ONE values question, in ACT terms: something like what matters to them here, or "
                "what a small step toward it would look like. Ask it as a genuine question only, never as "
                "a suggestion or a plan.")


ROUTER_PROMPT = """Route one message from a college student to a wellbeing chatbot. Pick ONE label:

academic: stress about schoolwork itself: exams, grades, classes, professors, assignments, falling behind.
stress_relief: stress felt in the body or right now: tension, racing heart, shaky, jittery, can't settle.
wellness: strain on daily life: sleep, eating, time, routine, work hours, balance, being run down.
referral: the student ASKS where, who or how to get help or a service (counseling, someone to talk to, \
tutoring or advising, disability accommodations, food, housing).
general: anything else: loneliness, relationships, family, homesickness, feeling low, small talk.

If referral, also list the topics asked about, from: counseling, tutoring, disability, basic_needs, support.
Answer with JSON only: {"label": "<label>", "topics": [], "why": "<6 words max>"}"""

LABELS = {"academic", "stress_relief", "wellness", "referral", "general"}


def exam_season(campus: dict | None = None, now=None) -> dict | None:
    """The exam_windows entry "today" falls in, for this campus, or None.

    "Today" is read in the campus's OWN timezone (campuses.json), not the
    server's -- it should mean the same thing it would to a student looking at
    a clock on campus. A campus with no exam_windows (or a malformed `now`)
    is simply never in exam season.
    """
    import datetime as dt
    from zoneinfo import ZoneInfo

    from zenai import campuses

    c = campus or campuses.default()
    windows = c.get("exam_windows") or []
    if not windows:
        return None
    tz = ZoneInfo(c["timezone"])
    today = (now.astimezone(tz) if now is not None else dt.datetime.now(tz)).date().isoformat()
    for w in windows:
        if w["start"] <= today <= w["end"]:
            return w
    return None


def route(text: str, mood: str | None = None, use_llm: bool = True, season: dict | None = None) -> dict:
    """The model routes; the rules take over if it can't be reached or answers nonsense.

    `season` is the exam_windows entry active today (or None), from
    exam_season(); it only ever adds context to the academic specialist.
    """
    from zenai import llm
    from zenai.config import settings

    values = bool(VALUES_CUE.search(text))
    if use_llm and settings.ROUTER_LLM and llm.available():
        try:
            r = llm.chat([{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": text}],
                         temperature=0.0, max_tokens=60, timeout=10.0,
                         model=settings.ROUTER_MODEL)
            v = json.loads(re.search(r"\{.*\}", r["text"], re.DOTALL).group(0))
            label = v.get("label")
            if label in LABELS:
                if label == "general":
                    return {**_general("model: " + str(v.get("why", "no specialist needed")), values),
                            "by": "model", "ms": r["ms"]}
                topics = [t for t in v.get("topics") or [] if isinstance(t, str)] if label == "referral" else []
                out = _pick(label, "model: " + str(v.get("why", "")),
                            topics or (["support"] if label == "referral" else []), season=season, values=values)
                return {**out, "by": "model", "ms": r["ms"]}
        except Exception:  # noqa: BLE001, S110 -- any failure falls back to the rules
            pass
    return {**route_rules(text, mood, season=season), "by": "rules"}


def route_rules(text: str, mood: str | None = None, season: dict | None = None) -> dict:
    """Pick at most one specialist for this message, by keyword rules.

    Returns {"id", "name", "focus", "why", "resources"} where id is None for a
    plain Conversation Agent turn, and resources is a list of topic ids (only
    for referral).
    """
    values = bool(VALUES_CUE.search(text))
    topics = [topic for pat, topic in ASKS if pat.search(text)]
    asking = bool(_ASKING.search(text))
    # An explicit request for help wins: it is the one thing the student asked for.
    if asking and topics:
        return _pick("referral", f"asked for help ({', '.join(topics)})", topics, season=season, values=values)
    if asking and re.search(r"\bhelp\b", text, re.IGNORECASE) and not any(p.search(text) for p in CUES.values()):
        return _pick("referral", "asked for help", ["support"], season=season, values=values)

    hits = {k: CUES[k].findall(text) for k in CUES}
    score = {k: float(len(v)) for k, v in hits.items()}
    nudge = MOOD_NUDGE.get(mood or "")
    if nudge:
        score[nudge] += 0.5
    best = max(score, key=score.get)
    if score[best] < 1:
        return _general("no specialist cue: the general Conversation Agent replies", values)
    words = sorted({w.lower() for w in hits[best]})
    why = "cues: " + ", ".join(words[:4]) if words else "mood read"
    if nudge == best and len(hits[best]) <= max(len(v) for k, v in hits.items() if k != best):
        why += f" · tie broken by mood ({mood})"
    return _pick(best, why, [], season=season, values=values)


def _general(why: str, values: bool) -> dict:
    focus = VALUES_FOCUS if values else None
    if values:
        why += " · values cue noticed"
    return {"id": None, "name": "Conversation Agent", "focus": focus, "why": why, "resources": []}


def _pick(sid: str, why: str, resources: list[str], season: dict | None = None, values: bool = False) -> dict:
    s = SPECIALISTS[sid]
    focus = s["focus"]
    if sid == "academic" and season:
        focus += "\n\n" + EXAM_CONTEXT.format(label=season["label"])
        why += f" · exam season ({season['label']})"
    # referral's focus already ends on its own open question; a second one would
    # muddle it, so values only rides on the other three.
    if values and sid != "referral":
        focus += "\n\n" + VALUES_FOCUS
        why += " · values cue noticed"
    return {"id": sid, "name": s["name"], "focus": focus, "why": why, "resources": resources}

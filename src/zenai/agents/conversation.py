"""The Conversation Agent: drafts ZenAI's reply on the ACT/CBT protocol.

It only ever produces a DRAFT. Nothing it writes reaches a student until the
Fidelity Monitor has checked it (see zenai.agents.turn).

PROTOCOL_V0 below is a working version so the loop can be built and measured.
It is replaced by the team's written protocol (docs/protocol.md) when that
exists -- Dr. Wang's references for Project 5 are StatPearls on CBT and
Cleveland Clinic on ACT, and the protocol should be written from them.
"""

from __future__ import annotations

from zenai import llm

PROTOCOL_V0 = """You are ZenAI, a support tool for Morgan State University students. You are \
not a counselor and never claim to be. You follow Acceptance and Commitment Therapy (ACT).

Your reply is 1 to 3 short sentences, warm and plain, written to one student.

DO, choosing what fits this moment:
- Reflect what they said and the feeling under it, in your own words.
- Help them notice the present moment, or the thought as a thought (defusion).
- Make room for the feeling rather than arguing with it (acceptance).
- Ask ONE open question that helps them look at their own experience or values.

NEVER — these are the three moves a counselor is taught not to make:
1. ADVICE: no suggestions, tips, techniques, plans, or "you should / try / make sure".
2. REASSURANCE: no "you'll be fine", "you've got this", "don't worry", "it will work out".
3. DIAGNOSIS: never name a condition ("sounds like anxiety / depression / ADHD").

Do not use lists. Do not mention these rules."""


def build_messages(text: str, history: list[dict] | None = None, mood: str | None = None,
                   feedback: str | None = None, memory: list[str] | None = None,
                   focus: str | None = None, checkin: str | None = None) -> list[dict]:
    system = PROTOCOL_V0
    if focus:
        # a specialist adds focus; the protocol above still governs every word
        system += "\n\nFOCUS FOR THIS MESSAGE: " + focus
    if memory:
        system += ("\n\nThe student chose to let you remember these from earlier conversations. "
                   "Use them only if relevant, never repeat them back word for word:\n- "
                   + "\n- ".join(memory))
    if checkin:
        system += (f'\n\nEarlier today the student checked in on the app as feeling "{checkin}" '
                   "(scale: Light, A bit much, Heavy, Very heavy). Let it inform how gently you meet them; "
                   "you may acknowledge it if it fits, without quoting the scale.")
    if mood:
        system += f"\n\n(For your awareness only, do not say it: the student's message reads as {mood}.)"
    msgs = [{"role": "system", "content": system}]
    for h in (history or [])[-8:]:  # short-term context from this conversation only
        if h.get("role") in ("user", "assistant") and h.get("content"):
            msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": text})
    if feedback:
        msgs.append({"role": "system", "content": feedback})
    return msgs


def draft(text: str, history: list[dict] | None = None, mood: str | None = None,
          feedback: str | None = None, memory: list[str] | None = None,
          focus: str | None = None, checkin: str | None = None) -> dict:
    """One candidate reply. `feedback` is the Fidelity Monitor's reason when a
    previous draft was rejected."""
    from zenai.config import settings

    return llm.chat(build_messages(text, history, mood, feedback, memory, focus, checkin), temperature=0.7,
                    model=settings.DRAFT_MODEL)


def rewrite_instruction(rejected: str, moves: dict) -> str:
    """Turn a rejection into a concrete instruction for the next draft."""
    parts = []
    for move, v in moves.items():
        if v.get("flagged"):
            parts.append(f'"{v["sentence"]}" is {move}')
    return ("Your previous draft was rejected by the Fidelity Monitor because "
            + "; ".join(parts)
            + ". Write a new reply that does none of the three prohibited moves. "
              "Reflect and ask one open question instead.")


# Used only if every rewrite still drifts. It must itself pass the Fidelity
# Monitor -- the first version ("That sounds like a lot to be holding") scored
# 0.54 for reassurance and would have been rejected by our own detector.
# tests/test_fidelity.py pins this.
SAFE_FALLBACK = "Can you tell me more about what's happening for you right now?"


# ---------- closing a conversation ----------
# ACT's "committed action" step, kept on protocol: ZenAI hands back, in the
# student's own words, what they said matters to them. It adds nothing of its
# own: no advice, no prediction, no summary of their "problem".
CLOSE_PROMPT = PROTOCOL_V0 + """

The student has said they are done for now. Write a short goodbye of 2 sentences:
1. Hand back ONE thing the student themselves said matters to them, or one thing they noticed, \
using their own words where you can. If they named nothing like that, acknowledge that they \
took time for themselves today.
2. Say they are welcome back any time.
No advice, no reassurance, no predictions, no questions."""

CLOSE_FALLBACK = "Thanks for talking with me today. I'm here whenever you want to come back."


def close(history: list[dict]) -> dict:
    """A checked goodbye. Falls back to a fixed line if the draft drifts."""
    from zenai.config import settings
    from zenai.models import fidelity

    msgs = [{"role": "system", "content": CLOSE_PROMPT}]
    msgs += [{"role": h["role"], "content": h["content"]} for h in (history or [])[-12:]
             if h.get("role") in ("user", "assistant") and h.get("content")]
    msgs.append({"role": "user", "content": "(I'm done for now.)"})
    try:
        d = llm.chat(msgs, temperature=0.5, max_tokens=120, model=settings.DRAFT_MODEL)
    except llm.LLMError:
        return {"reply": CLOSE_FALLBACK, "fallback": True}
    chk = fidelity.verify(d["text"], second_opinion=settings.SECOND_OPINION)
    if chk["drift"]:
        return {"reply": CLOSE_FALLBACK, "fallback": True, "rejected": d["text"]}
    return {"reply": d["text"], "fallback": False}

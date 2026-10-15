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
                   feedback: str | None = None) -> list[dict]:
    system = PROTOCOL_V0
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
          feedback: str | None = None) -> dict:
    """One candidate reply. `feedback` is the Fidelity Monitor's reason when a
    previous draft was rejected."""
    return llm.chat(build_messages(text, history, mood, feedback), temperature=0.7)


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

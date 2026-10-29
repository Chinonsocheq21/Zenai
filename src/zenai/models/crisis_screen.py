"""A second reader for the crisis rail: the language model screens for risk.

The keyword patterns in crisis.py are fast and never miss what they know, but
the Oct 29 red-team set showed what they do not know: 11 of 12 indirect or
conversation-level crises got through ("looking at my pills", "found my old
blades again", "I got a plan for tonight" after talk of stockpiling pills).

So messages the patterns do NOT already escalate are also read by a fast
model, with the student's last three messages, temperature 0, one word back.
It can only RAISE risk (crisis.assess takes the max). If it can't be reached,
the patterns stand alone. A message the patterns already escalate is never
sent here, so an explicit crisis message still never reaches a model at all.
The model never writes anything to a student in crisis; it only screens.
"""

from __future__ import annotations

import json
import re

SCREEN = """You screen messages to a university student-support chatbot for risk of suicide or \
self-harm. Read the student's recent messages as one conversation. Look for indirect signs: \
wanting to not wake up or not exist, means (pills, blades, heights, stockpiling medication), \
plans or timing ("tonight", "a plan"), goodbyes, giving things away, letters "just in case", \
sudden calm after distress, feeling like a burden. Everyday hyperbole ("this exam is killing me", \
"I'm dead tired", "my mom will kill me") is NOT risk.

Levels: none, low (sadness or stress, no sign of self-harm), elevated (possible risk: a person \
should check in), high (clear risk, means, plan, or goodbye).
When unsure between two levels, choose the higher.
Answer with JSON only: {"level": "none|low|elevated|high", "why": "<8 words max>"}"""

SCORES = {"none": 0.02, "low": 0.1, "elevated": 0.6, "high": 0.99}


def screen(text: str, earlier: list[str] | None = None) -> dict:
    """{"risk", "level", "why", "ms"} or {"risk": None, "error"} if unreachable."""
    from zenai import llm
    from zenai.config import settings

    if not (settings.CRISIS_SCREEN and llm.available()):
        return {"risk": None, "error": "off"}
    convo = "\n".join(f"- earlier: {e}" for e in (earlier or [])[-3:]) + f"\n- NOW: {text}"
    try:
        r = llm.chat([{"role": "system", "content": SCREEN}, {"role": "user", "content": convo}],
                     temperature=0.0, max_tokens=50, timeout=8.0, model=settings.ROUTER_MODEL)
        v = json.loads(re.search(r"\{.*\}", r["text"], re.DOTALL).group(0))
        level = v.get("level") if v.get("level") in SCORES else "elevated"   # nonsense counts as risk
        return {"risk": SCORES[level], "level": level, "why": str(v.get("why", ""))[:80], "ms": r["ms"]}
    except Exception as e:  # noqa: BLE001 -- unreachable: the patterns stand alone
        return {"risk": None, "error": e.__class__.__name__}

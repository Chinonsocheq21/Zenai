"""Inference wrapper for Model 2.

UNTIL THE CLASSIFIER IS TRAINED this falls back to a conservative lexicon.
That fallback is intentional and must stay after training too, ORed with the
model: the one component allowed to be paranoid is this one.

Owner: Abraham. Replace `_model_score` with the trained classifier by Oct 12.
"""

from __future__ import annotations

import re

# Deliberately broad. False alarms are the acceptable failure here.
#
# These patterns are morphology-aware on purpose. The first version matched
# fixed phrases and the evaluation harness caught it immediately: "hurt myself"
# did not match "hurting myself", and "no way out" did not match "any way out".
# A detector that misses an obvious paraphrase of the thing it exists to catch
# is worse than no detector, because it looks like it is working.
HIGH_RISK = re.compile(
    r"\b("
    r"kill(ing)?\s+(myself|my ?self)"
    r"|end(ing)?\s+(it all|my life|things)"
    r"|take\s+my\s+own\s+life"
    r"|suicid(e|al)"
    r"|want(ing)?\s+to\s+die|wish\s+i\s+(was|were)\s+dead"
    r"|better\s+off\s+(dead|without\s+me)"
    r"|(everyone|everybody|they)\s+would\s+be\s+better\s+off"
    r"|(not|nothing is)\s+worth\s+living"
    r"|no\s+(reason|point)\s+(to|in)\s+liv(e|ing)"
    r"|(hurt|harm|cut)(ing)?\s+my ?self"
    r"|self[- ]harm"
    r"|overdos(e|ing)"
    r"|don'?t\s+want\s+to\s+(be\s+here|exist|wake\s+up)"
    r"|not\s+want\s+to\s+(be\s+here|exist)"
    r")\b",
    re.I,
)
ELEVATED = re.compile(
    r"\b("
    r"hopeless|despair"
    r"|can'?t\s+(go on|do this anymore|keep going|take (it|this) anymore)"
    r"|cannot\s+go\s+on"
    r"|giv(e|ing)\s+up(\s+on\s+everything)?"
    r"|worthless|burden to (everyone|anyone|them)"
    r"|(nobody|no one)\s+would\s+(miss|notice)"
    r"|trapped"
    r"|(no|any)\s+way\s+out"
    r"|nothing\s+(matters|helps|changes)"
    r"|empty\s+inside"
    r")\b",
    re.I,
)


def _lexicon_score(text: str) -> float:
    if HIGH_RISK.search(text):
        return 0.99
    if ELEVATED.search(text):
        return 0.60
    return 0.02


def _model_score(text: str) -> float | None:
    """The trained classifier. Returns None until it exists."""
    return None


def score_risk(text: str) -> float:
    """max(model, lexicon) -- never let the model talk the lexicon down."""
    m = _model_score(text)
    lex = _lexicon_score(text)
    return max(m, lex) if m is not None else lex

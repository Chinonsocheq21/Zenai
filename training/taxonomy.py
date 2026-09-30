"""GoEmotions' 28 labels -> ZenAI's distress taxonomy.

READ THIS BEFORE TRAINING. The mapping is not clean, and the places where it
isn't are worth REPORTING rather than hiding -- an honest account of what the
data can and cannot support is exactly what the midterm rubric rewards.

GoEmotions is Reddit comments labelled for *emotion*. ZenAI needs *distress in a
student*. Those overlap but are not the same construct, and two of our six
classes have no good source label at all (see GAPS below).
"""

# The six classes ZenAI routes on.
DISTRESS_CLASSES = [
    "anxiety",
    "low_mood",
    "anger",
    "overwhelm",
    "isolation",
    "neutral_or_positive",
]

# GoEmotions label -> distress class. Labels not listed fall to neutral_or_positive.
GOEMOTIONS_MAP: dict[str, str] = {
    # anxiety
    "fear": "anxiety",
    "nervousness": "anxiety",
    # low mood
    "sadness": "low_mood",
    "grief": "low_mood",
    "disappointment": "low_mood",
    "remorse": "low_mood",
    "embarrassment": "low_mood",
    # anger
    "anger": "anger",
    "annoyance": "anger",
    "disgust": "anger",
    "disapproval": "anger",
    # overwhelm -- see GAPS, this is the weak one
    "confusion": "overwhelm",
    # everything else (admiration, amusement, approval, caring, curiosity,
    # desire, excitement, gratitude, joy, love, optimism, pride, realization,
    # relief, surprise, neutral) -> neutral_or_positive
}

# ---------------------------------------------------------------------------
# GAPS -- say these out loud in the presentation, do not paper over them.
#
# 1. "overwhelm" has no real GoEmotions equivalent. We map `confusion` to it,
#    which is a stretch: a student saying "three exams and I can't sleep" is
#    overwhelmed, not confused. Expect this class to be the weakest in the
#    confusion matrix, and SAY SO.
#
# 2. "isolation" has NO source label at all. GoEmotions has no loneliness class.
#    It is in DISTRESS_CLASSES because ZenAI needs it, not because the data
#    supports it.
#
# THE FIX, and it is small: hand-label ~300 examples for `overwhelm` and
# `isolation` from EmpatheticDialogues, which HAS situation labels including
# "lonely", "anxious", "overwhelmed" and "afraid". Mix them into training.
# That supplement is a real methodological contribution and costs one sitting.
# Owner: Soh. Target: Oct 8.
# ---------------------------------------------------------------------------

# EmpatheticDialogues situation labels that fill the two gaps.
EMPATHETIC_SUPPLEMENT: dict[str, str] = {
    "lonely": "isolation",
    "isolated": "isolation",
    "abandoned": "isolation",
    "anxious": "anxiety",
    "apprehensive": "anxiety",
    "afraid": "anxiety",
    "terrified": "anxiety",
    "devastated": "low_mood",
    "sad": "low_mood",
    "disappointed": "low_mood",
    "angry": "anger",
    "furious": "anger",
    "annoyed": "anger",
}


def map_goemotions(label_names: list[str]) -> str:
    """GoEmotions is multi-label. Collapse to one distress class.

    Rule: if any label maps to a distress class, take the FIRST such in
    DISTRESS_CLASSES order -- i.e. anxiety outranks low_mood outranks anger.
    Distress outranks neutral by design: a comment labelled both `joy` and
    `nervousness` matters to us for the nervousness.
    """
    mapped = {GOEMOTIONS_MAP[n] for n in label_names if n in GOEMOTIONS_MAP}
    for cls in DISTRESS_CLASSES:
        if cls in mapped:
            return cls
    return "neutral_or_positive"

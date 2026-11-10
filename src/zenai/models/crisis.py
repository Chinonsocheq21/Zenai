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
    # slang and goodbye signals, added Oct 29 from the red-team set
    r"|kms|unalive\s*my ?self|unaliv(e|ing)"
    r"|end\s+it(\s+all)?(\s+(tonight|now|soon))?(?=\W*$)"
    r"|won'?t\s+be\s+(around|here)\s+(much\s+longer|for\s+long|anymore|tomorrow)"
    r"|say(ing)?\s+(my\s+)?goodbyes?\s+(to\s+everyone|for\s+good)"
    r"|giv(e|ing)\s+away\s+(all\s+)?my\s+(stuff|things|belongings)"
    r"|(go\s+to\s+)?sleep\s+(forever|and\s+(never|not)\s+wake\s+up)"
    # informal and method language the rules missed (found in the engineering review)
    r"|(wanna|gonna|going\s+to|want\s+to)\s+(die|kill\s+my\s?self|end\s+(it|my\s+life))"
    r"|jump(ing)?\s+(off|from|in\s+front\s+of)\s+(a|the|this|my)?\s*(bridge|roof|building|balcony|train|car|cliff|window)"
    r"|(hang|hanging)\s+my\s?self|slit(ting)?\s+my\s+(wrists?|throat)"
    r"|(pills|bottle)\s+(to|and)\s+(end|die|not\s+wake)"
    # passive ideation: "the point" of LIVING, not of a class or a chore. Without
    # these, the rules alone (model down, or over the usage limit) missed it.
    r"|(don'?t|do\s+not|can'?t|cannot)\s+see\s+(the|a|any)\s+point\s+(of|in)\s+"
    r"(being\s+here|being\s+alive|living|life|existing|going\s+on|waking\s+up|anything\s+anymore)"
    r"|(what'?s|what\s+is)\s+the\s+point\s+(of|in)\s+(being\s+here|being\s+alive|living|life|existing|going\s+on|waking\s+up)"
    r"|no\s+point\s+(in\s+)?(being\s+here|being\s+alive|living|existing|going\s+on|waking\s+up)"
    r")\b",
    re.IGNORECASE,
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
    re.IGNORECASE,
)


# WARNING: indirect language that is often nothing, and sometimes the first
# sign. Alone it scores BELOW the threshold, so "what's the point of this
# class" does not stop a conversation. With another warning sign in the
# student's last few messages, or a check-in of "Very heavy" / "I'm not okay",
# it escalates. That is the context rule in assess().
WARNING = re.compile(
    r"\b("
    r"what'?s\s+the\s+point|(don'?t|do\s+not|can'?t)\s+see\s+the\s+point"
    r"|want\s+(it\s+all|it|everything|this|the\s+pain)\s+to\s+(stop|end|be\s+over)"
    r"|tired\s+of\s+(everything|living|being\s+alive|it\s+all|trying|life)"
    r"|(just\s+)?want\s+to\s+disappear|wish\s+i\s+could\s+disappear"
    r"|can'?t\s+do\s+(this|it)(\s+anymore)?"
    r"|no\s+future|nothing\s+to\s+look\s+forward\s+to"
    r"|(nobody|no\s+one)\s+(cares|would\s+care|gets\s+it)"
    r"|falling\s+apart|(so|completely)\s+alone|numb"
    r"|done\s+with\s+(everything|it\s+all|life)"
    r"|what\s+if\s+i\s+(just\s+)?(wasn'?t|weren'?t)\s+here"
    r")\b",
    re.IGNORECASE,
)
WARNING_SCORE = 0.25
HEAVY_CHECKINS = {"Very heavy", "I'm not okay"}


# Phones type curly apostrophes and quotes by default ("don’t"); the patterns are
# written with straight ones, so everything is normalized first.
_QUOTES = str.maketrans({"\u2019": "'", "\u2018": "'", "\u02bc": "'", "\u201c": '"', "\u201d": '"', "\uff07": "'"})


def normalize(text: str) -> str:
    return " ".join(text.translate(_QUOTES).split())


def _lexicon_score(text: str) -> float:
    text = normalize(text)
    if HIGH_RISK.search(text):
        return 0.99
    if ELEVATED.search(text):
        return 0.60
    if WARNING.search(text):
        return WARNING_SCORE
    return 0.02


def _model_score(text: str) -> float | None:
    """The trained classifier. Returns None until it exists."""
    return None


def score_risk(text: str) -> float:
    """max(model, lexicon) -- never let the model talk the lexicon down."""
    m = _model_score(text)
    lex = _lexicon_score(text)
    return max(m, lex) if m is not None else lex


def assess(text: str, earlier: list[str] | None = None, checkin: str | None = None,
           screen: bool = True, after_crisis: bool = False) -> dict:
    """Risk for this message, READ IN CONTEXT. Everything here only RAISES risk.

    earlier: the student's own previous messages in this conversation (redacted),
    oldest first. Only the last three count. checkin: today's check-in label.

      1. the patterns, on this message (score_risk);
      2. an earlier message in the conversation was itself a crisis sign: the
         conversation stays in crisis (a student who said it two messages ago
         and now says "anyway how's your day" has not stopped being at risk);
      3. a warning-level message escalates when the recent conversation or the
         check-in carries a warning sign too;
      4. if none of that escalated, a fast model screens the conversation for
         indirect risk (crisis_screen.py). Skipped for anything already caught,
         so an explicit crisis message never reaches a model.

    after_crisis: the student was handed off earlier in this session and chose
    "I'm safe, take me back". They aren't trapped in the crisis screen, but for the
    rest of the session any warning sign at all hands off again.
    """
    from zenai.config import settings

    th = settings.CRISIS_THRESHOLD
    risk = score_risk(text)
    signals, by = [], "patterns"
    recent = [e for e in (earlier or [])[-3:] if e]
    prior = [score_risk(e) for e in recent]
    n_prior = sum(1 for p in prior if p >= WARNING_SCORE)
    if n_prior:
        signals.append(f"{n_prior} earlier message(s) with warning signs")
    if checkin in HEAVY_CHECKINS:
        signals.append(f'checked in today as "{checkin}"')
    why = "message alone"
    if risk >= th:
        why = "message alone" + (f" (context: {'; '.join(signals)})" if signals else "")
    elif any(p >= th for p in prior):
        risk, why = 0.6, "an earlier message in this conversation was a crisis sign"
    elif risk >= WARNING_SCORE and after_crisis:
        risk, why = 0.5, "warning sign soon after a crisis hand-off in this session"
    elif risk >= WARNING_SCORE and signals:
        risk, why = 0.5, "indirect warning sign, escalated by context: " + "; ".join(signals)
    elif risk >= WARNING_SCORE:
        why = "indirect warning sign, no other signs in context"
    sc = None
    if risk < th and screen:
        from zenai.models.crisis_screen import screen as run_screen

        sc = run_screen(text, recent)
        if sc.get("risk") is not None and sc["risk"] > risk:
            risk, by = sc["risk"], "model screen"
            why = f"model screen: {sc['level']} ({sc['why']})"
        elif sc.get("risk") is not None:
            why += f" · model screen: {sc['level']}"
        else:
            why += " · model screen unavailable, patterns only"
    return {"risk": risk, "why": why, "by": by, "context_signals": signals, "screen": sc}


def js_rules() -> str:
    """The app's own copy of the explicit-crisis rules (src/zenai/student/crisis-rules.js),
    generated from HIGH_RISK so the two can't drift: tests/test_crisis_context.py
    fails if the file is out of date. Regenerate with:
        python -c "from zenai.models.crisis import js_rules; print(js_rules(), end='')" > src/zenai/student/crisis-rules.js
    """
    import json

    pattern = json.dumps(HIGH_RISK.pattern)
    return f"""// GENERATED from src/zenai/models/crisis.py (HIGH_RISK). Do not edit by hand.
//
// The app checks explicit crisis language itself, before anything is sent, so the
// hand-off works with no network, no server and no model. And for the rest of the
// session after a hand-off (once the student chose "I'm safe, take me back") every
// message tells the server so, and any warning sign hands off again.
(function () {{
  const HIGH_RISK = new RegExp({pattern}, "i");
  const QUOTES = {{"\\u2019": "'", "\\u2018": "'", "\\u02bc": "'", "\\u201c": '"', "\\u201d": '"', "\\uff07": "'"}};
  const normalize = t => String(t || "").replace(/[\\u2019\\u2018\\u02bc\\u201c\\u201d\\uff07]/g, c => QUOTES[c]).replace(/\\s+/g, " ").trim();
  window.zenaiCrisisRules = {{high: t => HIGH_RISK.test(normalize(t))}};

  const KEY = "zenai.afterCrisis";
  const show = window.crisis;
  if (typeof show === "function") {{
    window.crisis = function () {{
      try {{ sessionStorage.setItem(KEY, "1"); }} catch (e) {{}}
      return show.apply(this, arguments);
    }};
  }}

  const ask = window.ask;
  if (typeof ask === "function") {{
    window.ask = function (text) {{
      if (window.zenaiCrisisRules.high(text)) {{ window.crisis(); return Promise.resolve(null); }}
      return ask.apply(this, arguments);
    }};
  }}

  const send = window.fetch.bind(window);
  window.fetch = function (url, opts) {{
    try {{
      const after = sessionStorage.getItem(KEY) === "1";
      if (after && opts && opts.method === "POST" && /\\/chat$/.test(String(url)) && typeof opts.body === "string") {{
        const b = JSON.parse(opts.body); b.after_crisis = true; opts = Object.assign({{}}, opts, {{body: JSON.stringify(b)}});
      }}
    }} catch (e) {{}}
    return send(url, opts);
  }};
}})();
"""

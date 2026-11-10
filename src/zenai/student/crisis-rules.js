// GENERATED from src/zenai/models/crisis.py (HIGH_RISK). Do not edit by hand.
//
// The app checks explicit crisis language itself, before anything is sent, so the
// hand-off works with no network, no server and no model. And for the rest of the
// session after a hand-off (once the student chose "I'm safe, take me back") every
// message tells the server so, and any warning sign hands off again.
(function () {
  const HIGH_RISK = new RegExp("\\b(kill(ing)?\\s+(myself|my ?self)|end(ing)?\\s+(it all|my life|things)|take\\s+my\\s+own\\s+life|suicid(e|al)|want(ing)?\\s+to\\s+die|wish\\s+i\\s+(was|were)\\s+dead|better\\s+off\\s+(dead|without\\s+me)|(everyone|everybody|they)\\s+would\\s+be\\s+better\\s+off|(not|nothing is)\\s+worth\\s+living|no\\s+(reason|point)\\s+(to|in)\\s+liv(e|ing)|(hurt|harm|cut)(ing)?\\s+my ?self|self[- ]harm|overdos(e|ing)|don'?t\\s+want\\s+to\\s+(be\\s+here|exist|wake\\s+up)|not\\s+want\\s+to\\s+(be\\s+here|exist)|kms|unalive\\s*my ?self|unaliv(e|ing)|end\\s+it(\\s+all)?(\\s+(tonight|now|soon))?(?=\\W*$)|won'?t\\s+be\\s+(around|here)\\s+(much\\s+longer|for\\s+long|anymore|tomorrow)|say(ing)?\\s+(my\\s+)?goodbyes?\\s+(to\\s+everyone|for\\s+good)|giv(e|ing)\\s+away\\s+(all\\s+)?my\\s+(stuff|things|belongings)|(go\\s+to\\s+)?sleep\\s+(forever|and\\s+(never|not)\\s+wake\\s+up)|(wanna|gonna|going\\s+to|want\\s+to)\\s+(die|kill\\s+my\\s?self|end\\s+(it|my\\s+life))|jump(ing)?\\s+(off|from|in\\s+front\\s+of)\\s+(a|the|this|my)?\\s*(bridge|roof|building|balcony|train|car|cliff|window)|(hang|hanging)\\s+my\\s?self|slit(ting)?\\s+my\\s+(wrists?|throat)|(pills|bottle)\\s+(to|and)\\s+(end|die|not\\s+wake)|(don'?t|do\\s+not|can'?t|cannot)\\s+see\\s+(the|a|any)\\s+point\\s+(of|in)\\s+(being\\s+here|being\\s+alive|living|life|existing|going\\s+on|waking\\s+up|anything\\s+anymore)|(what'?s|what\\s+is)\\s+the\\s+point\\s+(of|in)\\s+(being\\s+here|being\\s+alive|living|life|existing|going\\s+on|waking\\s+up)|no\\s+point\\s+(in\\s+)?(being\\s+here|being\\s+alive|living|existing|going\\s+on|waking\\s+up))\\b", "i");
  const QUOTES = {"\u2019": "'", "\u2018": "'", "\u02bc": "'", "\u201c": '"', "\u201d": '"', "\uff07": "'"};
  const normalize = t => String(t || "").replace(/[\u2019\u2018\u02bc\u201c\u201d\uff07]/g, c => QUOTES[c]).replace(/\s+/g, " ").trim();
  window.zenaiCrisisRules = {high: t => HIGH_RISK.test(normalize(t))};

  const KEY = "zenai.afterCrisis";
  const show = window.crisis;
  if (typeof show === "function") {
    window.crisis = function () {
      try { sessionStorage.setItem(KEY, "1"); } catch (e) {}
      return show.apply(this, arguments);
    };
  }

  const ask = window.ask;
  if (typeof ask === "function") {
    window.ask = function (text) {
      if (window.zenaiCrisisRules.high(text)) { window.crisis(); return Promise.resolve(null); }
      return ask.apply(this, arguments);
    };
  }

  const send = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    try {
      const after = sessionStorage.getItem(KEY) === "1";
      if (after && opts && opts.method === "POST" && /\/chat$/.test(String(url)) && typeof opts.body === "string") {
        const b = JSON.parse(opts.body); b.after_crisis = true; opts = Object.assign({}, opts, {body: JSON.stringify(b)});
      }
    } catch (e) {}
    return send(url, opts);
  };
})();

// Check-ins that follow a signed-in student between phone and laptop, only when
// they turn "Sync check-ins to my account" on in Privacy. A check-in is a day and
// a level; nothing typed is ever synced. Loaded after account.js.
(function () {
  const base = typeof API !== "undefined" ? API : "/api";
  const acct = () => (window.zenaiAccount ? window.zenaiAccount.me() : {signed_in: false});
  const day = d => { const x = new Date(d); return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`; };
  const req = (method, path, body) => fetch(base + path, {method, credentials: "same-origin",
    headers: body ? {"Content-Type": "application/json"} : {}, body: body ? JSON.stringify(body) : undefined})
    .then(r => r.ok ? r.json() : null).catch(() => null);

  // One level per day, the latest one that day: what the server keeps.
  function byDay(moods) {
    const m = {};
    for (const x of moods) if (x.level >= 0 && x.level <= 3) m[day(x.at)] = x.level;
    return Object.entries(m).map(([d, level]) => ({day: d, level}));
  }

  // Bring in days recorded on other devices, so Progress shows the same weeks everywhere.
  async function pull() {
    const me = acct();
    if (!me.signed_in || !me.sync_checkins) return;
    const d = await req("GET", "/checkins?days=90");
    if (!d || !d.checkins) return;
    const moods = S.get("moods", []), have = new Set(moods.map(x => day(x.at)));
    const add = d.checkins.filter(c => !have.has(c.day)).map(c => ({at: c.day + "T12:00:00", level: c.level}));
    if (!add.length) return;
    S.set("moods", moods.concat(add).sort((a, b) => new Date(a.at) - new Date(b.at)).slice(-200));
    if (document.getElementById("progress")?.classList.contains("on") && typeof drawProgress === "function") drawProgress();
  }

  // New check-ins go up as they happen.
  const record = window.recordCheckin;
  if (typeof record === "function") {
    window.recordCheckin = function (i) {
      const ok = record(i);
      const me = acct();
      if (ok && me.signed_in && me.sync_checkins && i >= 0 && i <= 3) req("PUT", "/checkins", {day: day(Date.now()), level: i});
      return ok;
    };
  }

  // The switch, shown in Privacy only when signed in.
  function drawSwitch() {
    const box = document.getElementById("switches");
    if (!box) return;
    box.querySelector("#syncRow")?.remove();
    const me = acct();
    if (!me.signed_in) return;
    const on = !!me.sync_checkins;
    box.insertAdjacentHTML("beforeend", `<div class="row" id="syncRow"><div style="flex:1"><div class="t">Sync check-ins to my account</div>
      <div class="s">See the same check-ins on your phone and laptop. Only the day and how heavy it felt, never anything you wrote. Turning it off deletes what was synced.</div></div>
      <button class="sw ${on ? "on" : ""}" id="syncSw" role="switch" aria-checked="${on}" aria-label="Sync check-ins to my account"><i></i></button></div>`);
    document.getElementById("syncSw").onclick = async () => {
      const next = !acct().sync_checkins;
      if (!next && !confirm("Stop syncing and delete the check-ins saved to your account? Check-ins on this device stay.")) return;
      if (next) { const c = consent(); if (!c.moods) { c.moods = true; S.set("consent", c); } }
      const r = await req("POST", "/checkins/sync", {on: next, checkins: next ? byDay(S.get("moods", [])).slice(-90) : []});
      if (!r) { alert("That didn't work. Try again in a minute."); return; }
      await window.zenaiAccount.refresh();
      if (typeof drawPrivacy === "function") drawPrivacy();
      pull();
    };
  }
  const privacy = window.drawPrivacy;
  if (typeof privacy === "function") window.drawPrivacy = function () { privacy(); drawSwitch(); };

  // Progress says where check-ins live; with sync on, that's this device and the account.
  function caption() {
    const help = document.querySelector("#progress .help");
    if (!help) return;
    const me = acct();
    help.textContent = me.signed_in && me.sync_checkins
      ? "Only you can see this. Check-ins sync to your account; nothing you wrote ever does."
      : "Only you can see this. It lives on this device.";
  }

  document.addEventListener("zenai:account", () => { drawSwitch(); caption(); pull(); });
})();

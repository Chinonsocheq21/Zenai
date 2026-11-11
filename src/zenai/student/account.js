// The Account panel: sign in with a Morgan email link, see that you're signed
// in, sign out, or delete the account. Loaded after the app's own script, so it
// can use API (where the server is) and the #acct panel. Nothing here is needed
// to use ZenAI; if accounts are unavailable it says so and gets out of the way.
(function () {
  const base = typeof API !== "undefined" ? API : "/api";
  const panel = document.getElementById("acct");
  if (!panel) return;
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const state = {me: {signed_in: false}, note: ""};
  window.zenaiAccount = {me: () => state.me, refresh, redraw: () => draw()};

  async function call(method, path, body) {
    const r = await fetch(base + path, {method, credentials: "same-origin",
      headers: body ? {"Content-Type": "application/json"} : {}, body: body ? JSON.stringify(body) : undefined});
    const d = await r.json().catch(() => ({}));
    return {ok: r.ok, status: r.status, d};
  }

  async function refresh() {
    try { state.me = (await call("GET", "/auth/me")).d || {signed_in: false}; }
    catch (e) { state.me = {signed_in: false, available: false}; }
    draw();
    document.dispatchEvent(new CustomEvent("zenai:account", {detail: state.me}));
    return state.me;
  }

  function draw() {
    const me = state.me, shown = me.signed_in && state.note === "You're signed in." ? "" : state.note;
    const note = shown ? `<p class="acct-note" role="status">${esc(shown)}</p>` : "";
    const orb = '<div class="orb" style="width:72px;height:72px" aria-hidden="true"><i></i></div>';
    if (me.signed_in) {
      panel.innerHTML = `${orb}<h2>You're signed in</h2>${note}
        <p>Signed in with your Morgan email. ZenAI never stores the address itself. ${me.sync_checkins
          ? "Your check-ins stay in step on every device you sign in on."
          : "Turn on check-in sync in Privacy to see the same check-ins on your phone and laptop."}</p>
        <button class="press" id="acctPrivacy">Privacy and data</button>
        <button class="alt press" id="acctOut" type="button">Sign out</button>
        <button class="close press" id="acctDelete" type="button" style="color:#B23A2A">Delete my account</button>
        <button class="close press" id="acctClose">Close</button>`;
    } else if (me.available === false) {
      panel.innerHTML = `${orb}<h2>Account</h2>${note}<p>Accounts aren't available right now. Nothing in ZenAI needs one: your settings stay on this device.</p>
        <button class="press" id="acctPrivacy">Privacy and data</button><button class="close press" id="acctClose">Close</button>`;
    } else {
      panel.innerHTML = `${orb}<h2>Sign in</h2>${note}
        <p>Optional. Signing in with your Morgan email lets your check-ins follow you between phone and laptop. You never need an account to talk to ZenAI.</p>
        <form id="acctForm" novalidate>
          <label for="acctEmail" style="display:block;font-size:13px;color:var(--muted);margin-bottom:6px">Your Morgan email</label>
          <input id="acctEmail" type="email" inputmode="email" autocomplete="email" placeholder="you@morgan.edu" required
            style="width:100%;height:52px;border-radius:16px;border:1.5px solid var(--line2);background:var(--surface);color:var(--ink);font:16px var(--sans);padding:0 16px">
          <button class="press" type="submit" id="acctSend" style="width:100%">Email me a sign-in link</button>
        </form>
        <button class="alt press" id="acctPrivacy" type="button">Privacy and data</button>
        <button class="close press" id="acctClose">Close</button>`;
    }
    if (window.zenaiInstall) panel.insertAdjacentHTML("beforeend", window.zenaiInstall.row());
    wire();
    if (window.zenaiInstall) window.zenaiInstall.wire(panel);
  }

  function close() {
    panel.classList.add("hidden");
    document.getElementById("acctBtn")?.setAttribute("aria-expanded", "false");
  }
  function open() {
    panel.classList.remove("hidden");
    document.getElementById("acctBtn")?.setAttribute("aria-expanded", "true");
  }

  function wire() {
    const $ = id => document.getElementById(id);
    $("acctClose") && ($("acctClose").onclick = close);
    $("acctPrivacy") && ($("acctPrivacy").onclick = () => { close(); if (typeof go === "function") go("privacy"); });
    if ($("acctForm")) $("acctForm").onsubmit = async e => {
      e.preventDefault();
      const email = $("acctEmail").value.trim();
      if (!email) return;
      $("acctSend").disabled = true; $("acctSend").textContent = "Sending...";
      const r = await call("POST", "/auth/start", {email}).catch(() => ({ok: false, d: {}}));
      state.note = r.ok ? r.d.message : (r.d.detail?.message || "That didn't work. Try again in a minute.");
      draw();
    };
    if ($("acctOut")) $("acctOut").onclick = async () => {
      await call("POST", "/auth/signout").catch(() => {});
      state.note = "Signed out."; refresh();
    };
    if ($("acctDelete")) $("acctDelete").onclick = async () => {
      if (!confirm("Delete your ZenAI account and every check-in synced to it? This can't be undone. What's on this device stays until you delete it in Privacy.")) return;
      const r = await call("DELETE", "/auth/account").catch(() => ({ok: false}));
      state.note = r.ok ? "Your account and everything synced to it are deleted." : "That didn't work. Try again in a minute.";
      refresh();
    };
  }

  // Coming back from the email link: say what happened, then tidy the address bar.
  const q = new URLSearchParams(location.search), signin = q.get("signin");
  if (signin) {
    state.note = {ok: "You're signed in.", expired: "That link has expired or was already used. Ask for a new one below.",
                  unavailable: "Accounts aren't available right now. Try again later."}[signin] || "";
    q.delete("signin");
    history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : "") + location.hash);
  }
  refresh().then(() => { if (signin) open(); });
})();

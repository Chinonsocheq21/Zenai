// Add to Home Screen: a row in the Account panel, and once on the welcome
// screen. Android and Chrome offer a native prompt (beforeinstallprompt);
// iPhone Safari has no such API, so it gets the three manual steps instead.
// Hidden once the app is already installed and running standalone.
(function () {
  let deferred = null;
  let installed = false;

  function standalone() {
    try {
      return (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
    } catch (e) { return false; }
  }
  function iosSafari() {
    const ua = navigator.userAgent || "";
    const ios = /iPad|iPhone|iPod/.test(ua) || (ua.indexOf("Macintosh") !== -1 && navigator.maxTouchPoints > 1);
    const webkit = /AppleWebKit/.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/.test(ua);
    return ios && webkit;
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    refreshAll();
  });
  window.addEventListener("appinstalled", function () {
    installed = true; deferred = null; refreshAll();
  });

  function available() { return !installed && !standalone() && (deferred || iosSafari()); }

  const SHARE_IC = '<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="M8 7l4-4 4 4"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>';
  const ADD_IC = '<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M12 8v8M8 12h8"/></svg>';
  const DOT_IC = '<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="4"/></svg>';

  function stepsHtml() {
    return '<ol style="margin:10px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:9px">' +
      '<li style="display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--ink2)">' + SHARE_IC + 'Tap Share in Safari’s toolbar</li>' +
      '<li style="display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--ink2)">' + ADD_IC + 'Choose Add to Home Screen</li>' +
      '<li style="display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--ink2)">' + DOT_IC + 'Tap Add, top right</li>' +
      '</ol>';
  }

  function rowHtml(context) {
    if (!available()) return "";
    const id = "install-" + context;
    if (deferred) {
      return '<div class="row" style="flex-direction:column;align-items:stretch;gap:8px">' +
        '<div><div class="t">Add ZenAI to your home screen</div><div class="s">Open it like any other app, right from your phone.</div></div>' +
        '<button class="alt press" type="button" id="' + id + '">Add to home screen</button></div>';
    }
    return '<div class="row" style="flex-direction:column;align-items:stretch">' +
      '<div class="t">Add ZenAI to your home screen</div><div class="s">Open it like any other app, right from your phone.</div>' +
      stepsHtml() + '</div>';
  }

  async function doInstall() {
    if (!deferred) return;
    const e = deferred; deferred = null;
    try { e.prompt(); await e.userChoice; } catch (err) {}
    refreshAll();
  }

  function wireIn(root) {
    root.querySelectorAll('[id^="install-"]').forEach(function (b) { b.onclick = doInstall; });
  }

  // The Account panel: account.js inserts this after it draws and wires it.
  window.zenaiInstall = {row: function () { return rowHtml("acct"); }, wire: wireIn};

  function drawWelcome() {
    const host = document.getElementById("welcomeInstall");
    if (!host) return;
    const show = available();
    host.classList.toggle("hidden", !show);
    if (!show) { host.innerHTML = ""; return; }
    host.innerHTML = rowHtml("welcome");
    wireIn(host);
  }
  function refreshAll() {
    drawWelcome();
    if (window.zenaiAccount && typeof window.zenaiAccount.redraw === "function") {
      const acct = document.getElementById("acct");
      if (acct && !acct.classList.contains("hidden")) window.zenaiAccount.redraw();
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", drawWelcome);
  else drawWelcome();
})();

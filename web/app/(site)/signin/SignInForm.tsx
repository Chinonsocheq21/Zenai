"use client";

import { useState } from "react";

type State = { kind: "idle" | "sending" | "sent" | "error"; message?: string };

export default function SignInForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setState({ kind: "sending" });
    try {
      const r = await fetch("/api/auth/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const d = await r.json().catch(() => ({}));
      setState(r.ok ? { kind: "sent", message: d.message } : { kind: "error", message: d.detail?.message || "That didn't work. Try again in a minute." });
    } catch {
      setState({ kind: "error", message: "That didn't work. Check your connection and try again." });
    }
  }

  if (state.kind === "sent") {
    return (
      <div role="status" className="rounded-3xl border border-line bg-card p-6">
        <p className="font-semibold">Check your Morgan inbox.</p>
        <p className="mt-2 text-ink2">{state.message}</p>
        <button type="button" onClick={() => setState({ kind: "idle" })} className="mt-4 text-sm font-semibold text-navy hover:underline">
          Use a different address
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="rounded-3xl border border-line bg-card p-6">
      <label htmlFor="email" className="text-sm font-medium text-ink2">Your Morgan email</label>
      <input id="email" type="email" inputMode="email" autoComplete="email" required placeholder="you@morgan.edu"
        value={email} onChange={(e) => setEmail(e.target.value)}
        className="mt-2 h-13 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-base outline-none focus:border-navy" />
      {state.kind === "error" && <p role="alert" className="mt-3 text-sm text-crisis">{state.message}</p>}
      <button type="submit" disabled={state.kind === "sending"}
        className="mt-4 w-full rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2 disabled:opacity-60">
        {state.kind === "sending" ? "Sending..." : "Email me a sign-in link"}
      </button>
    </form>
  );
}

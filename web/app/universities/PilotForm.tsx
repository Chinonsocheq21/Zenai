"use client";

import { useState } from "react";

const FIELDS = [
  { id: "name", label: "Your name", type: "text", auto: "name", required: true },
  { id: "email", label: "Work email", type: "email", auto: "email", required: true },
  { id: "institution", label: "Institution", type: "text", auto: "organization", required: true },
  { id: "role", label: "Your role", type: "text", auto: "organization-title", required: false },
] as const;

const CALM = "Something went wrong on our side and your request didn't go through. Please try again later; your details are still in the form.";

export default function PilotForm() {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    setState("sending");
    try {
      const r = await fetch("/api/pilot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      if (r.ok) return setState("sent");
      const d = await r.json().catch(() => ({}));
      setError(r.status === 422 || r.status === 429 ? d.detail?.message || "Please check the fields and try again." : CALM);
      setState("error");
    } catch {
      setError("We couldn't reach our server. Please check your connection and try again later. Nothing you typed was lost, it's still in the form.");
      setState("error");
    }
  }

  if (state === "sent") {
    return (
      <div role="status" className="rounded-3xl border border-line bg-card p-8 text-center">
        <p className="font-serif text-2xl">Thank you.</p>
        <p className="mt-2 text-ink2">We've received your request.</p>
        <p className="mt-4 text-ink2">What happens next: we'll reply within two business days to the email you gave.</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="grid gap-4 rounded-3xl border border-line bg-card p-6 md:grid-cols-2 md:p-8">
      {FIELDS.map((f) => (
        <div key={f.id}>
          <label htmlFor={f.id} className="text-sm font-medium text-ink2">{f.label}{f.required ? "" : " (optional)"}</label>
          <input id={f.id} name={f.id} type={f.type} autoComplete={f.auto} required={f.required}
            className="mt-1.5 w-full rounded-2xl border border-line bg-paper px-4 py-3 outline-none focus:border-navy" />
        </div>
      ))}
      <div className="md:col-span-2">
        <label htmlFor="message" className="text-sm font-medium text-ink2">What would you like to know? (optional)</label>
        <textarea id="message" name="message" rows={4} maxLength={2000}
          className="mt-1.5 w-full rounded-2xl border border-line bg-paper px-4 py-3 outline-none focus:border-navy" />
      </div>
      <div aria-hidden className="hidden"><label htmlFor="website">Website</label><input id="website" name="website" tabIndex={-1} autoComplete="off" /></div>
      {state === "error" && <p role="alert" className="text-sm text-crisis md:col-span-2">{error}</p>}
      <div className="md:col-span-2">
        <button type="submit" disabled={state === "sending"}
          className="w-full rounded-full bg-navy px-6 py-3.5 font-semibold text-white hover:bg-navy2 disabled:opacity-60 md:w-auto">
          {state === "sending" ? "Sending..." : "Request a pilot"}
        </button>
        <p className="mt-3 text-xs text-muted">We use these details only to reply to you. This form is for staff: students sign in to ZenAI itself with their Morgan email or an invite code, not through this form.</p>
      </div>
    </form>
  );
}

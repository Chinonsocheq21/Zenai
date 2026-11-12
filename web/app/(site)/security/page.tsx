import Link from "next/link";
import { pageMeta } from "@/components/meta";
import NextStep from "@/components/NextStep";

export const metadata = pageMeta(
  "/security/",
  "Security",
  "How ZenAI is hosted and run, what is stored and how, and every subprocessor with what it receives.",
  "ZenAI security and subprocessors",
);

const PRACTICES = [
  ["Hosting", "The website, the app and the API run on Vercel. The API is a serverless function, so there is no long-running server holding conversations."],
  ["Encryption in transit", "Every page and API call is served over HTTPS."],
  ["Redaction first", "Names, email addresses, phone numbers and student ID numbers are removed from each message before the crisis check, the language model or anything else reads it."],
  ["No message storage", "ZenAI's servers do not store messages, replies or conversations, and ZenAI does not write message text to its logs. What a student chooses to keep stays on their own device."],
  ["Hashed tokens and emails", "Email addresses are never stored: an account is found by a keyed hash (HMAC-SHA-256) of the address. Sign-in links and sessions are stored only as SHA-256 hashes, so a leaked table can't be used to sign in or to list who uses ZenAI."],
  ["Short-lived sign-in", "Sign-in is by one-time email link, valid for 15 minutes. Sessions last 30 days and use an httpOnly cookie, marked Secure on the hosted site."],
  ["Anonymous campus counts", "A pilot campus sees weekly totals only, behind a per-campus access code, and any number under 10 is hidden."],
  ["Usage limits", "Per-device and daily limits slow down abuse. Device IDs are hashed before they are used as keys."],
  ["Crisis path without dependencies", "The crisis hand-off to 988 and the counseling center still works when the language model, the database or the usage-limit store is down."],
  ["Open source", "The code, the protocol, the tests and the results are public on GitHub, so reviewers can check every claim on this site."],
];

const SUBPROCESSORS = [
  ["xAI", "Language model that drafts and checks replies", "The redacted message, the recent conversation, and any memory notes the student chose to keep (removing names from notes is being added). Processed under xAI's API terms. ZenAI has not confirmed zero data retention for its xAI account."],
  ["Microsoft (speech service)", "Turns ZenAI's replies into a spoken voice, when voice is used", "The text of ZenAI's reply only. Never the student's message, and never any audio."],
  ["Vercel", "Hosting, serverless functions and cookieless page analytics", "Technical request data such as IP addresses. Analytics receive the page path only, with query strings and fragments removed."],
  ["Neon", "Postgres database for accounts and pilots", "Hashed account keys, hashed sign-in links and sessions, synced check-ins (a day and a level) for students who turned syncing on, weekly campus counts, and pilot requests from staff. No messages."],
  ["Upstash", "Redis store for usage limits", "Counters keyed by a hashed device ID, which expire within about a day. No messages."],
  ["Resend", "Sends sign-in emails", "The email address typed in and the one-time sign-in link, to deliver that email."],
];

export default function Security() {
  return (
    <article className="mx-auto max-w-4xl px-5 pb-10 pt-12">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange">Security</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">How ZenAI is run, and who touches what.</h1>
      <p className="mt-5 max-w-2xl text-lg text-ink2">
        ZenAI is designed to keep almost nothing. This page is for IT and security reviewers. For what this means for
        students, read the <Link href="/privacy/" className="font-semibold text-navy underline">privacy policy</Link>.
      </p>

      <section aria-labelledby="practices" className="mt-12">
        <h2 id="practices" className="font-serif text-3xl">Practices</h2>
        <dl className="mt-6 grid gap-3 sm:grid-cols-2">
          {PRACTICES.map(([t, b]) => (
            <div key={t} className="rounded-3xl border border-line bg-card p-5">
              <dt className="font-semibold">{t}</dt>
              <dd className="mt-1.5 text-[15px] leading-relaxed text-ink2">{b}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="subprocessors" className="mt-14">
        <h2 id="subprocessors" className="font-serif text-3xl">Subprocessors</h2>
        <p className="mt-3 max-w-2xl text-ink2">Every outside service ZenAI uses to run, and exactly what each one receives.</p>
        <div className="mt-6 overflow-x-auto rounded-3xl border border-line bg-card">
          <table className="w-full min-w-[640px] text-left text-[15px]">
            <thead>
              <tr className="border-b border-line">
                <th scope="col" className="px-5 py-3 font-semibold">Service</th>
                <th scope="col" className="px-5 py-3 font-semibold">What it does</th>
                <th scope="col" className="px-5 py-3 font-semibold">What it receives</th>
              </tr>
            </thead>
            <tbody>
              {SUBPROCESSORS.map(([name, does, gets]) => (
                <tr key={name} className="border-b border-line/70 align-top last:border-0">
                  <th scope="row" className="px-5 py-3 font-semibold text-ink">{name}</th>
                  <td className="px-5 py-3 text-ink2">{does}</td>
                  <td className="px-5 py-3 text-ink2">{gets}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="report" className="mt-14">
        <h2 id="report" className="font-serif text-3xl">Reporting a security problem</h2>
        <div className="mt-3 max-w-2xl space-y-3 leading-relaxed text-ink2">
          <p>
            If you find a vulnerability or think student data may be exposed, tell us through the{" "}
            <Link href="/contact/" className="font-semibold text-navy underline">contact page</Link>. Please do not include
            any student's personal information in your report, and give us a chance to fix the problem before you publish
            it.
          </p>
          <p>
            A machine-readable pointer is at{" "}
            <a href="/.well-known/security.txt" className="font-semibold text-navy underline">/.well-known/security.txt</a>.
            Service health is on the <Link href="/status/" className="font-semibold text-navy underline">status page</Link>.
          </p>
        </div>
      </section>
      <NextStep href="/universities/" label="For counseling centers" />
    </article>
  );
}

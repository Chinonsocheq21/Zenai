import Link from "next/link";
import { pageMeta } from "@/components/meta";

export const metadata = pageMeta(
  "/privacy/",
  "Privacy",
  "What ZenAI sees, what it keeps (almost nothing), how long, and who else is involved in running it.",
);

const UPDATED = "November 9, 2026";

const RETENTION = [
  ["Your messages and ZenAI's replies", "Not kept by ZenAI. Used to write the reply, then gone. See the note on xAI below."],
  ["Sign-in links", "15 minutes, and they work once. Stored only as a scrambled hash."],
  ["Signed-in sessions", "30 days, or until you sign out. Stored only as a scrambled hash."],
  ["Usage counters", "About a day. Keyed by a scrambled device ID, no messages."],
  ["Campus counts (pilot campuses)", "Kept as weekly totals. Never text, never who."],
  ["Synced check-ins", "Only if you sign in and turn syncing on. Until you turn it off or delete your account, which removes them."],
  ["Pilot requests from staff", "Until the pilot conversation with that campus ends."],
  ["Anything on your device", "Until you delete it in the app's Privacy screen or clear your browser's data."],
];

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="mt-10">
      <h2 id={id} className="font-serif text-2xl md:text-3xl">{title}</h2>
      <div className="mt-3 space-y-3 leading-relaxed text-ink2">{children}</div>
    </section>
  );
}

export default function Privacy() {
  return (
    <article className="mx-auto max-w-3xl px-5 pb-10 pt-12">
      <p className="inline-block rounded-full border border-orange/40 bg-card px-3 py-1 text-xs font-semibold text-orange">Draft for review · last updated {UPDATED}</p>
      <h1 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">Privacy</h1>
      <p className="mt-4 text-lg text-ink2">
        The short version: ZenAI keeps almost nothing. What you type is used to write a reply and then it is gone, unless
        you turn on a setting that keeps something on your own device. Your university never sees what you write or who
        you are. If your campus runs a pilot, it sees anonymous weekly totals only, and any number under 10 is hidden.
      </p>

      <div className="mt-8 grid gap-3 sm:grid-cols-3">
        {[
          ["Not kept", "ZenAI's servers do not store your messages."],
          ["Off by default", "Memory, check-in history and saved conversations."],
          ["Never sold", "No ads, no selling or renting data, ever."],
        ].map(([t, b]) => (
          <div key={t} className="rounded-3xl border border-line bg-card p-5">
            <p className="font-semibold text-navy">{t}</p>
            <p className="mt-1 text-sm text-ink2">{b}</p>
          </div>
        ))}
      </div>

      <Section id="message" title="What happens to a message">
        <p>
          When you send a message, the ZenAI server first removes names, email addresses, phone numbers and student ID
          numbers from the message. Only that redacted text is used from then on, and ZenAI does not write message text
          to its logs.
        </p>
        <p>
          A crisis check runs on the redacted text. To write and check the reply, the redacted text and the recent
          conversation are sent to our language model provider (see below). The reply comes back to you, and the
          hosted server does not keep the message, the reply or the conversation.
        </p>
      </Section>

      <Section id="device" title="What stays on your device">
        <p>These live in your browser's storage on your own phone or laptop, not on our servers (unless you sign in and turn on check-in syncing, below):</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>A random device ID, used only to apply fair usage limits.</li>
          <li>Your check-ins and the conversation, only if you turn those on in Privacy.</li>
          <li>Notes ZenAI may remember, only if you turn memory on. These are sent with your messages so ZenAI can use them, and are not kept on the server.</li>
        </ul>
        <p>
          Saved memory notes are sent to our language model provider along with your message. Today, names and numbers are
          removed from the message itself but not yet from saved notes; removing them from notes too is being added. Until
          then, keep names and contact details out of anything you ask ZenAI to remember.
        </p>
        <p>One tap in the app's Privacy screen deletes all of it. Clearing your browser's data does too.</p>
      </Section>

      <Section id="account" title="If you sign in">
        <p>
          Signing in is optional, and nothing in chat or a crisis hand-off needs it. You sign in with a one-time link sent
          to your Morgan email. ZenAI does not store your email address: it keeps only a keyed, scrambled version of it, so
          the account list can't be turned back into a list of who uses ZenAI. Sign-in links and sessions are stored only as
          scrambled hashes too.
        </p>
        <p>
          If you turn on check-in syncing, your check-ins are stored with your account as a day and a level, so they follow
          you between phone and laptop. Never a message, never a reply. Turning syncing off removes what was synced, and
          deleting your account in the app removes the account and everything synced to it.
        </p>
      </Section>

      <Section id="campus" title="Campus pilots">
        <p>
          When a campus runs a pilot, its counseling center can see a dashboard of anonymous weekly counts from the student
          app, for that campus only:
        </p>
        <ul className="list-disc space-y-1 pl-5">
          <li>How many messages were sent and how many conversations were started.</li>
          <li>How many crisis hand-offs happened.</li>
          <li>The check-in level conversations started with ("Light" to "I'm not okay").</li>
          <li>Which focus answered (for example Academic Stress or Stress-Relief).</li>
        </ul>
        <p>
          Counts are by week only, never by a finer time. Any number under 10 is hidden, so a small group can't be picked
          out. The dashboard never shows anyone's words, name, email or account, or whether a particular student uses
          ZenAI. Students who are not signed in are counted together under "open", not under any campus.
        </p>
      </Section>

      <Section id="voice" title="Voice">
        <p>
          If you talk instead of type, your browser's own speech service (Apple's or Google's, depending on your device)
          turns your voice into text. ZenAI only ever receives the text and never receives or keeps audio. When ZenAI
          speaks, the text of its reply is sent to a speech service to turn it into audio.
        </p>
      </Section>

      <Section id="others" title="Who else is involved">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <b className="text-ink">xAI</b> provides the language model that drafts and checks replies. It receives the
            redacted message, the recent conversation and any saved memory notes, and processes them under xAI's API terms.
            Those terms allow xAI to keep API requests for a period for its own safety checks. ZenAI has not confirmed that
            zero data retention is turned on for its xAI account, so assume xAI may keep this redacted text for a time.
          </li>
          <li><b className="text-ink">Microsoft</b> speech service turns ZenAI's replies into a voice, when you use voice.</li>
          <li><b className="text-ink">Vercel</b> hosts the website and app. Like any host, it processes technical request data such as IP addresses. Its Web Analytics counts page views without cookies; we cut each address down to the page's path first, so nothing you typed is ever part of it.</li>
          <li><b className="text-ink">Upstash</b> stores usage counters keyed by a scrambled version of your device ID. They expire within about a day and contain no messages.</li>
          <li><b className="text-ink">Neon</b> hosts ZenAI's database: scrambled account keys, hashed sign-in links and sessions, synced check-ins if you turned syncing on, campus weekly counts, and pilot requests from staff. No messages.</li>
          <li><b className="text-ink">Resend</b> sends sign-in emails. It receives the address you typed and the sign-in link, to deliver that one email.</li>
        </ul>
      </Section>

      <Section id="feedback" title="Feedback">
        <p>
          If you turn on sharing in Privacy and tap "Did this help?", we may record your yes or no, which kind of focus
          was used, and ZenAI's reply. Never your message. On the hosted service these answers are not stored yet.
        </p>
      </Section>

      <Section id="university" title="Morgan State University">
        <p>
          ZenAI is a student capstone project. It does not share anything you type, or whether you use ZenAI, with the
          university, your professors or the Counseling Center. If Morgan runs a pilot, the Counseling Center sees only
          the anonymous weekly counts described under Campus pilots. When ZenAI shows the Counseling Center during a hand-off,
          it only shows you how to reach them. It does not contact anyone for you.
        </p>
      </Section>

      <Section id="retention" title="How long things are kept">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[15px]">
            <thead>
              <tr className="border-b border-line text-ink"><th scope="col" className="py-2 pr-4 font-semibold">What</th><th scope="col" className="py-2 font-semibold">How long</th></tr>
            </thead>
            <tbody>
              {RETENTION.map(([what, how]) => (
                <tr key={what} className="border-b border-line/70 align-top"><td className="py-2 pr-4 text-ink">{what}</td><td className="py-2">{how}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="ferpa" title="FERPA and education records">
        <p>
          ZenAI does not receive education records from any university: no grades, transcripts, schedules, student
          directory data or records from the counseling center. Universities do not send ZenAI anything about students. A
          campus in a pilot receives only the anonymous weekly counts described above. This position has not yet been
          reviewed by a lawyer.
        </p>
      </Section>

      <Section id="safety" title="A note on safety">
        <p>
          ZenAI is not an emergency service and cannot send help. If you are in danger, call or text 988, or call 911.{" "}
          <Link href="/help/" className="font-semibold text-crisis underline">Get help now</Link>.
        </p>
      </Section>

      <Section id="contact" title="Questions">
        <p>
          ZenAI is open source. Questions about this policy can be raised on the project's{" "}
          <a href="https://github.com/Chinonsocheq21/Zenai/issues" className="font-semibold text-navy underline">GitHub page</a>.
          See <Link href="/contact/" className="font-semibold text-navy underline">Contact</Link> for other ways to reach us, and{" "}
          <Link href="/security/" className="font-semibold text-navy underline">Security</Link> for how ZenAI is run.
          This policy is a draft and will be reviewed before ZenAI is offered to students beyond testing.
        </p>
      </Section>
    </article>
  );
}

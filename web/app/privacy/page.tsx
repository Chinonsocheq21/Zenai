import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy",
  description: "What ZenAI sees, what it keeps (almost nothing), and who else is involved in running it.",
};

const UPDATED = "November 6, 2026";

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
      <p className="inline-block rounded-full bg-orange/15 px-3 py-1 text-xs font-semibold text-orange">Draft for review · last updated {UPDATED}</p>
      <h1 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">Privacy</h1>
      <p className="mt-4 text-lg text-ink2">
        The short version: ZenAI keeps almost nothing. What you type is used to write a reply and then it is gone, unless
        you turn on a setting that keeps something on your own device. Nothing is shared with Morgan State University.
      </p>

      <div className="mt-8 grid gap-3 sm:grid-cols-3">
        {[
          ["Not kept", "Your messages are not stored on our servers."],
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
          numbers. Only that redacted text is used from then on.
        </p>
        <p>
          A crisis check runs on the redacted text. To write and check the reply, the redacted text and the recent
          conversation are sent to our language model provider (see below). The reply comes back to you, and the
          hosted server does not keep the message, the reply or the conversation.
        </p>
      </Section>

      <Section id="device" title="What stays on your device">
        <p>These live in your browser's storage on your own phone or laptop, never on our servers:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>A random device ID, used only to apply fair usage limits.</li>
          <li>Your check-ins and the conversation, only if you turn those on in Privacy.</li>
          <li>Notes ZenAI may remember, only if you turn memory on. These are sent with your messages so ZenAI can use them, and are not kept on the server.</li>
        </ul>
        <p>One tap in the app's Privacy screen deletes all of it. Clearing your browser's data does too.</p>
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
          <li><b className="text-ink">xAI</b> provides the language model that drafts and checks replies. It receives redacted text, under xAI's API terms.</li>
          <li><b className="text-ink">Microsoft</b> speech service turns ZenAI's replies into a voice, when you use voice.</li>
          <li><b className="text-ink">Vercel</b> hosts the website and app. Like any host, it processes technical request data such as IP addresses.</li>
          <li><b className="text-ink">Upstash</b> stores usage counters keyed by a scrambled version of your device ID. They expire within about a day and contain no messages.</li>
        </ul>
      </Section>

      <Section id="feedback" title="Feedback">
        <p>
          If you turn on sharing in Privacy and tap "Did this help?", we may record your yes or no, which kind of focus
          was used, and ZenAI's reply. Never your message.
        </p>
      </Section>

      <Section id="university" title="Morgan State University">
        <p>
          ZenAI is a student capstone project. It does not share anything you type, or whether you use ZenAI, with the
          university, your professors or the Counseling Center. When ZenAI shows the Counseling Center during a hand-off,
          it only shows you how to reach them. It does not contact anyone for you.
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
          This policy is a draft and will be reviewed before ZenAI is offered to students beyond testing.
        </p>
      </Section>
    </article>
  );
}

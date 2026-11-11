import type { Metadata } from "next";
import Link from "next/link";
import Orb from "@/components/Orb";
import SignInForm from "./SignInForm";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Optional: sign in with your Morgan email so your check-ins follow you between phone and laptop.",
};

export default function SignIn() {
  return (
    <div className="mx-auto max-w-md px-5 pb-10 pt-14">
      <div className="flex justify-center"><Orb size={72} /></div>
      <h1 className="mt-6 text-center font-serif text-4xl">Sign in</h1>
      <p className="mt-3 text-center text-ink2">
        Sign in with your Morgan email, or an invite code if you have one. Your check-ins follow you between your phone
        and laptop.
      </p>
      <div className="mt-8"><SignInForm /></div>
      <ul className="mt-6 space-y-2 text-sm text-ink2">
        <li>No password. We email a link that works once, for 15 minutes.</li>
        <li>ZenAI never stores your email address, only a scrambled code that recognizes it.</li>
        <li>Delete your account any time from the app.</li>
      </ul>
      <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm">
        <a href="/app/" className="font-semibold text-navy hover:underline">Open ZenAI</a>
        <Link href="/privacy/" className="text-ink2 hover:underline">Privacy</Link>
      </div>
    </div>
  );
}
